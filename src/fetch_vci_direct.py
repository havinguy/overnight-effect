"""Standalone daily-OHLC fetcher that calls VCI's chart endpoint directly (no vnstock import).

Purpose: survive the vnstock v4/v5 sunset (Decree 363/2026). Reproduces what vnstock 4.0.4
Quote(symbol, source="VCI").history(interval="1D") returns, byte-for-byte on the fields the repo stores.

Endpoint : POST https://trading.vietcap.com.vn/api/chart/OHLCChart/gap-chart
Payload  : {"timeFrame": "ONE_DAY", "symbols": [SYM], "to": <unix seconds>, "countBack": <N>}
Headers  : copied VERBATIM from the live wire capture of vnstock 4.0.4 (results/vci_headers_captured.json,
           2026-11-26, monkeypatched requests.Session.request). vnstock 4.0.4 sends NO Device-Id (its
           _generate_vci_device_id() helper is defined but never called), no cookies, no auth. So none are sent here.
           The difference from src/source_probe.py's HTTP 400 is the browser User-Agent + browser Accept/Sec-Fetch headers.
Transform (mirrors vnstock.core.utils.transform.ohlc_to_df for source VCI, 1D):
  t (unix s) -> UTC -> Asia/Ho_Chi_Minh -> naive -> normalized date
  stocks only: prices / 1000 (VCI serves VND; repo stores thousand-VND). Index and derivative: unscaled.
  all assets : OHLC rounded to 2 decimals; volume int64.
  open_suspicious via fetch_indices.flag_suspicious (open == prior close, FLAG_TOL), computed within the
  returned window (first row has no prior close -> False).
Symbol codes (confirmed 2026-11-26 against live vnstock calls, see results/vci_direct_validation.md):
  VNINDEX -> VNINDEX, VN30 -> VN30, VN30F1M -> VN30F1M, VN30F2M -> VN30F2M (continuous), 3-letter stocks unchanged.
  Only symbols vnstock itself classifies the same way are mapped (no VNI/HNX/UPCOM aliases: vnstock 4.0.4 treats VNI/HNX as
  3-letter stocks and rejects UPCOM, so mapping them here would NOT mirror vnstock).
Fails loudly: network error/timeout, non-200, non-JSON, missing/ragged/null/non-numeric arrays, empty data,
  duplicate dates, non-positive prices -> VCIDirectError.

Usage:  from fetch_vci_direct import fetch ; fetch("VN30F1M", 40)
        python3 src/fetch_vci_direct.py VN30F1M 10
"""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).parent))
from fetch_indices import flag_suspicious  # same open_suspicious rule as data/raw  # noqa: E402

URL = "https://trading.vietcap.com.vn/api/chart/OHLCChart/gap-chart"
TIMEOUT = 20
COLS = ["date", "open", "high", "low", "close", "volume"]

# Verbatim from results/vci_headers_captured.json (minus Content-Length, which requests sets itself).
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
    "Accept-Encoding": "gzip, deflate",
    "Accept": "application/json, text/plain, */*",
    "Connection": "keep-alive",
    "Accept-Language": "en-US,en;q=0.9,vi-VN;q=0.8,vi;q=0.7",
    "Content-Type": "application/json",
    "Cache-Control": "no-cache",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
    "DNT": "1",
    "Pragma": "no-cache",
    "sec-ch-ua-platform": '"Windows"',
    "sec-ch-ua-mobile": "?0",
    "Referer": "https://trading.vietcap.com.vn/",
    "Origin": "https://trading.vietcap.com.vn/",
}

INDEX_CODES = {"VNINDEX": "VNINDEX", "VN30": "VN30", "VN100": "VN100",
               "HNXINDEX": "HNXIndex", "HNX30": "HNX30", "UPCOMINDEX": "HNXUpcomIndex"}
DERIVATIVES = {"VN30F1M", "VN30F2M", "VN30F1Q", "VN30F2Q"}


class VCIDirectError(RuntimeError):
    pass


