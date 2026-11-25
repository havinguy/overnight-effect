# VN30F1M open-definition audit (diagnostic, read-only)

Per-contract source: VCI VN30Fyymm daily bars in data/raw_rollgap/ (contracts expiring 2022-07 .. 2025-06), stitched to the front month by calendar expiry. Continuous: data/raw/VN30F1M.csv. Price match tolerance 0.05 pt (tick 0.1).

## 1. Match rate by month (all overlap days)
         n_days  open_match_rate  high_match_rate  low_match_rate  close_match_rate  volume_match_rate  median_volume_ratio_ticker_over_cont
date                                                                                                                                        
2022-06       9            1.000            1.000           1.000             1.000              1.000                                 1.000
2022-07      21            0.571            0.619           0.476             1.000              0.476                                 1.000
2022-08      23            0.391            0.348           0.304             1.000              0.087                                 1.001
2022-09      20            0.450            0.300           0.200             1.000              0.000                                 1.002
2022-10      21            0.190            0.333           0.190             1.000              0.000                                 1.002
2022-11      21            0.905            0.857           0.857             1.000              0.810                                 1.000
2022-12      21            1.000            1.000           1.000             1.000              1.000                                 1.000
2023-01      15            1.000            1.000           1.000             1.000              1.000                                 1.000
2023-02      19            1.000            1.000           1.000             1.000              1.000                                 1.000
2023-03      22            1.000            1.000           1.000             1.000              1.000                                 1.000
2023-04      19            1.000            1.000           1.000             1.000              1.000                                 1.000
2023-05      19            1.000            1.000           1.000             1.000              1.000                                 1.000
2023-06      21            1.000            1.000           1.000             1.000              1.000                                 1.000
2023-07      20            1.000            1.000           1.000             1.000              1.000                                 1.000
2023-08      22            1.000            1.000           1.000             1.000              1.000                                 1.000
2023-09      18            1.000            1.000           1.000             1.000              1.000                                 1.000
2023-10      21            1.000            1.000           1.000             1.000              1.000                                 1.000
2023-11      21            1.000            1.000           1.000             1.000              1.000                                 1.000
2023-12      20            1.000            1.000           1.000             1.000              1.000                                 1.000
2024-01      22            1.000            1.000           1.000             1.000              1.000                                 1.000
2024-02      16            1.000            1.000           1.000             1.000              1.000                                 1.000
2024-03      21            1.000            1.000           1.000             1.000              1.000                                 1.000
2024-04      19            0.947            1.000           1.000             1.000              1.000                                 1.000
2024-05      22            1.000            1.000           1.000             1.000              1.000                                 1.000
2024-06      20            1.000            0.950           1.000             1.000              0.950                                 1.000

- Overlap starts 2022-06-20 (the first front contract served is VN30F2207). The first 9 overlap days (2022-06-20 .. 06-30) match on open 100%.
- Mismatches run 2022-07-11 .. 2022-11-02; from **2022-11-03** every open matches (exceptions after that: 2024-04-24 (-0.1 pt)).
- Transition: last mismatch 2022-11-02 (Wed), first clean day 2022-11-03 (Thu). Nearest roll days: 2022-10-21, 2022-11-21 -> not a roll; not a month or quarter boundary; a vendor change cannot be verified from the data (the files carry no vendor or revision metadata). Close matches 100% on every day, before and after.
- The pattern is NOT 'different before date X': June 2022 matches fully, then four months mismatch, then everything matches. It looks like a bounded episode, not a regime boundary.

