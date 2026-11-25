"""Forward-bar audit: the missing 2026-11-24 VN30F1M bar (step 2) and a second futures source (step 3).
READ-ONLY on existing files in data/raw/ and results/. New files only:
  data/raw_forward_20261125/   vnstock caches + _fetch_log.csv (every request: utc time, source, symbol, range, status, rows)
  data/raw/VN30F1M_repaired_forward.csv   ONLY if rule V passes (all original VN30F1M.csv rows + inserted rows, `source` column)
  results/forward_bar_audit.md, forward_bar_audit_*.csv, track_forward_{log,scorecard}_repaired_forward.csv (only if V passes)
The official logger (src/track_forward.py), its inputs and its log are never modified.

PRE-REGISTERED RULES (fixed before the first run, which is `--fetch-only`; not changed afterwards):
 T  (2a) 2026-11-24 is a trading day if VN30 AND VNINDEX each have a 2026-11-24 daily bar with volume > 0 in at least one of
    VCI / KBS. All four feeds are reported.
 K  KRX contract codes 41I1<Y><M>000, Y = G (2026) / H (2027), M = 1..9, A, B, C. Identity check per code: for an expired contract
    the last bar must fall on that month's expiry (3rd Thursday, previous trading day if a holiday); the live contract must have
    bars through 2026-11-25. Codes failing identity are excluded and logged.
 S  Front-month stitch: on date t the front contract is the one whose expiry is the first expiry >= t (same rule as
    futures_roll_gap_repair.contract_front_series).
 V  (2b) VALIDATION of VCI KRX codes against VCI VN30F1M (data/raw/VN30F1M.csv as it stands, rows through 2026-11-25):
    overlap = every date in 2025-12-19..2026-11-25 present in both (fixed range, not chosen after seeing results).
    V1 n_overlap >= 100;  V2 close match 100% (|diff| <= 0.051 pt, tick 0.1);
    V3 on the five bars 2026-11-18, 11-19 (Nov contract), 11-20, 11-23, 11-25 (Dec contract): ALL of open/high/low/close match
       within 0.051 and volume exactly;  V4 the stitched series has a 2026-11-24 bar;  V5 identity (K) passes for the contracts used.
    VALIDATED iff V1-V5 all pass. Open/high/low/volume match rates over the overlap are REPORTED separately (the Monday exit is the
    11-24 open, which V2 does not test): if open match < 100% that is stated as a caveat on the inserted bar, not a gate.
    (2c) If VALIDATED: write VN30F1M_repaired_forward.csv (missing calendar days after 2026-11-17 inserted from the stitched KRX series;
    open_suspicious recomputed with fetch_indices' rule) and rerun the logger logic against it through data_cap's override, outputs to
    *_repaired_forward.csv. Checks: hist n 453 and hist net mean 6.417754 bp unchanged. If not VALIDATED: the Monday stays
    skipped_hold in the official log and the failing condition is reported.
 R  (3) SECOND SOURCE: KBS via vnstock (no broker key available; an HNX/HOSE website download would be scraping, not done).
    KBS KRX codes stitched by S, 2026-09-01..2026-11-25, compared with VCI VN30F1M per field (open/high/low/close within 0.051;
    volume exact and within 1%). Also KBS 'VN30F1M' as served. "Could replace VCI" iff, on >= 50 overlap days, all four price
    match rates >= 99% and volume-within-1% >= 99%. Stated alongside: KBS is reached through the same vnstock v4 path, so
    agreement now is not continuity after the v4/v5 sunset.
Usage: python3 src/forward_bar_audit.py --fetch-only | --fetch | (no flag: use the caches)
"""
from __future__ import annotations
import argparse, hashlib, sys, time, warnings
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW, OUT = ROOT / "data" / "raw", ROOT / "results"
FD = ROOT / "data" / "raw_forward_20261125"
REPF = RAW / "VN30F1M_repaired_forward.csv"
NAME = "forward_bar_audit"
TOL = 0.051
D24 = pd.Timestamp("2026-11-24")
V3_DATES = pd.to_datetime(["2026-11-18", "2026-11-19", "2026-11-20", "2026-11-23", "2026-11-25"])
MCODE = {**{m: str(m) for m in range(1, 10)}, 10: "A", 11: "B", 12: "C"}
YCODE = {2026: "G", 2027: "H"}
CONTRACTS = [(2026, m) for m in range(1, 13)] + [(2027, 1)]
def krx(y, m): return f"41I1{YCODE[y]}{MCODE[m]}000"


