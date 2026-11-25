"""Data-source continuity probe (section D). READ-ONLY on data/raw and results; writes fetched bars only to data/raw_probe/<run_utc>/ and its own
results/source_probe* outputs. Does NOT change the logger, fetch_indices defaults, or any schedule. Adoption of any source is a HARD STOP (user decision).

PRE-REGISTERED (before the first run)
Symbols: VN30F1M (continuous, as the logger reads it), 41I1GC000 (Dec-2026 contract = current front month until its 2026-12-17 expiry), VN30, VNINDEX. Daily bars.
Window: the last 10 sessions available in each source up to the run date.
Probes:
 P1 installed vnstock (version printed) via Quote(symbol, source="VCI").history  - the logger's current path.
 P2 direct POST to VCI's public chart endpoint (the one vnstock 4.0.4 wraps: trading.vietcap.com.vn/api/chart/OHLCChart/gap-chart, payload
    {timeFrame: ONE_DAY, symbols:[s], to: <unix>, countBack: 15}). Headers: an honest generic client User-Agent plus the Referer/Origin vnstock uses.
    NO browser-impersonation / device-id spoofing; if the endpoint refuses that, record the refusal and stop the branch.
 P3 installed vnstock via Quote(symbol, source="KBS").history (known limits: refuses recent contracts, rounds opens).
 P0 newer vnstock with a free key: checked separately (PyPI listing, web); no registration, no credential entered. Recorded in the md only.
Comparison: for each source x symbol and each of its last 10 sessions: match vs data/raw/<file> (current) and vs the frozen copy where one exists
 (futures only, frozen at 2026-11-17). Per field open/high/low/close: |diff| <= 1e-6 (same units after vnstock's scaling) ; volume exact.
 Missing days: sessions present in a source but absent in data/raw and vice versa within the overlap window; 2026-11-24 called out.
 A source is "REPLACEMENT-GRADE on this probe" only if close match = 100% and all OHLCV >= 99% on every symbol over overlapping sessions AND it returns
 bars after the last data/raw date. That is a probe statement, not an adoption decision.
Each request is logged (utc, probe, symbol, status, rows) to data/raw_probe/<run>/_fetch_log.csv. BaseException is caught (vnstock's limiter raises SystemExit).
Usage: python3 src/source_probe.py
"""
from __future__ import annotations
import sys, json, time, hashlib, datetime as dt
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parent.parent; RAW = ROOT / "data" / "raw"; OUT = ROOT / "results"; NAME = "source_probe"
FROZEN = ROOT / "data" / "snapshots" / "frozen_20261117"
RUN = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ"); PROBE = ROOT / "data" / "raw_probe" / RUN
SYMS = ["VN30F1M", "41I1GC000", "VN30", "VNINDEX"]
RAWFILE = {"VN30F1M": "VN30F1M", "41I1GC000": None, "VN30": "VN30", "VNINDEX": "VNINDEX"}
LOG = []


def hash_tree():
    h = {}
    for d in (RAW, OUT):
        for p in sorted(d.glob("*")):
            if p.is_file(): h[str(p)] = hashlib.sha256(p.read_bytes()).hexdigest()
    return h


def log(probe, sym, status, rows):
    LOG.append(dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(), probe=probe, symbol=sym, status=status, rows=rows))


def p_vnstock(sym, source):
    try:
        from vnstock import Quote
        start = (dt.date.today() - dt.timedelta(days=30)).isoformat(); end = dt.date.today().isoformat()
        df = Quote(symbol=sym, source=source).history(start=start, end=end, interval="1D")
        df = df.rename(columns={"time": "date"}); df["date"] = pd.to_datetime(df["date"]).dt.normalize()
        log(f"vnstock-{source}", sym, "ok", len(df)); return df[["date", "open", "high", "low", "close", "volume"]]
    except BaseException as e:  # noqa: BLE001  (vnstock limiter raises SystemExit)
        log(f"vnstock-{source}", sym, f"{type(e).__name__}: {str(e)[:120]}", 0); return None


def p_vci_direct(sym):
    import requests
    url = "https://trading.vietcap.com.vn/api/chart/OHLCChart/gap-chart"
    to = int((dt.datetime.now() + dt.timedelta(days=1)).timestamp())
    headers = {"User-Agent": "overnight-effect-research-probe/1.0 (python-requests)", "Content-Type": "application/json",
               "Referer": "https://trading.vietcap.com.vn/", "Origin": "https://trading.vietcap.com.vn/"}
    try:
        r = requests.post(url, json={"timeFrame": "ONE_DAY", "symbols": [sym], "to": to, "countBack": 15}, headers=headers, timeout=20)
        if r.status_code != 200:
            log("vci-direct", sym, f"HTTP {r.status_code}", 0); return None
        j = r.json(); j = j["data"] if isinstance(j, dict) and "data" in j else j
        d = j[0] if isinstance(j, list) and j else None
        if not d or "o" not in d:
            log("vci-direct", sym, "no data", 0); return None
        df = pd.DataFrame({"date": pd.to_datetime(pd.Series(d["t"]).astype(int), unit="s", utc=True).dt.tz_convert("Asia/Ho_Chi_Minh").dt.tz_localize(None).dt.normalize(),
                           "open": d["o"], "high": d["h"], "low": d["l"], "close": d["c"], "volume": d["v"]})
        log("vci-direct", sym, "ok", len(df)); return df
    except BaseException as e:  # noqa: BLE001
        log("vci-direct", sym, f"{type(e).__name__}: {str(e)[:120]}", 0); return None