## 2. Mismatch days (pre-transition window)
Window 2022-06-20 .. 2022-11-02: 96 days; open mismatches 53, high 52, low 62, close 0, volume 75.
Ticker open - continuous open: points {'count': 53.0, 'mean': -1.13, 'std': 6.6, 'min': -47.0, '25%': -0.6, '50%': -0.1, '75%': 0.2, 'max': 3.8}; bp {'count': 53.0, 'mean': -11.1, 'std': 66.4, 'min': -476.5, '25%': -5.0, '50%': -0.8, '75%': 2.0, 'max': 30.5}
|diff| quantiles (pts): {0.25: 0.2, 0.5: 0.5, 0.75: 1.1, 0.9: 2.82}; share ticker > continuous 0.42; median -0.10 pt (-0.84 bp). No consistent sign.
Largest: 2022-10-10 -47.0 pt (-476 bp; ticker open 963.1 ); 2022-09-30 -5.8 pt (-51 bp; ticker open 1138.1 ); 2022-09-09 -4.7 pt (-37 bp; ticker open 1264.3 ); 2022-08-03 +3.8 pt (+30 bp; ticker open 1249.2 )
2022-10-10 outlier: ticker open 963.1 = ticker low, -693 bp from its prior close (inside the 7% limit, not at it) and far below the VN30 index low that day (1011.4; index open 1025.5). The continuous open 1010.1 is consistent with the index; the ticker print looks erroneous. It dominates the window means.
What the continuous open equals on mismatch days (share of days):
  - ticker prior close: 0.019
  - ticker high: 0.000
  - ticker low: 0.019
  - ticker close: 0.000
  - VN30F2M open (continuous): 0.000
  - VN30 index open: 0.000
  - open of another listed contract that day: 0.075 ({'2303': 4})
  - inside the ticker's [low, high]: 0.906
  - ticker open at the +/-7% limit price: 0 day(s) ()
  - the ticker's SECOND bar / first continuous print: NOT TESTABLE (no per-contract intraday data; VCI 1m VN30F1M starts 2023-09-11, after the transition).
High/low: continuous high <= ticker high on 0.55 of days, continuous low >= ticker low on 0.55: the continuous bar is NOT a subset of the ticker's trades (it has prints outside the ticker range), so 'continuous = ticker minus the ATO' is contradicted.
Clustering: open-mismatch rate by weekday {'Mon': 0.6, 'Tue': 0.4, 'Wed': 0.6, 'Thu': 0.56, 'Fri': 0.61}; by trading days since roll {Interval(-1, 0, closed='right'): 0.5, Interval(0, 2, closed='right'): 0.4, Interval(2, 5, closed='right'): 0.53, Interval(5, 10, closed='right'): 0.57, Interval(10, 15, closed='right'): 0.45, Interval(15, 30, closed='right'): 0.71}. No weekday or roll clustering.
Volume: ticker / continuous median 1.0011 (range 1.0000 .. 1.0261); the ticker is NEVER below the continuous (continuous short by median 275 contracts, max 6294). Ratio on open-mismatch days 1.0012 vs match days 1.0006. Continuous volume never equals the sum over listed contracts.
Pre-July 2022 overlap (9 days): open match 1.00, volume exact 1.00.

## 3. Effect on gross in the window (same entry = build() prior close; only the open differs)
                                              subset   n  gross_cont_bp  gross_tick_bp  se_mean_cont_bp  diff_bp  diff_se_iid_bp  diff_nw_t  diff_ex_20221010_bp  k_cont  k_se_cont  r2_cont  k_tick  k_se_tick  r2_tick  diff_in_se_units
                                          all nights  96          5.318         -0.599            6.391   -5.917           4.832     -1.254               -1.186   0.917      0.072    0.687   1.132      0.228    0.476               NaN
                      Monday (Mon close -> Tue open)  20         11.321         10.560            8.868   -0.761           0.700     -1.891               -0.761   0.581      0.092    0.533   0.607      0.098    0.535               NaN
2022 all nights (ticker opens substituted in window) 247          1.178         -1.121            3.895   -2.300             NaN     -1.217                  NaN     NaN        NaN      NaN     NaN        NaN      NaN            -0.590
                                         2022 Monday  48          0.500          0.183            5.534   -0.317             NaN     -1.382                  NaN     NaN        NaN      NaN     NaN        NaN      NaN            -0.057

k, R2: slope and R2 of ln(1 + futures ON) on index overnight (NW), continuous-open vs ticker-open version, window nights only.

