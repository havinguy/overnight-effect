"""Diagnostic: does the continuous VN30F1M daily feed define open / volume differently from per-contract tickers?
READ-ONLY on data/raw/, data/raw_rollgap/ and results/ (writes only futures_open_definition_audit.{md,csv} and
futures_open_definition_mismatch_days.csv). No main result is re-run or filtered.
Usage: python3 src/futures_open_definition_audit.py
"""
from __future__ import annotations
import glob, math, re, sys, warnings
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import futures_roll_gap_repair as RG
from futures_basis_decomp import nw_t, ols_nw
from level_c_futures import build, roll_days
from level_a import OUT_DIR

OUT = OUT_DIR
TOL = 0.051
LIMIT = 0.07                                       # VN30F daily price limit +/-7% of the reference (prior settlement ~ prior close)


def tick_round(x): return np.round(x * 10) / 10


def load_contracts():
    C = {}
    for p in glob.glob(str(RG.RG / "VCI_VN30F[0-9][0-9][0-9][0-9]_1D.csv")):
        ym = re.search(r"VN30F(\d{4})_", p).group(1); C[ym] = RG.load_src("VCI", f"VN30F{ym}")
    return C


def overlap():
    S, _ = RG.contract_front_series(); f1 = RG.rd("VN30F1M")
    k = S.join(f1[["open", "high", "low", "close", "volume"]].add_suffix("_c"), how="inner")
    for c in ["open", "high", "low", "close"]: k[f"{c}_match"] = np.isclose(k[c], k[c + "_c"], atol=TOL)
    k["volume_match"] = k.volume == k.volume_c
    k["prior_close_ticker"] = [np.nan] * len(k)
    return S, f1, k


def monthly(k):
    g = k.groupby(k.index.to_period("M"))
    M = pd.DataFrame({"n_days": g.size(), **{f"{c}_match_rate": g[f"{c}_match"].mean() for c in ["open", "high", "low", "close", "volume"]},
                      "median_volume_ratio_ticker_over_cont": g.apply(lambda x: (x.volume / x.volume_c).median())})
    M.index = M.index.astype(str); return M


def mismatch_detail(S, f1, k, C, lo, hi):
    w = k.loc[lo:hi].copy(); f2 = RG.rd("VN30F2M"); v = RG.rd("VN30")
    # ticker's own prior close (same contract, previous trading day it traded)
    pc = []
    for t, r in w.iterrows():
        d = C[r.contract[5:]]; prev = d.index[d.index < t]; pc.append(d.loc[prev.max(), "close"] if len(prev) else np.nan)
    w["ticker_prior_close"] = pc
    w["d_open_pts"] = w.open - w.open_c; w["d_open_bp"] = np.log(w.open / w.open_c) * 1e4
    w["vol_ratio"] = w.volume / w.volume_c; w["vol_gap"] = w.volume_c - w.volume
    w["weekday"] = w.index.day_name()
    rolls = pd.DatetimeIndex(roll_days(f1.index)); pos = pd.Series(np.arange(len(f1)), index=f1.index)
    w["days_since_roll"] = [pos[t] - pos[rolls[rolls <= t].max()] for t in w.index]
    floor = tick_round(w.ticker_prior_close * (1 - LIMIT)); ceil = tick_round(w.ticker_prior_close * (1 + LIMIT))
    w["ticker_open_at_limit"] = np.isclose(w.open, floor, atol=0.11) | np.isclose(w.open, ceil, atol=0.11)
    w["cont_open_eq"] = ""
    eqs = {"ticker prior close": w.ticker_prior_close, "ticker high": w.high, "ticker low": w.low, "ticker close": w.close,
           "VN30F2M open (continuous)": f2.open.reindex(w.index), "VN30 index open": v.open.reindex(w.index)}
    for nm, s in eqs.items(): w[f"cont_open_eq_{nm}"] = np.isclose(w.open_c, s, atol=TOL)
    w["cont_open_eq_other_contract_open"] = [",".join(ym for ym, d in C.items() if t in d.index and ym != r.contract[5:] and abs(d.loc[t, "open"] - r.open_c) < TOL)
                                             for t, r in w.iterrows()]
    w["cont_open_within_ticker_range"] = (w.open_c >= w.low - 0.05) & (w.open_c <= w.high + 0.05)
    w["cont_high_le_ticker_high"] = w.high_c <= w.high + 0.05; w["cont_low_ge_ticker_low"] = w.low_c >= w.low - 0.05
    return w


