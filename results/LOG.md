# results/LOG.md: one dated entry per audit (newest last). Overrides the 2026-11-22 report on every number and status.

## 2026-11-25 · data safety (queue 1)
Script: src/data_cap.py + 5 read-site edits; snapshot data/snapshots/20261125_pre_v6 (183 files, SHA-256 OK), data/snapshots/frozen_20261117. 4.99 bp gate reproduces from frozen copy (4.9902 bp, n 2284). Log: data/snapshots/SNAPSHOT_LOG.md.

## 2026-11-25 · 11-24 bar + second source (queue 2-3)
Script: src/forward_bar_audit.py -> results/forward_bar_audit.md. 11-24 bar absent from VN30/VNINDEX/futures in VCI and KBS: unrecoverable, Monday stays skipped_hold. KRX-coded VCI contracts match VCI VN30F1M 100% on 230 overlap days (all fields). KBS second source: coverage fail (2 overlap days on stitched front month); on one shared contract close/high/low/volume 100%, open 30.9% (KBS rounds opens). Cannot replace VCI; continuity needs a user decision (HARD STOP).

## 2026-11-25 · change-point rerun on repaired roll days (queue 4)
Script: src/regime_changepoint_repaired.py -> results/regime_changepoint_repaired_compare.md. n 1559->1572. No LS date changed, no Holm crossing 0.05, same detected set. Interval endpoints moved (bootstrap noise at changed n).

## 2026-11-25 · Level B + 2x2 rebuild, symmetric 7% rule (queue 6)
Script: src/level_b_rebuild.py -> results/level_b_rebuild.md (+ _run0/_run1 md kept). Treatments P (none), L (drop night if |ON| or |ID| > 7%), O (legacy). Found and fixed (labelled, rerun 1): first-row bug also in stock panels (gap and prev close taken after decompose dropped row 0) => 2018-11-21 night had been missing from the old 2x2 / level_b_dayofweek; restored. Break t (PIT CW): ON 3.70/4.78/4.35, ID -2.80/-3.32/-2.88 for P/L/O; C2C ~0 in all. H3: ON spread t 10.4, ID t -5.4, C2C spread ~0. Reviewer pass (fresh agent): arithmetic OK; fixes applied in rerun 2 (R4 coded, D1 redefined, CC label, wording, disclosures). R4 not triggered. Old files not edited.

## 2026-11-25 · final deliverable + reviewer pass (queue 8)
FINAL_REPORT.md drafted from CLAIMS_REGISTER.md. Fresh reviewer: 15 of 18 numbers matched; fixes applied: ex-2026 t source cited, weekday t range, eight over-strong sentences softened (futures stability, KBS, T+2, relocation, ID break not Holm-detected, causal basis wording), 'Not covered' section added, two [calc] CIs recomputed.

## 2026-11-25 · market-state controls (queue 5)
Script: src/regime_market_state_audit.py -> results/regime_market_state_audit.md. CW ON survives all four controls (t 3.77->4.13). CW ID attenuates (t -2.62->-1.59, spec A); survives in specs B and C. Neither 2018 nor 2020 drawdown shows the ON-up/ID-down signature.

## 2026-11-25 · record fixes (section A)
CLAIMS_REGISTER: added C23-C27 from option_c_summary.md / open_audit_summary.md (each number checked against the file: 1,052 dates, 9.0 bp NW t 1.30; net -21.0/-31.0/-51.0; give-back 79% unfiltered from ON1+ON2 23.5 vs ID1+ID2 -18.7, 62% filtered biased; regime 1 T+3 close 19.2 bp t 1.67; flags 11.7 bp lower t -5.77). Settlement-rule inputs labelled UNCONFIRMED (C26a). Post-2022 basket ID now -2.35 bp (file value). Copies of previous register/report in data/snapshots/record_20261125/.

## 2026-11-25 · Q1 date-level flat-open test (section B)
Script: src/q1_flat_open_regime.py -> results/q1_flat_open_regime.md. R1 PASS: flat-open share 27.3% -> 26.2% (-1.1 pp); unflagged CW ON break +15.6 bp (t 3.85); identity check: share change moves ON by ~0.2 bp. R3 (H3 on unflagged nights): fails (ON t 1.91) on 18/94 eligible months; post hoc coverage-matched version ON t 9.0. Run 0 crashed (.diff attribute) before output; run 1 added (iv-b) post hoc; reviewer -> rerun 2 (identity check, lag-20/60 CIs, R3 wording, integrity scope). Q3 resolved (universe).