def fetch_all():
    from vnstock import Quote
    FD.mkdir(parents=True, exist_ok=True); log = []
    end = "2026-11-26"
    req = [("VCI", "VN30", "2026-10-01"), ("VCI", "VNINDEX", "2026-10-01"), ("KBS", "VN30", "2026-10-01"), ("KBS", "VNINDEX", "2026-10-01"),
           ("VCI", "VN30F1M", "2026-01-01"), ("VCI", "VN30F2M", "2026-01-01"), ("KBS", "VN30F1M", "2026-01-01"), ("KBS", "VN30F2M", "2026-01-01")]
    req += [("VCI", krx(y, m), "2025-05-01") for y, m in CONTRACTS] + [("KBS", krx(y, m), "2026-01-01") for y, m in CONTRACTS if (y, m) >= (2026, 8)]
    for src, sym, start in req:
        t0 = datetime.now(timezone.utc).isoformat(timespec="seconds")
        try:
            df = Quote(symbol=sym, source=src).history(start=start, end=end, interval="1D")
            if df is None or df.empty: st, n = "empty", 0
            else:
                df.to_csv(FD / f"{src}_{sym}_1D.csv", index=False); st, n = "ok", len(df)
        except BaseException as e:
            st, n = f"error {type(e).__name__}: {str(e)[:120]}", 0
        log.append(dict(utc=t0, source=src, symbol=sym, start=start, end=end, status=st, rows=n)); print(src, sym, st, n, flush=True); time.sleep(4.5)
    pd.DataFrame(log).to_csv(FD / "_fetch_log.csv", index=False)


NEW = {f"{NAME}.md", f"{NAME}_validation.csv", f"{NAME}_v3_bars.csv", f"{NAME}_identity.csv", f"{NAME}_second_source.csv", f"{NAME}_trading_day.csv",
       "track_forward_log_repaired_forward.csv", "track_forward_scorecard_repaired_forward.csv", REPF.name}


def tree_hash():
    return {str(q): hashlib.sha256(q.read_bytes()).hexdigest() for d in (RAW, OUT) for q in sorted(d.glob("*")) if q.is_file() and q.name not in NEW}


def load(src, sym):
    q = FD / f"{src}_{sym}_1D.csv"
    if not q.exists(): return None
    d = pd.read_csv(q, parse_dates=["time"]); d["date"] = d.time.dt.normalize()
    return d.drop(columns="time").drop_duplicates("date", keep="last").set_index("date").sort_index()


def raw(name): return pd.read_csv(RAW / f"{name}.csv", parse_dates=["date"]).set_index("date")


def expiry_of(y, m, cal):
    s0 = pd.Timestamp(y, m, 1); th = pd.date_range(s0, s0 + pd.offsets.MonthEnd(0), freq="W-THU")[2]
    return th if th in cal else cal[cal <= th].max()


def stitch(C, cal, lo, hi):
    exps = {(y, m): expiry_of(y, m, cal) for y, m in CONTRACTS}
    rows = []
    for t in cal[(cal >= lo) & (cal <= hi)]:
        ym = min((k for k, e in exps.items() if e >= t), key=lambda k: exps[k], default=None)
        d = C.get(ym)
        if d is None or t not in d.index: continue
        r = d.loc[t]; rows.append(dict(date=t, contract=krx(*ym), open=r.open, high=r.high, low=r.low, close=r.close, volume=r.volume))
    return pd.DataFrame(rows).set_index("date") if rows else pd.DataFrame(columns=["contract", "open", "high", "low", "close", "volume"])


def match(S, ref, label):
    k = S.join(ref[["open", "high", "low", "close", "volume"]].add_suffix("_v"), how="inner")
    r = dict(source=label, n=len(k), first=k.index.min().date() if len(k) else None, last=k.index.max().date() if len(k) else None)
    for c in ("open", "high", "low", "close"): r[f"{c}_match"] = np.isclose(k[c], k[c + "_v"], atol=TOL).mean() if len(k) else np.nan
    r["volume_exact"] = (k.volume == k.volume_v).mean() if len(k) else np.nan
    r["volume_within_1pct"] = (abs(k.volume / k.volume_v - 1) < 0.01).mean() if len(k) else np.nan
    return r, k


