"""Level C: overnight strategy on VN30 futures - buy at the close, sell at next open.

Entry price on day T-1 is the front-month (VN30F1M) close, EXCEPT before a roll day,
where the front-month series switches contracts between close(T-1) and open(T).
On those days the entry is VN30F2M's close(T-1) (the contract that becomes the front
month), so the roll basis is not booked as a fake overnight return. Where F2M
data does not exist (before 2018-11-20) the roll night is skipped (flat).

Roll day = first trading day after expiry; expiry = 3rd Thursday of the month (previous
trading day if it is a holiday). Validated: on roll days the new F1M open is ~0.00% from
F2M's prior close but ~0.31% from F1M's prior close.

Gross = no costs. Net = per-side cost on both legs (round trip each night) plus a roll
placeholder on roll days. 1x notional, flat each morning, no financing/margin interest.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW, OUT = ROOT / "data" / "raw", ROOT / "results"
TD = 252


def roll_days(dates: pd.DatetimeIndex) -> pd.DatetimeIndex:
    out = []
    for y in range(dates[0].year, dates[-1].year + 1):
        for m in range(1, 13):
            first = pd.Timestamp(y, m, 1)
            thursdays = [first + pd.Timedelta(days=i) for i in range(31)
                         if (first + pd.Timedelta(days=i)).month == m
                         and (first + pd.Timedelta(days=i)).weekday() == 3]
            th = thursdays[2]
            if th < dates[0] or th > dates[-1]:
                continue
            expiry = dates[dates <= th].max()
            nxt = dates[dates > expiry]
            if len(nxt):
                out.append(nxt[0])
    return pd.DatetimeIndex(out)


MULT = 100_000  # VND per index point (VN30F1M)


def build(per_side: float, roll_cost: float, fix_rolls: bool = True,
          fee_vnd: float | None = None, slippage: float = 0.0) -> pd.DataFrame:
    """Cost model per night: if fee_vnd is given, fee_vnd/(MULT*price) on each leg using that
    day's price (entry price on the way in, open on the way out) + slippage per side;
    otherwise a flat `per_side` fraction. Roll nights add roll_cost."""
    from data_cap import futures_csv  # frozen snapshot for analysis, data/raw for the logger (see data_cap.py)
    f1 = pd.read_csv(futures_csv("VN30F1M"), parse_dates=["date"]).set_index("date")
    f2 = pd.read_csv(futures_csv("VN30F2M"), parse_dates=["date"]).set_index("date")
    d = f1[["open", "close", "open_suspicious"]].copy()
    d["is_roll"] = d.index.isin(roll_days(d.index))
    entry = d["close"].shift(1)
    if fix_rolls:
        f2c = f2["close"].reindex(d.index).shift(1)
        entry = entry.where(~d["is_roll"], f2c)  # NaN => skipped (no F2M history)
    d["entry"] = entry
    d["invested"] = d["entry"].notna()
    d["r_gross"] = (d["open"] / d["entry"] - 1).fillna(0.0)
    if fee_vnd is None:
        side_cost = 2 * per_side
    else:
        side_cost = fee_vnd / (MULT * d["entry"]) + fee_vnd / (MULT * d["open"]) + 2 * slippage
    d["cost"] = side_cost + np.where(d["is_roll"], roll_cost, 0.0)
    d["r_net"] = np.where(d["invested"], d["r_gross"] - d["cost"], 0.0)
    # calendar gap of the night ending at this row's open; hold nights = gap >= 2 calendar days.
    # Weekend = Friday close -> next trading day 3 days later; everything else is a holiday gap.
    prev = d.index.to_series().shift(1)
    d["gap_days"] = (d.index.to_series() - prev).dt.days
    d["hold_type"] = np.where(d["gap_days"] < 2, "", np.where((prev.dt.weekday == 4) & (d["gap_days"] == 3), "weekend", "holiday"))
    d = d.iloc[1:]  # first row has no prior close
    d["eq_gross"] = (1 + d["r_gross"]).cumprod()
    d["eq_net"] = (1 + d["r_net"]).cumprod()
    return d


def stats(r: pd.Series, eq: pd.Series, invested: pd.Series, years: float | None = None) -> dict:
    """Daily strategy: annualise with 252. If `years` (calendar span) is given, the number of
    observations per year is n/years instead (low-frequency strategies), and the return is
    compounded over calendar time, so a strategy that is flat most nights is not overstated."""
    x = r[invested]
    n = len(x)
    mean, sd = x.mean(), x.std(ddof=1)
    dd = (eq / eq.cummax() - 1).min()
    ppy = TD if years is None else n / years
    ann = eq.iloc[-1] ** (TD / n) - 1 if years is None else eq.iloc[-1] ** (1 / years) - 1
    return {"n_obs": n, "obs_per_year": ppy, "mean_daily_%": mean * 100, "ann_return_%": ann * 100,
            "ann_vol_%": sd * np.sqrt(ppy) * 100, "sharpe": mean / sd * np.sqrt(ppy),
            "t_stat": mean / (sd / np.sqrt(n)), "max_drawdown_%": dd * 100,
            "win_rate_%": (x > 0).mean() * 100, "final_equity": eq.iloc[-1]}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--fee-vnd", type=float, default=12_500, help="broker fee per contract per side")
    ap.add_argument("--slippage", type=float, default=0.0001, help="per side, fraction of price")
    ap.add_argument("--roll-cost", type=float, default=0.0005, help="extra cost on roll nights")
    ap.add_argument("--old-per-side", type=float, default=0.0005, help="flat per-side cost of the first run (reference)")
    a = ap.parse_args()
    OUT.mkdir(exist_ok=True)

    d = build(0, a.roll_cost, fee_vnd=a.fee_vnd, slippage=a.slippage)
    old = build(a.old_per_side, 0.0005)
    inv = d["invested"]
    rows = {"gross": stats(d["r_gross"], d["eq_gross"], inv),
            f"net_realistic (fee {a.fee_vnd:,.0f} VND + {a.slippage*1e4:.0f}bp slip + {a.roll_cost*100:.2f}%/roll)":
                stats(d["r_net"], d["eq_net"], inv),
            f"net_old ({a.old_per_side*100:.2f}%/side flat)": stats(old["r_net"], old["eq_net"], old["invested"])}
    s = pd.DataFrame(rows).T
    s.to_csv(OUT / "level_c_summary.csv")
    out = d[["open", "close", "is_roll", "invested", "cost", "r_gross", "r_net", "eq_gross", "eq_net"]].copy()
    out["eq_net_old"] = old["eq_net"]
    out.to_csv(OUT / "level_c_equity_curves.csv")

    fee_pct = (a.fee_vnd / (MULT * d["close"]))[inv] * 100
    avg_side = (d.loc[inv, "cost"] - np.where(d.loc[inv, "is_roll"], a.roll_cost, 0)) / 2
    print(f"{d.index[0]:%Y-%m-%d} .. {d.index[-1]:%Y-%m-%d}; invested nights {int(inv.sum())}")
    print(f"Fee as % of notional per side: mean {fee_pct.mean():.4f}% (min {fee_pct.min():.4f}, max {fee_pct.max():.4f}); "
          f"all-in per side incl. slippage: mean {avg_side.mean()*100:.4f}%; avg per-night cost incl. rolls: "
          f"{d.loc[inv,'cost'].mean()*1e4:.2f} bp vs gross {d.loc[inv,'r_gross'].mean()*1e4:.2f} bp")
    with pd.option_context("display.width", 250, "display.float_format", "{:.3f}".format, "display.max_colwidth", 80):
        print(s.T.to_string())

    # sensitivity grid: fee x slippage at base roll cost; then roll-cost sweep
    grid = []
    for fee in (10_000, 12_500, 15_000):
        for sl in (0.0, 0.00005, 0.0001, 0.00015):
            b = build(0, a.roll_cost, fee_vnd=fee, slippage=sl)
            st = stats(b["r_net"], b["eq_net"], b["invested"])
            grid.append({"fee_vnd": fee, "slippage_bp": sl * 1e4, "allin_side_bp": ((b.loc[b.invested, "cost"]
                         - np.where(b.loc[b.invested, "is_roll"], a.roll_cost, 0)) / 2).mean() * 1e4,
                         "net_mean_bp": st["mean_daily_%"] * 100, "ann_return_%": st["ann_return_%"],
                         "sharpe": st["sharpe"], "t_stat": st["t_stat"], "max_dd_%": st["max_drawdown_%"]})
    grid = pd.DataFrame(grid); grid.to_csv(OUT / "level_c_cost_sensitivity.csv", index=False)
    print("\nSensitivity (roll cost %.2f%%):" % (a.roll_cost * 100))
    with pd.option_context("display.width", 200, "display.float_format", "{:.3f}".format):
        print(grid.to_string(index=False))
    rolls = []
    for rc in (0.0, 0.0005, 0.0030, 0.0080):
        b = build(0, rc, fee_vnd=a.fee_vnd, slippage=a.slippage)
        st = stats(b["r_net"], b["eq_net"], b["invested"])
        rolls.append({"roll_cost_%": rc * 100, "net_mean_bp": st["mean_daily_%"] * 100, "sharpe": st["sharpe"],
                      "t_stat": st["t_stat"], "ann_return_%": st["ann_return_%"]})
    print("\nRoll-cost sweep (0.30% = mean signed expiry-day calendar spread, 0.80% = mean |spread|; neither is "
          "actually paid by this construction):")
    print(pd.DataFrame(rolls).to_string(index=False, float_format=lambda x: f"{x:.3f}"))

    ok = d.loc[inv & ~d["open_suspicious"].astype(bool)]
    print(f"\nNet excl. open_suspicious days: mean {ok['r_net'].mean()*1e4:.2f} bp, "
          f"Sharpe {ok['r_net'].mean()/ok['r_net'].std()*np.sqrt(TD):.2f}")
    di = d[inv]; yr = di.index.year
    by = pd.DataFrame({"n": di.groupby(yr).size(), "gross_bp": di.groupby(yr)["r_gross"].mean() * 1e4,
                       "cost_bp": di.groupby(yr)["cost"].mean() * 1e4, "net_bp": di.groupby(yr)["r_net"].mean() * 1e4})
    by["net_sharpe"] = di.groupby(yr)["r_net"].mean() / di.groupby(yr)["r_net"].std() * np.sqrt(TD)
    print("\nBy year (realistic):"); print(by.round(2).to_string())
    # block-bootstrap-free uncertainty: standard error of the Sharpe
    n = int(inv.sum()); sr = s.iloc[1]["sharpe"]
    se = np.sqrt((1 + 0.5 * (sr / np.sqrt(TD)) ** 2) / n) * np.sqrt(TD)
    print(f"\nNet Sharpe {sr:.2f}, approx. standard error {se:.2f} (iid) -> 95% CI [{sr-1.96*se:.2f}, {sr+1.96*se:.2f}]")

    # ---------------- selective strategy: hold only over weekends / holidays ----------------
    years = (d.index[-1] - d.index[0]).days / 365.25
    print("\n=== Selective hold nights (gap >= 2 calendar days) ===")

    def sel(b, mask, col):
        r = b[col].where(mask & b["invested"], 0.0)
        return r, (1 + r).cumprod(), mask & b["invested"]
    hold = d["hold_type"] != ""
    masks = {"selective (weekend+holiday)": hold, "  weekend (Fri->Mon)": d["hold_type"] == "weekend",
             "  holiday": d["hold_type"] == "holiday", "non-hold weeknights (reference)": ~hold}
    rows2, costs = {}, {}
    for name, m in masks.items():
        for col, lab in (("r_gross", "gross"), ("r_net", "net")):
            r, eq, iv = sel(d, m, col)
            rows2[f"{name} | {lab}"] = stats(r, eq, iv, years)
            costs[f"{name} | {lab}"] = d.loc[iv, "cost"].mean() * 1e4 if lab == "net" else 0.0
    s2 = pd.DataFrame(rows2).T
    s2["avg_cost_bp"] = pd.Series(costs)
    r_sel, eq_sel, iv_sel = sel(d, hold, "r_net")
    d["eq_selective_net"] = eq_sel
    d["eq_selective_gross"] = sel(d, hold, "r_gross")[1]
    s2.loc["daily net (all nights, reference)"] = {**stats(d["r_net"], d["eq_net"], inv),
                                                   "avg_cost_bp": d.loc[inv, "cost"].mean() * 1e4}
    s2.to_csv(OUT / "level_c_selective_summary.csv")
    with pd.option_context("display.width", 250, "display.float_format", "{:.3f}".format):
        print(s2.to_string())
    ss = s2.loc["selective (weekend+holiday) | net"]
    se_s = np.sqrt((1 + 0.5 * (ss["sharpe"] / np.sqrt(ss["obs_per_year"])) ** 2) / ss["n_obs"]) * np.sqrt(ss["obs_per_year"])
    print(f"\nSelective net: Sharpe {ss['sharpe']:.2f} (SE ~{se_s:.2f}, 95% CI [{ss['sharpe']-1.96*se_s:.2f}, {ss['sharpe']+1.96*se_s:.2f}]), "
          f"t = {ss['t_stat']:.2f}, n = {int(ss['n_obs'])} over {years:.1f} years")
    g2 = []
    for fee in (10_000, 12_500, 15_000):
        for sl in (0.0, 0.00005, 0.0001, 0.00015):
            b = build(0, a.roll_cost, fee_vnd=fee, slippage=sl)
            r, eq, iv = sel(b, b["hold_type"] != "", "r_net")
            st = stats(r, eq, iv, years)
            g2.append({"fee_vnd": fee, "slippage_bp": sl * 1e4, "net_mean_bp": st["mean_daily_%"] * 100,
                       "ann_return_%": st["ann_return_%"], "sharpe": st["sharpe"], "t_stat": st["t_stat"],
                       "max_dd_%": st["max_drawdown_%"]})
    g2 = pd.DataFrame(g2); g2.to_csv(OUT / "level_c_selective_cost_sensitivity.csv", index=False)
    print("\nSelective sensitivity:")
    with pd.option_context("display.width", 200, "display.float_format", "{:.3f}".format):
        print(g2.to_string(index=False))
    print("\nSelective by year (per hold night):")
    hy = d[iv_sel]; print(pd.DataFrame({"n": hy.groupby(hy.index.year).size(),
          "gross_bp": hy.groupby(hy.index.year)["r_gross"].mean() * 1e4,
          "net_bp": hy.groupby(hy.index.year)["r_net"].mean() * 1e4}).round(2).to_string())
    d[["hold_type", "gap_days", "eq_selective_net", "eq_selective_gross"]].to_csv(OUT / "level_c_selective_equity_curve.csv")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.plot(d.index, d["eq_gross"], label=f"Gross (Sharpe {rows['gross']['sharpe']:.2f})", color="#1f77b4", lw=1.6)
    ax.plot(d.index, d["eq_net"], label=f"Net, realistic costs (Sharpe {sr:.2f})", color="#2ca02c", lw=1.8)
    ax.plot(old.index, old["eq_net"], label=f"Net, flat 0.05%/side (Sharpe {s.iloc[2]['sharpe']:.2f})",
            color="#d62728", lw=1.2, ls="--", alpha=0.7)
    ax.plot(d.index, d["eq_selective_net"], color="#ff7f0e", lw=1.8,
            label=f"Net, weekend/holiday nights only (Sharpe {ss['sharpe']:.2f})")
    ax.axhline(1, color="grey", lw=0.8, ls=":")
    ax.set_yscale("log"); ax.set_ylabel("Growth of 1 (log scale)")
    ax.set_title("VN30F1M overnight strategy: buy close, sell next open")
    ax.legend(frameon=False); ax.grid(alpha=0.25)
    fig.tight_layout(); fig.savefig(OUT / "level_c_equity.png", dpi=150)
    print(f"saved {OUT/'level_c_equity.png'}")


if __name__ == "__main__":
    main()