## 2026-11-25 · Level A robustness (section C)
Script: src/level_a_robustness.py -> results/level_a_robustness.md. Split dates sourced: COVID 2020-01-23 (first confirmed cases; CDC, ASCP/The Hill; WHO says 01-24), KRX go-live 2025-05-05 (Vietnam News, Tuoi Tre/NLD, The Investor). Run 0 had an alignment bug (index rows NaN; md kept); rerun 1 fixed. Finding: ON-ID significant on all nights (VNINDEX +7.11, t 3.84) but not on one-day nights (+1.43, t 0.66); Monday ID -22.3 bp (t -4.74) -> Test 1b added post hoc. COVID/KRX splits change the H1 label for the basket but not within regime 2. Reviewer -> rerun 2 (same-date R3, R4 blanking, break t, labels).

## 2026-11-25 · data-source probe + logger guard (section D)
Script: src/source_probe.py -> results/source_probe.md + source_probe_notes.md; bars in data/raw_probe/<run>/. vnstock 4.0.4 -> VCI exact (100% all fields); direct VCI POST with honest headers HTTP 400 (no impersonation, branch stopped); KBS not field-exact; PyPI 404 for vnstock; v6 needs broker key (HARD STOP). VCI 1-minute history reaches 2024-05-31 (PARKED 5). src/track_forward.py: prints data paths/last bars; checks first N rows of data/raw/VN30F1M.csv vs manifest-verified snapshot, exit 2 before log rebuild if rewritten. Tested on scratch copy (clean / tampered -> exit 2 / appended / real --refresh); live run: log, scorecard, boundary byte-identical. Original in data/snapshots/code_20261125/.

## 2026-11-25 · final review of A-D (section E)
Fresh reviewer on register C1/C4/C5/C9/C21/C23-C30, FINAL_REPORT, track_forward diff, source probe. Numbers matched. Fixes: C9 no longer counts the post hoc selected-sample H3 check as evidence; 30% give-back labelled filtered/biased; C26 net negative only significant at 60 bp; Monday flat-open check moved into a results file (level_a_robustness Test 1c, rerun 3); 'after 2022' wording scoped to basket ON and VNINDEX ON-ID; futures 'no detected break'; Holm detail (CW vs EW ID); C2C power (~15 bp); intraday history corrected to 2023-09-11 (cached probe); P1 described as self-consistency and its grade explained. track_forward: fixed reference snapshot, fails closed, checks VN30F1M and VN30F2M via futures_csv, pre-refresh backup folder; retested on scratch (clean, tamper F1M, tamper F2M, append, missing manifest, real --refresh); live run: log, scorecard, boundary and VN30F1M equal to the snapshot manifest.

## 2026-11-25 · regime break by night length
Script: src/regime_nightlength.py -> results/regime_nightlength.md (+ _run0.md). Header (V1-V4) written before the first run in this session (no git, so not externally timestamped). Verdict CW and EW: V1 RELOCATION STANDS on one-day nights (CW ON +13.81 bp t 3.70, ID -14.02 t -2.80; EW +15.59 t 4.04, -18.02 t -3.69); post-weekend breaks not significant (CW ID -4.12, t -0.30) and underpowered (MDE80 38.8 bp, power ~17%). Post-weekend ID drop present in both regimes. Fresh reviewer: arithmetic and a from-scratch CW rebuild match exactly; fixes in rerun 1 (power/MDE line, V3 code aligned to header, integrity after writes, calendar from file, <250 tag shown); estimates unchanged. Register: C31 added, C4/C5/C30 updated; FINAL_REPORT sections 1-2 updated. data/raw, boundary and logger untouched.

