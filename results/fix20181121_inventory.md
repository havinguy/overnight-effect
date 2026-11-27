# 2018-11-21 first-night bug: fix applied (FB only) and inventory of the remaining carriers

Written 2026-11-27. Measurement / hygiene only. Uncommitted.

> **Status update (2026-11-27, later):** Harry approved the full fix. It has now been applied to all remaining carriers listed below (code changed and outputs regenerated). See results/LOG.md and the cell-level change log results/fix20181121_fullfix_changes.csv. The 'NOT edited' / 'would move' wording below describes the inventory as measured before that.

## Applied (Option A, FB only)
- `src/futures_basis_decomp.py` `index_nights()`: prior date and prior close are now taken from the raw VN30 series BEFORE `decompose()` drops row 0. This is the `futures_roll_gap_repair.index_nights_fixed()` pattern; the two DataFrames are `.equals()`.
- `src/futures_roll_gap_repair.py`: `index_nights_legacy()` pinned (a frozen pre-fix copy, verified equal to the function at HEAD 0c3c8f4). The "before (as reported)" variant now calls it. The script was not rerun; its `main()` writes `data/raw/VN30F1M_repaired.csv` and the twins.
- Regenerated: `futures_basis_decomp.py` (its reproduction gate passed) and `futures_basis_followup.py`. Decomposition N goes from 1,962 to 1,963; misaligned nights from 16 to 15.
- **GATE: PASS.** All 9 tables equal their `*_fix20181121.csv` twins byte-for-byte: year, weekday, monday, wednesday, expiry, robustness, followup_reconcile, followup_weekday_tests, followup_offset. The twins are now redundant with the primaries. They were not deleted; that is Harry's call. `futures_roll_gap_fix20181121_changes.csv` is a change log, not a twin.
- The intraday table (`futures_basis_followup_intraday.csv`) and the Monday and Wednesday tables are unchanged.

