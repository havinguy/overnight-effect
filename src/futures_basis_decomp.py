"""Decompose VN30F1M overnight into VN30 index overnight + overnight basis change. MEASUREMENT ONLY.

  b_t        = ln F_t - ln I_t
  fut_ON_T   = ln F_open_T - ln F_entry_{T-1}       (F_entry = F1M close, or F2M close on roll nights: level_c_futures.build)
  idx_ON_T   = ln I_open_T - ln I_close_{T-1}
  dbasis_ON  = [ln F_open_T - ln I_open_T] - [ln F_entry_{T-1} - ln I_close_{T-1}]   (identity: fut_ON = idx_ON + dbasis_ON)
  intraday analogue: fut_ID = ln F_close_T - ln F_open_T, idx_ID likewise, dbasis_ID = fut_ID - idx_ID.
Log returns throughout (the gate also reports the simple-return figures build() uses). One observation per date;
Newey-West t with 5 lags. Nights are assigned to the open date T; weekday label = weekday of the entry close.
Usage: python3 src/futures_basis_decomp.py [--gate]
"""
from __future__ import annotations
import argparse, math, sys, warnings
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from level_a import RAW_DIR, OUT_DIR, decompose
from level_c_futures import build, roll_days

CUTOVER = pd.Timestamp("2022-08-25")
LAGS = 5
OUT = OUT_DIR
NIGHT = {0: "Mon->Tue", 1: "Tue->Wed", 2: "Wed->Thu", 3: "Thu->Fri"}
ORDER = list(NIGHT.values()) + ["Fri->Mon (weekend)", "holiday"]


# ------------------------------------------------------------------ helpers
def nw_t(x, L=LAGS):
    x = pd.Series(x).dropna().values.astype(float); n = len(x)
    if n < 3: return np.nan
    u = x - x.mean(); lrv = u @ u / n
    for l in range(1, min(L, n - 1) + 1): lrv += 2 * (1 - l / (L + 1)) * (u[l:] @ u[:-l]) / n
    return x.mean() / math.sqrt(lrv / n) if lrv > 0 else np.nan


def ols_nw(y, x, L=LAGS):
    """y = a + b x; returns slope, NW SE of slope, R^2."""
    j = pd.concat([y, x], axis=1).dropna(); Y, Xv = j.iloc[:, 0].values, j.iloc[:, 1].values; n = len(Y)
    if n < 10: return np.nan, np.nan, np.nan
    Xm = np.column_stack([np.ones(n), Xv]); XtXi = np.linalg.inv(Xm.T @ Xm); b = XtXi @ Xm.T @ Y; u = Y - Xm @ b; g = Xm * u[:, None]
    S = g.T @ g
    for l in range(1, L + 1): G = g[l:].T @ g[:-l]; S += (1 - l / (L + 1)) * (G + G.T)
    V = XtXi @ S @ XtXi
    return b[1], math.sqrt(V[1, 1]), 1 - (u @ u) / ((Y - Y.mean()) @ (Y - Y.mean()))


def mstat(x):
    x = pd.Series(x).dropna(); return dict(n=len(x), mean_bp=x.mean() * 1e4 if len(x) else np.nan, nw_t=nw_t(x))


