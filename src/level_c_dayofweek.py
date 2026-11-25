"""Level C follow-up: split non-hold overnight nights by the weekday of the entry close."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).parent))
from level_c_futures import build, OUT, TD

d = build(0, 0.0005, fee_vnd=12_500, slippage=0.0001)
years = (d.index[-1] - d.index[0]).days / 365.25
prev_wd = d.index.to_series().shift(1).dt.weekday
m = (d["hold_type"] == "") & d["invested"]
names = {0: "Mon close -> Tue open", 1: "Tue -> Wed", 2: "Wed -> Thu", 3: "Thu -> Fri"}
rows = []
for wd, nm in names.items():
    x = d[m & (prev_wd == wd)]
    g, n = x["r_gross"], x["r_net"]
    k = len(x)
    ppy = k / years
    rows.append({"night": nm, "n_obs": k,
                 "mean_gross_bp": g.mean() * 1e4, "mean_net_bp": n.mean() * 1e4,
                 "gross_sharpe": g.mean() / g.std() * np.sqrt(ppy),
                 "net_sharpe": n.mean() / n.std() * np.sqrt(ppy),
                 "gross_sharpe_per252": g.mean() / g.std() * np.sqrt(TD),
                 "net_sharpe_per252": n.mean() / n.std() * np.sqrt(TD),
                 "gross_t": g.mean() / (g.std() / np.sqrt(k)), "net_t": n.mean() / (n.std() / np.sqrt(k)),
                 "gross_hit_%": (g > 0).mean() * 100})
t = pd.DataFrame(rows)
t["flag_gross_sharpe>0.8_and_t>1.5"] = (t["gross_sharpe"] > 0.8) & (t["gross_t"] > 1.5)
t.to_csv(OUT / "level_c_dayofweek.csv", index=False)
with pd.option_context("display.width", 250, "display.float_format", "{:.3f}".format):
    print(t.to_string(index=False)); print("total n", t.n_obs.sum())
    # year stability per day
    x = d[m].assign(wd=prev_wd[m], yr=d[m].index.year)
    print((x.pivot_table(index="yr", columns="wd", values="r_gross", aggfunc="mean") * 1e4).rename(columns=names).round(1))

import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(8, 4.8))
xs = np.arange(4); w = 0.38
se_g = [d[m & (prev_wd == k)]["r_gross"].std() / np.sqrt(((m & (prev_wd == k)).sum())) * 1e4 for k in names]
ax.bar(xs - w/2, t["mean_gross_bp"], w, yerr=1.96 * np.array(se_g), capsize=3, label="Gross", color="#1f77b4")
ax.bar(xs + w/2, t["mean_net_bp"], w, label="Net (realistic costs)", color="#2ca02c")
ax.axhline(0, color="grey", lw=0.8)
ax.set_xticks(xs, [n.replace(" -> ", "\n-> ") for n in names.values()])
ax.set_ylabel("Mean overnight return (bp per night)")
ax.set_title("VN30F1M overnight return by entry weekday (non-hold nights; 95% CI on gross)")
ax.legend(frameon=False); ax.grid(axis="y", alpha=0.25)
fig.tight_layout(); fig.savefig(OUT / "level_c_dayofweek.png", dpi=150)