### Headline figures fed by these two scripts (old -> new)
| claim / figure | old | new | moves? |
|---|---|---|---|
| C14 post-2022 offset a (NW t), k (t vs 1), n | -3.22 (-2.40), 0.820 (-2.84), 1026 | same | no |
| C32 W1 Wed->Thu minus others (t) | -1.79 (-0.65) | same | no |
| C32 W2 Mon->Tue minus others (t) | +1.76 (0.67) | same | no |
| C32 T2 recovery (intraday window) | 61%, Fieller -29..117% | same | no |
| futures all invested nights, gross (FB gate) | 4.99 bp | same | no |
| basis Monday table, Wednesday table (R2 Wed->Thu dbasis -4.10 bp, t -2.00) | | byte-identical | no |
| pooled decomposition fut_ON / idx_ON / dbasis_ON (t) | 5.42 / 5.92 / -0.50 (-0.41) | 5.39 / 5.86 / -0.47 (-0.39) | yes; not cited in CLAIMS_REGISTER, FINAL_REPORT or README |
| weekday table Tue->Wed, full: n, fut_ON, idx_ON, dbasis_ON (t) | 394, 6.74, 8.05, -1.31 (-0.57) | 395, 6.57, 7.75, -1.18 (-0.51) | yes; not cited |
| weekday table Tue->Wed, pre-2022 | 185, 4.25, 2.57, 1.68 (0.60) | 186, 3.90, 1.96, 1.94 (0.69) | yes; not cited |
| 2018 decomposition row: n, idx_ON | 27, -6.40 | 28, -10.10 | yes; not cited |
| pre-2022 offset a t, k t vs 1 (reference rows) | 2.32, -5.22 | 2.33, -5.28 | yes; not cited |
| R1 / R2 / R3 / W1 / W2 / O1 verdict labels | | unchanged (only R3's 2018 slope changes, 0.84 -> 0.80) | no |

No registered claim moves under the applied fix.

## Inventory of the remaining carriers (NOT edited)

**Method.** Two throwaway copies of the current tree (FB already fixed):
- **B:** unpatched;
- **A:** the same raw-series-first fix applied to every remaining carrier, stock side included.

The same chain was run in both:
- pit_dayofweek_2x2, level_b_dayofweek, composition_diagnostic, open_filter_audit, pit_residual_split, pit_vs_futures;
- index_open_degradation_audit, option_c_t2_equity, regime_legs_audit, regime_changepoint_audit, regime_changepoint_repaired, regime_market_state_audit, futures_basis_decomp.

B reproduces every committed CSV byte-for-byte; the only differences are integrity file counts in the md footers. Impact = A minus B. Nothing in the repo was changed by this measurement.

**Nights lost.** Every stock's first row is dropped by a `gap == 1` filter computed after `decompose()`. 53 of the 54 PIT/current tickers lose a one-day night:
- 27 lose 2018-11-21 (files start 2018-11-20);
- 22 lose 2018-11-22 (files start 2018-11-21);
- SSB loses 2021-03-25, VPL 2025-05-14, TCX 2025-10-22;
- BMP loses 2017-08-08, before the basket START.

`pit_dayofweek_2x2` also takes the prior close (cap-weight input `PC`) after the drop, so the cap-weighted basket loses 2018-11-21 entirely. The index-side copies lose VN30 2018-11-21 and VNINDEX 2011-04-29.

| carrier (own pattern line) | series / night lost | committed tables it feeds | quantified impact if fixed (A - B) | registered claim |
|---|---|---|---|---|
| pit_dayofweek_2x2.py (RET gap, PC prior close) | stock panels: first night per stock; CW basket 2018-11-21 | _pit_cells.pkl, pit_dayofweek_2x2.csv, pit_dayofweek_effects.csv; exports X.RET / X.PC / cell_series downstream | 2x2 max 0.39 bp (PIT EW full-period 11.91 -> 11.52); effects max 0.07 bp | none directly; upstream of regime_legs (cap weights) |
| level_b_dayofweek.py | current-30 stocks, first night | level_b_dayofweek.csv, _by_stock.csv | basket rows max 0.58 bp (EW Mon+Tue - Wed+Thu, filtered 2018-21: 6.23 -> 5.65); per stock up to 11.5 bp (VPL, short history) | none (C12 cites level_b_rebuild_dayofweek.csv, already fixed) |
| composition_diagnostic.py | current-30 stocks, first night | composition_diagnostic.csv | max 2.0 bp (recent-joiner Tue->Wed 2023-26) | none |
| open_filter_audit.py ret_panel (stocks) + index_on (VN30 2018-11-21, VNINDEX 2011-04-29) | stocks + index | open_audit_benchmark.csv, open_audit_regime.csv, open_audit_summary.md | max 5.1 bp, 2018 only (PIT EW one-day basket 2018 mean -18.68 -> -23.82, ~28 nights); pooled cells <= 0.3 bp | C27: unchanged (flags table identical; 11.7 bp, t -5.77) |
| pit_residual_split.py (VN30 idx + stock sens_rep) | VN30 2018-11-21, stocks | pit_residual_split.csv | max 0.42 bp | none |
| regime_legs_audit.py stock_panels (+ X.PC) | CW basket 2018-11-21 (sample n 1559 -> 1560) | regime_legs_breaks/legs/monday/tolerance.csv, regime_legs_audit.md | pre-2022 cells <= 0.28 bp; post-2022 unchanged | **C4, C5, C13 move (below)**; C15 unchanged (48%, Fieller -88..138%) |
| regime_changepoint_audit.py (inherits RL; own vci_vnindex: VNINDEX 2011-04-29) | basket + VNINDEX | regime_changepoint_*.csv/md | LS dates unchanged; date intervals shift ~2 months; placebo cells up to 2.5 bp; scan +6 rows | **C6 interval moves**; C7 base t 3.77 -> 3.81 |
| regime_changepoint_repaired.py (rewrites and runs regime_changepoint_audit source) | as above | regime_changepoint_repaired_* | intervals shift | **C6 repaired interval moves** |
| regime_market_state_audit.py (inherits RL; own VNINDEX 2011-04-29, outside the episode windows) | basket | regime_market_state_controls.csv, _collinearity.csv | coefficients <= 0.3 bp; t +0.04..0.06 | **C7 moves at 2 dp**; C8 unchanged (episodes file identical) |
| inheritors, no own line: index_open_degradation_audit (X.PC, OA.ret_panel) | | index_open_degradation_quarterly.csv, md | 2018Q4 cells up to 5.1 bp | C19 (retired; no figure) |
| option_c_t2_equity (X.cell_series) | | levelb_dayofweek_basket.csv, md table | <= 0.78 bp; option_c_holds/legs/cost_grid identical | C23-C26 unchanged |
| pit_vs_futures (_pit_cells.pkl) | | pit_vs_futures_dayofweek.csv | <= 0.37 bp | none |
| futures_basis_decomp.pit_basket (OA.ret_panel) | | futures_basis_wednesday.csv, _robustness.csv (basket-minus cells) | <= 0.002 bp | none (R2 unchanged) |

### Registered figures that WOULD move if the remaining carriers were fixed (not applied; register not edited)
| claim | registered | with full fix | verdict / status change? |
|---|---|---|---|
| C4 CW ON pre (t) / post (t) | -0.7 (-0.2) / +13.5 (5.7) | -0.8 (-0.3) / +13.5 (5.7) | no |
| C5 CW ID pre / post; C2C break (t) | +10.75 / -2.35; +1.0 (0.19) | +10.96 / -2.35; +1.0 (0.18) | no |
| C13 futures ON pre (t) / post (t) / break, CI | 5.5 (2.6) / 7.1 (4.5) / +1.55, -3.6..6.7 | 5.4 (2.6) / 7.1 (4.5) / +1.64, -3.5..6.8 | no |
| C6 ON date interval (orig; repaired) | 2021-04-09..2024-08-20; 2021-03-10..2024-08-21 | 2021-06-18..2024-10-01; 2021-06-30..2024-10-29 | no (LS dates 2022-11-25 ON / 2022-08-26 ID unchanged; still 'undetermined within ~2021-2024') |
| C7 CW ON t base -> controls; CW ID spec A | 3.77 -> 4.13; -2.62 -> -1.59 | 3.81 -> 4.19; -2.66 -> -1.65 | no (SURVIVES / ATTENUATED N.S. unchanged) |

Every move is in a pre-2022 cell or a date interval, and none changes a verdict or status.

Note: under a full fix, the Task A FB outputs `futures_basis_wednesday.csv` and `futures_basis_robustness.csv` would change again, by at most 0.002 bp, through `pit_basket`. So the stock-side fix is not yet folded into these primaries.
