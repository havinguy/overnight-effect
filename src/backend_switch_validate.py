"""Validation gate for the scoped fetch-backend switch (fetch_indices: VN30F1M/VN30F2M/VN30/VNINDEX -> fetch_vci_direct).

READ-ONLY on data/raw/, data/snapshots/ and results/ (except its own results/backend_switch_validation.md). Fetched files go
to data/raw_probe/backend_switch_<run>/ only; the track_forward dry runs execute in throwaway copies of the repo under --scratch.

PRE-REGISTERED (written 2026-11-27 before the first run)
G1 FULL-HISTORY REFETCH, new backend. For each of VN30F1M, VN30F2M (start 2017-08-10, as track_forward.refresh) and VN30, VNINDEX
   (start 2011-01-01, before the first data/raw row 2011-04-28), call fetch_indices.update(sym, start, "VCI", raw_dir=<probe>/direct,
   full=True), i.e. the real code path with backend vci_direct. Compare with data/raw/<sym>.csv (all 4) and with
   data/snapshots/frozen_20261117/<sym>.csv (futures) on every overlapping date, excluding today (Asia/Ho_Chi_Minh).
   open/high/low/close |diff| <= 1e-6, volume exact, open_suspicious equal (the first fetched row is excluded from the flag check because it has no prior close).
   PASS iff every field = 100% on every symbol x reference. Any mismatch -> STOP: the switch is not usable, report it.
   Coverage (dates on one side only) is reported separately and is not a field mismatch.
G2 SAME-RUN A/B (diagnostic + transport check). The same calls with OVERNIGHT_FETCH_BACKEND=vnstock into <probe>/vnstock, run back-to-back per
   symbol. The two output CSVs should be byte-identical. If they are not, the differing rows are reported. G2 FAIL also blocks.
G3 TRACK_FORWARD DRY RUN. Two copies of the repo (src, results, data/raw, data/snapshots/{frozen_20261117,20261125_pre_v6}, data/*.txt|csv):
   copy D (default env = direct backend) and copy V (OVERNIGHT_FETCH_BACKEND=vnstock). In each copy run
   (a) `python3 src/track_forward.py`: exit 0; boundary, log and scorecard byte-identical to the live results/;
   (b) `python3 src/track_forward.py --refresh`: exit 0 (the old-row guard did not trip), with '[fetch] ... backend=vci_direct' printed in D and 'backend=vnstock' in V;
       boundary byte-identical; every row of VN30F1M/VN30F2M dated <= 2026-11-17 byte-identical to the live data/raw rows; scorecard identical to the
       live scorecard (any new forward Monday is reported instead of failing). D and V must produce byte-identical VN30F1M/F2M, log and scorecard.
G4 INTEGRITY. sha256 of data/raw/*, data/snapshots/frozen_20261117/*, results/track_forward_{boundary.txt,log.csv,scorecard.csv} and
   src/track_forward.py before == after.
Overall PASS iff G1, G2, G3 and G4 all pass.
REV 1 (2026-11-27, after run 0 crashed in report formatting, BEFORE any verdict was printed): run 0 showed vnstock 4.0.4 now enforces a
  community '1D limited to 8 years' cap (vnai), so with OVERNIGHT_FETCH_BACKEND=vnstock a full refetch of VN30F2M/VN30/VNINDEX starts 2018-11-29,
  while direct VCI returns the full history. G2 is therefore redefined: on the dates vnstock returns, every field (O/H/L/C/V and open_suspicious,
  excluding each side's first row) must match 100%, and vnstock must not return dates the direct fetch lacks. Byte-identity is still reported.
  G1 and G3 (the user's gate) are unchanged. The report table uses to_string (tabulate is not installed).
Usage: python3 src/backend_switch_validate.py --scratch <dir outside the repo>
"""
from __future__ import annotations
import argparse, datetime as dt, hashlib, os, shutil, subprocess, sys, time
from pathlib import Path
from zoneinfo import ZoneInfo
import numpy as np, pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import fetch_indices as F  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent; RAW = ROOT / "data" / "raw"; FROZEN = ROOT / "data" / "snapshots" / "frozen_20261117"
RES = ROOT / "results"; MD = RES / "backend_switch_validation.md"; PY = sys.executable
RUN = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ"); PROBE = ROOT / "data" / "raw_probe" / f"backend_switch_{RUN}"
TODAY = pd.Timestamp(dt.datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).date()); CAP = pd.Timestamp("2026-11-17")
SYMS = {"VN30F1M": "2017-08-10", "VN30F2M": "2017-08-10", "VN30": "2011-01-01", "VNINDEX": "2011-01-01"}
TF_FILES = ["track_forward_boundary.txt", "track_forward_log.csv", "track_forward_scorecard.csv"]
FIELDS = ["open", "high", "low", "close", "volume"]