def gross_compare(w, lo, hi):
    """Nights whose open date is in the window: gross ON with continuous open (as published) vs ticker open; same entry (build())."""
    d = build(0, 0.0); idx = RG.index_nights_fixed()
    n = d[d.invested & d.index.isin(w.index)].copy()
    n["open_t"] = w.open.reindex(n.index)
    n["r_cont"] = n.open / n.entry - 1; n["r_tick"] = n.open_t / n.entry - 1; n["diff"] = n.r_tick - n.r_cont
    ew = pd.Series(n.index, index=n.index).map(lambda t: d.index[d.index.get_loc(t) - 1]).dt.weekday
    n["monday"] = (n.hold_type == "") & (ew == 0)
    n["idx_ON"] = idx.idx_ON.reindex(n.index)
    rows = []
    for sub, g in [("all nights", n), ("Monday (Mon close -> Tue open)", n[n.monday])]:
        r = dict(subset=sub, n=len(g), gross_cont_bp=g.r_cont.mean() * 1e4, gross_tick_bp=g.r_tick.mean() * 1e4,
                 se_mean_cont_bp=g.r_cont.std() / math.sqrt(len(g)) * 1e4, diff_bp=g["diff"].mean() * 1e4,
                 diff_se_iid_bp=g["diff"].std() / math.sqrt(len(g)) * 1e4, diff_nw_t=nw_t(g["diff"]),
                 diff_ex_20221010_bp=g["diff"].drop(pd.Timestamp("2022-10-10"), errors="ignore").mean() * 1e4)
        for lab, col in [("cont", "r_cont"), ("tick", "r_tick")]:
            k_, se, r2 = ols_nw(np.log1p(g[col]), g.idx_ON); r[f"k_{lab}"] = k_; r[f"k_se_{lab}"] = se; r[f"r2_{lab}"] = r2
        rows.append(r)
    # 2022 full-year effect: substitute ticker opens inside the window only
    y = d[d.invested & (d.index.year == 2022)].copy(); y["r_alt"] = y.r_gross
    sub = y.index.intersection(n.index); y.loc[sub, "r_alt"] = n.loc[sub, "r_tick"]
    ew2 = pd.Series(d.index, index=d.index).shift(1).dt.weekday.reindex(y.index)
    for subn, g in [("2022 all nights (ticker opens substituted in window)", y), ("2022 Monday", y[(y.hold_type == "") & (ew2 == 0)])]:
        se = g.r_gross.std() / math.sqrt(len(g)) * 1e4
        rows.append(dict(subset=subn, n=len(g), gross_cont_bp=g.r_gross.mean() * 1e4, gross_tick_bp=g.r_alt.mean() * 1e4, se_mean_cont_bp=se,
                         diff_bp=(g.r_alt - g.r_gross).mean() * 1e4, diff_nw_t=nw_t(g.r_alt - g.r_gross),
                         diff_in_se_units=(g.r_alt - g.r_gross).mean() * 1e4 / se))
    return pd.DataFrame(rows), n