## 2026-11-25 · weekly refresh automated (launchd)
Added scripts/weekly_refresh.sh and ~/Library/LaunchAgents/com.harry.overnight-refresh.plist (Tue 04:30, Wed 12:00 local; RunAtLoad false; logs in logs/). No change to src/track_forward.py, boundary, kill rule or data source; no credentials; no sudo.
python3 used: /Library/Frameworks/Python.framework/Versions/3.13/bin/python3 (3.13.14; vnstock 4.0.4, pandas 2.3.3). Note: `vnstock.__version__` does not exist in 4.0.4 (AttributeError); version read via importlib.metadata.
Tests: bash -n OK; plutil OK; separate dry-run job (com.harry.overnight-refresh.dryrun, --dry) bootstrapped and kickstarted through launchd: correct python, PATH, HOME, cwd, vnstock/pandas import, logs/ writable, exit 0; booted out after. data/raw hashes identical before/after. Real-branch logic tested on the scratch project copy only (wrapper copy with REPO pointed there): real --refresh exit 0 with status file; tampered old row exit 2 with guard notification. No real refresh was run in the project (not due). Real job bootstrapped in gui/501; launchctl print shows both calendar triggers, runs = 0. First automatic run Tue 2026-12-01 04:30 local.


## 2026-11-26 | relocation mechanism (why 2022), cross-section
Script: src/relocation_mechanism.py -> results/relocation_mechanism.{md,csv}. Pre-registered. 30 PIT members as of 2022-08-01, +/-365d around D=2022-08-25, unfiltered nights. Pooled ON break +6.63 bp, ID -10.15, C2C -3.51 (EW, this window). Decision test: ON break on log(ADV) OLS slope -3.57 bp/unit, t -1.23 (n.s.); Spearman -0.11; price t -0.41; turnover t +0.46. ADV terciles ON break 8.5/6.5/4.9 (low->high liq). VERDICT: no significant liquidity/retail-proxy gradient -> relocation looks broadly market-wide, with at most a weak (non-significant) tilt toward lower-liquidity names; settlement-behaviour mechanism NOT confirmed. C18 moved from untestable -> tested/inconclusive (underpowered, n=30). Limit: OHLCV has no retail/institutional split.

## 2026-11-26 | relocation mechanism -- verification + interpretation correction
Validated engine: full pre/post EW relocation reproduces (per-stock-avg and date-level agree: ON +11.3, ID -15.5, C2C -4.1 bp; C2C -4 bp EW vs ~0 cap-weighted = weighting, not a bug). Robustness: ON-break-on-log(ADV) slope negative at +/-180/365/504/730d (t -1.80/-1.23/-1.58/-1.63), consistent but never |t|>=2, strongest (near-sig) at +/-180d. CORRECTION: the first-cut 'leans market-wide, mechanism not supported' overreached -- (a) the tilt is weakly FAVOURABLE to a retail/low-liquidity channel, not against it; (b) the T+2 rule is market-wide, so a uniform/null gradient is consistent with settlement and cannot be used against it. Verdict: genuinely inconclusive; open.

