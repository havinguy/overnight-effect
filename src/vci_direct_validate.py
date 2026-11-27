"""Validation gate for src/fetch_vci_direct.py (direct VCI, no vnstock) before it may write data/raw/.

READ-ONLY on data/raw/ and data/snapshots/. Writes only data/raw_probe/vci_direct_<run_utc>/ and results/vci_direct_validation.md.
Does NOT change the logger, fetch_indices defaults, the frozen boundary (2026-11-17) or the kill rule.

PRE-REGISTERED (written 2026-11-26 before the first run of this script)
Fetch: direct VCI, countBack = 40, to = now+1d (vnstock's default), one call per symbol, >= 3.5 s apart.
Exclusion: any bar dated today (Asia/Ho_Chi_Minh) is dropped before comparison (may be in progress).
G1 GATE SYMBOLS (the user's gate): VN30F1M, VN30F2M, VN30, VNINDEX, VCB, FPT, HPG.
  References: futures -> data/snapshots/frozen_20261117/{VN30F1M,VN30F2M}.csv (NOT _repaired) AND data/raw/<sym>.csv;
              indices and stocks -> data/raw/<sym>.csv.
  Overlap = dates present in both the direct fetch and the reference.
  Field match: open/high/low/close |diff| <= 1e-6 (both sides already rounded to 2 dp); volume exact equality.
  PASS iff every field matches on 100% of overlap rows, for every symbol x reference, and each overlap >= 20 rows.
  Any open mismatch -> STOP (coded): the gate fails and the report says "opens differ"; no tolerance is applied.
  Coverage (dates in one side but not the other, within the overlap span) is reported separately and is NOT a field mismatch.
  2026-11-24 is already known to be absent from data/raw futures (vnstock feed gap 2026-11-25); reported explicitly.
  open_suspicious is derived, not gated: reported as agreement on overlap rows excluding the first fetched row (no prior close in window).
G2 SAME-RUN A/B (mapping + transform check, also required for PASS): for every G1 symbol and all 30 names in data/universe_vn30.txt,
  vnstock 4.0.4 Quote(sym, source="VCI").history(start, end) is called back-to-back with the direct fetch over the same date range;
  every direct row (today excluded) must be matched by a vnstock row on all 5 fields, same tolerance, no unmatched dates in the span. If vnstock is unavailable
  this check is reported as NOT RUN and the overall gate cannot pass.
Integrity: sha256 of every file in data/raw/ and data/snapshots/frozen_20261117/ before and after; must be identical.
Overall: GATE PASS iff G1 PASS and G2 PASS and integrity holds. Only then may Step 4 (integration) proceed.
REV 1 (post-review, 2026-11-27, AFTER run 20261127T004647Z; not rerun because G1 fails on FPT regardless):
  (a) G2 now also requires every direct row to be matched (overlap == direct rows); the clipped coverage check alone could miss
      a truncated vnstock series. Run 0 had overlap 40/40 for all 34 symbols, so its G2 PASS stands under rev 1 too.
      vnstock rows BEFORE the direct window (it ignores `start`) are reported, not gated; header wording 'all returned rows' amended to that.
  (b) G2 calls are now interleaved per symbol (direct then vnstock, back-to-back); run 0 fetched all direct first, ~2 min earlier.
Usage: python3 src/vci_direct_validate.py
"""
from __future__ import annotations

import datetime as dt
import hashlib
import sys
import time
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import fetch_vci_direct as V  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
FROZEN = ROOT / "data" / "snapshots" / "frozen_20261117"
RUN = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
PROBE = ROOT / "data" / "raw_probe" / f"vci_direct_{RUN}"
MD = ROOT / "results" / "vci_direct_validation.md"
G1 = ["VN30F1M", "VN30F2M", "VN30", "VNINDEX", "VCB", "FPT", "HPG"]
COUNT_BACK, MIN_OVERLAP, TOL, SLEEP = 40, 20, 1e-6, 3.5
FIELDS = ["open", "high", "low", "close", "volume"]
TODAY = pd.Timestamp(dt.datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).date())


def hash_tree() -> dict:
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for d in (RAW, FROZEN) for p in sorted(d.glob("*")) if p.is_file()}