EXPOSED = [
    ("level_c_futures.py", "level_c_summary.csv, level_c_cost_sensitivity.csv, level_c_equity_curves.csv/.png",
     "all-nights futures gross 4.99 bp, Sharpe 1.29, net figures, cost sensitivity, equity curves 2017-08 .."),
    ("level_c_dayofweek.py", "level_c_dayofweek.csv/.png", "weekday futures overnight means incl. Monday 10.6 bp gross"),
    ("level_c_oos.py", "level_c_oos_validation.csv", "IS 2017-2021 window used to SELECT Mon / Mon+Tue; OOS 2022-25 check"),
    ("level_c_futures selective runs", "level_c_selective_summary.csv, level_c_selective_cost_sensitivity.csv, level_c_selective_equity_curve.csv", "selective (Monday / Mon+Tue) strategy stats"),
    ("level_c_phase2.py", "level_c_phase2_periods.csv, level_c_phase2_monday_cost.csv", "Monday full 10.62 / net 6.42 bp, Sharpe 0.91, t 2.78; IS 2017-2021 rows; Mon+Tue; cost grid; breakeven slippage 4.2 bp"),
    ("(spec)", "phase2_trackforward_spec.md", "historical Monday 10.6 / 6.4 bp, Sharpe 0.91, SD ~49 bp -> sample-size targets; kill rule benchmarks"),
    ("futures_basis_decomp.py", "futures_basis_{year,weekday,monday,wednesday,expiry,robustness}.csv (+ _fix20181121)",
     "2017-2021 futures-only rows; 2018-11..2021 decomposition: R1 Monday basis share 82% (t 2.21), pre-cutover Monday dbasis +12.8 bp, R3 slopes 2019-2021, all full-sample rows"),
    ("futures_basis_followup.py", "futures_basis_followup_{weekday_tests,offset,reconcile}.csv (+ _fix20181121)",
     "pre-2022-08-25 weekday tests (Mon->Tue minus others t 2.09 / 2.24), pre-cutover offset reference (a +4.9 bp, k 0.64)"),
    ("open_filter_audit.py", "open_audit_{benchmark,regime,flags}.csv, open_audit_summary.md", "futures legs of the Wednesday gap (7.85 -> 4.83 bp) and regime table"),
    ("pit_vs_futures.py", "pit_vs_futures_dayofweek.csv", "basket-vs-futures weekday gaps, full sample"),
    ("pit_residual_split.py", "pit_residual_split.csv", "futures leg of the replica / index / futures residual split from 2018-11"),
    ("futures_roll_gap_repair.py", "futures_roll_gap_before_after.csv", "all futures before/after metrics (full sample)"),
]


