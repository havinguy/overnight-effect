"""Cached, incremental daily OHLC pull for Vietnamese index series.

One CSV per index in data/raw/. Re-running fetches only days since the last
stored date (with a small overlap so a previously partial bar gets refreshed).

Note: vnstock 4.x removed stock_historical_data(); Quote.history() is the
equivalent. Intraday/in-progress bars are dropped so every stored row is a
completed session (ATO open .. ATC close).
"""
from __future__ import annotations

import argparse
import os
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


# FETCH BACKEND SWITCH (2026-11-27, approved by Harry; scoped): with source="VCI", these four symbols are fetched through
# src/fetch_vci_direct.py (direct VCI POST, no vnstock) instead of vnstock's Quote. Every other symbol (all 3-letter
# stocks) and every other source stays on vnstock. Validated: results/backend_switch_validation.md.
# ROLLBACK: set OVERNIGHT_FETCH_BACKEND=vnstock in the environment (restores vnstock for all symbols, no code change),
# or revert this block. Nothing else in the fetch path (overlap, keep='last', _drop_incomplete, flag_suspicious) changes.
DIRECT_VCI_SYMBOLS = frozenset({"VN30F1M", "VN30F2M", "VN30", "VNINDEX"})
BACKEND_ENV = "OVERNIGHT_FETCH_BACKEND"


def backend_for(symbol: str, source: str) -> str:
    if source == "VCI" and symbol in DIRECT_VCI_SYMBOLS and os.environ.get(BACKEND_ENV, "").strip().lower() != "vnstock":
        return "vci_direct"
    return "vnstock"


def _download_vci_direct(symbol: str, start: str, end: str) -> pd.DataFrame:
    """Same request vnstock 4.0.4 VCI Quote.history(start, end, '1D') sends: to = end date + 1 day (local), countBack =
    business days in [start, to] + 1. Like vnstock, rows before `start` are NOT filtered (the merge handles them)."""
    import fetch_vci_direct as V
    end_time = datetime.strptime(end, "%Y-%m-%d") + timedelta(days=1)
    count_back = len(pd.bdate_range(start=datetime.strptime(start, "%Y-%m-%d"), end=end_time)) + 1
    df = V.fetch(symbol, count_back, to=int(end_time.timestamp()))
    return df[COLS].copy()


def _download(symbol: str, start: str, end: str, source: str) -> pd.DataFrame:
    backend = backend_for(symbol, source)
    print(f"[fetch] {symbol}: backend={backend} (source={source})")
    if backend == "vci_direct":
        return _download_vci_direct(symbol, start, end)
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


# STOCK BACK-ADJUSTMENT GUARD (2026-11-27; policy approved by Harry). Stock data is FROZEN: VCI back-adjusts stock history after
# corporate actions (FPT 2026-11: every past price x0.9775, volumes revised), so an incremental refresh would splice adjusted new
# rows onto unadjusted old rows (false overnight gap + wrong open_suspicious at the splice). For every symbol that is not one of
# the futures/index symbols, update() compares the cached rows that the fresh fetch overlaps; if ANY open/high/low/close
# (|diff| > PRICE_TOL) or volume differs, it raises StockRevisionError BEFORE merging or writing anything. The reopen path is a
# FULL re-pull via direct VCI into a new dated snapshot, not an incremental refresh (data/README.md). Futures/index rows are not
# checked here (track_forward.py has its own rewritten-row guard), so the logger's behaviour is unchanged.
PRICE_TOL = 1e-6        # prices are stored rounded to 2 dp, so any real change is >= 0.005


class StockRevisionError(RuntimeError):
    """The vendor revised already-stored stock rows. Never retried, never spliced."""


def is_frozen_stock(symbol: str) -> bool:
    return symbol not in DIRECT_VCI_SYMBOLS            # the futures/index set; everything else fetched here is a stock


def check_stock_overlap(symbol: str, cached: pd.DataFrame, new: pd.DataFrame, path: Path) -> int:
    """Raise StockRevisionError if any overlapping cached row changed in the fresh fetch; else return the number of rows compared."""
    j = cached[COLS].merge(new[COLS], on="date", how="inner", suffixes=("_old", "_new"))
    if j.empty:
        return 0
    bad = pd.Series(False, index=j.index); fields = {}
    for c in ["open", "high", "low", "close"]:
        m = (j[f"{c}_old"].astype(float) - j[f"{c}_new"].astype(float)).abs() > PRICE_TOL
        bad |= m; fields[c] = int(m.sum())
    mv = j["volume_old"].astype(float) != j["volume_new"].astype(float); bad |= mv; fields["volume"] = int(mv.sum())
    if bad.any():
        ex = j[bad].head(3)
        eg = "; ".join(f"{r.date:%Y-%m-%d} close {r.close_old} -> {r.close_new}, open {r.open_old} -> {r.open_new}, volume {r.volume_old} -> {r.volume_new}"
                       for r in ex.itertuples())
        raise StockRevisionError(
            f"{symbol}: the vendor REVISED {int(bad.sum())} of {len(j)} already-stored rows "
            f"({j.date.min():%Y-%m-%d}..{j.date.max():%Y-%m-%d}; changed fields: {fields}). Example: {eg}. "
            f"This looks like a back-adjustment (corporate action). Stock data is frozen: NOTHING was written to {path}. "
            "Do NOT splice. Reopen equities with a FULL re-pull via direct VCI into a new dated snapshot (see data/README.md).")
    return len(j)


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
    if is_frozen_stock(symbol) and not cached.empty:                      # stock back-adjustment guard (see above)
        n_cmp = check_stock_overlap(symbol, cached, new, csv_path(symbol, raw_dir))
        print(f"[guard] {symbol}: {n_cmp} overlapping stored rows unchanged in the fresh fetch")
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
        except StockRevisionError:
            raise                                   # a vendor revision is not a rate limit: abort at once, never retry
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
