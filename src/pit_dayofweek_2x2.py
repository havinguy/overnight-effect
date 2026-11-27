"""Step 4: 2x2 day-of-week overnight decomposition (Level B filters): {current-30, point-in-time} x {equal-weight, FF-cap-weight}.
Nights = ordinary one-day nights (gap==1) per stock; drop open_suspicious and |overnight log return|>7%.
Cap-weights: p(t-1 close) * index shares * free-float * capping factor c (c refreshed on the quarterly schedule, price recomputed daily)."""
import sys; sys.path.insert(0, "src")
from pathlib import Path
import numpy as np, pandas as pd
import pit_reconstruct as P
from level_a import RAW_DIR, decompose
NAMES = {1: "Mon->Tue", 2: "Tue->Wed", 3: "Wed->Thu", 4: "Thu->Fri"}   # keyed by weekday of the OPEN date
M = pd.read_csv("data/vn30_pit_membership.csv", parse_dates=["effective_date"])
SG = pd.read_csv("data/vn30_sector_groups.csv").fillna("").set_index("ticker")
cur30 = (RAW_DIR.parent / "universe_vn30.txt").read_text().split()
tickers = sorted(set(cur30) | set(M.ticker))
START = pd.Timestamp("2018-11-21")

# ---------- per-stock panel ----------
RET, PC, CL = {}, {}, {}
for t in tickers:
    # 2018-11-21 first-night fix (2026-11-27): gap / prior close taken from the RAW series BEFORE decompose() drops row 0
    raw = pd.read_csv(RAW_DIR / f"{t}.csv", parse_dates=["date"]).sort_values("date").reset_index(drop=True)
    raw["gap"] = raw["date"].diff().dt.days; raw["prev_close"] = raw["close"].shift(1)
    d = decompose(raw)
    gap = d["gap"]
    flag = d["open_suspicious"].astype(bool) | (d["r_overnight"].abs() > 0.07)
    ok = (gap == 1) & ~flag
    d = d.set_index("date")
    RET[t] = d["r_overnight"].where(ok.values)
    PC[t] = d["prev_close"]                     # raw prior close (was d.close.shift(1) after the drop: NaN on the first night)
    CL[t] = d["close"]
RET, PC = pd.DataFrame(RET).sort_index(), pd.DataFrame(PC).sort_index()
RET = RET.loc[START:]; PC = PC.reindex(RET.index)
px = P.load_close()

# ---------- reference table for names not in the PIT basket on a date ----------
allsh = pd.read_csv("data/raw_pdf/ref_allshare.csv").rename(columns={"ref_date": "effective_date"})
refs = pd.concat([M[M.source != "interp"][["ticker", "effective_date", "shares", "free_float"]],
                  allsh[["ticker", "effective_date", "shares", "free_float"]].assign(effective_date=lambda x: pd.to_datetime(x.effective_date))]).sort_values(["ticker", "effective_date"])
def sf_ref(tk, d):
    r = refs[refs.ticker == tk].drop_duplicates("effective_date", keep="last")
    if r.empty: return None
    x = np.interp(d.toordinal(), r.effective_date.map(pd.Timestamp.toordinal).values.astype(float), r.shares.values.astype(float))
    f = np.interp(d.toordinal(), r.effective_date.map(pd.Timestamp.toordinal).values.astype(float), r.free_float.values.astype(float))
    return x, (round(f) if f < 15 else 5 * round(f / 5))
last_sh = M.sort_values("effective_date").groupby("ticker").shares.last()
eff_dates = sorted(M.effective_date.unique())

def build_weights(basket, variant):
    """returns {effective_date: Series(s*f*c)} ; basket in {'pit','cur30'}"""
    out = {}
    for d in eff_dates:
        g = M[M.effective_date == d].set_index("ticker")
        names = list(g.index) if basket == "pit" else cur30
        co = P.cap_date(d); pco = px.loc[:co].ffill().iloc[-1]
        sh, ff = {}, {}
        for tk in names:
            if tk in g.index: sh[tk], ff[tk] = g.shares[tk], g.free_float[tk]
            else:
                r = sf_ref(tk, d)
                if r is None: continue
                sh[tk], ff[tk] = r
        names = [tk for tk in names if tk in sh and pd.notna(pco.get(tk, np.nan)) and (tk in px.columns) and px[tk].first_valid_index() <= co]
        if not names: continue
        if variant == "B": sh = {tk: last_sh.get(tk, sh[tk]) for tk in names}
        m = np.array([pco[tk] * sh[tk] * ff[tk] / 100 for tk in names])
        c = P.cap_factors(m, names, [SG.related_group.get(t, "") for t in names], None)
        out[d] = pd.Series([sh[tk] * ff[tk] / 100 * ci for tk, ci in zip(names, c)], index=names)
    return out

def levelb_ew():
    r = RET[cur30]; k = r.notna().sum(axis=1); s = pd.DataFrame({"r": r.mean(axis=1), "k": k})[k >= 10]; s["wd"] = s.index.weekday
    return s