def futures_nights() -> pd.DataFrame:
    """level_c_futures.build (gross, roll-fixed), plus log legs, night labels, expiry calendar."""
    d = build(0, 0.0)
    from data_cap import futures_csv
    f1 = pd.read_csv(futures_csv("VN30F1M"), parse_dates=["date"]).set_index("date")
    d["high"], d["low"], d["volume"] = f1["high"].reindex(d.index), f1["low"].reindex(d.index), f1["volume"].reindex(d.index)
    d["prev_date"] = d.index.to_series().shift(1)
    d.loc[d.index[0], "prev_date"] = f1.index[f1.index < d.index[0]].max()
    d["fut_ON"] = np.log(d["open"] / d["entry"])                 # NaN on uninvested roll nights (no F2M)
    d["fut_ID"] = np.log(d["close"] / d["open"])
    d["fut_ON_simple"] = (d["open"] / d["entry"] - 1).where(d["invested"])
    ew = d["prev_date"].dt.weekday
    d["night"] = np.where(d["hold_type"] == "", ew.map(NIGHT), np.where(d["hold_type"] == "weekend", "Fri->Mon (weekend)", "holiday"))
    d["entry_weekday"] = ew
    # expiry calendar: expiry = last trading day before each roll day; days-to-expiry (trading days) for the contract held at T
    allf = f1.index
    rolls = roll_days(allf); exp = pd.DatetimeIndex([allf[allf < r].max() for r in rolls])
    pos = pd.Series(np.arange(len(allf)), index=allf)
    nxt = np.searchsorted(exp.values, d.index.values, side="left")
    d["expiry"] = [exp[i] if i < len(exp) else pd.NaT for i in nxt]
    d["dte"] = [pos[e] - pos[t] if pd.notna(e) else np.nan for t, e in zip(d.index, d["expiry"])]
    # nights near expiry: open date within expiry-1 .. expiry+1 (expiry+1 = roll day)
    near = set()
    for e in exp:
        if e in pos.index:
            for k in (-1, 0, 1):
                p = pos[e] + k
                if 0 <= p < len(allf): near.add(allf[p])
    d["near_expiry"] = d.index.isin(list(near))
    return d


def index_nights() -> pd.DataFrame:
    v = decompose(pd.read_csv(RAW_DIR / "VN30.csv", parse_dates=["date"]))   # all nights (Level A convention)
    v["prev_date"] = v["date"].shift(1)
    v["prev_close"] = v["close"].shift(1)
    return v.set_index("date").rename(columns={"r_overnight": "idx_ON", "r_intraday": "idx_ID", "open_suspicious": "idx_flag"})


def panel() -> pd.DataFrame:
    f, i = futures_nights(), index_nights()
    j = f.join(i[["open", "close", "prev_close", "prev_date", "idx_ON", "idx_ID", "idx_flag"]], how="inner", rsuffix="_idx")
    j = j[j["invested"] & j["idx_ON"].notna()]
    j["aligned"] = j["prev_date"] == j["prev_date_idx"]             # both legs start from the same prior trading day
    j["b_open"] = np.log(j["open"] / j["open_idx"])
    j["b_prevclose"] = np.log(j["entry"] / j["prev_close"])        # F2M prior close on roll nights, as in build()
    j["b_close"] = np.log(j["close"] / j["close_idx"])
    j["dbasis_ON"] = j["b_open"] - j["b_prevclose"]
    j["dbasis_ID"] = j["fut_ID"] - j["idx_ID"]
    res = (j["fut_ON"] - j["idx_ON"] - j["dbasis_ON"]).abs().max()
    assert res < 1e-10, f"identity residual {res}"
    j.attrs["identity_residual"] = float(res)
    return j


