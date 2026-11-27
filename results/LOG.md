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
