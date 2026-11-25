"""Step 2 (HOSE capping) + Step 3 (reconstruct VN30 from the PIT panel and validate vs published VN30)."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
RAW = Path("data/raw")
LIM_STOCK, LIM_GROUP, LIM_SECTOR = 0.10, 0.15, 0.40

def cap_factors(m, tickers, groups, sectors=None, iters=5000, tol=1e-12, use_sector=False):
    """HOSE-style capping on raw free-float cap m = p*s*f.
    Entities = related groups (>=2 members present; limit 15%, ONE common factor per group) and all other single
    stocks (limit 10%). Iterative proportional clipping (Ground Rules s7.8): scale any entity above its limit down to
    the limit, renormalise, repeat. Then, inside a capped group, a member still above 10% is cut to 10% and the excess is
    reallocated pro rata to the group's other members (group total unchanged).
    The 40% same-sector cap is OFF by default: published VN30 factors do not apply it (banks are 100% in 2023-25 while
    their combined weight is >40%). use_sector=True reproduces the spec's literal s7.5 for comparison."""
    m = np.asarray(m, float); n = len(m); c = np.ones(n)
    gcount = {}
    for g in groups:
        if g: gcount[g] = gcount.get(g, 0) + 1
    ent = []
    for g, k in gcount.items():
        if k >= 2: ent.append((LIM_GROUP, [i for i in range(n) if groups[i] == g]))
    gm = {i for _, ix in ent for i in ix}
    for i in range(n):
        if i not in gm: ent.append((LIM_STOCK, [i]))
    if use_sector and sectors is not None:
        for sct in sorted({x for x in sectors if x}): ent.append((LIM_SECTOR, [i for i in range(n) if sectors[i] == sct]))
    for _ in range(iters):
        w = c * m; w = w / w.sum(); changed = False
        for lim, ix in ent:
            tot = w[ix].sum()
            if tot > lim + tol: c[ix] *= lim / tot; w = c * m; w = w / w.sum(); changed = True
        if not changed: break
    for lim, ix in [e for e in ent if e[0] == LIM_GROUP]:           # single stock inside a capped group
        for _ in range(100):
            w = c * m; w = w / w.sum(); gtot = w[ix].sum(); over = [i for i in ix if w[i] > LIM_STOCK + tol]
            if not over: break
            free = [i for i in ix if i not in over]
            if not free: break
            for i in over: c[i] *= LIM_STOCK / w[i]
            w2 = c * m; w2 = w2 / w2.sum(); k = (gtot - sum(w2[i] for i in over)) / w2[free].sum()
            for i in free: c[i] *= k
    return c / c.max()

def third_wed(y, m):
    d = pd.Timestamp(y, m, 1); d += pd.Timedelta(days=(2 - d.weekday()) % 7); return d + pd.Timedelta(days=14)
def cutoff(d):
    d = pd.Timestamp(d) - pd.Timedelta(days=5)
    cands = [third_wed(y, m) for y in (d.year - 1, d.year) for m in (1, 4, 7, 10)]
    return max(c for c in cands if c <= d)

DATA_START = pd.Timestamp('2018-11-21')   # first date with price data; earlier cutoffs use this day's prices (flagged)
def cap_date(d):
    return max(cutoff(d), DATA_START)

def load_close():
    px = {}
    for f in RAW.glob("*.csv"):
        d = pd.read_csv(f, parse_dates=["date"]); px[f.stem] = d.set_index("date")["close"]
    return pd.DataFrame(px).sort_index()

def main():
    M = pd.read_csv("data/vn30_pit_membership.csv", parse_dates=["effective_date"])
    SG = pd.read_csv("data/vn30_sector_groups.csv").fillna("").set_index("ticker")
    px = load_close(); idx = px["VN30"].dropna(); days = idx.index
    miss = sorted(set(M.ticker) - set(px.columns)); assert not miss, miss
    # latest known share count per ticker (variant B)
    last = M.sort_values("effective_date").groupby("ticker").shares.last()
    res = {}
    cap_rows = []
    for var in ("A_pit_shares", "B_latest_shares"):
        C = {}
        for d, g in M.groupby("effective_date"):
            g = g.set_index("ticker"); co = cap_date(d)
            pco = px.loc[:co].ffill().iloc[-1].reindex(g.index)
            sh = g.shares if var.startswith("A") else last.reindex(g.index)
            m = (pco * sh * g.free_float / 100).values
            ok = ~np.isnan(m)
            c = np.ones(len(g))
            if ok.all(): c = cap_factors(m, list(g.index), [SG.related_group.get(t, "") for t in g.index], [SG.gics_l1.get(t, "") for t in g.index])
            C[d] = pd.Series(c, index=g.index)
            if var.startswith("A"):
                for t in g.index: cap_rows.append(dict(effective_date=d, ticker=t, c_model=C[d][t], cap_published=g.cap_published[t], source=g.source[t]))
        # daily reconstruction
        eff = sorted(C); rets = {}
        for k in range(1, len(days)):
            t, tp = days[k], days[k - 1]
            e = [x for x in eff if x <= t]
            if not e: continue
            e = e[-1]; g = M[M.effective_date == e].set_index("ticker")
            p0 = px.loc[tp, g.index]; p1 = px.loc[t, g.index]
            sh = g.shares if var.startswith("A") else last.reindex(g.index)
            w = (p0 * sh * g.free_float / 100 * C[e]); r = (p1 / p0 - 1)
            okm = w.notna() & r.notna()
            rets[t] = (e, (w[okm] * r[okm]).sum() / w[okm].sum(), int((~okm).sum()))
        R = pd.DataFrame(rets, index=["basket", "rec", "n_missing"]).T
        R["rec"] = R.rec.astype(float); R["pub"] = idx.pct_change().reindex(R.index)
        res[var] = R
    pd.to_pickle(res, "results/_pit_recon.pkl")
    pd.DataFrame(cap_rows).to_csv("results/pit_cap_factors.csv", index=False)
    return res

if __name__ == "__main__":
    main()
