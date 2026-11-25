"""Level A: overnight vs intraday decomposition of VN-Index and VN30 (index level).

r_overnight_T = ln(Open_T)  - ln(Close_{T-1})
r_intraday_T  = ln(Close_T) - ln(Open_T)
r_cc_T        = r_overnight_T + r_intraday_T = ln(Close_T) - ln(Close_{T-1})

Pure measurement; no trading simulation. Reads data/raw/*.csv (run
fetch_indices.py first).
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
OUT_DIR = ROOT / "results"
TRADING_DAYS = 252


def decompose(df: pd.DataFrame) -> pd.DataFrame:
    d = df.sort_values("date").reset_index(drop=True).copy()
    d["r_overnight"] = np.log(d["open"]) - np.log(d["close"].shift(1))
    d["r_intraday"] = np.log(d["close"]) - np.log(d["open"])
    d["r_cc"] = np.log(d["close"]) - np.log(d["close"].shift(1))
    return d.dropna(subset=["r_overnight"]).reset_index(drop=True)


def quality_flags(d: pd.DataFrame) -> dict:
    """Open-price sanity: indices whose open == prior close look like stale/filled opens."""
    return {
        "open_eq_prev_close_pct": float((d["r_overnight"].abs() < 1e-12).mean() * 100),
        "open_eq_close_pct": float((d["r_intraday"].abs() < 1e-12).mean() * 100),
        "max_abs_overnight": float(d["r_overnight"].abs().max()),
        "max_abs_intraday": float(d["r_intraday"].abs().max()),
    }


def leg_stats(r: pd.Series) -> dict:
    n = int(r.count())
    mean, sd = r.mean(), r.std(ddof=1)
    return {
        "n": n,
        "mean_daily_%": mean * 100,
        "sd_daily_%": sd * 100,
        "sharpe_like_daily": mean / sd,
        "sharpe_ann": mean / sd * np.sqrt(TRADING_DAYS),
        "t_stat": mean / (sd / np.sqrt(n)),
        "ann_mean_%": mean * TRADING_DAYS * 100,
        "cum_log_%": r.sum() * 100,
        "hit_rate_%": float((r > 0).mean() * 100),
    }


def summarize(d: pd.DataFrame, symbol: str, sample: str) -> pd.DataFrame:
    rows = []
    for leg in ("r_overnight", "r_intraday", "r_cc"):
        rows.append({"symbol": symbol, "sample": sample, "leg": leg.removeprefix("r_"),
                     **leg_stats(d[leg])})
    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--symbols", nargs="+", default=["VNINDEX", "VN30"])
    ap.add_argument("--exclude-suspicious", action="store_true",
                    help="drop days flagged open_suspicious (open == prior close)")
    ap.add_argument("--exclude-years", nargs="+", type=int, default=[],
                    help="drop these calendar years entirely")
    ap.add_argument("--tag", default="", help="suffix for output summary filename")
    a = ap.parse_args()

    OUT_DIR.mkdir(exist_ok=True)
    dec = {}
    for s in a.symbols:
        p = RAW_DIR / f"{s}.csv"
        if not p.exists():
            raise SystemExit(f"{p} missing - run: python src/fetch_indices.py")
        raw = pd.read_csv(p, parse_dates=["date"])
        d = decompose(raw)
        if a.exclude_years:
            d = d[~d["date"].dt.year.isin(a.exclude_years)].reset_index(drop=True)
        if a.exclude_suspicious:
            if "open_suspicious" not in d:
                raise SystemExit("no open_suspicious column - rerun fetch_indices.py")
            d = d[~d["open_suspicious"].fillna(False).astype(bool)].reset_index(drop=True)
        dec[s] = d
        d.to_csv(OUT_DIR / f"{s}_decomposed{a.tag}.csv", index=False)

    # common window = intersection of date ranges, so symbols are comparable
    common_start = max(d["date"].min() for d in dec.values())
    tables = []
    for s, d in dec.items():
        print(f"\n{s} quality: " + ", ".join(f"{k}={v:.4g}" for k, v in quality_flags(d).items()))
        tables.append(summarize(d, s, f"full {d['date'].min():%Y-%m-%d}+"))
        tables.append(summarize(d[d["date"] >= common_start], s, f"common {common_start:%Y-%m-%d}+"))
    out = pd.concat(tables, ignore_index=True)
    out.to_csv(OUT_DIR / f"level_a_summary{a.tag}.csv", index=False)

    with pd.option_context("display.width", 200, "display.max_columns", 20,
                           "display.float_format", "{:.3f}".format):
        print("\n", out.to_string(index=False))


if __name__ == "__main__":
    main()