def compare(src, ref, label):
    if src is None or ref is None: return None
    s10 = src.sort_values("date").drop_duplicates("date").tail(10).set_index("date")
    r = ref.rename(columns={"time": "date"}).copy(); r["date"] = pd.to_datetime(r["date"]).dt.normalize(); r = r.set_index("date")
    ov = s10.index.intersection(r.index)
    if len(ov) == 0: return dict(ref=label, overlap=0)
    row = dict(ref=label, overlap=len(ov), src_first=str(s10.index.min().date()), src_last=str(s10.index.max().date()),
               missing_in_ref=",".join(str(d.date()) for d in s10.index if d not in r.index and d <= r.index.max()),
               after_ref_last=int((s10.index > r.index.max()).sum()), ref_last=str(r.index.max().date()))
    for f_ in ("open", "high", "low", "close"):
        row[f"{f_}_match_pct"] = float((np.abs(s10.loc[ov, f_].astype(float) - r.loc[ov, f_].astype(float)) <= 1e-6).mean() * 100)
    row["volume_match_pct"] = float((s10.loc[ov, "volume"].astype(float) == r.loc[ov, "volume"].astype(float)).mean() * 100)
    row["max_abs_close_diff"] = float(np.abs(s10.loc[ov, "close"].astype(float) - r.loc[ov, "close"].astype(float)).max())
    return row


def main():
    H0 = hash_tree(); PROBE.mkdir(parents=True, exist_ok=True)
    try:
        import importlib.metadata as md; ver = md.version("vnstock")
    except Exception: ver = "unknown"
    res = {}
    for sym in SYMS:
        res[("P1 vnstock VCI", sym)] = p_vnstock(sym, "VCI"); time.sleep(3)
        res[("P2 VCI direct", sym)] = p_vci_direct(sym); time.sleep(3)
        res[("P3 vnstock KBS", sym)] = p_vnstock(sym, "KBS"); time.sleep(3)
    for (probe, sym), df in res.items():
        if df is not None: df.to_csv(PROBE / f"{probe.split()[0]}_{probe.split()[-1]}_{sym}.csv", index=False)
    pd.DataFrame(LOG).to_csv(PROBE / "_fetch_log.csv", index=False)
    rows = []
    for (probe, sym), df in res.items():
        refs = []
        if RAWFILE[sym]: refs.append((pd.read_csv(RAW / f"{RAWFILE[sym]}.csv"), f"data/raw/{RAWFILE[sym]}.csv"))
        fz = FROZEN / f"{RAWFILE[sym]}.csv" if RAWFILE[sym] else None
        if fz and fz.exists(): refs.append((pd.read_csv(fz), f"frozen/{RAWFILE[sym]}.csv"))
        if sym == "41I1GC000":
            p = ROOT / "data" / "raw_forward_20261125"
            cand = sorted(p.glob("*41I1GC000*.csv"))
            for c in cand: refs.append((pd.read_csv(c), f"raw_forward_20261125/{c.name}"))
        if df is None:
            key = {"P1 vnstock VCI": "vnstock-VCI", "P2 VCI direct": "vci-direct", "P3 vnstock KBS": "vnstock-KBS"}[probe]
            rows.append(dict(probe=probe, symbol=sym, ref="-", status=next((l["status"] for l in reversed(LOG) if l["probe"] == key and l["symbol"] == sym), "fail")))
            continue
        has1124 = bool((df.date == pd.Timestamp("2026-11-24")).any())
        for ref, lab in refs:
            c = compare(df, ref, lab)
            if c: rows.append(dict(probe=probe, symbol=sym, status="ok", has_2026_11_24=has1124, **c))
    R = pd.DataFrame(rows)
    R.to_csv(OUT / f"{NAME}_matches.csv", index=False)
    def grade(probe):
        g = R[(R.probe == probe) & R.ref.astype(str).str.startswith("data/raw")]
        if len(g) == 0 or (R[R.probe == probe].status != "ok").any(): return "NOT replacement-grade on this probe (missing symbols or failed requests)"
        ok = (g.close_match_pct == 100).all() and (g[[c for c in g.columns if c.endswith("_match_pct")]] >= 99).all().all() and (g.after_ref_last > 0).all()
        return "REPLACEMENT-GRADE on this probe" if ok else "NOT replacement-grade on this probe"
    GR = {p: grade(p) for p in ("P1 vnstock VCI", "P2 VCI direct", "P3 vnstock KBS")}
    H1 = hash_tree(); outs = {f"{NAME}.md", f"{NAME}_matches.csv"}
    changed = [k for k in H1 if k in H0 and H0[k] != H1[k] and Path(k).name not in outs]
    integrity = not changed and all(Path(k).name in outs for k in H1 if k not in H0)
    f = lambda D: D.to_string(index=False, float_format=lambda v: f"{v:.2f}")
    L = [f"# Data-source continuity probe (src/{NAME}.py), run {RUN}", "", f"Installed vnstock {ver}. Fetched bars and request log: data/raw_probe/{RUN}/. Rules pre-registered in the header.", "",
         "## Request log", "", "```", pd.DataFrame(LOG).to_string(index=False), "```", "", "## Last-10-session match rates", "", "```", f(R), "```", "",
         "## Grades (probe statement, not an adoption decision)", ""] + [f"- {k}: {v}" for k, v in GR.items()] + ["", f"Integrity (data/raw and results unchanged except own outputs): {integrity}"]
    (OUT / f"{NAME}.md").write_text("\n".join(L) + "\n"); print("\n".join(L)); assert integrity


if __name__ == "__main__":
    main()