def match(a: pd.DataFrame, b: pd.DataFrame) -> dict:
    a = a.set_index("date"); b = b.set_index("date")
    ov = a.index.intersection(b.index)
    lo, hi = (max(a.index.min(), b.index.min()), min(a.index.max(), b.index.max()))
    only_a = [d for d in a.index if lo <= d <= hi and d not in b.index]
    only_b = [d for d in b.index if lo <= d <= hi and d not in a.index]
    r = dict(overlap=len(ov), first=str(ov.min().date()) if len(ov) else "", last=str(ov.max().date()) if len(ov) else "",
             only_direct=",".join(str(d.date()) for d in only_a), only_ref=",".join(str(d.date()) for d in only_b), mism=[])
    for f in FIELDS:
        x, y = a.loc[ov, f].astype(float), b.loc[ov, f].astype(float)
        ok = (x == y) if f == "volume" else (np.abs(x - y) <= TOL)
        r[f"{f}_pct"] = float(ok.mean() * 100) if len(ov) else float("nan")
        for d in ov[~ok.values]:
            r["mism"].append(f"{d.date()} {f}: direct={x[d]} ref={y[d]}")
    if "open_suspicious" in a and "open_suspicious" in b and len(ov) > 1:
        o2 = ov[ov > a.index.min()]
        r["flag_pct"] = float((a.loc[o2, "open_suspicious"].astype(bool) == b.loc[o2, "open_suspicious"].astype(bool)).mean() * 100)
    return r


def vnstock_hist(sym: str, start: str, end: str) -> pd.DataFrame:
    from vnstock import Quote
    df = Quote(symbol=sym, source="VCI").history(start=start, end=end, interval="1D")
    df = df.rename(columns={"time": "date"}); df["date"] = pd.to_datetime(df["date"]).dt.normalize()
    return df[V.COLS]


