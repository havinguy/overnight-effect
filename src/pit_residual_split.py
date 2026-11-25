"""Split the replica-vs-futures residual: stock replica -> published VN30 index (open/close) -> VN30F1M."""
import sys; sys.path.insert(0, "src")
import numpy as np, pandas as pd
import pit_dayofweek_2x2 as X
from level_a import RAW_DIR, decompose
from level_c_futures import build
NAMES = X.NAMES
cells = pd.read_pickle("results/_pit_cells.pkl")
rep = cells[("pit", "cap", "B")].r; repA = cells[("pit", "cap", "A")].r
# published index overnight (ln open / prev close), ordinary nights, index open not flagged
v = pd.read_csv(RAW_DIR / "VN30.csv", parse_dates=["date"]); dv = decompose(v); gap = dv["date"].diff().dt.days
idx_ok = (gap == 1) & ~dv["open_suspicious"].astype(bool)
idx = dv.set_index("date")["r_overnight"].where(idx_ok.values).dropna(); idx = idx.loc["2018-11-21":]
print("index nights usable:", len(idx), "| index open_suspicious share by year:", dv.groupby(dv.date.dt.year).open_suspicious.mean().round(2).to_dict())
d = build(0, 0.0005, fee_vnd=12_500, slippage=0.0001).loc["2018-11-21":]
fut = d.loc[(d["hold_type"] == "") & d["invested"], "r_gross"]
def sens_rep():  # keep open_suspicious stock-nights (their overnight return is 0) instead of dropping them
    alt = {}
    for t in X.tickers:
        dd = decompose(pd.read_csv(RAW_DIR / f"{t}.csv", parse_dates=["date"])); g = dd["date"].diff().dt.days
        ok = (g == 1) & (dd["r_overnight"].abs() <= 0.07)
        alt[t] = dd.set_index("date")["r_overnight"].where(ok.values)
    old = X.RET; X.RET = pd.DataFrame(alt).sort_index().loc[X.START:]
    try: s = X.cell_series("pit", "cap", "B").r
    finally: X.RET = old
    return s
rep0 = sens_rep()
def block(label, mask_years=None):
    J = pd.concat({"replica": rep, "replica_keep0": rep0, "index": idx, "futures": fut}, axis=1, join="inner").dropna()
    if mask_years == "ex2021": J = J[J.index.year != 2021]
    J["wd"] = J.index.weekday; rows = []
    for w, nm in NAMES.items():
        g = J[J.wd == w]; r = {"sample": label, "night": nm, "n": len(g)}
        for c in ("replica", "replica_keep0", "index", "futures"): r[c + "_bp"] = g[c].mean() * 1e4
        for a, b in (("replica", "index"), ("index", "futures"), ("replica", "futures")):
            dd = g[a] - g[b]; r[f"{a}-{b}_bp"] = dd.mean() * 1e4; r[f"{a}-{b}_t"] = dd.mean() / (dd.std() / np.sqrt(len(dd)))
        rows.append(r)
    return pd.DataFrame(rows), J
out = []
for lab, my in (("all", None), ("ex-2021", "ex2021")):
    t, J = block(lab, my); out.append(t)
T = pd.concat(out); T.to_csv("results/pit_residual_split.csv", index=False)
pd.set_option("display.width", 250, "display.float_format", "{:.2f}".format, "display.max_columns", 30)
print(T[["sample", "night", "n", "replica_bp", "replica_keep0_bp", "index_bp", "futures_bp", "replica-index_bp", "replica-index_t", "index-futures_bp", "index-futures_t", "replica-futures_bp", "replica-futures_t"]].to_string(index=False))
# level vs shape: Wed gap vs gap on other nights (paired by night; Welch on the per-night gaps)
J = block("all")[1]; J["gap"] = J.replica - J.futures; J["gap_ri"] = J.replica - J["index"]; J["gap_if"] = J["index"] - J.futures
for col in ("gap", "gap_ri", "gap_if"):
    a, b = J[J.wd == 3][col], J[J.wd != 3][col]
    print(f"{col}: Wed->Thu {a.mean()*1e4:.2f} bp vs other nights {b.mean()*1e4:.2f} bp; difference {(a.mean()-b.mean())*1e4:.2f} bp, Welch t {(a.mean()-b.mean())/np.sqrt(a.var()/len(a)+b.var()/len(b)):.2f}")
# Tet 2019 check and dividend drift
print("VN30 trading days 2019-02-01..2019-02-12:", [str(x.date()) for x in dv.date if pd.Timestamp("2019-02-01") <= x <= pd.Timestamp("2019-02-12")])
R = pd.read_csv("results/_recon_B_latest_shares.csv", index_col=0, parse_dates=True)
print("variant B mean daily bias bp:", round((R.rec - R.pub).mean() * 1e4, 3), "-> annualised %.2f%%" % ((R.rec - R.pub).mean() * 252 * 100))
Ra = pd.read_csv("results/_recon_A_pit_shares.csv", index_col=0, parse_dates=True)
print("variant A mean daily bias bp:", round((Ra.rec - Ra.pub).mean() * 1e4, 3), "-> annualised %.2f%%" % ((Ra.rec - Ra.pub).mean() * 252 * 100))
# naive baselines for the gate: uncapped PIT cap-weight and PIT equal weight, daily return tracking
import pit_reconstruct as P
M = pd.read_csv("data/vn30_pit_membership.csv", parse_dates=["effective_date"]); px = P.load_close(); idxp = px["VN30"].dropna(); days = idxp.index
last = M.sort_values("effective_date").groupby("ticker").shares.last(); eff = sorted(M.effective_date.unique()); rows = []
for name in ("uncapped_PIT_capweight_B", "PIT_equal_weight"):
    rr = {}
    for k in range(1, len(days)):
        t, tp = days[k], days[k - 1]; e = [x for x in eff if x <= t]
        if not e: continue
        g = M[M.effective_date == e[-1]].set_index("ticker"); p0, p1 = px.loc[tp, g.index], px.loc[t, g.index]
        w = (p0 * last.reindex(g.index) * g.free_float / 100) if name.startswith("uncapped") else pd.Series(1.0, index=g.index)
        r = p1 / p0 - 1; ok = w.notna() & r.notna(); rr[t] = (w[ok] * r[ok]).sum() / w[ok].sum()
    s = pd.Series(rr); e = (s - idxp.pct_change().reindex(s.index)).dropna()
    rows.append(dict(variant=name, n=len(e), corr=s.corr(idxp.pct_change().reindex(s.index)), mae_bp=e.abs().mean() * 1e4))
print(pd.DataFrame(rows).round(4).to_string(index=False))
pd.DataFrame(rows).to_csv("results/vn30_tracking_naive_baselines.csv", index=False)