def protected():
    ps = [*sorted(RAW.glob("*")), *sorted(FROZEN.glob("*")), *(RES / f for f in TF_FILES), ROOT / "src" / "track_forward.py"]
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in ps if p.is_file()}


def cmp(a: pd.DataFrame, b: pd.DataFrame) -> dict:
    a = a[a.date < TODAY].set_index("date"); b = b[b.date < TODAY].set_index("date")
    ov = a.index.intersection(b.index); lo, hi = max(a.index.min(), b.index.min()), min(a.index.max(), b.index.max())
    r = dict(overlap=len(ov), first=str(ov.min().date()), last=str(ov.max().date()),
             only_fetch=[str(d.date()) for d in a.index if lo <= d <= hi and d not in b.index],
             only_ref=[str(d.date()) for d in b.index if lo <= d <= hi and d not in a.index], mism=[])
    for f in FIELDS:
        x, y = a.loc[ov, f].astype(float), b.loc[ov, f].astype(float)
        ok = (x == y) if f == "volume" else (np.abs(x - y) <= 1e-6)
        r[f] = float(ok.mean() * 100); r["mism"] += [f"{d.date()} {f}: fetch={x[d]} ref={y[d]}" for d in ov[~ok.values]][:10]
    o2 = ov[ov > a.index.min()]
    fl = a.loc[o2, "open_suspicious"].astype(bool) == b.loc[o2, "open_suspicious"].astype(bool)
    r["open_suspicious"] = float(fl.mean() * 100); r["mism"] += [f"{d.date()} open_suspicious" for d in o2[~fl.values]][:10]
    r["pass"] = all(r[f] == 100.0 for f in FIELDS + ["open_suspicious"])
    return r