def cell_series(basket, scheme, variant="B"):
    W = build_weights(basket, variant); ed = sorted(W)
    res = {}
    for t in RET.index:
        e = [x for x in ed if x <= t]
        if not e: continue
        w = W[e[-1]]; r = RET.loc[t, w.index]; p = PC.loc[t, w.index]
        ww = (np.ones(len(w)) if scheme == "ew" else (w * p).values)
        v = r.notna().values & (pd.notna(ww))
        if v.sum() < 10: continue
        res[t] = (np.sum(ww[v] * r.values[v]) / ww[v].sum(), int(v.sum()))
    s = pd.DataFrame(res, index=["r", "k"]).T; s["wd"] = s.index.weekday
    return s

def table(s, label, cell, variant):
    yrs = (s.index[-1] - s.index[0]).days / 365.25; rows = []
    for wd, nm in NAMES.items():
        x = s[s.wd == wd].r
        rows.append(dict(cell=cell, variant=variant, sample=label, night=nm, n=len(x), mean_bp=x.mean() * 1e4, sharpe_own=x.mean() / x.std() * np.sqrt(len(x) / yrs),
                         t=x.mean() / (x.std() / np.sqrt(len(x))), hit_pct=(x > 0).mean() * 100))
    mt, wt = s[s.wd.isin([1, 2])].r, s[s.wd.isin([3, 4])].r
    wl = (mt.mean() - wt.mean()) / np.sqrt(mt.var() / len(mt) + wt.var() / len(wt))
    rows.append(dict(cell=cell, variant=variant, sample=label, night="Mon+Tue minus Wed+Thu", n=len(mt) + len(wt), mean_bp=(mt.mean() - wt.mean()) * 1e4, t=wl))
    return rows

if __name__ == "__main__":
    cells = {}
    for basket in ("cur30", "pit"):
        ew = cell_series(basket, "ew")
        if basket == "cur30": cells[("cur30", "ew_levelB", "B")] = cells[("cur30", "ew_levelB", "A")] = levelb_ew()
        for variant in ("A", "B"):
            cells[(basket, "ew", variant)] = ew
            cells[(basket, "cap", variant)] = cell_series(basket, "cap", variant)
    rows = []
    for (b, s, v), ser in cells.items():
        rows += table(ser, "2018-11..2026-11", f"{b}_{s}", v)
    T = pd.DataFrame(rows)
    # effects (paired by date)
    eff = []
    for v in ("A", "B"):
        def paired(a, b, label):
            j = pd.concat([cells[a].r, cells[b].r], axis=1, join="inner").dropna(); j.columns = ["x", "y"]; j["d"] = j.x - j.y; j["wd"] = j.index.weekday
            for wd, nm in NAMES.items():
                dd = j[j.wd == wd].d; eff.append(dict(variant=v, effect=label, night=nm, n=len(dd), diff_bp=dd.mean() * 1e4, paired_t=dd.mean() / (dd.std() / np.sqrt(len(dd)))))
        paired(("pit", "ew", v), ("cur30", "ew_levelB", v), "composition (PIT - current30 Level B), equal-weight")
        paired(("pit", "cap", v), ("cur30", "cap", v), "composition (PIT - current30), cap-weight")
        paired(("cur30", "cap", v), ("cur30", "ew", v), "weighting (cap - EW), current30")
        paired(("pit", "cap", v), ("pit", "ew", v), "weighting (cap - EW), PIT")
        paired(("pit", "cap", v), ("cur30", "ew_levelB", v), "total (PIT cap - current30 Level B EW)")
    E = pd.DataFrame(eff)
    pd.to_pickle(cells, "results/_pit_cells.pkl")
    T.to_csv("results/pit_dayofweek_2x2.csv", index=False); E.to_csv("results/pit_dayofweek_effects.csv", index=False)
    pd.set_option("display.width", 220, "display.float_format", "{:.2f}".format)
    for v in ("B", "A"):
        print(f"\n===== variant {v} ({'latest shares' if v=='B' else 'PIT shares'}) : mean overnight bp / t =====")
        piv = T[(T.variant == v)].pivot(index="night", columns="cell", values="mean_bp").reindex(list(NAMES.values()) + ["Mon+Tue minus Wed+Thu"])
        pt = T[(T.variant == v)].pivot(index="night", columns="cell", values="t").reindex(list(NAMES.values()) + ["Mon+Tue minus Wed+Thu"])
        print(piv[["cur30_ew_levelB", "cur30_ew", "cur30_cap", "pit_ew", "pit_cap"]].to_string()); print("t:"); print(pt[["cur30_ew_levelB", "cur30_ew", "cur30_cap", "pit_ew", "pit_cap"]].to_string())
        print("Sharpe(own-freq):"); print(T[(T.variant == v) & T.sharpe_own.notna()].pivot(index="night", columns="cell", values="sharpe_own")[["cur30_ew_levelB", "cur30_ew", "cur30_cap", "pit_ew", "pit_cap"]].to_string())
        print("effects:"); print(E[E.variant == v].pivot(index="effect", columns="night", values="diff_bp")[list(NAMES.values())].to_string())
        print("paired t:"); print(E[E.variant == v].pivot(index="effect", columns="night", values="paired_t")[list(NAMES.values())].to_string())
