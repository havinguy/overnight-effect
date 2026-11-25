"""Live track-forward logger for the frozen Monday-close -> Tuesday-open VN30F1M signal.

Return / roll / cost logic is NOT reimplemented: every number comes from level_c_futures.build()
and stats(), base cost build(0, 0.0005, fee_vnd=12_500, slippage=0.0001), so live == backtest
by construction.

Freeze boundary: results/track_forward_boundary.txt holds the max date in data/raw/VN30F1M.csv on
first run (end of the Option B backtest). A Monday is forward iff its Tuesday exit date is
STRICTLY AFTER that date. The file is write-once; this script never rewrites it.

Usage:
  python3 track_forward.py             rebuild log + scorecard from the CSV already on disk
  python3 track_forward.py --refresh   first pull new VN30F1M/F2M bars (fetch_indices.update), then rebuild

The log is rebuilt from scratch on every run (idempotent); manual columns are carried over by
monday_date from the existing log, never from the model. Per-side units: realized_fee_bp and
realized_slip_bp are bp of notional PER SIDE (comparable to the assumed ~1.0 bp slippage/side).

Added 2026-11-25 (user request; no change to signal, boundary, kill rule or data source):
- every run prints the futures data file paths actually used and their last bar dates;
- every run (and always after --refresh) checks that the first N rows of VN30F1M.csv and VN30F2M.csv (the files build() reads)
  are byte-identical to the FIXED reference snapshot REF_SNAPSHOT (data/snapshots/20261125_pre_v6/raw/, verified against its
  MANIFEST.sha256). It fails closed. If any old row was rewritten it prints a loud warning and exits with code 2 BEFORE
  rebuilding the log. Note: --refresh re-downloads a 7-day overlap (keep='last'), so a vendor revision of recent rows also
  triggers exit 2; --refresh therefore first copies both files to data/snapshots/pre_refresh_<utc>/ (new folder, never
  overwritten) for a one-step restore. Original file kept in data/snapshots/code_20261125/track_forward.py.orig.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from level_c_futures import OUT, RAW, TD, build, stats
from data_cap import futures_csv
import hashlib, sys

BASE = dict(roll_cost=0.0005, fee_vnd=12_500, slippage=0.0001)
BOUNDARY = OUT / "track_forward_boundary.txt"
LOG = OUT / "track_forward_log.csv"
SCORE = OUT / "track_forward_scorecard.csv"
AUTO = ["tuesday_date", "monday_date", "entry", "exit", "is_roll", "gross_bp", "modeled_cost_bp",
        "modeled_net_bp", "status"]
MANUAL = ["realized_entry", "realized_exit", "realized_fee_bp", "realized_slip_bp", "realized_net_bp", "note"]
ASSUMED_SLIP_BP = BASE["slippage"] * 1e4
MILESTONES = (30, 100, 235)


def freeze_boundary() -> pd.Timestamp:
    """Write-once. Returns the frozen boundary date."""
    if not BOUNDARY.exists():
        last = pd.read_csv(RAW / "VN30F1M.csv", parse_dates=["date"])["date"].max()
        OUT.mkdir(exist_ok=True)
        BOUNDARY.write_text(f"{last:%Y-%m-%d}\n")
        print(f"[freeze] boundary written: {last:%Y-%m-%d} (end of Option B backtest; never moved)")
    return pd.Timestamp(BOUNDARY.read_text().strip())


def refresh() -> None:
    from fetch_indices import update_with_retry
    for s in ("VN30F1M", "VN30F2M"):
        update_with_retry(s, "2017-08-10", "VCI")


def print_data_paths() -> None:
    for s in ("VN30F1M", "VN30F2M"):
        p = futures_csv(s)
        last = pd.read_csv(p, usecols=["date"])["date"].max()
        print(f"[data] {s}: {p} | last bar {last}")


REF_SNAPSHOT = RAW.parent / "snapshots" / "20261125_pre_v6"   # fixed reference; change deliberately after a verified new snapshot


def check_raw_rows_unchanged() -> bool:
    """First N rows of each futures file build() reads must equal the fixed reference snapshot (verified against its manifest). Fails closed."""
    man = REF_SNAPSHOT / "MANIFEST.sha256"
    if not man.exists():
        print(f"[check] FAIL: reference manifest {man} missing; old-row check cannot run"); return False
    ok_all = True
    for s in ("VN30F1M", "VN30F2M"):
        snap = REF_SNAPSHOT / "raw" / f"{s}.csv"
        want = next((ln.split()[0] for ln in man.read_text().splitlines() if ln.endswith(f"./raw/{s}.csv")), None)
        if not snap.exists() or want is None or hashlib.sha256(snap.read_bytes()).hexdigest() != want:
            print(f"[check] FAIL: reference {snap} missing or not matching its manifest"); ok_all = False; continue
        live = futures_csv(s)
        old = snap.read_text().splitlines(); cur = Path(live).read_text().splitlines()
        n = len(old); bad = [i for i in range(min(n, len(cur))) if old[i] != cur[i]]
        if len(cur) < n or bad:
            bar = "!" * 100
            print(f"{bar}\n[check] DATA REWRITE: {live} differs from reference {snap} in its first {n} rows "
                  f"({len(bad)} changed lines, current rows {len(cur)}); first changed: {[old[i] for i in bad[:2]]} -> {[cur[i] for i in bad[:2]]}\n"
                  f"Log NOT rebuilt. Pre-refresh copies (if --refresh ran) are in data/snapshots/pre_refresh_*/. A vendor revision inside the\n"
                  f"7-day refresh overlap also triggers this: compare, then restore or document before continuing.\n{bar}")
            ok_all = False
        else:
            print(f"[check] {s}: first {n} rows of {live} identical to reference {REF_SNAPSHOT.name} (manifest-verified); {len(cur) - n} rows appended since")
    return ok_all


def backup_before_refresh() -> None:
    import datetime as _dt, shutil
    d = RAW.parent / "snapshots" / f"pre_refresh_{_dt.datetime.now(_dt.timezone.utc):%Y%m%dT%H%M%SZ}"
    d.mkdir(parents=True, exist_ok=False)
    for s in ("VN30F1M", "VN30F2M"):
        shutil.copy2(RAW / f"{s}.csv", d / f"{s}.csv")
    (d / "MANIFEST.sha256").write_text("".join(f"{hashlib.sha256((d / f'{s}.csv').read_bytes()).hexdigest()}  ./{s}.csv\n" for s in ("VN30F1M", "VN30F2M")))
    print(f"[backup] pre-refresh copies written to {d}")


def monday_nights(d: pd.DataFrame) -> pd.DataFrame:
    """One row per night ending at an open in d whose entry close is a Monday (prior trading day),
    or whose calendar Monday was not a trading day. Mirrors level_c_phase2 selection."""
    prev = pd.Series(d.index, index=d.index).shift(1)
    rows = []
    for t, r in d.iterrows():
        if pd.isna(prev[t]) or prev[t].weekday() != 0:
            continue
        if r["hold_type"] != "":
            status = "skipped_hold"          # Tuesday was a holiday: night runs Mon close -> Wed+ open
        elif not r["invested"]:
            status = "skipped_no_entry"      # roll night without F2M history
        else:
            status = "ok"
        rows.append({"tuesday_date": t, "monday_date": prev[t],
                     "entry": r["entry"], "exit": r["open"], "is_roll": int(r["is_roll"]),
                     "gross_bp": r["r_gross"] * 1e4, "modeled_cost_bp": r["cost"] * 1e4,
                     "modeled_net_bp": r["r_net"] * 1e4, "status": status})
    out = pd.DataFrame(rows, columns=AUTO)
    # Mondays that were holidays: calendar Monday with no bar -> no Monday close to enter on
    idx = set(d.index)
    for m in pd.date_range(d.index[0], d.index[-1], freq="W-MON"):
        if m not in idx and m > d.index[0]:
            out = pd.concat([out, pd.DataFrame([{"tuesday_date": m + pd.Timedelta(days=1), "monday_date": m,
                                                 "status": "skipped_hold"}])], ignore_index=True)
    return out


def build_log(boundary: pd.Timestamp) -> tuple[pd.DataFrame, pd.DataFrame]:
    d = build(0, **BASE)
    nights = monday_nights(d)
    hist = nights[(nights["status"] == "ok") & (nights["tuesday_date"] <= boundary)]
    fwd = nights[nights["tuesday_date"] > boundary].copy()      # strictly after the frozen boundary
    fwd = fwd.sort_values("tuesday_date").reset_index(drop=True)
    for c in MANUAL:
        fwd[c] = "" if c == "note" else np.nan
    if LOG.exists():
        old = pd.read_csv(LOG, parse_dates=["tuesday_date"]).drop_duplicates("tuesday_date", keep="last")
        old = old.set_index("tuesday_date")
        for c in MANUAL:
            if c in old.columns:
                m = fwd["tuesday_date"].map(old[c])
                fwd[c] = m.where(m.notna(), fwd[c])
        fwd["note"] = fwd["note"].fillna("").astype(str)
        had = old[[c for c in MANUAL if c in old.columns]].replace("", np.nan).notna().any(axis=1)
        lost = old.index[had & ~old.index.isin(fwd["tuesday_date"])]
        if len(lost):
            print(f"WARNING: manual entries for {[f'{x:%Y-%m-%d}' for x in lost]} have no matching night in the rebuilt log "
                  f"and were NOT carried over (old file kept as {LOG.name}.bak)")
            LOG.replace(LOG.with_suffix(".csv.bak"))
    fwd[AUTO + MANUAL].to_csv(LOG, index=False, date_format="%Y-%m-%d")
    return fwd, hist


REF = {"full_sample_net_bp": 6.42, "oos_2022_25_net_bp": 3.55, "breakeven_slip_bp_per_side": 4.21,
       "assumed_slip_bp_per_side": ASSUMED_SLIP_BP}
FLAG_SLIP_BP = 1.5   # "materially > 1 bp" at the n>=30 checkpoint (50% above the assumption)

HOW_TO_RUN = """## How to run (weekly operating procedure)
1. Each week, **after Tuesday's open** (the ATO print must be in the feed), run
   `python3 src/track_forward.py --refresh`. This pulls new VN30F1M and VN30F2M bars from vnstock via
   `fetch_indices.update_with_retry` (the same incremental fetcher / CSV schema as `data/raw/VN30F1M.csv`),
   then rebuilds `results/track_forward_log.csv` and `results/track_forward_scorecard.csv`. The new night is
   picked up automatically. Without `--refresh` the script runs off the cached CSV.