def copy_repo(dst: Path):
    if dst.exists(): shutil.rmtree(dst)
    (dst / "data" / "snapshots").mkdir(parents=True)
    shutil.copytree(ROOT / "src", dst / "src", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(RES, dst / "results")
    shutil.copytree(RAW, dst / "data" / "raw")
    for s in ("frozen_20261117", "20261125_pre_v6"): shutil.copytree(ROOT / "data" / "snapshots" / s, dst / "data" / "snapshots" / s)
    for p in (ROOT / "data").glob("*.*"):
        if p.suffix in (".txt", ".csv"): shutil.copy2(p, dst / "data" / p.name)


def run_tf(repo: Path, env_backend: str | None, refresh: bool) -> tuple[int, str]:
    env = {k: v for k, v in os.environ.items() if k not in ("OVERNIGHT_LIVE", F.BACKEND_ENV)}
    if env_backend: env[F.BACKEND_ENV] = env_backend
    p = subprocess.run([PY, "src/track_forward.py"] + (["--refresh"] if refresh else []), cwd=repo, env=env, capture_output=True, text=True, timeout=900)
    return p.returncode, p.stdout + p.stderr


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--scratch", required=True); a = ap.parse_args()
    scratch = Path(a.scratch).resolve(); assert ROOT not in scratch.parents and scratch != ROOT, "scratch must be outside the repo"
    H0 = protected(); L, ok = [], {}
    # ---------------- G1 + G2
    (PROBE / "direct").mkdir(parents=True); (PROBE / "vnstock").mkdir(parents=True)
    g1, g2 = [], []
    for s, start in SYMS.items():
        os.environ.pop(F.BACKEND_ENV, None)
        assert F.backend_for(s, "VCI") == "vci_direct"
        F.update_with_retry(s, start, "VCI", raw_dir=PROBE / "direct", full=True); time.sleep(4)
        os.environ[F.BACKEND_ENV] = "vnstock"
        F.update_with_retry(s, start, "VCI", raw_dir=PROBE / "vnstock", full=True); time.sleep(4)
        os.environ.pop(F.BACKEND_ENV, None)
        d = pd.read_csv(PROBE / "direct" / f"{s}.csv", parse_dates=["date"])
        v = pd.read_csv(PROBE / "vnstock" / f"{s}.csv", parse_dates=["date"])
        refs = [("data/raw", RAW / f"{s}.csv")] + ([("frozen_20261117", FROZEN / f"{s}.csv")] if s.startswith("VN30F") else [])
        for lab, p in refs:
            g1.append(dict(symbol=s, ref=lab, fetched_rows=len(d), **cmp(d, pd.read_csv(p, parse_dates=["date"]))))
        same = (PROBE / "direct" / f"{s}.csv").read_bytes() == (PROBE / "vnstock" / f"{s}.csv").read_bytes()
        vv = v[v.date > v.date.min()]                                       # drop vnstock's first row (no prior close -> flag differs)
        c = cmp(d[d.date >= vv.date.min()], vv)
        g2.append(dict(symbol=s, direct_rows=len(d), vnstock_rows=len(v), vnstock_first=str(v.date.min().date()), byte_identical=same,
                       window_pass=c["pass"] and not c["only_ref"] and c["overlap"] == len(vv[vv.date < TODAY]), **c))
    ok["G1"] = all(r["pass"] for r in g1); ok["G2"] = all(r["window_pass"] for r in g2)
    L += ["## G1: full-history refetch via the new backend vs references (today excluded)", "",
          "| symbol | ref | fetched rows | overlap | span | open | high | low | close | volume | open_suspicious | only fetch | only ref |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in g1:
        L.append(f"| {r['symbol']} | {r['ref']} | {r['fetched_rows']} | {r['overlap']} | {r['first']}..{r['last']} | "
                 + " | ".join(f"{r[f]:.2f}%" for f in FIELDS + ["open_suspicious"])
                 + f" | {len(r['only_fetch'])} {r['only_fetch'][:4] if r['only_fetch'] else ''} | {len(r['only_ref'])} {r['only_ref'][:4] if r['only_ref'] else ''} |")
    mm = [f"- {r['symbol']} vs {r['ref']}: {m}" for r in g1 for m in r["mism"]]
    L += ["", "Mismatches: none." if not mm else "Mismatches:", *mm[:80], "",
          "## G2: same-run A/B, new backend vs OVERNIGHT_FETCH_BACKEND=vnstock (output CSV bytes)", "",
          "| symbol | direct rows | vnstock rows | vnstock first date | byte-identical | overlap | O/H/L/C/V/flag match | only vnstock | REV1 window pass |", "|---|---|---|---|---|---|---|---|---|"]
    L += [f"| {r['symbol']} | {r['direct_rows']} | {r['vnstock_rows']} | {r['vnstock_first']} | {r['byte_identical']} | {r['overlap']} | "
          + "/".join(f"{r[f]:.0f}" for f in FIELDS + ["open_suspicious"]) + f"% | {len(r['only_ref'])} | {r['window_pass']} |" for r in g2]
    L += [f"- {r['symbol']} mismatches: {r['mism'][:10]}" for r in g2 if r["mism"]]
    L.append("")
    # ---------------- G3
    live = {f: (RES / f).read_bytes() for f in TF_FILES}
    rawlive = {s: (RAW / f"{s}.csv").read_text().splitlines() for s in ("VN30F1M", "VN30F2M")}
    g3, outs = [], {}
    for tag, envb in [("D", None), ("V", "vnstock")]:
        repo = scratch / f"tf_copy_{tag}"; copy_repo(repo)
        rc0, o0 = run_tf(repo, envb, False)
        same0 = {f: (repo / "results" / f).read_bytes() == live[f] for f in TF_FILES}
        rc1, o1 = run_tf(repo, envb, True)
        back = [ln for ln in o1.splitlines() if ln.startswith("[fetch]")]
        want = "backend=vnstock" if envb else "backend=vci_direct"
        old_ok = {}
        for s in ("VN30F1M", "VN30F2M"):
            new = (repo / "data" / "raw" / f"{s}.csv").read_text().splitlines()
            keep = [ln for ln in rawlive[s] if ln[:10] <= "2026-11-17" or not ln[0].isdigit()]
            old_ok[s] = new[:len(keep)] == keep
        added = {s: len((repo / "data" / "raw" / f"{s}.csv").read_text().splitlines()) - len(rawlive[s]) for s in ("VN30F1M", "VN30F2M")}
        sc_same = (repo / "results" / "track_forward_scorecard.csv").read_bytes() == live["track_forward_scorecard.csv"]
        bnd_same = (repo / "results" / "track_forward_boundary.txt").read_bytes() == live["track_forward_boundary.txt"]
        r = dict(copy=tag, env=envb or "(default)", rc_norefresh=rc0, norefresh_identical=all(same0.values()), rc_refresh=rc1,
                 backend_lines=len(back), backend_ok=bool(back) and all(want in ln for ln in back), boundary_same=bnd_same,
                 rows_le_cap_unchanged=all(old_ok.values()), rows_added=added, scorecard_same=sc_same,
                 guard="tripped" if "DATA REWRITE" in o1 or "[check] FAIL" in o1 else "passed")
        g3.append(r); outs[tag] = (repo, o1)
        (PROBE / f"tf_{tag}_refresh_stdout.txt").write_text(o1); (PROBE / f"tf_{tag}_norefresh_stdout.txt").write_text(o0)
    dv = {f: (outs["D"][0] / p).read_bytes() == (outs["V"][0] / p).read_bytes()
          for f, p in [("VN30F1M", "data/raw/VN30F1M.csv"), ("VN30F2M", "data/raw/VN30F2M.csv"),
                       ("log", "results/track_forward_log.csv"), ("scorecard", "results/track_forward_scorecard.csv")]}
    if not all(r["scorecard_same"] for r in g3):
        sd = pd.read_csv(outs["D"][0] / "results" / "track_forward_scorecard.csv").merge(
            pd.read_csv(RES / "track_forward_scorecard.csv"), on="metric", how="outer", suffixes=("_dryrun", "_live"))
        sdiff = sd[sd.value_dryrun.astype(str) != sd.value_live.astype(str)]
    else:
        sdiff = pd.DataFrame()
    ok["G3"] = all(r["rc_norefresh"] == 0 and r["norefresh_identical"] and r["rc_refresh"] == 0 and r["backend_ok"] and r["boundary_same"]
                   and r["rows_le_cap_unchanged"] and r["guard"] == "passed" for r in g3) and all(dv.values())
    sc_note = "identical to live in both copies" if all(r["scorecard_same"] for r in g3) else "DIFFERS from live (rows below; new forward data, not a failure by itself)"
    L += ["## G3: track_forward dry runs in throwaway repo copies", "", pd.DataFrame(g3).to_string(index=False), "",
          f"D vs V byte-identical after --refresh: {dv}", f"Scorecard after --refresh: {sc_note}",
          *([sdiff.to_string(index=False)] if len(sdiff) else []), ""]
    H1 = protected(); ok["G4"] = H0 == H1
    L += ["## G4: integrity", f"{len(H0)} protected files (data/raw/*, frozen_20261117/*, track_forward boundary/log/scorecard, src/track_forward.py): "
          + ("unchanged (sha256 before == after)" if ok["G4"] else f"CHANGED: {[k for k in H0 if H0.get(k) != H1.get(k)]}"), ""]
    gate = all(ok.values())
    head = [f"# Backend switch validation (run {RUN})", "",
            "Switch: `src/fetch_indices.py` sends VN30F1M, VN30F2M, VN30, VNINDEX (source VCI) to `src/fetch_vci_direct.py`; all other symbols stay on vnstock. "
            f"Gate pre-registered in `src/backend_switch_validate.py`. Fetched files in `data/raw_probe/backend_switch_{RUN}/`. Today ({TODAY.date()}) excluded.", "",
            f"## VERDICT: GATE {'PASS' if gate else 'FAIL'}  " + "  ".join(f"{k} {'PASS' if v else 'FAIL'}" for k, v in ok.items()), "",
            "Rollback: `export OVERNIGHT_FETCH_BACKEND=vnstock` (or put it in the launchd job / scripts/weekly_refresh.sh) restores vnstock for every symbol "
            "with no code change. Full revert: remove the FETCH BACKEND SWITCH block in `src/fetch_indices.py` (backend_for / _download_vci_direct and the "
            "4-line dispatch at the top of _download).", ""]
    MD.write_text("\n".join(head + L) + "\n"); print("\n".join(head + L)); return 0 if gate else 1


if __name__ == "__main__":
    sys.exit(main())