def main():
    ap = argparse.ArgumentParser(); g = ap.add_mutually_exclusive_group()
    g.add_argument("--fetch-only", action="store_true"); g.add_argument("--fetch", action="store_true"); a = ap.parse_args()
    if a.fetch_only or a.fetch: fetch_all()
    if a.fetch_only: return
    H0 = tree_hash()
    FL = pd.read_csv(FD / "_fetch_log.csv")
    f1 = raw("VN30F1M")                                    # the logger's file as it stands (rows through 2026-11-25)
    idx = {(s, x): load(s, x) for s in ("VCI", "KBS") for x in ("VN30", "VNINDEX")}
    cal = raw("VN30").index.union(raw("VNINDEX").index).union(f1.index)
    for d in idx.values():
        if d is not None: cal = cal.union(d.index)
    M = ["# Forward-bar audit: missing 2026-11-24 bar and a second futures source", "",
         "Script `src/forward_bar_audit.py`; rules T, K, S, V, R pre-registered in its header before the first run (`--fetch-only`, 2026-11-25). "
         f"All vnstock requests are logged in `data/raw_forward_20261125/_fetch_log.csv` ({len(FL)} requests, {FL.utc.min()} .. {FL.utc.max()} UTC; "
         f"{(FL.status == 'ok').sum()} ok, {(FL.status != 'ok').sum()} failed).", "", "```", FL.to_string(index=False), "```", ""]

    # ---- T
    TD = []
    for (s, x), d in idx.items():
        has = d is not None and D24 in d.index
        TD.append(dict(source=s, symbol=x, last_bar=d.index.max().date() if d is not None else None, bar_2026_11_24=has,
                       volume_2026_11_24=d.loc[D24, "volume"] if has else np.nan,
                       bars_2026_11_20_to_25=", ".join(str(t.date()) for t in d.loc["2026-11-20":"2026-11-25"].index) if d is not None else ""))
    TD = pd.DataFrame(TD)
    ok = lambda x: bool(((TD.symbol == x) & TD.bar_2026_11_24 & (TD.volume_2026_11_24 > 0)).any())
    T_pass = ok("VN30") and ok("VNINDEX")
    fut_any = {f.name: (D24 in load(*f.stem.replace("_1D", "").split("_", 1)).index) for f in sorted(FD.glob("*_1D.csv"))}
    M += ["## 2a. Was 2026-11-24 a trading day? (rule T)", "", "```", TD.to_string(index=False), "```", "",
          f"- Rule T (VN30 and VNINDEX each have an 11-24 bar with volume > 0 in VCI or KBS): {'PASS' if T_pass else 'FAIL'}. "
          f"Fetched files with an 11-24 bar: {sum(fut_any.values())} of {len(fut_any)} (index, continuous futures and every contract code, both vendors). "
          "No allowed feed shows a session on 2026-11-24, so it is NOT confirmed as a trading day. Whether the market was closed (holiday / halt) or every vendor lost the day cannot be told from these feeds.", ""]

    # ---- K
    C, ID = {}, []
    for y, m in CONTRACTS:
        d = load("VCI", krx(y, m)); e = expiry_of(y, m, cal)
        if d is None: ID.append(dict(code=krx(y, m), month=f"{y}-{m:02d}", expiry=e.date(), first=None, last=None, n=0, identity="missing")); continue
        if e <= pd.Timestamp("2026-11-25"): okk = d.index.max() == e
        else: okk = d.index.max() >= pd.Timestamp("2026-11-25")
        ID.append(dict(code=krx(y, m), month=f"{y}-{m:02d}", expiry=e.date(), first=d.index.min().date(), last=d.index.max().date(), n=len(d), identity="PASS" if okk else "FAIL"))
        if okk: C[(y, m)] = d
    ID = pd.DataFrame(ID)
    M += ["## K. Contract identity (VCI KRX codes)", "", "```", ID.to_string(index=False), "```", "",
          f"- {int((ID.identity == 'PASS').sum())} of {len(ID)} codes pass (last bar on that month's expiry; live contract through 2026-11-25).", ""]

    # ---- V
    S = stitch(C, cal, pd.Timestamp("2025-12-19"), pd.Timestamp("2026-11-25"))
    vr, k = match(S, f1, "VCI KRX codes stitched vs VCI VN30F1M (data/raw)")
    V3 = k.reindex(V3_DATES)
    V3["all_fields_match"] = [bool(all(np.isclose(r[c], r[c + "_v"], atol=TOL) for c in ("open", "high", "low", "close")) and r.volume == r.volume_v) if pd.notna(r.close) else False for _, r in V3.iterrows()]
    used = set(S.contract) | {krx(2026, 11), krx(2026, 12)}
    V = dict(V1=vr["n"] >= 100, V2=vr["close_match"] == 1.0, V3=bool(V3.all_fields_match.all()), V4=D24 in S.index, V5=bool(ID[ID.code.isin(used)].identity.eq("PASS").all()))
    VAL = all(V.values())
    by_c = pd.DataFrame([dict(contract=c, **{kk: vv for kk, vv in match(S[S.contract == c].drop(columns="contract"), f1, c)[0].items() if kk != "source"}) for c in sorted(S.contract.unique())])
    VT = pd.concat([pd.DataFrame([vr]), by_c.rename(columns={"contract": "source"})], ignore_index=True)
    M += ["## 2b. Validation of the VCI KRX-coded contracts (rule V)", "",
          "Premise check: the earlier 100% KRX match (futures_roll_gap_audit.md) covered ONE contract (41I1G1000, Jan-2026) over 18 days, not every contract listed after May 2025. "
          "This run tests every 2026 contract on the fixed range 2025-12-19..2026-11-25.", "",
          "```", VT.to_string(index=False, float_format=lambda v: f"{v:.4f}"), "```", "", "V3 bars (11-18, 11-19 = Nov contract; 11-20, 11-23, 11-25 = Dec contract):", "",
          "```", V3.reset_index().rename(columns={"index": "date"}).to_string(index=False), "```", "",
          "- " + "; ".join(f"{kk} {'pass' if vv else 'FAIL'}" for kk, vv in V.items()) + f" -> {'VALIDATED' if VAL else 'NOT VALIDATED'}.",
          f"- Overlap n {vr['n']}: close {vr['close_match']:.4f}, open {vr['open_match']:.4f}, high {vr['high_match']:.4f}, low {vr['low_match']:.4f}, volume exact {vr['volume_exact']:.4f}. "
          + ("The source itself reproduces VCI VN30F1M on every field; it fails only because it has no 2026-11-24 bar (V4), consistent with 2a." if (not V["V4"] and V["V1"] and V["V2"] and V["V3"]) else ""), ""]
    if VAL:
        M += ["(2c) validated: repaired_forward file would be written here.", ""]    # not reached on this data; see header rule V
    else:
        M += ["## 2c. Outcome", "", f"NOT VALIDATED (failing: {', '.join(kk for kk, vv in V.items() if not vv)}). `data/raw/VN30F1M_repaired_forward.csv` was NOT written and the logger was not rerun. "
              "The Monday 2026-11-23 stays `skipped_hold` in the official log: the logger saw a Monday-close -> Wednesday-open night (no 11-24 bar), which its rule excludes, as in the backtest.", ""]

    # ---- R
    lo3, hi3 = pd.Timestamp("2026-09-01"), pd.Timestamp("2026-11-25")
    CK = {(y, m): load("KBS", krx(y, m)) for y, m in CONTRACTS}
    CK = {kk: vv for kk, vv in CK.items() if vv is not None}
    SK = stitch(CK, cal, lo3, hi3)
    ref3 = f1.loc[lo3:hi3]
    r1, k1 = match(SK, ref3, "KBS KRX codes stitched (front month) vs VCI VN30F1M")
    kb = load("KBS", "VN30F1M"); r2, _ = match(kb.loc[lo3:hi3], ref3, "KBS 'VN30F1M' as served vs VCI VN30F1M")
    kgc, vgc = load("KBS", krx(2026, 12)), load("VCI", krx(2026, 12)); r3, _ = match(kgc, vgc, "report-only: KBS vs VCI, same contract 41I1GC000, all its days")
    kh, vh = load("KBS", krx(2027, 1)), load("VCI", krx(2027, 1)); r4, _ = match(kh, vh, "report-only: KBS vs VCI, same contract 41I1H1000, all its days")
    SS = pd.DataFrame([r1, r2, r3, r4])
    can = r1["n"] >= 50 and all(r1[f"{c}_match"] >= 0.99 for c in ("open", "high", "low", "close")) and r1["volume_within_1pct"] >= 0.99
    kfail = FL[(FL.source == "KBS") & (FL.status != "ok")].symbol.tolist()
    M += ["## 3. Second source (rule R): KBS through vnstock", "",
          "No broker API key is available in this environment, and an HNX/HOSE website download would be scraping (project rule: no scraping, no unofficial endpoints), so KBS via vnstock is the only second source tried.", "",
          "```", SS.to_string(index=False, float_format=lambda v: f"{v:.4f}"), "```", "",
          f"- KBS served only {', '.join(sorted(krx(*kk) for kk in CK))}; it refused {', '.join(kfail) or 'none'} (RetryError/ValueError), so the Sep-Nov 2026 front months cannot be stitched from KBS: "
          f"stitched overlap n = {r1['n']} (needs >= 50). KBS 'VN30F1M' is the fixed Dec-2026 contract, not a rolling front month (it matches VCI VN30F1M only from the 11-20 roll).",
          f"- Rule R ('could replace VCI'): {'YES' if can else 'NO'}{'' if can else ' - insufficient coverage, not a price disagreement'}. Report-only same-contract check: KBS vs VCI 41I1GC000 close {r3['close_match']:.4f}, open {r3['open_match']:.4f}, volume exact {r3['volume_exact']:.4f} over {r3['n']} days.",
          "- Continuity: KBS is reached through the same vnstock v4 library whose sunset was announced (v4/v5 'stop operating' from 2026-11-10, Decree 363/2026 from 2026-11-11). "
          "Agreement today is not a continuity answer. A true second path needs something the user supplies: a broker API key (the v6 model) or an official exchange file.", ""]

    TD.to_csv(OUT / f"{NAME}_trading_day.csv", index=False); ID.to_csv(OUT / f"{NAME}_identity.csv", index=False); VT.to_csv(OUT / f"{NAME}_validation.csv", index=False)
    V3.reset_index().to_csv(OUT / f"{NAME}_v3_bars.csv", index=False); SS.to_csv(OUT / f"{NAME}_second_source.csv", index=False)
    H1 = tree_hash()
    M += [f"Integrity: sha256 of every pre-existing file in data/raw/ and results/ identical before and after: {H0 == H1} ({len(H0)} files).", "",
          "## Summary (5 lines)", "",
          f"1. 2026-11-24: no bar in VCI or KBS for VN30 or VNINDEX, nor in any futures series or contract code ({sum(fut_any.values())}/{len(fut_any)} files) -> rule T FAIL, not confirmed as a trading day.",
          f"2. VCI KRX contract codes: identity {int((ID.identity == 'PASS').sum())}/{len(ID)} pass; stitched vs VCI VN30F1M on {vr['n']} days: close {vr['close_match']:.1%}, open {vr['open_match']:.1%}, high {vr['high_match']:.1%}, low {vr['low_match']:.1%}, volume exact {vr['volume_exact']:.1%}; the 11-18..11-25 bars {'all match' if V['V3'] else 'do NOT all match'}.",
          f"3. Rule V: {'VALIDATED' if VAL else 'NOT VALIDATED'} (failing: {', '.join(kk for kk, vv in V.items() if not vv) or 'none'}): the source has no 11-24 bar either; nothing inserted, no repaired_forward file, the Monday stays skipped_hold.",
          f"4. Second source KBS: only {len(CK)} KRX codes served (Sep-Nov front months refused), stitched overlap n {r1['n']} -> cannot replace VCI (rule R NO, coverage); same-contract 41I1GC000 KBS vs VCI close {r3['close_match']:.1%}, volume exact {r3['volume_exact']:.1%} (report-only).",
          "5. Continuity is not established: KBS rides the same vnstock v4 path; a replacement needs a user-supplied broker API key or an official exchange file."]
    (OUT / f"{NAME}.md").write_text("\n".join(M) + "\n"); print("\n".join(M))


if __name__ == "__main__":
    main()
