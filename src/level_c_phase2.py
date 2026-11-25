"""Phase 2, Option B: Monday / Mon+Tue VN30F1M overnight signal, two-period robustness design.

Reuses build() and stats() from level_c_futures.py (unchanged). Base cost: build(0, 0.0005,
fee_vnd=12_500, slippage=0.0001). Non-hold nights only (hold_type == "" & invested).
Signal weekday = weekday of the ENTRY close (previous trading day): Mon -> Tue open is weekday 0.
A night is assigned to a period by its exit (open) date; non-hold nights never straddle a year end.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from level_c_futures import OUT, TD, build, stats

BASE = dict(roll_cost=0.0005, fee_vnd=12_500, slippage=0.0001)
SIGNALS = {"Monday": {0}, "Mon+Tue": {0, 1}}
PERIODS = {"Full 2017-2026": ("2017-01-01", "2026-12-31"), "IS 2017-2021": ("2017-01-01", "2021-12-31"),
           "OOS-proper 2022-2025 (ex-2026)": ("2022-01-01", "2025-12-31"), "2026 isolated": ("2026-01-01", "2026-12-31")}


def entry_weekday(d: pd.DataFrame) -> pd.Series:
    return pd.Series(d.index, index=d.index).shift(1).dt.weekday


def select(d: pd.DataFrame, wd: set, lo: str, hi: str) -> pd.DataFrame:
    m = (d["hold_type"] == "") & d["invested"] & entry_weekday(d).isin(wd)
    return d.loc[m & (d.index >= lo) & (d.index <= hi)]


def row(d: pd.DataFrame, wd: set, lo: str, hi: str, years: float) -> dict:
    s = select(d, wd, lo, hi)
    n = len(s)
    if n < 3:
        return {"n_obs": n}
    mask = d.index.isin(s.index)
    r = d["r_net"].where(mask, 0.0)
    sub = (d.index >= lo) & (d.index <= hi)
    eq = (1 + r[sub]).cumprod()
    st = stats(r[sub], eq, pd.Series(mask[sub], index=eq.index), years)
    sr, ppy = st["sharpe"], st["obs_per_year"]
    se = np.sqrt((1 + 0.5 * (sr / np.sqrt(ppy)) ** 2) / n) * np.sqrt(ppy)
    return {"n_obs": n, "mean_gross_bp": s["r_gross"].mean() * 1e4, "mean_net_bp": s["r_net"].mean() * 1e4,
            "net_sharpe": sr, "sharpe_se": se, "sharpe_ci_lo": sr - 1.96 * se, "sharpe_ci_hi": sr + 1.96 * se,
            "net_t": st["t_stat"], "ann_return_%": st["ann_return_%"], "max_dd_%": st["max_drawdown_%"],
            "win_rate_%": st["win_rate_%"], "years": years}


def monday_stats(fee: float, slip: float) -> dict:
    d = build(0, BASE["roll_cost"], fee_vnd=fee, slippage=slip)
    yrs = (d.index[-1] - d.index[0]).days / 365.25
    return row(d, {0}, *PERIODS["Full 2017-2026"], yrs)


def main() -> None:
    OUT.mkdir(exist_ok=True)
    d = build(0, **BASE)
    print(f"Data {d.index[0]:%Y-%m-%d}..{d.index[-1]:%Y-%m-%d}")
    rows = []
    for sig, wd in SIGNALS.items():
        for per, (lo, hi) in PERIODS.items():
            a, b = max(pd.Timestamp(lo), d.index[0]), min(pd.Timestamp(hi), d.index[-1])
            rows.append({"signal": sig, "period": per, **row(d, wd, lo, hi, (b - a).days / 365.25)})
    t = pd.DataFrame(rows)
    t.to_csv(OUT / "level_c_phase2_periods.csv", index=False)
    with pd.option_context("display.width", 250, "display.float_format", "{:.2f}".format, "display.max_columns", 30):
        print(t.to_string(index=False))

    # central question
    def g(sig, per, col):
        return t[(t.signal == sig) & (t.period.str.startswith(per))][col].iloc[0]
    print("\nCENTRAL QUESTION: does the edge survive 2022-2025 with 2026 removed?")
    for sig in SIGNALS:
        print(f"  {sig}: OOS-proper net {g(sig,'OOS',  'mean_net_bp'):.2f} bp, Sharpe {g(sig,'OOS','net_sharpe'):.2f} "
              f"(95% CI {g(sig,'OOS','sharpe_ci_lo'):.2f}..{g(sig,'OOS','sharpe_ci_hi'):.2f}), t {g(sig,'OOS','net_t'):.2f}, n {int(g(sig,'OOS','n_obs'))}"
              f" | 2026 alone net {g(sig,'2026','mean_net_bp'):.2f} bp, Sharpe {g(sig,'2026','net_sharpe'):.2f}, "
              f"t {g(sig,'2026','net_t'):.2f}, n {int(g(sig,'2026','n_obs'))}")

    # Monday cost grid (full sample)
    grid = []
    for fee in (10_000, 12_500, 15_000):
        for sl_bp in (0.0, 0.5, 1.0, 1.5):
            s = monday_stats(fee, sl_bp / 1e4)
            grid.append({"fee_vnd": fee, "slippage_bp_per_side": sl_bp, "net_mean_bp": s["mean_net_bp"],
                         "net_sharpe": s["net_sharpe"], "net_t": s["net_t"]})
    grid = pd.DataFrame(grid)
    # breakeven slippage at fee 12,500: bisection on mean net (Sharpe sign == mean sign)
    lo, hi = 0.0, 0.01
    for _ in range(50):
        mid = (lo + hi) / 2
        if monday_stats(12_500, mid)["mean_net_bp"] > 0:
            lo = mid
        else:
            hi = mid
    be = (lo + hi) / 2
    grid["breakeven_slippage_bp_fee12500"] = be * 1e4
    grid.to_csv(OUT / "level_c_phase2_monday_cost.csv", index=False)
    print("\nMonday cost grid (full sample):")
    with pd.option_context("display.width", 200, "display.float_format", "{:.2f}".format):
        print(grid.to_string(index=False))
    print(f"Breakeven slippage (fee 12,500, Monday net Sharpe = 0): {be*1e4:.2f} bp per side "
          f"(base assumption 1.0 bp -> headroom {be*1e4-1:.2f} bp per side, {2*(be*1e4-1):.2f} bp round trip)")

    # verdict
    sig = "Monday"
    oos_sr, oos_t, oos_n = g(sig, "OOS", "net_sharpe"), g(sig, "OOS", "net_t"), int(g(sig, "OOS", "n_obs"))
    y_sr, y_t = g(sig, "2026", "net_sharpe"), g(sig, "2026", "net_t")
    print(f"\nVERDICT: Monday full-sample net {g(sig,'Full','mean_net_bp'):.1f} bp/night, Sharpe {g(sig,'Full','net_sharpe'):.2f} "
          f"(t {g(sig,'Full','net_t'):.2f}); IS Sharpe {g(sig,'IS','net_sharpe'):.2f}; OOS-proper 2022-25 Sharpe {oos_sr:.2f} "
          f"(t {oos_t:.2f}, n {oos_n}); 2026 alone Sharpe {y_sr:.2f} (t {y_t:.2f}). "
          "Classification is left to these numbers (rule: live candidate if OOS-proper t >= ~2 and Sharpe CI excludes 0; "
          "2026-dependent if OOS-proper t < ~1.5 while 2026 is strong; else neither). Not pristine OOS: signal chosen after "
          "seeing the full sample; legitimacy comes only from freezing the rule and tracking forward.")
    t.attrs["be"] = be


if __name__ == "__main__":
    main()