2. The log is rebuilt from source on every run (keyed on `tuesday_date`), so re-running never double-counts.
   Manually entered `realized_*` / `note` values are preserved across rebuilds.
3. If you actually traded the night, fill `realized_entry`, `realized_exit`, `realized_fee_bp`,
   `realized_slip_bp` (bp of notional per side) and `realized_net_bp` in the log. Where `realized_net_bp`
   is present the scorecard uses it instead of `modeled_net_bp`. Never edit the modeled columns.
4. `results/track_forward_boundary.txt` is the frozen end of the in-sample backtest. Never edit or delete it:
   only Tuesdays strictly after it are forward observations.
5. Weeks where Monday or Tuesday was a holiday are logged `skipped_hold` and excluded from the scorecard,
   as in the backtest. Check the printed scorecard against the kill rule: n>=30 flag slippage > 1.5 bp/side;
   n>=100 KILL if net mean < 0 or mean slippage > 4 bp/side; decision-grade at 235 Mondays.
"""


def scorecard(fwd: pd.DataFrame, hist: pd.DataFrame, boundary: pd.Timestamp) -> pd.DataFrame:
    ok = fwd[fwd["status"] == "ok"].copy()
    ok["net_bp"] = ok["realized_net_bp"].where(ok["realized_net_bp"].notna(), ok["modeled_net_bp"])
    n = len(ok)
    h_mean, h_sd = hist["modeled_net_bp"].mean(), hist["modeled_net_bp"].std(ddof=1)
    s = {"boundary_frozen": f"{boundary:%Y-%m-%d}", "n_forward_mondays": n,
         "n_skipped_hold_or_no_entry": int((fwd["status"] != "ok").sum()),
         "n_with_realized_net": int(ok["realized_net_bp"].notna().sum()),
         "ref_full_sample_net_bp": REF["full_sample_net_bp"], "ref_2022_25_net_bp": REF["oos_2022_25_net_bp"],
         "ref_breakeven_slip_bp_per_side": REF["breakeven_slip_bp_per_side"],
         "ref_assumed_slip_bp_per_side": REF["assumed_slip_bp_per_side"],
         "check_hist_n_recomputed": len(hist), "check_hist_net_mean_bp_recomputed": h_mean}
    sr = np.nan
    if n >= 1:
        s["cum_gross_mean_bp (modeled)"] = ok["gross_bp"].mean()
        s["cum_net_mean_bp"] = ok["net_bp"].mean()
        s["last_forward_tuesday"] = f"{ok['tuesday_date'].max():%Y-%m-%d}"
    if n >= 3:
        years = max((ok["tuesday_date"].max() - boundary).days / 365.25, 1 / 52)
        r = pd.Series(ok["net_bp"].values / 1e4, index=ok["tuesday_date"].values)
        st = stats(r, (1 + r).cumprod(), pd.Series(True, index=r.index), years)
        sr, ppy = st["sharpe"], st["obs_per_year"]
        se = np.sqrt((1 + 0.5 * (sr / np.sqrt(ppy)) ** 2) / n) * np.sqrt(ppy)   # Lo iid, as in level_c_phase2
        s.update({"net_sharpe": sr, "net_sharpe_se": se, "net_sharpe_ci95_lo": sr - 1.96 * se,
                  "net_sharpe_ci95_hi": sr + 1.96 * se, "net_t": st["t_stat"],
                  "win_rate_%": st["win_rate_%"], "max_dd_%": st["max_drawdown_%"], "years_since_boundary": years,
                  "z_vs_hist_mean": (ok["net_bp"].mean() - h_mean) / (h_sd / np.sqrt(n))})
        if n < 30:
            s["sharpe_note"] = "n<30: annualised stats are indicative only"
    slip = fwd["realized_slip_bp"].dropna()
    s["n_realized_slip"] = len(slip)
    if len(slip):
        m = slip.mean()
        s["mean_realized_slip_bp_per_side"] = m
        s["slip_vs_assumed_1bp"] = m - REF["assumed_slip_bp_per_side"]
        s["slip_vs_breakeven_4.21bp"] = m - REF["breakeven_slip_bp_per_side"]
    # pre-registered kill rule
    msgs = []
    if n >= 100:
        if s["cum_net_mean_bp"] < 0:
            msgs.append("KILL: forward net mean < 0 at n>=100")
        if len(slip) and slip.mean() > 4.0:
            msgs.append("KILL: mean realized slippage > 4 bp/side at n>=100")
        if not msgs:
            msgs.append("n>=100: kill rule NOT triggered")
    if n >= 30 and len(slip) and slip.mean() > FLAG_SLIP_BP:
        msgs.append(f"FLAG (n>=30): mean realized slippage {slip.mean():.2f} bp/side materially > 1 bp (threshold {FLAG_SLIP_BP})")
    if n >= 30 and not len(slip):
        msgs.append("n>=30 but no realized slippage logged: cannot check the 1 bp assumption")
    s["kill_rule_status"] = "; ".join(msgs) or f"not yet evaluable (n={n}; checkpoints at 30 and 100)"
    for m_ in MILESTONES:
        s[f"mondays_remaining_to_{m_}"] = max(m_ - n, 0)
    nxt = next((m_ for m_ in MILESTONES if n < m_), None)
    s["next_checkpoint"] = f"{nxt} ({nxt - n} to go)" if nxt else "all checkpoints reached"
    sc = pd.Series(s, name="value").astype(object).to_frame()
    sc.to_csv(SCORE, index_label="metric")
    return sc


def append_spec() -> None:
    spec = OUT / "phase2_trackforward_spec.md"
    txt = spec.read_text() if spec.exists() else ""
    if "## How to run (weekly operating procedure)" not in txt:
        spec.write_text(txt.rstrip("\n") + "\n\n" + HOW_TO_RUN)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--refresh", action="store_true", help="pull new VN30F1M/F2M bars before rebuilding")
    a = ap.parse_args()
    boundary = freeze_boundary()
    if a.refresh:
        backup_before_refresh()
        refresh()
    print_data_paths()
    if not check_raw_rows_unchanged():
        sys.exit(2)
    fwd, hist = build_log(boundary)
    sc = scorecard(fwd, hist, boundary)
    append_spec()
    last = pd.read_csv(RAW / "VN30F1M.csv")["date"].max()
    print(f"Frozen boundary: {boundary:%Y-%m-%d} | data through {last} | forward Mondays so far: "
          f"{int(sc.loc['n_forward_mondays', 'value'])} | next checkpoint: {sc.loc['next_checkpoint', 'value']}")
    if len(fwd):
        with pd.option_context("display.width", 200, "display.float_format", "{:.2f}".format):
            print(fwd[AUTO].to_string(index=False))
    print("\nScorecard:")
    print(sc.to_string())
    print("\n" + HOW_TO_RUN)


if __name__ == "__main__":
    main()
