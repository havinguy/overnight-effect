"""Level B: per-stock overnight vs intraday decomposition for the VN30 constituents.

Same log-return decomposition and per-leg stats as Level A, one row per ticker,
sorted by overnight Sharpe. Universe = CURRENT VN30 composition (survivorship-
biased; to be addressed later). Reads data/raw/<TICKER>.csv.

Caveat: individual-stock prices from the vendor are assumed corporate-action
adjusted; the script reports the count of |overnight| gaps above the 7% HOSE
daily limit as a check for unadjusted splits / bonus issues.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from level_a import RAW_DIR, OUT_DIR, TRADING_DAYS, decompose, leg_stats

T_THRESHOLD = 1.5
HOSE_LIMIT = 0.07


def ticker_row(sym: str, raw: pd.DataFrame, exclude_suspicious: bool,
               exclude_years: list[int], exclude_large_gaps: bool = False) -> dict:
    d = decompose(raw)
    # large_overnight_gap: |ln(open/prev close)| > 7%. Investigated 2026-11-17: NOT corporate
    # actions (see results/open_quality.md); mostly genuine limit-down opens, so exclusion is
    # a sensitivity check only, not a data-cleaning step.
    d["large_overnight_gap"] = d["r_overnight"].abs() > HOSE_LIMIT
    n_large = int(d["large_overnight_gap"].sum())
    if exclude_large_gaps:
        d = d[~d["large_overnight_gap"]]
    if exclude_years:
        d = d[~d["date"].dt.year.isin(exclude_years)]
    n_all = len(d)
    susp = d["open_suspicious"].astype(bool) if "open_suspicious" in d else pd.Series(False, index=d.index)
    if exclude_suspicious:
        d = d[~susp.reindex(d.index).fillna(False)]
    ov, intra = leg_stats(d["r_overnight"]), leg_stats(d["r_intraday"])
    return {
        "ticker": sym,
        "start": d["date"].min().date(),
        "n": ov["n"],
        "overnight_mean_%": ov["mean_daily_%"],
        "intraday_mean_%": intra["mean_daily_%"],
        "overnight_sharpe": ov["sharpe_ann"],
        "intraday_sharpe": intra["sharpe_ann"],
        "overnight_t": ov["t_stat"],
        "intraday_t": intra["t_stat"],
        "pct_open_suspicious": float(susp.mean() * 100),
        "n_gap_gt_limit": n_large,
        "significance": "" if ov["t_stat"] >= T_THRESHOLD else "not significant individually",
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--exclude-suspicious", action="store_true")
    ap.add_argument("--exclude-years", nargs="+", type=int, default=[])
    ap.add_argument("--exclude-large-gaps", action="store_true",
                    help="sensitivity: drop days with |overnight log return| > 7%%")
    ap.add_argument("--tag", default="")
    a = ap.parse_args()

    syms = (RAW_DIR.parent / "universe_vn30.txt").read_text().split()
    rows = [ticker_row(s, pd.read_csv(RAW_DIR / f"{s}.csv", parse_dates=["date"]),
                       a.exclude_suspicious, a.exclude_years, a.exclude_large_gaps) for s in syms]
    t = pd.DataFrame(rows).sort_values("overnight_sharpe", ascending=False).reset_index(drop=True)
    OUT_DIR.mkdir(exist_ok=True)
    t.to_csv(OUT_DIR / f"level_b_cross_section{a.tag}.csv", index=False)

    with pd.option_context("display.width", 250, "display.max_columns", 30,
                           "display.float_format", "{:.3f}".format):
        print(t.to_string())
    full = t[t["n"] >= 750]  # >= ~3y of data for the breadth stats
    print(f"\nTickers: {len(t)} ({len(full)} with >=750 obs)")
    print(f"Overnight mean > 0: {(t['overnight_mean_%'] > 0).sum()}/{len(t)}; "
          f"t >= {T_THRESHOLD}: {(t['overnight_t'] >= T_THRESHOLD).sum()}/{len(t)}; "
          f"t >= 2: {(t['overnight_t'] >= 2).sum()}/{len(t)}")
    print(f"Intraday mean > 0: {(t['intraday_mean_%'] > 0).sum()}/{len(t)}; "
          f"intraday t <= -1.5: {(t['intraday_t'] <= -1.5).sum()}/{len(t)}")
    print(f"Median overnight Sharpe {t['overnight_sharpe'].median():.2f} "
          f"vs median intraday Sharpe {t['intraday_sharpe'].median():.2f}")


if __name__ == "__main__":
    main()