# ------------------------------------------------------------------ Step 0
def gate() -> pd.DataFrame:
    d = futures_nights(); inv = d[d["invested"]]
    v = index_nights(); v = v[v.index >= "2018-11-21"]
    rows = [dict(item="futures gross ON, all invested nights (simple)", target=4.99, ours=inv["fut_ON_simple"].mean() * 1e4,
                 note=f"n {len(inv)} nights ({len(d)} nights from {len(d)+1} bars; the file has {len(d)+2} lines incl. header); log mean {inv['fut_ON'].mean()*1e4:.2f} bp"),
            dict(item="futures gross Mon->Tue (simple, non-hold)", target=10.6, ours=inv.loc[inv["night"] == "Mon->Tue", "fut_ON_simple"].mean() * 1e4,
                 note=f"n {(inv['night']=='Mon->Tue').sum()}; log {inv.loc[inv['night']=='Mon->Tue','fut_ON'].mean()*1e4:.2f} bp")]
    tgt = {2017: 9.4, 2018: 2.4, 2019: 4.1, 2020: 7.4, 2021: 8.2, 2022: 1.2, 2023: 5.0, 2024: 3.7, 2025: 6.6, 2026: 4.5}
    by = inv.groupby(inv.index.year)["fut_ON_simple"].mean() * 1e4
    for y, t in tgt.items(): rows.append(dict(item=f"futures gross {y} (simple)", target=t, ours=by.get(y, np.nan), note=""))
    pre, post = v[v.index < CUTOVER]["idx_ON"], v[v.index >= CUTOVER]["idx_ON"]
    from math import sqrt
    pt = lambda x: x.mean() / (x.std() / sqrt(len(x)))
    rows += [dict(item="VN30 index ON pre 2022-08-25 (log, all nights, from 2018-11-21)", target=0.89, ours=pre.mean() * 1e4, note=f"plain t {pt(pre):.2f} (target 0.70); NW t {nw_t(pre):.2f}"),
             dict(item="VN30 index ON post 2022-08-25", target=9.99, ours=post.mean() * 1e4, note=f"plain t {pt(post):.2f} (target 6.42); NW t {nw_t(post):.2f}")]
    ti = {2018: -10.1, 2019: 0.0, 2020: -1.3, 2021: 5.9, 2022: -2.5, 2023: 9.9, 2024: 8.8, 2025: 16.6, 2026: 10.8}
    byi = v.groupby(v.index.year)["idx_ON"].mean() * 1e4
    for y, t in ti.items(): rows.append(dict(item=f"VN30 index ON {y}", target=t, ours=byi.get(y, np.nan), note=""))
    G = pd.DataFrame(rows); G["diff"] = G["ours"] - G["target"]
    tol = np.where(G["item"].str.contains("all invested|Mon->Tue|pre|post"), 0.05, 0.1)
    G["pass"] = G["diff"].abs() <= tol + 1e-9
    return G


# ------------------------------------------------------------------ tables
def yearly(j: pd.DataFrame, futonly: pd.DataFrame | None = None) -> pd.DataFrame:
    rows = []
    for y, g in j.groupby(j.index.year):
        sl, se, r2 = ols_nw(g["fut_ON"], g["idx_ON"])
        rows.append(dict(year=y, n=len(g), fut_ON_bp=g.fut_ON.mean() * 1e4, fut_t=nw_t(g.fut_ON), idx_ON_bp=g.idx_ON.mean() * 1e4, idx_t=nw_t(g.idx_ON),
                         dbasis_ON_bp=g.dbasis_ON.mean() * 1e4, dbasis_t=nw_t(g.dbasis_ON), corr=g.fut_ON.corr(g.idx_ON), slope=sl, slope_nw_se=se, r2=r2,
                         dbasis_ID_bp=g.dbasis_ID.mean() * 1e4, dbasis_ID_t=nw_t(g.dbasis_ID), idx_flag_pct=g.idx_flag.mean() * 100))
    sl, se, r2 = ols_nw(j["fut_ON"], j["idx_ON"])
    rows.append(dict(year="all", n=len(j), fut_ON_bp=j.fut_ON.mean() * 1e4, fut_t=nw_t(j.fut_ON), idx_ON_bp=j.idx_ON.mean() * 1e4, idx_t=nw_t(j.idx_ON),
                     dbasis_ON_bp=j.dbasis_ON.mean() * 1e4, dbasis_t=nw_t(j.dbasis_ON), corr=j.fut_ON.corr(j.idx_ON), slope=sl, slope_nw_se=se, r2=r2,
                     dbasis_ID_bp=j.dbasis_ID.mean() * 1e4, dbasis_ID_t=nw_t(j.dbasis_ID), idx_flag_pct=j.idx_flag.mean() * 100))
    out = pd.DataFrame(rows)
    if futonly is not None:
        fo = futonly[futonly.index < j.index.min()]
        for y, g in fo.groupby(fo.index.year):
            out = pd.concat([pd.DataFrame([dict(year=f"{y} (futures only, before index data)", n=len(g), fut_ON_bp=g.fut_ON.mean() * 1e4, fut_t=nw_t(g.fut_ON))]), out], ignore_index=True)
    return out


def periods(j):
    return {"full (index sample)": j, "pre 2022-08-25": j[j.index < CUTOVER], "post 2022-08-25": j[j.index >= CUTOVER], "2026 only": j[j.index.year == 2026]}


