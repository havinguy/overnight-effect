"""Compare the PIT cap-weighted stock replica's day-of-week table to VN30F1M (same window, same nights, paired by date)."""
import sys; sys.path.insert(0, "src")
import numpy as np, pandas as pd
from level_c_futures import build
cells = pd.read_pickle("results/_pit_cells.pkl")
d = build(0, 0.0005, fee_vnd=12_500, slippage=0.0001)
d = d.loc["2018-11-21":]
m = (d["hold_type"] == "") & d["invested"]
fut = d.loc[m, "r_gross"]; wd = fut.index.weekday           # index = open date; Tue=1 .. Fri=4  (Mon->Tue etc.)
NAMES = {1: "Mon->Tue", 2: "Tue->Wed", 3: "Wed->Thu", 4: "Thu->Fri"}
rows = []
for v in ("B", "A"):
    rep = cells[("pit", "cap", v)].r
    for w, nm in NAMES.items():
        f = fut[wd == w]; r = rep[rep.index.weekday == w]
        j = pd.concat([f, r], axis=1, join="inner").dropna(); j.columns = ["fut", "rep"]; dd = j.rep - j.fut
        rows.append(dict(variant=v, night=nm, fut_n=len(f), fut_mean_bp=f.mean() * 1e4, fut_t=f.mean() / (f.std() / np.sqrt(len(f))),
                         replica_mean_bp=r.mean() * 1e4, replica_t=r.mean() / (r.std() / np.sqrt(len(r))),
                         common_n=len(j), replica_minus_fut_bp=dd.mean() * 1e4, paired_t=dd.mean() / (dd.std() / np.sqrt(len(dd))),
                         corr_rep_fut=j.rep.corr(j.fut)))
    mt = pd.concat([fut[wd <= 2], rep[rep.index.weekday <= 2]], axis=1, join="inner").dropna(); wt = pd.concat([fut[wd >= 3], rep[rep.index.weekday >= 3]], axis=1, join="inner").dropna()
    for nm, s in (("Mon+Tue", mt), ("Wed+Thu", wt)):
        s.columns = ["fut", "rep"]; dd = s.rep - s.fut
        rows.append(dict(variant=v, night=nm, common_n=len(s), fut_mean_bp=s.fut.mean() * 1e4, replica_mean_bp=s.rep.mean() * 1e4, replica_minus_fut_bp=dd.mean() * 1e4, paired_t=dd.mean() / (dd.std() / np.sqrt(len(dd)))))
R = pd.DataFrame(rows); R.to_csv("results/pit_vs_futures_dayofweek.csv", index=False)
pd.set_option("display.width", 220, "display.float_format", "{:.2f}".format); print(R.to_string(index=False))
# Wed->Thu-specific: is the Wednesday gap the same size in both bases?