## 2026-11-27 | direct VCI fetcher (vnstock v4/v5 sunset) -- GATE FAIL (FPT), not integrated
Scripts: src/fetch_vci_direct.py (fetcher, no vnstock import), src/vci_direct_validate.py (gate pre-registered in header) -> results/vci_direct_validation.md; headers in results/vci_headers_captured.json; bars in data/raw_probe/vci_direct_20261127T004647Z/ only.
Headers: live wire capture of vnstock 4.0.4 (monkeypatched requests.Session.request). It sends NO Device-Id (the helper exists but is never called), no cookie, no auth; a browser UA + Accept/Sec-Fetch headers are what avoid source_probe's HTTP 400. Direct POST with the captured headers -> HTTP 200. Symbol codes 1:1 (VNINDEX, VN30, VN30F1M, VN30F2M, stocks). Transform mirrors vnstock: stocks /1000, all round(2), HCM dates.
G1 (vs frozen_20261117 + data/raw, 100% required): 8/9 symbol x ref comparisons exact on 34-39 overlap rows (VN30F1M, VN30F2M both refs; VN30; VNINDEX; VCB; HPG). FPT 0% OHLC, 2.9% volume -> STOP (opens differ). Cause: VCI rescaled FPT prices by a constant ~0.9775 (corporate action, ex-date 11-18..11-27, unverified); FPT volumes also revised separately (cause unknown). G2 same-run A/B vs vnstock: 34/34 symbols 100% all fields (fetcher == vnstock, including revised FPT). Integrity: data/raw + frozen hashes unchanged (63 files).
Fresh reviewer: numbers recomputed exactly; no code must-fix. Fixes applied: FPT volume wording (not uniform), 6 (not 8) index/futures comparisons, ex-date window, G2 strict-match + interleaving (REV 1, labelled; not rerun, verdict can't change), alias removal, fail-loud wrapping.
Flag (pre-existing): fetch_indices incremental stock refresh can splice VCI back-adjusted rows onto unadjusted data/raw rows. Not changed. Step 4 not done; fetch_indices, track_forward, data/raw, boundary, kill rule untouched. Uncommitted.

## 2026-11-27 | ATC-drift test (futures closing auction), pre-registered, measurement only
Script: src/atc_drift_test.py -> results/atc_drift_summary.md (pre-registration written above the results marker before the first run) + atc_drift_{nights,tests,posthoc}.csv. Cached data only (VCI VN30F1M 1m, VCI VN30 5m); cap 2026-11-17. Backup first: data/snapshots/raw_intraday_20261127T014311Z.tar.gz (+ .sha256, + per-file MANIFEST.sha256; untar verified 13/13).
Gate: 2.2a reproduced (n 782, 5.5975 bp, t 3.535). The "5.0 bp" quick cut is not reproduced exactly; the nearest cuts are keeping the 4 misaligned nights (4.81) and naive pairing without a roll fix (4.59).
P1 fails: auction leg a -0.85 bp (t -1.00, n 786; 95% CI -2.5..+0.8, so this is not a power problem). P2 fails: slope of on_atc on a +0.20 (t 1.14). P3 holds as pre-registered (>= 5 bp): Wed minus others +5.69 bp (t 2.67); it would fail under a >= 10 bp reading, but Thu ex-expiry -7.5 bp and Fri -4.1 bp. Joint weekday Wald p 0.004. VERDICT: H REJECTED by the rule. B gets the rule's default label. The pre-registered symmetric-revert check is NO (-0.83 bp, t -0.18, power-limited), but the mean give-back points B's way: index 09:15->10:00 -7.28 bp (t -1.93) vs futures -1.84 (t -0.71).
C (1-yr window, n 243): index auction leg -5.08 bp (t -3.48), futures -1.01 (t -0.60), difference +4.06 (t 2.89). POST HOC (labelled): on the same 232 non-roll nights the index-minus-futures ON gap is 6.51 bp from closing prints (t 2.70) and 1.86 bp from pre-auction clocks (t 0.82); the difference is the auction leg, 4.64 bp (t 3.35). Mean-level only: index ON on its auction leg has slope +0.42 (continuation), but the basis shortfall does revert (slope 0.54, t 2.56). One year; needs its own pre-registration.
Protected files (data/raw, frozen, raw_intraday, track_forward.py, boundary; 78 files) hash-identical before/after. Uncommitted.

## 2026-11-27 | fetch backend switch: futures/index -> direct VCI (approved, scoped) -- GATE PASS, uncommitted
Change: src/fetch_indices.py only (backend_for + _download_vci_direct + 4-line dispatch). VN30F1M/VN30F2M/VN30/VNINDEX with source VCI -> src/fetch_vci_direct.py; stocks and other sources unchanged (vnstock). It sends the same request vnstock does (to = end+1d, countBack = bdays+1, no start filter). Overlap/keep='last', _drop_incomplete, flag_suspicious, track_forward.py, boundary, kill rule untouched. Rollback: OVERNIGHT_FETCH_BACKEND=vnstock (docs/fetch_backend_rollback.md).
Gate (src/backend_switch_validate.py, pre-registered; REV 1 labelled) -> results/backend_switch_validation.md; bars in data/raw_probe/backend_switch_20261127T034849Z/.
G1 full-history refetch, new backend: 100% on O/H/L/C/V + open_suspicious. VN30F1M 2306 rows vs raw, 2301 vs frozen; VN30F2M 1997 / 1992; VN30 1994; VNINDEX 3885 (from 2011-04-28). No coverage differences.
G2 A/B vs vnstock: all fields 100% on vnstock's window; VN30F1M byte-identical. vnstock now caps 1D history at 8 years (VN30F2M/VN30/VNINDEX start 2018-11-29), so G2 was redefined from file bytes to that window (REV 1, written after run 0 crashed in formatting and before any verdict).
G3 track_forward dry runs in two throwaway repo copies (direct vs vnstock): no-refresh outputs byte-identical to live; --refresh exit 0, guard passed, +1 bar each (2026-11-26), boundary unchanged, rows <= 2026-11-17 unchanged, scorecard identical to live; D == V byte-for-byte (F1M, F2M, log, scorecard).
G4: 67 protected files (data/raw, frozen_20261117, track_forward boundary/log/scorecard, track_forward.py) hash-identical before/after. No real refresh run in the project.

## 2026-11-27 | 2018-11-21 first-night bug: FB-only fix (Option A) + inventory (#5) -- GATE PASS, uncommitted
Fixed: src/futures_basis_decomp.py index_nights(). Prior date/close now come from the RAW series before decompose() drops row 0; the result .equals() futures_roll_gap_repair.index_nights_fixed(). src/futures_roll_gap_repair.py now has index_nights_legacy() pinned (frozen pre-fix copy, equal to HEAD 0c3c8f4, labelled DO NOT 'fix'), and the 'before (as reported)' variant uses it. That script was not rerun.
Regenerated futures_basis_decomp.py (its own gate PASSED; N 1,962 -> 1,963) and futures_basis_followup.py. GATE: all 9 tables equal their *_fix20181121.csv twins byte-for-byte. The twins are now redundant; not deleted (Harry's call).
Headline: C14 (a -3.22, t -2.40, k 0.820), C32 (W1 -1.79/t -0.65, W2 +1.76/t 0.67, T2 61%), futures all-nights 4.99 bp, and the Monday/Wednesday tables are unchanged. Moved but not cited anywhere: pooled decomposition fut/idx/dbasis 5.42/5.92/-0.50 -> 5.39/5.86/-0.47; Tue->Wed weekday cells (full and pre-2022); the 2018 row. No registered claim moves.
Correction to the earlier pass: a first pass also edited the index-series lines in pit_residual_split, open_filter_audit, regime_changepoint_audit and regime_market_state_audit (Option B). Reverted to HEAD after Harry chose Option A, together with their 2 regenerated md footers. Their outputs had been byte-identical anyway.
Inventory (not edited) -> results/fix20181121_inventory.md. Measured in two throwaway copies of the tree (B unpatched reproduces every committed CSV; A has every remaining carrier fixed).
- Carriers: pit_dayofweek_2x2 (RET + PC), level_b_dayofweek, composition_diagnostic, open_filter_audit (ret_panel + index_on), pit_residual_split, regime_legs_audit, regime_changepoint_audit (+_repaired) and regime_market_state_audit. Inheritors: index_open_degradation_audit, option_c_t2_equity, pit_vs_futures, futures_basis_decomp.pit_basket.
- Lost nights: 53/54 tickers lose their first one-day night (27 lose 2018-11-21, 22 lose 2018-11-22, plus SSB/VPL/TCX/BMP); the CW basket loses 2018-11-21; VN30 loses 2018-11-21; VNINDEX loses 2011-04-29.
- If fixed, these registered figures would move with no verdict change: C4 CW ON pre -0.7 -> -0.8; C5 CW ID pre 10.75 -> 10.96 (C2C t 0.19 -> 0.18); C13 futures pre 5.5 -> 5.4, break 1.55 -> 1.64; C6 ON interval 2021-04-09..2024-08-20 -> 2021-06-18..2024-10-01 (LS dates unchanged); C7 CW ON t 3.77->4.13 becomes 3.81->4.19.
- Unchanged: C8, C15, C23-C27. Largest table shift: 5.1 bp in 2018-only basket cells (open_audit, index_open_degradation).
- CLAIMS_REGISTER not edited.

## 2026-11-27 | stock back-adjustment guard (policy: stock data frozen; reopen = full re-pull) -- uncommitted
src/fetch_indices.py: in update(), for every symbol outside DIRECT_VCI_SYMBOLS (i.e. stocks), check_stock_overlap() compares the cached rows the fresh fetch overlaps BEFORE the keep='last' merge. Any O/H/L/C change (|diff| > 1e-6) or any volume change raises StockRevisionError and nothing is written. The message names the changed rows and fields and the reopen path. update_with_retry re-raises it at once (no 65 s retry). Volume is included on purpose (FPT's volumes were revised too, and it mirrors track_forward's any-change guard); narrow to OHLC by deleting one line.
Futures/index: not checked here; logger, boundary and kill rule unchanged.
data/README.md: one note (stocks frozen; reopen = full re-pull via direct VCI into a new dated snapshot).
Tests on scratch copies of data/raw (repo data untouched):
- Offline (_download monkeypatched): FPT x0.9775 -> abort; a single close +0.05 -> abort; volume-only change -> abort; identical overlap -> passes; update_with_retry -> abort with 0 sleeps; VN30F1M/VNINDEX changed overlap -> no guard (unchanged behaviour).
- Live vnstock: FPT ABORTED (the real VCI back-adjustment); VCB passed (8 overlapping rows unchanged, +6 rows in scratch).
Open:
- The guard blocks splicing, not incremental stock refresh as such: an unchanged overlap still appends.
- The full-re-pull path itself is not built: stocks still route to vnstock, which now caps 1D history at 8 years. A direct-VCI stock re-pull into a dated snapshot is still to do.

## 2026-11-27 | 2018-11-21 first-night bug: FULL fix across all remaining carriers (approved) -- both gates PASS, uncommitted
Fixed (gap and prior close taken from the RAW series before decompose() drops row 0): pit_dayofweek_2x2 (RET gap + PC prior close), level_b_dayofweek, composition_diagnostic, open_filter_audit (ret_panel + index_on), pit_residual_split (VN30 idx + sens_rep), regime_legs_audit, regime_changepoint_audit (VNINDEX 2011-04-29), regime_market_state_audit. The inheritors have no pattern line of their own and were regenerated: pit_vs_futures, index_open_degradation_audit, option_c_t2_equity, regime_changepoint_repaired, regime_rebase_audit, level_b_rebuild (only its old-vs-O table), futures_basis_decomp (pit_basket; code untouched). level_b_rebuild and futures_basis_decomp code untouched; futures_roll_gap_repair not run.
Regenerated: the whole import closure of the carriers (22 scripts) in the repo. 36 CSV/PKL changed and 11 md.
GATE (a): an unpatched copy of the tree (476e99c) reproduces all 152 committed CSV/PKL byte-for-byte; mds differ only in integrity file counts. PASS.
GATE (b): PASS on both levels.
- Table level: control tree M (the fixed code plus one line per fix site re-blanking only the first decomposed row; 10 lines in 8 files) reproduces all 152 committed CSV/PKL byte-for-byte, so every diff is caused solely by the first-night rows.
- Series level, 16 exported panels (2x2 RET/PC, OA ret_panel x4 / index_on x4, RL ON/ID/CC, RC vci_vnindex, LBD load x2): 0 existing cells changed; every new cell is on its own series' first night (52 stock series; 42 under the flag/7% filter; VN30 and VNINDEX 1 each).
- The repo regeneration equals the patched tree byte-for-byte.
Registered figures updated (marker "(2026-11-27: 2018-11-21 first-night fix)"):
- C4 CW ON pre -0.7 -> -0.8; C5 CW ID pre 10.75 -> 10.96; C13 futures ON pre 5.5 -> 5.4, break 1.55 -> 1.64; C6 ON interval 2021-04-09..2024-08-20 -> 2021-06-18..2024-10-01; C7 CW ON t 3.77->4.13 -> 3.81->4.19.
- Edited in CLAIMS_REGISTER (5) and FINAL_REPORT (3; C6 and C13 appear there only at a precision that does not move).
FLAGGED, NOT EDITED (these move too but were not on the approved list):
- Register: C4 t -0.2 -> -0.3; C5 C2C t 0.19 -> 0.18 (break +1.0 unchanged at 1 dp); C6 repaired interval 2021-03-10..2024-08-21 -> 2021-06-30..2024-10-29; C7 CW ID spec-A t -1.59 -> -1.65; C13 break CI -3.6..6.7 -> -3.5..6.8.
- FINAL_REPORT line 12: ON break +14.1 -> +14.3 (CI 6.8..21.5 -> 6.9..21.6); ID break -13.1 -> -13.3 (CI -22.9..-3.3 -> -23.1..-3.5).
- Line 18: '739/820' -> 740/820 and '13.8 vs 14.1' -> 14.3. Line 19: ID t -1.59 -> -1.65. Line 20: Holm p CW ID 0.168 -> 0.166, EW ID 0.018 -> 0.015. Line 40: futures break CI -3.6..6.7 -> -3.5..6.8, paired break t 5.0 -> 5.1.
Verdicts:
- No verdict, status or detection label changed: md verdict keywords identical; LS dates and Holm 'detected' flags identical; SURVIVES / ATTENUATED N.S. unchanged.
- Unchanged figures: C8 (episodes file identical), C15 (48%, Fieller -88..138%), C23-C26 (option_c holds/legs/grid identical), C27 (flags identical; 11.7 bp, t -5.77).
- Exception, descriptive and uncited: in the legacy level_b_dayofweek_by_stock.csv the per-stock 'top night' label flips for BID, LPB (Tue->Wed -> Wed->Thu) and SSB, and STB's Mon/Tue-top-2 flag flips. Its stdout breadth count goes 19/30 (binomial p 0.100) -> 17/30 (p 0.292); it is in no results file or document.
Stale text: level_b_rebuild.md's hard-coded sentence 'Legacy-vs-O differences (e.g. Tue->Wed n 394 vs 395) come from the 2018-11-21 fix' no longer applies; legacy now equals O. Left unedited.
Cell-level change log: results/fix20181121_fullfix_changes.csv (2,442 cells in 33 tables, plus per-series summaries for the 2 scan tables, which gain 1 candidate date per series).
Deleted the 9 superseded twins results/*_fix20181121.csv (recoverable: git show 6ab59cf:<path>). 7 were byte-identical to their primaries. futures_basis_wednesday and futures_basis_robustness now differ from their twins by <= 0.002 bp, because pit_basket inherits the stock-side fix. Kept futures_roll_gap_fix20181121_changes.csv (change log) and index_nights_legacy().
Integrity: data/raw, frozen_20261117, raw_intraday, track_forward.py, level_c_futures.py, futures_basis_decomp.py, level_b_rebuild.py and the track_forward results are hash-identical before/after.

## 2026-11-27 | 2018-11-21 first-night fix: doc sweep (no figure that moved may sit next to a stale one) -- doc edits only, uncommitted
Approved by Harry: every figure that moved under the full fix is updated wherever it is cited, with the marker "(2026-11-27: 2018-11-21 first-night fix)". No code, data or results table was regenerated in this pass.
CLAIMS_REGISTER (8 edits):
- C4: pre t -0.2 -> -0.3; CI column: pre CI [calc] -6.4..5.1 -> -6.5..4.9; break +14.1 bp, CI 6.8..21.5 -> +14.3, CI 6.9..21.6.
- C5: C2C break t 0.19 -> 0.18 (the +1.0 bp is unchanged at 1 dp); CI column: ID break -13.1, CI -22.9..-3.3 -> -13.3, CI -23.1..-3.5.
- C6: repaired ON interval 2021-03-10..2024-08-21 -> 2021-06-30..2024-10-29.
- C7: CW ID t with all four controls -1.59 -> -1.65.
- C13: break CI -3.6..6.7 -> -3.5..6.8.
- C22: the pre-2022 CI [calc] -6.4..5.1 -> -6.5..4.9. This is the same interval as C4 and was not on the flagged list.
FINAL_REPORT (8 edits):
- Line 9: CI about -6.4..5.1 -> -6.5..4.9. This is C22 and was not on the flagged list.
- Line 12: ON break +14.1 (CI 6.8..21.5) -> +14.3 (6.9..21.6); ID break -13.1 (CI -22.9..-3.3) -> -13.3 (-23.1..-3.5).
- Line 18: 739/820 -> 740/820; '13.8 vs 14.1' -> '13.8 vs 14.3'.
- Line 19: t -1.59 -> -1.65.
- Line 20: Holm p 0.168 -> 0.166 (CW ID, not detected) and 0.018 -> 0.015 (EW ID, detected).
- Line 40: futures break CI -3.6..6.7 -> -3.5..6.8; paired break t 5.0 -> 5.1 (5.018 -> 5.050; the +12.6 bp is unchanged).
Note on the old [calc] CI: mean +/- 1.96*mean/t on the old file gives -6.381..5.048. The registered '5.1' was a double rounding of 5.048; the new interval is -6.530..4.887.
Sweep of the other publish-bound docs:
- README.md: no figure moved. All its figures come from unmodified sources (Level A, the post-2022 basket level, Option C holds) or are unchanged at the precision shown.
- docs/medium-writeup.md: one figure moved. In the relocation table (line 76) the intraday pre level +10.8 -> +11.0 (10.75 -> 10.96). Every other figure in it is unchanged at its precision.
- Two figures in that same row are FLAGGED, NOT EDITED. Neither was caused by the fix:
  - 't -2.8' does not match the source the row uses. regime_legs ID break t is -2.62 old / -2.66 new, which displays as -2.6 / -2.7. -2.80 is the one-day-night (C31 / level_b_rebuild P) ID break t, which is unchanged.
  - '-2.4' is a double rounding of -2.3496 (post-2022, unchanged by the fix; -2.3 at 1 dp).
results/level_b_rebuild.md: rewrote the false sentence 'Legacy-vs-O differences (e.g. Tue->Wed n 394 vs 395) come from the 2018-11-21 fix'.
- The new text says legacy and O now agree on every row. All 5 rows of level_b_rebuild_old_vs_O.csv are equal in n and mean, and t agrees to 1e-15.
- It also says the old 394-vs-395 gap was the first-night bug in the legacy 2x2.
- This is a doc edit only; level_b_rebuild.py is untouched. That script hard-codes the old sentence, so any rerun will write it back.
Uncited breadth change, for the record: legacy per-stock day-of-week table results/level_b_dayofweek_by_stock.csv (src/level_b_dayofweek.py).
- Stocks whose top overnight night is Mon->Tue or Tue->Wed (sum of column top_is_mon_or_tue): 19/30 (one-sided binomial p 0.100) -> 17/30 (p 0.292). The count is in the CSV; the p-value is printed to stdout only.
- Flips: BID and LPB top night Tue->Wed -> Wed->Thu; SSB Thu->Fri -> Wed->Thu; STB rank_monTue_top2 True -> False (column total 12 -> 11).
- Not cited in CLAIMS_REGISTER, FINAL_REPORT, README or the Medium draft. C12 cites level_b_rebuild_dayofweek.csv, which is unmodified.
Verdicts: no verdict label, status, break date or detected/not-detected flag changed.
- LS dates: CW/EW ON 2022-11-25, CW/EW ID 2022-08-26, paired 2022-12-07, FUT ON 2020-03-17. Original and repaired runs both.
- Holm p values stay on the same side of 0.05:
  - CW ON 0.012; CW ID 0.166 (not detected); EW ON 0.012; EW ID 0.015 (detected); FUT ON 0.262 (not detected); paired 0.012.
  - Repaired set: CW ID 0.106, FUT ON 0.327 (both not detected); the rest are <= 0.012 (detected).
- Spec-A labels: SURVIVES / ATTENUATED N.S. unchanged.
- Provenance check: every number on every touched row (C4, C5, C6, C7, C13, C22; FINAL_REPORT lines 9, 12, 18, 19, 20, 40; Medium lines 75-76) was re-derived from the regenerated table at the precision shown and matches. The only exceptions are the two flagged Medium figures.
- The q1_flat_open_regime, regime_nightlength, level_b_rebuild_dayofweek, level_a_robustness, futures_basis_followup_summary and level_c sources behind the other numbers on those rows are unmodified.
Label/date/flag column sweep. Covers every bool, object and date column of the 36 changed CSV/PKL files, HEAD vs working tree: row by row where the row count is unchanged, old-rows-subset-of-new where rows were added. Only the following differ:
- the level_b_dayofweek_by_stock flips above;
- the change-point date intervals (ci_lo/ci_hi/ci_orig/ci_rep), already reported;
- +1 row per _pit_cells.pkl series and +1 candidate date per series in the two scan tables (old rows are a strict subset of the new);
- 2 of the 10 'random' placebo dates per series in regime_changepoint_placebo.csv and ..._repaired_placebo.csv: 2019-11-14 -> 2019-11-13 and 2020-05-26 -> 2020-05-22.
The placebo dates are fixed-seed draws of positions in the night list, so adding one night shifts the draws. The placebo result line in both audit mds is identical: random dates above the 08-25 |t| are CW ON 3/10, CW ID 0/10, EW ON 3/10, EW ID 0/10, FUT ON 7/10 (repaired 10/10), paired 4/10. These dates are cited nowhere; C8 rests on the regime_market_state episodes, which are unchanged.
Correction to the previous entry: it said the 19/30 -> 17/30 breadth count 'is in no results file or document'. The count is the column sum of top_is_mon_or_tue in results/level_b_dayofweek_by_stock.csv; only the binomial p-value is stdout-only. Neither is cited in a publish-bound document.