## 4. What cannot be tested
- 2017-08 (start of VN30F1M.csv) .. 2022-06-19: no per-contract source (VCI serves no contract expiring before 2022-07; KBS daily starts 2026-04; no per-contract intraday at all). Whether the continuous open is defined like the ticker open in that period is UNKNOWN; the June 2022 days that can be checked match, the July-October 2022 days do not, so neither behaviour can be assumed for earlier years.
- The ATO-vs-first-continuous-print hypothesis itself: no intraday data exists for the mismatch window.
Published results that depend on continuous-feed opens in 2017-08 .. 2022-06 (none re-run here):
  - level_c_futures.py: level_c_summary.csv, level_c_cost_sensitivity.csv, level_c_equity_curves.csv/.png -- all-nights futures gross 4.99 bp, Sharpe 1.29, net figures, cost sensitivity, equity curves 2017-08 ..
  - level_c_dayofweek.py: level_c_dayofweek.csv/.png -- weekday futures overnight means incl. Monday 10.6 bp gross
  - level_c_oos.py: level_c_oos_validation.csv -- IS 2017-2021 window used to SELECT Mon / Mon+Tue; OOS 2022-25 check
  - level_c_futures selective runs: level_c_selective_summary.csv, level_c_selective_cost_sensitivity.csv, level_c_selective_equity_curve.csv -- selective (Monday / Mon+Tue) strategy stats
  - level_c_phase2.py: level_c_phase2_periods.csv, level_c_phase2_monday_cost.csv -- Monday full 10.62 / net 6.42 bp, Sharpe 0.91, t 2.78; IS 2017-2021 rows; Mon+Tue; cost grid; breakeven slippage 4.2 bp
  - (spec): phase2_trackforward_spec.md -- historical Monday 10.6 / 6.4 bp, Sharpe 0.91, SD ~49 bp -> sample-size targets; kill rule benchmarks
  - futures_basis_decomp.py: futures_basis_{year,weekday,monday,wednesday,expiry,robustness}.csv (+ _fix20181121) -- 2017-2021 futures-only rows; 2018-11..2021 decomposition: R1 Monday basis share 82% (t 2.21), pre-cutover Monday dbasis +12.8 bp, R3 slopes 2019-2021, all full-sample rows
  - futures_basis_followup.py: futures_basis_followup_{weekday_tests,offset,reconcile}.csv (+ _fix20181121) -- pre-2022-08-25 weekday tests (Mon->Tue minus others t 2.09 / 2.24), pre-cutover offset reference (a +4.9 bp, k 0.64)
  - open_filter_audit.py: open_audit_{benchmark,regime,flags}.csv, open_audit_summary.md -- futures legs of the Wednesday gap (7.85 -> 4.83 bp) and regime table
  - pit_vs_futures.py: pit_vs_futures_dayofweek.csv -- basket-vs-futures weekday gaps, full sample
  - pit_residual_split.py: pit_residual_split.csv -- futures leg of the replica / index / futures residual split from 2018-11
  - futures_roll_gap_repair.py: futures_roll_gap_before_after.csv -- all futures before/after metrics (full sample)
  Not exposed: Level A/B and Option C (stocks and index only), the intraday follow-up (2023-09 onward), the forward track log (after 2026-11-17).

## Summary
1. Transition found: open mismatches end 2022-11-02, clean from 2022-11-03; not a roll or calendar boundary, vendor change unverifiable; June 2022 already matched, so this is an episode (2022-07-11 .. 2022-11-02), not a 'before date X' regime.
2. Open difference: no consistent sign (median -0.10 pt, -0.8 bp; 90% within 2.8 pt), one outlier 2022-10-10 (-47 pt; the ticker print, not the continuous open, is implausible vs the index); volume: continuous always slightly lower (median 0.11%).
3. Effect: window all-nights gross 5.32 vs -0.60 bp (diff -5.92, NW t -1.25; ex 2022-10-10 -1.19); Monday diff -0.76 bp (n 20). 2022 full-year gross moves -2.30 bp = -0.59 SE; 2022 Monday -0.32 bp = -0.06 SE -> within one SE.
4. Exposed: every futures result using 2017-08 .. 2022-06 opens (Level C summary / weekday / OOS selection window 2017-21 / phase2 Monday & Mon+Tue / track-forward spec benchmarks / futures_basis R1 Monday 2018-21 basis share / pre-cutover weekday and offset tests / open-audit futures legs / pit_vs_futures / pit_residual_split).
5. Open question: what the continuous feed did in 2017-08 .. 2022-06 and why July-October 2022 differs (bar construction from a different tick set: the continuous bar has prints outside the ticker range and less volume) cannot be resolved without a per-contract or intraday source for that period.
