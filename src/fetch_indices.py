"""Cached, incremental daily OHLC pull for Vietnamese index series.

One CSV per index in data/raw/. Re-running fetches only days since the last
stored date (with a small overlap so a previously partial bar gets refreshed).

Note: vnstock 4.x removed stock_historical_data(); Quote.history() is the
equivalent. Intraday/in-progress bars are dropped so every stored row is a
completed session (ATO open .. ATC close).
"""
from __future__ import annotations

import argparse
import time as _time
from datetime import datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
SYMBOLS = ("VNINDEX", "VN30")
DEFAULT_START = "2012-01-01"
OVERLAP_DAYS = 7
COLS = ["date", "open", "high", "low", "close", "volume"]
FLAG_TOL = 1e-9  # open == prior close to the last printed digit
VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")
MARKET_CLOSE = time(15, 5)  # ATC ends 14:45; small buffer


def csv_path(symbol: str, raw_dir: Path = RAW_DIR) -> Path:
    return raw_dir / f"{symbol}.csv"


def load_cached(symbol: str, raw_dir: Path = RAW_DIR) -> pd.DataFrame:
    p = csv_path(symbol, raw_dir)
    if not p.exists():
        return pd.DataFrame(columns=COLS)
    return pd.read_csv(p, parse_dates=["date"])


def _drop_incomplete(df: pd.DataFrame, now: datetime | None = None) -> pd.DataFrame:
    now = now or datetime.now(VN_TZ)
    today = now.date()
    keep = df["date"].dt.date < today
    if now.time() >= MARKET_CLOSE:
        keep |= df["date"].dt.date == today
    return df[keep]


def _download(symbol: str, start: str, end: str, source: str) -> pd.DataFrame:
    from vnstock import Quote  # imported lazily so analysis works offline

    raw = Quote(symbol=symbol, source=source).history(start=start, end=end, interval="1D")
    if raw is None or raw.empty:
        return pd.DataFrame(columns=COLS)
    df = raw.rename(columns={"time": "date"})[COLS].copy()
    df["date"] = pd.to_datetime(df["date"]).dt.normalize()
    return df


# KNOWN DATA ARTIFACT (2021): 133 of 250 VNINDEX sessions in 2021 (53%) have
# open == prior close in the VCI feed, vs 1-8% in other years. That is almost
# certainly a VCI feed problem, not a market event (KBS shows a different open
# on ~92% of VCI-flagged VNINDEX days). Any analysis on this data must either
# exclude 2021 or caveat it. See results/open_quality.md.
def flag_suspicious(df: pd.DataFrame) -> pd.DataFrame:
    """open_suspicious = open equals prior close exactly. A genuine ATO-vs-prior-close
    zero gap is rare (~0.3%), while VCI fills the open from the prior close on many
    days (see results/open_quality.md). Recomputed over the whole series each update."""
    d = df.sort_values("date").reset_index(drop=True).copy()
    d["open_suspicious"] = ((d["open"] - d["close"].shift(1)).abs() < FLAG_TOL).fillna(False)
    return d


def update(symbol: str, start: str = DEFAULT_START, source: str = "VCI",
           raw_dir: Path = RAW_DIR, full: bool = False) -> pd.DataFrame:
    raw_dir.mkdir(parents=True, exist_ok=True)
    cached = pd.DataFrame(columns=COLS) if full else load_cached(symbol, raw_dir)[COLS]
    if cached.empty:
        fetch_from = start
    else:
        fetch_from = (cached["date"].max() - timedelta(days=OVERLAP_DAYS)).strftime("%Y-%m-%d")
    end = (datetime.now(VN_TZ).date() + timedelta(days=1)).strftime("%Y-%m-%d")

    new = _drop_incomplete(_download(symbol, fetch_from, end, source))
    merged = pd.concat([cached, new], ignore_index=True)
    merged = (merged.drop_duplicates("date", keep="last")
                    .sort_values("date").reset_index(drop=True))
    merged = flag_suspicious(merged)
    merged.to_csv(csv_path(symbol, raw_dir), index=False)
    added = len(merged) - len(cached)
    print(f"{symbol}: {len(merged)} rows "
          f"({merged['date'].min():%Y-%m-%d} .. {merged['date'].max():%Y-%m-%d}), "
          f"+{added} new (fetched from {fetch_from})")
    return merged


THROTTLE_SECS = 4  # community tier allows ~20 requests/min


def update_with_retry(symbol: str, *args, retries: int = 4, **kw) -> pd.DataFrame:
    """vnstock's rate limiter raises SystemExit, so catch BaseException and wait it out."""
    for attempt in range(retries):
        try:
            return update(symbol, *args, **kw)
        except (Exception, SystemExit) as e:
            if attempt == retries - 1:
                raise
            print(f"{symbol}: {type(e).__name__} (rate limit?) - waiting 65s, retry {attempt + 1}")
            _time.sleep(65)


def vn30_constituents(refresh: bool = False) -> list[str]:
    """Current VN30 composition (survivorship-biased starting universe; see notes)."""
    p = RAW_DIR.parent / "universe_vn30.txt"
    if p.exists() and not refresh:
        return p.read_text().split()
    from vnstock import Listing

    syms = sorted(Listing(source="VCI").symbols_by_group("VN30").tolist())
    p.write_text("\n".join(syms) + "\n")
    return syms


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--symbols", nargs="+", default=list(SYMBOLS))
    ap.add_argument("--start", default=DEFAULT_START)
    ap.add_argument("--source", default="VCI")
    ap.add_argument("--vn30", action="store_true",
                    help="pull current VN30 constituents (list cached in data/universe_vn30.txt)")
    ap.add_argument("--full", action="store_true", help="ignore cache, refetch everything")
    a = ap.parse_args()
    if a.vn30:
        a.symbols = vn30_constituents()
    for i, s in enumerate(a.symbols):
        update_with_retry(s, a.start, a.source, full=a.full)
        if i < len(a.symbols) - 1:
            _time.sleep(THROTTLE_SECS)


if __name__ == "__main__":
    main()
