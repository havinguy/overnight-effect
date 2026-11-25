"""Out-of-sample validation of the day-of-week result (select on 2017-2021, test on 2022-2026)."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).parent))
from level_c_futures import build, stats, OUT

d = build(0, 0.0005, fee_vnd=12_500, slippage=0.0001)
d["prev_wd"] = (d.index.weekday - d["gap_days"].astype(int)) % 7   # weekday of the entry close
nonhold = (d["hold_type"] == "") & d["invested"]
NAMES = {0: "Mon->Tue", 1: "Tue->Wed", 2: "Wed->Thu", 3: "Thu->Fri"}
IS = (d.index >= "2017-01-01") & (d.index <= "2021-12-31")
OOS = (d.index >= "2022-01-01") & (d.index <= "2026-12-31")

def run(mask, days, label, exclude_year=None, period_label=""):
    m = mask & nonhold & d["prev_wd"].isin(days)
    if exclude_year:
        m = m & (d.index.year != exclude_year)
    x = d[m]
    span = d[mask]
    yrs = (span.index[-1] - span.index[0]).days / 365.25
    if exclude_year:
        yrs -= 366 / 365.25
    r_n = pd.Series(0.0, index=d.index); r_n[m] = d.loc[m, "r_net"]
    r_g = pd.Series(0.0, index=d.index); r_g[m] = d.loc[m, "r_gross"]
    keep = mask & (d.index.year != exclude_year if exclude_year else True)
    rn, rg = r_n[keep], r_g[keep]
    eq_n, eq_g = (1 + rn).cumprod(), (1 + rg).cumprod()
    sn = stats(rn, eq_n, m[keep], yrs)
    sg = stats(rg, eq_g, m[keep], yrs)
    return {"test": label, "period": period_label, "days": "+".join(NAMES[k] for k in days),
            "n_obs": sn["n_obs"], "years": yrs, "mean_gross_bp": sg["mean_daily_%"] * 100,
            "mean_net_bp": sn["mean_daily_%"] * 100, "gross_sharpe": sg["sharpe"], "gross_t": sg["t_stat"],
            "net_sharpe": sn["sharpe"], "net_t": sn["t_stat"], "ann_return_%": sn["ann_return_%"],
            "ann_vol_%": sn["ann_vol_%"], "max_drawdown_%": sn["max_drawdown_%"], "win_rate_%": sn["win_rate_%"]}

rows = []
# 1. in-sample ranking per day
ins = [run(IS, [k], f"IS single day {NAMES[k]}", period_label="2017-2021") for k in NAMES]
ins_df = pd.DataFrame(ins).sort_values("net_sharpe", ascending=False)
ins_df["passes_flag"] = (ins_df["gross_sharpe"] > 0.8) & (ins_df["gross_t"] > 1.5)
rows += ins_df.drop(columns="passes_flag").to_dict("records")
sel = [k for k, nm in NAMES.items() if ins_df.set_index("days").loc[nm, "passes_flag"]]
print("IN-SAMPLE (2017-2021), ranked by net Sharpe:")
with pd.option_context("display.width", 250, "display.float_format", "{:.2f}".format):
    print(ins_df[["days", "n_obs", "mean_gross_bp", "gross_sharpe", "gross_t", "net_sharpe", "net_t", "passes_flag"]].to_string(index=False))
print("Selected in-sample:", [NAMES[k] for k in sel])

# 2. out-of-sample, frozen selection, plus each day for reference
for k in NAMES:
    rows.append(run(OOS, [k], f"OOS single day {NAMES[k]}" + (" [SELECTED]" if k in sel else ""), period_label="2022-2026"))
if sel:
    rows.append(run(OOS, sel, "OOS selected days combined", period_label="2022-2026"))
    rows.append(run(IS, sel, "IS selected days combined", period_label="2017-2021"))
rows.append(run(OOS, [2, 3], "OOS Wed+Thu (rejected days)", period_label="2022-2026"))
# 3. Mon+Tue full sample and ex-2020
full = np.ones(len(d), bool)
rows.append(run(full, [0, 1], "Mon+Tue full sample", period_label="2017-2026"))
rows.append(run(full, [0, 1], "Mon+Tue full sample ex-2020", exclude_year=2020, period_label="2017-2026 ex 2020"))
rows.append(run(OOS, [0, 1], "Mon+Tue OOS", period_label="2022-2026"))
t = pd.DataFrame(rows)
t.to_csv(OUT / "level_c_oos_validation.csv", index=False)
with pd.option_context("display.width", 300, "display.max_columns", 30, "display.float_format", "{:.2f}".format):
    print("\n", t[["test", "n_obs", "mean_gross_bp", "mean_net_bp", "net_sharpe", "net_t", "ann_return_%", "max_drawdown_%", "win_rate_%"]].to_string(index=False))
    # by-year for Mon+Tue
    m = nonhold & d["prev_wd"].isin([0, 1]); y = d[m]
    print("\nMon+Tue by year:", (y.groupby(y.index.year)[["r_gross", "r_net"]].mean() * 1e4).round(1).assign(n=y.groupby(y.index.year).size()).to_string())