def asset_type(symbol: str) -> str:
    s = symbol.upper()
    if s in INDEX_CODES:
        return "index"
    if s in DERIVATIVES or (len(s) == 9 and s.startswith("41")):   # KRX contract codes, e.g. 41I1GC000
        return "derivative"
    if len(s) == 3 and s.isalpha():
        return "stock"
    raise ValueError(f"unmapped symbol {symbol!r}: add it to fetch_vci_direct after confirming against vnstock")


def vci_code(symbol: str) -> str:
    s = symbol.upper()
    return INDEX_CODES.get(s, s)


def default_to() -> int:
    """Same 'to' vnstock uses when no end is given: now (local) + 1 day, unix seconds."""
    return int((dt.datetime.now() + dt.timedelta(days=1)).timestamp())


def fetch_raw_json(symbol: str, count_back: int, to: int | None = None, session: requests.Session | None = None):
    payload = {"timeFrame": "ONE_DAY", "symbols": [vci_code(symbol)], "to": int(to or default_to()), "countBack": int(count_back)}
    try:
        r = (session or requests).post(URL, json=payload, headers=HEADERS, timeout=TIMEOUT)
    except requests.RequestException as e:
        raise VCIDirectError(f"{symbol}: network error: {type(e).__name__}: {e}") from e
    if r.status_code != 200:
        raise VCIDirectError(f"{symbol}: HTTP {r.status_code} from VCI: {r.text[:200]!r}")
    try:
        j = r.json()
    except ValueError as e:
        raise VCIDirectError(f"{symbol}: non-JSON response: {r.text[:200]!r}") from e
    return j, payload


def parse(j, symbol: str) -> pd.DataFrame:
    if isinstance(j, dict) and "data" in j:
        j = j["data"]
    if not isinstance(j, list) or not j or not isinstance(j[0], dict):
        raise VCIDirectError(f"{symbol}: malformed JSON (expected non-empty list of dicts): {str(j)[:200]}")
    d = j[0]
    keys = ("t", "o", "h", "l", "c", "v")
    if any(k not in d or not isinstance(d[k], list) for k in keys):
        raise VCIDirectError(f"{symbol}: malformed JSON, missing arrays; keys={list(d)}")
    n = {k: len(d[k]) for k in keys}
    if len(set(n.values())) != 1:
        raise VCIDirectError(f"{symbol}: ragged arrays {n}")
    if n["t"] == 0:
        raise VCIDirectError(f"{symbol}: VCI returned no bars")
    df = pd.DataFrame({"t": d["t"], "open": d["o"], "high": d["h"], "low": d["l"], "close": d["c"], "volume": d["v"]})
    if df.isna().any().any():
        raise VCIDirectError(f"{symbol}: null values in VCI arrays")
    ts = pd.to_datetime(df["t"].astype(int), unit="s").dt.tz_localize("UTC").dt.tz_convert("Asia/Ho_Chi_Minh")
    df["date"] = ts.dt.tz_localize(None).dt.normalize()
    px = ["open", "high", "low", "close"]
    try:
        df[px] = df[px].astype(float)
        df["t"] = df["t"].astype(int)
    except (TypeError, ValueError) as e:
        raise VCIDirectError(f"{symbol}: non-numeric values in VCI arrays") from e
    if (df[px] <= 0).any().any():
        raise VCIDirectError(f"{symbol}: non-positive price in VCI arrays")
    if asset_type(symbol) == "stock":
        df[px] = df[px].div(1000)
    df[px] = df[px].round(2)
    df["volume"] = df["volume"].astype("int64")
    df = df[COLS]
    if df["date"].duplicated().any():
        raise VCIDirectError(f"{symbol}: duplicate dates in VCI response")
    return flag_suspicious(df)


def fetch(symbol: str, count_back: int, to: int | None = None, session: requests.Session | None = None) -> pd.DataFrame:
    """Daily bars [date, open, high, low, close, volume, open_suspicious], oldest first. May include today's in-progress bar."""
    asset_type(symbol)  # raise early on unmapped symbols
    j, _ = fetch_raw_json(symbol, count_back, to, session)
    return parse(j, symbol)


if __name__ == "__main__":
    sym = sys.argv[1] if len(sys.argv) > 1 else "VN30F1M"
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    print(fetch(sym, n).to_string(index=False))