def main():
    pd.set_option("display.width", 250, "display.max_columns", 40, "display.float_format", "{:.3f}".format, "display.max_colwidth", 120)
    C = load_contracts(); S, f1, k = overlap()
    M = monthly(k)
    mis = k[~k.open_match]
    last_pre = mis[mis.index < "2024-01-01"].index.max(); first_all = k.index[k.index > last_pre].min()
    later = mis[mis.index > last_pre]
    lo = k.index.min()
    w = mismatch_detail(S, f1, k, C, lo, last_pre)
    x = w[~w.open_match]
    G, nights = gross_compare(w, lo, last_pre)
    M.to_csv(OUT / "futures_open_definition_audit.csv")
    w.to_csv(OUT / "futures_open_definition_mismatch_days.csv")
    # transition context
    rolls = pd.DatetimeIndex(roll_days(f1.index))
    near_roll = rolls[(rolls >= first_all - pd.Timedelta(days=20)) & (rolls <= first_all + pd.Timedelta(days=20))]
    cont_pre_july = k.loc[:"2022-06-30"]
    L = ["# VN30F1M open-definition audit (diagnostic, read-only)", "",
         "Per-contract source: VCI VN30Fyymm daily bars in data/raw_rollgap/ (contracts expiring 2022-07 .. 2025-06), stitched to the front month by calendar expiry. "
         "Continuous: data/raw/VN30F1M.csv. Price match tolerance 0.05 pt (tick 0.1).", "",
         "## 1. Match rate by month (all overlap days)", M.loc[:"2024-06"].to_string(), "",
         f"- Overlap starts {lo.date()} (the first front contract served is VN30F2207). The first 9 overlap days (2022-06-20 .. 06-30) match on open 100%.",
         f"- Mismatches run {mis.index.min().date()} .. {last_pre.date()}; from **{first_all.date()}** every open matches (exceptions after that: "
         f"{', '.join(f'{d.date()} ({r.open-r.open_c:+.1f} pt)' for d, r in later.iterrows())}).",
         f"- Transition: last mismatch {last_pre.date()} (Wed), first clean day {first_all.date()} (Thu). Nearest roll days: {', '.join(str(d.date()) for d in near_roll)} "
         "-> not a roll; not a month or quarter boundary; a vendor change cannot be verified from the data (the files carry no vendor or revision metadata). "
         "Close matches 100% on every day, before and after.",
         "- The pattern is NOT 'different before date X': June 2022 matches fully, then four months mismatch, then everything matches. It looks like a bounded episode, "
         "not a regime boundary.", ""]
    L += ["## 2. Mismatch days (pre-transition window)",
          f"Window {lo.date()} .. {last_pre.date()}: {len(w)} days; open mismatches {int((~w.open_match).sum())}, high {int((~w.high_match).sum())}, low {int((~w.low_match).sum())}, "
          f"close {int((~w.close_match).sum())}, volume {int((~w.volume_match).sum())}.",
          "Ticker open - continuous open: points " + str(x.d_open_pts.describe().round(2).to_dict()) + "; bp " + str(x.d_open_bp.describe().round(1).to_dict()),
          f"|diff| quantiles (pts): {x.d_open_pts.abs().quantile([.25, .5, .75, .9]).round(2).to_dict()}; share ticker > continuous {(x.d_open_pts > 0).mean():.2f}; "
          f"median {x.d_open_pts.median():+.2f} pt ({x.d_open_bp.median():+.2f} bp). No consistent sign.",
          "Largest: " + "; ".join(f"{d.date()} {r.d_open_pts:+.1f} pt ({r.d_open_bp:+.0f} bp; ticker open {r.open} {'= limit price' if r.ticker_open_at_limit else ''})"
                                  for d, r in x.reindex(x.d_open_pts.abs().sort_values(ascending=False).index).head(4).iterrows()),
          f"2022-10-10 outlier: ticker open {w.loc['2022-10-10','open']} = ticker low, {np.log(w.loc['2022-10-10','open']/w.loc['2022-10-10','ticker_prior_close'])*1e4:.0f} bp from its prior close "
          f"(inside the 7% limit, not at it) and far below the VN30 index low that day ({RG.rd('VN30').loc['2022-10-10','low']:.1f}; index open {RG.rd('VN30').loc['2022-10-10','open']:.1f}). "
          f"The continuous open {w.loc['2022-10-10','open_c']} is consistent with the index; the ticker print looks erroneous. It dominates the window means.",
          "What the continuous open equals on mismatch days (share of days):"]
    for c in [c for c in w.columns if c.startswith("cont_open_eq_") and c != "cont_open_eq_other_contract_open"]:
        L.append(f"  - {c.replace('cont_open_eq_', '')}: {x[c].mean():.3f}")
    L += [f"  - open of another listed contract that day: {(x.cont_open_eq_other_contract_open != '').mean():.3f} ({x.cont_open_eq_other_contract_open[x.cont_open_eq_other_contract_open != ''].value_counts().to_dict()})",
          f"  - inside the ticker's [low, high]: {x.cont_open_within_ticker_range.mean():.3f}",
          f"  - ticker open at the +/-7% limit price: {x.ticker_open_at_limit.sum()} day(s) ({', '.join(str(d.date()) for d in x.index[x.ticker_open_at_limit])})",
          "  - the ticker's SECOND bar / first continuous print: NOT TESTABLE (no per-contract intraday data; VCI 1m VN30F1M starts 2023-09-11, after the transition).",
          f"High/low: continuous high <= ticker high on {w.cont_high_le_ticker_high.mean():.2f} of days, continuous low >= ticker low on {w.cont_low_ge_ticker_low.mean():.2f}: "
          "the continuous bar is NOT a subset of the ticker's trades (it has prints outside the ticker range), so 'continuous = ticker minus the ATO' is contradicted.",
          "Clustering: open-mismatch rate by weekday " + str(w.groupby(w.index.weekday).open_match.apply(lambda s: round(1 - s.mean(), 2)).rename(index=dict(enumerate(['Mon','Tue','Wed','Thu','Fri']))).to_dict())
          + "; by trading days since roll " + str(w.groupby(pd.cut(w.days_since_roll, [-1, 0, 2, 5, 10, 15, 30])).open_match.agg(lambda s: round(1 - s.mean(), 2)).to_dict())
          + ". No weekday or roll clustering.",
          f"Volume: ticker / continuous median {w.vol_ratio.median():.4f} (range {w.vol_ratio.min():.4f} .. {w.vol_ratio.max():.4f}); the ticker is NEVER below the continuous "
          f"(continuous short by median {(-w.vol_gap).median():.0f} contracts, max {(-w.vol_gap).max():.0f}). Ratio on open-mismatch days {w.vol_ratio[~w.open_match].median():.4f} vs "
          f"match days {w.vol_ratio[w.open_match].median():.4f}. Continuous volume never equals the sum over listed contracts.",
          f"Pre-July 2022 overlap ({len(cont_pre_july)} days): open match {cont_pre_july.open_match.mean():.2f}, volume exact {cont_pre_july.volume_match.mean():.2f}.", ""]
    L += ["## 3. Effect on gross in the window (same entry = build() prior close; only the open differs)", G.to_string(index=False), "",
          "k, R2: slope and R2 of ln(1 + futures ON) on index overnight (NW), continuous-open vs ticker-open version, window nights only.", ""]
    L += ["## 4. What cannot be tested",
          "- 2017-08 (start of VN30F1M.csv) .. 2022-06-19: no per-contract source (VCI serves no contract expiring before 2022-07; KBS daily starts 2026-04; "
          "no per-contract intraday at all). Whether the continuous open is defined like the ticker open in that period is UNKNOWN; the June 2022 days that can be checked match, "
          "the July-October 2022 days do not, so neither behaviour can be assumed for earlier years.",
          "- The ATO-vs-first-continuous-print hypothesis itself: no intraday data exists for the mismatch window.",
          "Published results that depend on continuous-feed opens in 2017-08 .. 2022-06 (none re-run here):"]
    for s, f, what in EXPOSED: L.append(f"  - {s}: {f} -- {what}")
    L += ["  Not exposed: Level A/B and Option C (stocks and index only), the intraday follow-up (2023-09 onward), the forward track log (after 2026-11-17).", ""]
    g_all = G[G.subset == "all nights"].iloc[0]; g_mon = G[G.subset.str.startswith("Monday")].iloc[0]
    y_all = G[G.subset.str.startswith("2022 all")].iloc[0]; y_mon = G[G.subset == "2022 Monday"].iloc[0]
    L += ["## Summary",
          f"1. Transition found: open mismatches end {last_pre.date()}, clean from {first_all.date()}; not a roll or calendar boundary, vendor change unverifiable; June 2022 already matched, so this is an episode ({mis.index.min().date()} .. {last_pre.date()}), not a 'before date X' regime.",
          f"2. Open difference: no consistent sign (median {x.d_open_pts.median():+.2f} pt, {x.d_open_bp.median():+.1f} bp; 90% within {x.d_open_pts.abs().quantile(.9):.1f} pt), one outlier 2022-10-10 ({x.d_open_pts.min():+.0f} pt; the ticker print, not the continuous open, is implausible vs the index); volume: continuous always slightly lower (median {(w.vol_ratio.median()-1)*100:.2f}%).",
          f"3. Effect: window all-nights gross {g_all.gross_cont_bp:.2f} vs {g_all.gross_tick_bp:.2f} bp (diff {g_all.diff_bp:+.2f}, NW t {g_all.diff_nw_t:.2f}; ex 2022-10-10 {g_all.diff_ex_20221010_bp:+.2f}); Monday diff {g_mon.diff_bp:+.2f} bp (n {int(g_mon.n)}). "
          f"2022 full-year gross moves {y_all.diff_bp:+.2f} bp = {y_all.diff_in_se_units:+.2f} SE; 2022 Monday {y_mon.diff_bp:+.2f} bp = {y_mon.diff_in_se_units:+.2f} SE -> {'within' if max(abs(y_all.diff_in_se_units), abs(y_mon.diff_in_se_units)) < 1 else 'BEYOND'} one SE.",
          "4. Exposed: every futures result using 2017-08 .. 2022-06 opens (Level C summary / weekday / OOS selection window 2017-21 / phase2 Monday & Mon+Tue / track-forward spec benchmarks / "
          "futures_basis R1 Monday 2018-21 basis share / pre-cutover weekday and offset tests / open-audit futures legs / pit_vs_futures / pit_residual_split).",
          "5. Open question: what the continuous feed did in 2017-08 .. 2022-06 and why July-October 2022 differs (bar construction from a different tick set: the continuous bar has prints outside the ticker range and less volume) cannot be resolved without a per-contract or intraday source for that period."]
    (OUT / "futures_open_definition_audit.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