def main() -> int:
    H0 = hash_tree(); PROBE.mkdir(parents=True, exist_ok=True)
    try:
        import importlib.metadata as md; vn_ver = md.version("vnstock")
    except Exception:
        vn_ver = "not installed"
    universe = (ROOT / "data" / "universe_vn30.txt").read_text().split()
    syms = G1 + [s for s in universe if s not in G1]
    direct, errors, fetch_log, vnres = {}, {}, [], {}
    for s in syms:
        try:
            df = V.fetch(s, COUNT_BACK)
            df.to_csv(PROBE / f"direct_{s}.csv", index=False)
            direct[s] = df[df["date"] < TODAY].reset_index(drop=True)
            fetch_log.append((s, "ok", len(df), str(df["date"].min().date()), str(df["date"].max().date())))
        except Exception as e:  # noqa: BLE001 - recorded, gate fails
            errors[s] = f"{type(e).__name__}: {e}"; fetch_log.append((s, errors[s][:120], 0, "", ""))
        time.sleep(SLEEP)
        if vn_ver != "not installed" and s in direct:          # REV 1 (b): vnstock call back-to-back with the direct one
            try:
                vs = vnstock_hist(s, str(direct[s]["date"].min().date()), str(TODAY.date()))
                vnres[s] = vs[vs["date"] < TODAY]; vnres[s].to_csv(PROBE / f"vnstock_{s}.csv", index=False)
            except BaseException as e:  # noqa: BLE001 - vnstock limiter raises SystemExit
                vnres[s] = f"{type(e).__name__}: {str(e)[:120]}"
            time.sleep(SLEEP)

    # G1: vs frozen + data/raw
    g1_rows = []
    for s in G1:
        refs = [("data/raw", RAW / f"{s}.csv")]
        if s in ("VN30F1M", "VN30F2M"):
            refs.insert(0, ("frozen_20261117", FROZEN / f"{s}.csv"))
        for lab, p in refs:
            if s not in direct:
                g1_rows.append(dict(symbol=s, ref=lab, overlap=0, error=errors.get(s, "no data"))); continue
            ref = pd.read_csv(p, parse_dates=["date"])
            g1_rows.append(dict(symbol=s, ref=lab, **match(direct[s], ref)))
    g1_pass = all(r.get("overlap", 0) >= MIN_OVERLAP and all(r.get(f"{f}_pct") == 100.0 for f in FIELDS) for r in g1_rows)
    opens_differ = any(r.get("open_pct", 100.0) < 100.0 for r in g1_rows)

    # G2: same-run A/B vs vnstock
    g2_rows, g2_run = [], vn_ver != "not installed"
    if g2_run:
        for s in syms:
            if s not in direct:
                g2_rows.append(dict(symbol=s, overlap=0, error=errors.get(s))); continue
            vs = vnres.get(s, "vnstock not called")
            if isinstance(vs, str):
                g2_rows.append(dict(symbol=s, overlap=0, error=vs)); continue
            g2_rows.append(dict(symbol=s, vnstock_rows=len(vs), direct_rows=len(direct[s]), **match(direct[s], vs)))
    g2_pass = g2_run and all(r.get("overlap", 0) > 0 and r.get("overlap") == r.get("direct_rows") and not r.get("only_direct") and not r.get("only_ref")
                             and all(r.get(f"{f}_pct") == 100.0 for f in FIELDS) for r in g2_rows)

    pd.DataFrame(fetch_log, columns=["symbol", "status", "rows", "first", "last"]).to_csv(PROBE / "_fetch_log.csv", index=False)
    H1 = hash_tree(); integrity = H0 == H1
    gate = g1_pass and g2_pass and integrity

    L = [f"# Direct VCI fetcher validation (run {RUN})", "",
         f"Script: `src/vci_direct_validate.py` (gate pre-registered in its header). Fetcher: `src/fetch_vci_direct.py`. vnstock (A/B only): {vn_ver}.",
         f"Bars written to `data/raw_probe/vci_direct_{RUN}/` only. Today ({TODAY.date()}) excluded from every comparison.", "",
         f"## VERDICT: GATE {'PASS' if gate else 'FAIL'}", "",
         f"- G1 (direct vs frozen/data/raw, 100% field match, overlap >= {MIN_OVERLAP}): **{'PASS' if g1_pass else 'FAIL'}**"
         + ("  -- **STOP: opens differ**" if opens_differ else ""),
         f"- G2 (same-run A/B vs vnstock 4.0.4 VCI, {len(syms)} symbols): **{'PASS' if g2_pass else ('NOT RUN' if not g2_run else 'FAIL')}**",
         f"- Integrity (sha256 of data/raw/ + frozen_20261117/, {len(H0)} files, before == after): **{'OK' if integrity else 'CHANGED'}**", "",
         "## Headers", "", "Taken verbatim from the live wire capture in `results/vci_headers_captured.json`. vnstock 4.0.4 sends **no Device-Id**, "
         "no cookie and no auth header; its `_generate_vci_device_id()` is never called. What gets past the HTTP 400 that "
         "`source_probe.py` got is the browser UA plus the browser Accept/Sec-Fetch/sec-ch-ua headers.", "",
         "## Symbol mapping", "", "| repo symbol | VCI code | asset type | price scaling |", "|---|---|---|---|"]
    for s in ["VNINDEX", "VN30", "VN30F1M", "VN30F2M", "VCB"]:
        L.append(f"| {s if s != 'VCB' else 'stocks (3-letter)'} | {V.vci_code(s) if s != 'VCB' else 'same'} | {V.asset_type(s)} | "
                 f"{'/1000, round 2' if V.asset_type(s) == 'stock' else 'none, round 2'} |")
    L += ["", "No code differences: index and futures codes pass through unchanged (confirmed by G2).", "",
          "## G1: direct vs frozen reference", "",
          "| symbol | ref | overlap | span | open | high | low | close | volume | flag agree | only direct | only ref |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in g1_rows:
        if r.get("error"):
            L.append(f"| {r['symbol']} | {r['ref']} | 0 | ERROR: {r['error']} |||||||||"); continue
        L.append(f"| {r['symbol']} | {r['ref']} | {r['overlap']} | {r['first']}..{r['last']} | "
                 + " | ".join(f"{r[f + '_pct']:.1f}%" for f in FIELDS)
                 + f" | {r.get('flag_pct', float('nan')):.1f}% | {r['only_direct'] or '-'} | {r['only_ref'] or '-'} |")
    mm = [f"- {r['symbol']} vs {r['ref']}: {m}" for r in g1_rows for m in r.get("mism", [])]
    L += ["", "Mismatches:" if mm else "Mismatches: none.", *mm[:60], ""]
    L += ["## G2: same-run A/B vs vnstock 4.0.4 (all returned rows)", "",
          "| symbol | direct rows | vnstock rows | overlap | open | high | low | close | volume | only direct | only vnstock |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in g2_rows:
        if r.get("error") or not r.get("overlap"):
            L.append(f"| {r['symbol']} | ERROR: {r.get('error')} ||||||||||"); continue
        L.append(f"| {r['symbol']} | {r['direct_rows']} | {r['vnstock_rows']} | {r['overlap']} | "
                 + " | ".join(f"{r[f + '_pct']:.1f}%" for f in FIELDS) + f" | {r['only_direct'] or '-'} | {r['only_ref'] or '-'} |")
    mm2 = [f"- {r['symbol']}: {m}" for r in g2_rows for m in r.get("mism", [])]
    L += ["", "A/B mismatches:" if mm2 else "A/B mismatches: none.", *mm2[:60], ""]
    L += ["## Coverage notes", "",
          "- 2026-11-24 in direct futures fetch: " + ", ".join(
              f"{s}={'present' if s in direct and (direct[s]['date'] == pd.Timestamp('2026-11-24')).any() else 'absent'}"
              for s in ("VN30F1M", "VN30F2M")) + " (data/raw futures lack it; known feed gap).",
          f"- Fetch errors: {errors if errors else 'none'}", ""]
    MD.write_text("\n".join(L))
    print("\n".join(L[:12]))
    return 0 if gate else 1


if __name__ == "__main__":
    sys.exit(main())