def weekday(j: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for per, g0 in periods(j).items():
        for nm in ORDER:
            g = g0[g0.night == nm]
            if len(g) < 3: continue
            rows.append(dict(period=per, night=nm, n=len(g), fut_ON_bp=g.fut_ON.mean() * 1e4, fut_t=nw_t(g.fut_ON), idx_ON_bp=g.idx_ON.mean() * 1e4,
                             idx_t=nw_t(g.idx_ON), dbasis_ON_bp=g.dbasis_ON.mean() * 1e4, dbasis_t=nw_t(g.dbasis_ON),
                             dbasis_ID_bp=g.dbasis_ID.mean() * 1e4, dbasis_ID_t=nw_t(g.dbasis_ID)))
    return pd.DataFrame(rows)


def monday(j: pd.DataFrame, fut_all: pd.DataFrame) -> pd.DataFrame:
    P = {"full (index sample, 2018-11..2026)": (j.index.min(), "2026-12-31"), "2017-21 where index exists (2018-11..2021)": (j.index.min(), "2021-12-31"),
         "2022-25": ("2022-01-01", "2025-12-31"), "2026": ("2026-01-01", "2026-12-31")}
    rows = []
    m = j[j.night == "Mon->Tue"]
    for per, (a, b) in P.items():
        g = m[(m.index >= a) & (m.index <= b)]
        f = g.fut_ON.mean()
        rows.append(dict(period=per, n=len(g), fut_ON_bp=f * 1e4, fut_t=nw_t(g.fut_ON), idx_part_bp=g.idx_ON.mean() * 1e4, idx_t=nw_t(g.idx_ON),
                         dbasis_part_bp=g.dbasis_ON.mean() * 1e4, dbasis_t=nw_t(g.dbasis_ON),
                         dbasis_share_pct=100 * g.dbasis_ON.mean() / f if f else np.nan))
    fm = fut_all[(fut_all.night == "Mon->Tue") & fut_all.invested]
    for per, (a, b) in {"reference: futures-only Option B full 2017-26": ("2017-01-01", "2026-12-31"), "reference: futures-only 2017-21": ("2017-01-01", "2021-12-31")}.items():
        g = fm[(fm.index >= a) & (fm.index <= b)]
        rows.append(dict(period=per, n=len(g), fut_ON_bp=g.fut_ON.mean() * 1e4, fut_t=nw_t(g.fut_ON)))
    return pd.DataFrame(rows)


def pit_basket():
    """PIT cap-weighted stock basket overnight, one-day nights, filters OFF (open_filter_audit version c)."""
    import open_filter_audit as OA
    R = OA.ret_panel(False, False)
    return OA.with_ret(R, lambda: OA.X.cell_series("pit", "cap", "B")).r


def wednesday(j: pd.DataFrame, basket: pd.Series | None) -> pd.DataFrame:
    rows = []
    for per, g0 in periods(j).items():
        g = g0[g0.night == "Wed->Thu"]
        gap = g.idx_ON - g.fut_ON
        r = dict(period=per, n=len(g), idx_ON_bp=g.idx_ON.mean() * 1e4, fut_ON_bp=g.fut_ON.mean() * 1e4, idx_minus_fut_bp=gap.mean() * 1e4, idx_minus_fut_t=nw_t(gap),
                 minus_dbasis_ON_bp=-g.dbasis_ON.mean() * 1e4, dbasis_ON_bp=g.dbasis_ON.mean() * 1e4, dbasis_t=nw_t(g.dbasis_ON))
        if basket is not None:
            k = pd.concat({"bas": basket, "idx": g.idx_ON, "fut": g.fut_ON, "db": g.dbasis_ON}, axis=1, join="inner").dropna()
            r.update(n_with_basket=len(k), basket_minus_fut_bp=(k.bas - k.fut).mean() * 1e4, basket_minus_fut_t=nw_t(k.bas - k.fut),
                     basket_minus_idx_bp=(k.bas - k.idx).mean() * 1e4, basket_minus_idx_t=nw_t(k.bas - k.idx),
                     minus_dbasis_on_basket_dates_bp=-k.db.mean() * 1e4)
        rows.append(r)
    return pd.DataFrame(rows)


def expiry(j: pd.DataFrame) -> pd.DataFrame:
    rows = []
    b = pd.cut(j.dte, [-1, 5, 10, 15, 1e9], labels=["0-5", "6-10", "11-15", "16+"])
    for nm, g in j.groupby(b):
        rows.append(dict(cut="days-to-expiry", group=str(nm), n=len(g), b_close_mean_bp=g.b_close.mean() * 1e4, b_close_sd_bp=g.b_close.std() * 1e4,
                         dbasis_ON_bp=g.dbasis_ON.mean() * 1e4, dbasis_ON_t=nw_t(g.dbasis_ON), dbasis_ID_bp=g.dbasis_ID.mean() * 1e4, dbasis_ID_t=nw_t(g.dbasis_ID)))
    for nm in ORDER:
        g = j[j.night == nm]
        rows.append(dict(cut="night (entry weekday)", group=nm, n=len(g), b_close_mean_bp=g.b_close.mean() * 1e4, b_close_sd_bp=g.b_close.std() * 1e4,
                         dbasis_ON_bp=g.dbasis_ON.mean() * 1e4, dbasis_ON_t=nw_t(g.dbasis_ON), dbasis_ID_bp=g.dbasis_ID.mean() * 1e4, dbasis_ID_t=nw_t(g.dbasis_ID),
                         prev_b_close_mean_bp=g.b_prevclose.mean() * 1e4))
    for nm in ORDER:                                                 # Mon->Tue etc. inside dte buckets (is the weekday basis effect just expiry timing?)
        for bb, g in j[j.night == nm].groupby(b[j.night == nm]):
            if len(g) >= 10:
                rows.append(dict(cut="night x dte", group=f"{nm} | dte {bb}", n=len(g), dbasis_ON_bp=g.dbasis_ON.mean() * 1e4, dbasis_ON_t=nw_t(g.dbasis_ON)))
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--gate", action="store_true"); a = ap.parse_args()
    pd.set_option("display.width", 260, "display.max_columns", 40, "display.float_format", "{:.2f}".format)
    G = gate(); L = ["# VN30F1M overnight = VN30 index overnight + overnight basis change (measurement only)\n", "## Step 0: reproduction gate",
                     G.to_string(index=False), f"\nGATE {'PASSED' if G['pass'].all() else 'FAILED'}\n"]
    print("\n".join(L))
    if a.gate or not G["pass"].all():
        if not G["pass"].all(): print("Gate failed; stopping.")
        return
    fut = futures_nights(); j = panel()
    mis = int((~j.aligned).sum())
    J = {"a_all_days": j[j.aligned], "b_ex_index_flagged": j[j.aligned & ~j.idx_flag.astype(bool)]}
    fopen = fut[fut.invested]
    flat_f = (fopen.open == fopen.entry).mean() * 100
    degen = fopen[(fopen.open == fopen.high) & (fopen.open == fopen.low) & (fopen.open == fopen.close)]
    zero_vol = int((fopen.volume <= 0).sum())
    L += ["## Step 1: alignment and sample",
          f"- Futures nights (invested): {len(fopen)}, {fopen.index.min():%Y-%m-%d} .. {fopen.index.max():%Y-%m-%d}. Index nights from {j.index.min():%Y-%m-%d}.",
          f"- Decomposition sample (intersection, both legs from the same prior trading day): N = {len(J['a_all_days'])}, {J['a_all_days'].index.min():%Y-%m-%d} .. {J['a_all_days'].index.max():%Y-%m-%d}; "
          f"{mis} intersection nights dropped because the prior trading day differs between the two series.",
          f"- Excluding index-flagged opens: N = {len(J['b_ex_index_flagged'])}. Identity fut_ON = idx_ON + dbasis_ON: max |residual| = {j.attrs['identity_residual']:.2e}.",
          f"- Roll nights in sample: {int(J['a_all_days'].is_roll.sum())}; prior-close leg uses the VN30F2M close (build() entry) for both the futures return and the basis.",
          "- Index-flag rate by year (%): " + ", ".join(f"{y} {v:.1f}" for y, v in (j.groupby(j.index.year).idx_flag.mean() * 100).items()),
          f"- Futures open == prior close (entry): {flat_f:.2f}% of invested nights; degenerate bars (O=H=L=C): {len(degen)}"
          + (f" ({', '.join(str(x.date()) for x in degen.index[:8])}{'...' if len(degen) > 8 else ''})" if len(degen) else "") + f"; zero-volume bars: {zero_vol}.",
          "- Derivatives session times are UNVERIFIED: the futures 'open' is the vendor daily-bar open, assumed to be the first print of the derivatives session "
          "(which has opened 15 minutes before the stock ATO for much of the sample); the index open is the ATO-based index open. If the two opens are struck at different times, "
          "dbasis_ON contains the index move over that window by construction.", ""]
    basket = pit_basket()
    outs = {k: [] for k in ("year", "weekday", "monday", "wednesday", "expiry", "robustness")}
    for lab, jj in J.items():
        outs["year"].append(yearly(jj, fut[fut.invested]).assign(sample=lab))
        outs["weekday"].append(weekday(jj).assign(sample=lab))
        outs["monday"].append(monday(jj, fut).assign(sample=lab))
        outs["wednesday"].append(wednesday(jj, basket).assign(sample=lab))
        outs["expiry"].append(expiry(jj).assign(sample=lab))
        r = jj[~jj.is_roll & ~jj.near_expiry]
        outs["robustness"] += [yearly(r).assign(table="A", sample=lab), weekday(r).assign(table="B", sample=lab),
                               monday(r, fut[~fut.is_roll & ~fut.near_expiry]).assign(table="C", sample=lab), wednesday(r, basket).assign(table="D", sample=lab)]
    T = {k: pd.concat(v, ignore_index=True) for k, v in outs.items()}
    for k, v in T.items(): v.to_csv(OUT / f"futures_basis_{k}.csv", index=False)

    def show(df, cols, sample="a_all_days"): return df[df["sample"] == sample][cols].to_string(index=False)
    YA = ["year", "n", "fut_ON_bp", "fut_t", "idx_ON_bp", "idx_t", "dbasis_ON_bp", "dbasis_t", "corr", "slope", "slope_nw_se", "r2", "dbasis_ID_bp", "idx_flag_pct"]
    WB = ["period", "night", "n", "fut_ON_bp", "fut_t", "idx_ON_bp", "idx_t", "dbasis_ON_bp", "dbasis_t", "dbasis_ID_bp"]
    MC = ["period", "n", "fut_ON_bp", "fut_t", "idx_part_bp", "idx_t", "dbasis_part_bp", "dbasis_t", "dbasis_share_pct"]
    WD = ["period", "n", "idx_ON_bp", "fut_ON_bp", "idx_minus_fut_bp", "idx_minus_fut_t", "dbasis_ON_bp", "dbasis_t", "basket_minus_fut_bp", "basket_minus_fut_t", "basket_minus_idx_bp", "basket_minus_idx_t"]
    for lab in J:
        L += [f"## Tables, sample {lab}", "A. By year:", show(T["year"], YA, lab), "", "B. By night (entry weekday), NW t lag 5. 6 night types x 4 periods = 24 cells: "
              "Bonferroni |t| ~3.1 at 5%; weekday cells are descriptive.", show(T["weekday"], WB, lab), "", "C. Monday->Tuesday split:", show(T["monday"], MC, lab), "",
              "D. Wednesday->Thursday (PIT CW basket = one-day nights, filters off):", show(T["wednesday"], WD, lab), "",
              "E. Basis level and dbasis by days-to-expiry / night:", show(T["expiry"], ["cut", "group", "n", "b_close_mean_bp", "dbasis_ON_bp", "dbasis_ON_t", "dbasis_ID_bp", "dbasis_ID_t"], lab), ""]
    RB = T["robustness"]
    L += ["## F. Robustness: excluding roll nights and nights whose open date is expiry-1, expiry or expiry+1 (all days sample)",
          "A:", RB[(RB.table == "A") & (RB["sample"] == "a_all_days")][YA].to_string(index=False), "",
          "B:", RB[(RB.table == "B") & (RB["sample"] == "a_all_days")][WB].to_string(index=False), "",
          "C:", RB[(RB.table == "C") & (RB["sample"] == "a_all_days")][MC].to_string(index=False), "",
          "D:", RB[(RB.table == "D") & (RB["sample"] == "a_all_days")][WD].to_string(index=False), ""]

    # ---------------- pre-registered reads ----------------
    L += ["## Step 3: pre-registered reads (as written, before results)",
          "- R1: Monday futures edge is mostly basis if dbasis_ON accounts for >50% of Monday futures ON with |t| > 2 in the periods where the index exists.",
          "- R2: Wednesday gap is an overnight-basis effect if mean dbasis_ON on Wed->Thu is negative, within ~1.5 bp of -(index ON - futures ON), with |t| > 2.",
          "- R3: Futures track the index overnight only if the slope in table A is within +/-0.25 of 1 in most years.",
          "- Between thresholds = ambiguous.", ""]
    verdicts = []
    for lab in J:
        mc = T["monday"][(T["monday"]["sample"] == lab) & ~T["monday"].period.str.startswith("reference")]
        ok = (mc.dbasis_share_pct > 50) & (mc.dbasis_t.abs() > 2)
        bad = (mc.dbasis_share_pct <= 50) & (mc.dbasis_t.abs() <= 2)
        r1 = "HOLDS" if ok.all() else ("DOES NOT HOLD" if bad.all() else "AMBIGUOUS")
        r1d = "; ".join(f"{p}: share {s:.0f}%, t {t:.2f}" for p, s, t in zip(mc.period, mc.dbasis_share_pct, mc.dbasis_t))
        wd = T["wednesday"][(T["wednesday"]["sample"] == lab)].iloc[0]
        lit = (wd.dbasis_ON_bp < 0) and abs(wd.dbasis_ON_bp + wd.idx_minus_fut_bp) <= 1.5 and abs(wd.dbasis_t) > 2
        r2 = "HOLDS" if lit else ("DOES NOT HOLD" if wd.dbasis_ON_bp >= 0 or abs(wd.dbasis_t) < 1.5 else "AMBIGUOUS")
        sub = abs(-wd.dbasis_ON_bp - 4.83)
        ya = T["year"][(T["year"]["sample"] == lab) & T["year"].year.astype(str).str.fullmatch(r"\d{4}")]
        inband = ((ya.slope - 1).abs() <= 0.25).sum(); r3 = "HOLDS (futures track the index overnight)" if inband > len(ya) / 2 else "DOES NOT HOLD"
        rw = T["robustness"][(T["robustness"].table == "D") & (T["robustness"]["sample"] == lab)].iloc[0]
        if r1 == "AMBIGUOUS": r1 = "MIXED/AMBIGUOUS (holds only in: " + ", ".join(mc.period[ok]) + ")"
        verdicts.append(f"[{lab}] R1 {r1} ({r1d}). R2 {r2}: Wed->Thu dbasis_ON {wd.dbasis_ON_bp:.2f} bp (NW t {wd.dbasis_t:.3f}; excluding roll/near-expiry nights {rw.dbasis_ON_bp:.2f} bp, t {rw.dbasis_t:.2f}, n {int(rw.n)}); -(idx-fut) on the same nights is "
                        f"{-wd.idx_minus_fut_bp:.2f} bp, identical by construction, so the 1.5 bp condition is automatic; the substantive check is against the earlier "
                        f"PIT-basket-minus-futures gap of 4.83 bp: -dbasis_ON = {-wd.dbasis_ON_bp:.2f} bp, {sub:.2f} bp away; on the basket's own dates the basket-minus-futures gap is "
                        f"{wd.basket_minus_fut_bp:.2f} bp = basket-minus-index {wd.basket_minus_idx_bp:.2f} bp + index-minus-futures {wd.minus_dbasis_on_basket_dates_bp:.2f} bp. "
                        f"R3 {r3}: slope within 1 +/- 0.25 in {inband} of {len(ya)} years (slopes {', '.join(f'{y}: {s:.2f}' for y, s in zip(ya.year, ya.slope))}).")
    L += ["## Verdicts"] + verdicts
    (OUT / "futures_basis_summary.md").write_text("\n".join(L) + "\n")
    print("\n".join(L[5:]))


if __name__ == "__main__":
    main()
