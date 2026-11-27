# Claude Code spec — direct VCI fetcher (replace vnstock after the v4/v5 sunset)

RUN THIS ON THE MAC (it needs live network to VCI; the cloud sandbox cannot reach Vietnamese hosts).

## Goal
A standalone, credential-free fetcher that replaces `vnstock 4.0.4 -> VCI` for daily OHLC of the indices, VN30 futures, and constituents, so the project (and the weekly track-forward) survive when the vnstock v4/v5 library is retired. It must hit the VCI chart endpoint directly, so it does not depend on the vnstock library continuing to work.

## Known facts
- Endpoint: `POST https://trading.vietcap.com.vn/api/chart/OHLCChart/gap-chart`
- Payload: `{"timeFrame":"ONE_DAY","symbols":[SYM],"to":<unix_seconds>,"countBack":<N>}`
- `src/source_probe.py` already calls it with honest headers and gets **HTTP 400**. vnstock 4.0.4 reaches the same endpoint successfully with **browser-impersonating headers (a browser User-Agent + a Device-Id)**. The missing piece is the headers, not the payload.

## Step 1 — capture the exact headers that work (do this first; do NOT guess)
vnstock 4.0.4 is installed and works. Capture the real outgoing request rather than reverse-engineering headers:
- Easiest: monkeypatch `requests.Session.request` (or `requests.post`) to print `method, url, headers, body`, then run one working `Quote(symbol, source="VCI").history(...)` call. Record the full header dict and the exact `to`/`countBack` it sends.
- Or read vnstock's VCI client source for the headers dict and any Device-Id generation.
Save the captured headers to `results/vci_headers_captured.json` (redact nothing — these are not secrets, just a UA + device id).

## Step 2 — build `src/fetch_vci_direct.py`
- `fetch(symbol, count_back, to=None) -> DataFrame[date, open, high, low, close, volume]` (+ `open_suspicious` computed as `open == prev_close`, same rule the repo already uses).
- Use the captured headers verbatim (generate a fresh random Device-Id per run if vnstock does). Payload as above. Parse the VCI JSON (arrays of o/h/l/c/v and t); convert `t` (unix) to dates in `Asia/Ho_Chi_Minh`.
- Symbol coverage + mapping (confirm each against a working vnstock call): `VNINDEX`, `VN30`, `VN30F1M`, `VN30F2M`, and the VN30 constituents. Note any code differences for index/futures.
- No credentials, no cookies. Fail loudly (raise) on non-200 or malformed JSON.

## Step 3 — VALIDATE before adopting (gate)
- Fetch the last ~40 bars for `VN30F1M`, `VN30`, `VNINDEX`, and 3 stocks (e.g., VCB, FPT, HPG).
- Compare O/H/L/C/V against the frozen reference for the overlapping dates: `data/snapshots/frozen_20261117/` (futures) and `data/raw/` (everything, read-only).
- **Gate: require 100% field match on the overlap** (the only allowed mismatch is the known KBS-style open rounding, which should NOT occur for VCI; if opens differ, stop and report).
- Write the comparison to `results/vci_direct_validation.md` and the fetched bars to `data/raw_probe/` only. Do NOT touch `data/raw/` until the gate passes.

## Step 4 — integrate (only if the gate passes; else stop and report)
- Add behind the existing interface: either a `--source vci_direct` flag in `src/fetch_indices.py`, or a thin adapter the fetchers import. Keep `vnstock->VCI` as the default until Harry switches.
- **HARD STOPS (do not do without Harry):** change the live logger's data source, the frozen boundary (2026-11-17), or the kill rule. Keep the snapshot + old-row guard in `src/track_forward.py` intact.

## Discipline
Pre-register the validation gate in the script header; fresh-reviewer pass on the fetcher + validation; add a `results/LOG.md` entry; never write `data/raw/` before the gate passes; never commit captured headers if they contain anything account-specific (they shouldn't).

## If VCI direct also fails
If the endpoint rejects even the captured headers (e.g., VCI changed auth with the decree), report that and fall back to the pending options: a broker Open API (ACBS — needs Harry's key in an env var) or official HOSE/HNX files. Do not hard-coded any key.
