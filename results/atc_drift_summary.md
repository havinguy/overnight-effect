# ATC-drift test: does the futures closing auction price in overnight drift? (measurement only)

## PRE-REGISTRATION (written 2026-11-27 UTC before any number in this file was computed; data/raw_intraday backed up first to data/snapshots/raw_intraday_20261127T014311Z.tar.gz)

**Data.** Only the cached files: `data/raw_intraday/VCI_VN30F1M_1m.csv` (futures, 2023-09-11 onward) and `data/raw_intraday/VCI_VN30_5m.csv` (index, 2025-11-24 onward). Nothing is re-fetched. Daily futures come from the frozen snapshot via `data_cap.futures_csv`, daily index from `data/raw/VN30.csv`. Every sample is capped at DATA_CAP 2026-11-17: no night with an open date after the cap, and no auction day after it.
**Conventions** are reused from `src/futures_basis_followup.py` / `futures_basis_decomp.py`:
- log returns; bars labelled by bar START;
- a night is dated by its open date T, and its weekday label is the weekday of the entry (auction) day, so the "Wed night" is the Wednesday auction followed by the Thursday open;
- NW/HAC Bartlett lag 5 over consecutive nights (`nw_t`, `hac`, `ols_ak`, `weekday_test`);
- holiday nights are excluded from weekday cells.

**Night set (= 2.2a).** Invested `futures_nights()` nights that have a futures 1m day and are in the aligned `panel()`. This drops the 4 misaligned Thu-close -> Mon-open nights. Roll nights enter at the VN30F2M daily close, as `level_c_futures.build` does.

**Legs (night T, auction day E = prior futures trading day):**
- `a` = ln C(14:45, E) - ln C(14:29, E) from 1m VN30F1M bars. C(14:29) is the close of the bar labelled 14:29, i.e. the last continuous print before the ATC. If that bar is missing, the last close before 14:30 is used, and these cases are counted. C(14:45) is the ATC bar close; how often it equals the daily close is reported.
- `on_atc` = ln F(09:00 open, T) - ln entry(T): entry = C(14:45, E) on normal nights, the F2M daily close on roll nights. This is exactly 2.2a's `cum_09:00`.
- `on_1429` = ln F(09:00, T) - ln C(14:29, E). On non-roll nights the identity `on_1429 = a + on_atc` holds exactly. On roll nights it does not: `a` is the expiring contract's auction, `on_atc` starts from the next contract.

**STEP 2 gate.** On the night set, mean(on_atc) must reproduce 2.2a's "2023-09-11 onward, all nights, 09:00" row: n = 782 exactly and mean = 5.597 bp within 0.0005 bp (t 3.535 within 0.0005). The script raises (exit 1) and computes nothing else if this fails. A reported quick cut of 5.0 bp is reconciled explicitly in a diagnostic table of alternative night sets / entries.

**Predictions (H, Harry): the 14:30-14:45 futures closing auction prices in overnight drift.**
- **P1 (capture).** mean(a) > 0 with NW t > 2. Sample: every night in the gate set (auction day = E), which is the full intraday sample and is entirely post-2022-08-25.
- **P2 (front-running).** OLS on_atc = c + b*a with NW SEs: b < 0 and NW t(b) < -2. Primary sample: the gate set excluding roll nights, so the auction and the next open are on the same contract. All nights are also reported. Pearson r is reported too.
- **P3 (Wednesday).** In `weekday_test` on a (5 night dummies, HAC), Wed->Thu minus the mean of the other four must be > 0, at least 5 bp (i.e. of order 10 bp), and have t > 2.576 (Bonferroni over 5 cells at 5% two-sided).
- **Verdict rule.** H is SUPPORTED only if P1 holds AND (P2 or P3) holds. If mean(a) ~ 0 AND slope ~ 0 (both |t| < 2), H is REJECTED and B is reported as the better-supported account. Any other combination is "H NOT SUPPORTED (mixed)" and is described as such.

**Competing hypothesis B.** The futures-vs-index ON gap is an index-OPEN overshoot: index ON is inflated at the ATO and reverts after 09:15, while futures do not move.
- D (1-yr window). Reversion stat rev_h = -sign(idx_ON) * ln(I_h / I_09:15) for h = 09:30, 10:00, where idx_ON = ln I_open(T) - ln I_close(E). A positive mean means the open reverts symmetrically for gap-ups and gap-downs.
- The futures counterpart uses the same sign: -sign(idx_ON) * ln(F_h / F_09:15).
- B counts as INDEPENDENTLY CORROBORATED only if the index rev_10:00 mean is > 0 with t > 2 and the futures counterpart has |t| < 2. This is reported next to the verdict rule and does not change it.
- Wed cut reported. Also reported: the plain post-open index drift ln(I_h/I_09:15), as in 2.2e, and the OLS slope of that drift on idx_ON.

**Tests.**
- A. `a`: full sample; by weekday (Bonferroni |t| ~ 2.58); auction-on-expiry-day cells separately (E = expiry day, i.e. roll nights) and ex-expiry.
- B. P2 regression and Pearson r. Decomposition by weekday on non-roll nights: mean on_1429 = mean a + mean on_atc, with share = mean a / mean on_1429.
- C. Matched auction, 1-yr window (nights whose E has index 5m bars, 2025-11-24 .. 2026-11-17). Index leg = ln I_close(14:45 bar, E) - ln I_close(14:25 bar, E). The 14:25 bar is the last 5m bar before the ATC; the 14:30 bar is missing on ~23% of days, so it is not used. Report a - idx_leg by weekday.
  **Power limit stated up front:** n ~ 244 overall, Wed ~ 47. For each cell the MDE80 = 2.80 * NW SE of the cell mean (5% two-sided, 80% power) is reported. A cell whose MDE80 exceeds 10 bp is flagged POWER-LIMITED: it cannot detect a ~10 bp effect.
- D as above.

Everything below the marker is produced by `src/atc_drift_test.py`, which keeps this section verbatim.

<!-- RESULTS BELOW (generated) -->

## STEP 2 reproduction gate
n 782 (target 782), mean 5.597453 bp (target 5.597; full-precision 2.2a value 5.597453 from futures_basis_followup_intraday.csv, diff 0.0e+00), NW t 3.53472 (2.2a 3.53472): PASS

Reconciliation of alternative cuts (diagnostic only; the gate row is the one used):
                                                                                         cut   n  mean_bp     t
             GATE: 2.2a set, entry = build() (F2M close on roll nights), exit 09:00 bar open 782    5.597 3.535
                        + misaligned nights kept (all invested futures nights with a 1m day) 786    4.812 2.905
entry = intraday 14:45 close of prior 1m day (no roll fix: crosses contracts on roll nights) 781    5.404 3.323
  naive: every consecutive 1m day pair, 14:45 close -> 09:00 open, no roll fix, no alignment 785    4.588 2.754
                                                       GATE set but simple (not log) returns 782    5.759 3.646
                                            GATE set, exit = daily open instead of 09:00 bar 787    5.523 3.490
                                                                     GATE set ex roll nights 748    5.402 3.304

Data checks: C(14:29) filled from an earlier bar on 0 auction days; ATC 14:45 bar close == F1M daily close on 99.9% of auction days (non-roll 99.9%); identity on_1429 = a + on_atc on non-roll nights, max residual 2.70e-16. Index 14:45 close == daily index close on 100.0% of window nights; index 14:25 filled on 0 days. Futures 09:00 forward-fills {'09:00': 0, '09:15': 1, '09:30': 0, '10:00': 1}. Cap 2026-11-17: last night 2026-11-17, last auction day 2026-11-16.

## A. Auction leg a = ln C(14:45) - ln C(14:29)
                                         sample   n  mean_bp      t  se_bp  mde80_bp
          all nights (full intraday sample, P1) 786   -0.851 -1.003  0.849     2.377
                         ex expiry-day auctions 752   -0.866 -0.988  0.877     2.456
expiry-day auctions only (E = expiry, T = roll)  34   -0.531 -1.427  0.372     1.043
                                      year 2023  71   -2.718 -0.742  3.664    10.264
                                      year 2024 250   -0.387 -0.356  1.088     3.049
                                      year 2025 249   -1.849 -0.959  1.928     5.401
                                      year 2026 216    0.375  0.323  1.160     3.251

By weekday (auction day; Bonferroni |t| > 2.576), all nights:
             night   n  mean_bp  mean_t  minus_others_bp  minus_others_t
          Mon->Tue 157   -0.144  -0.075            0.917           0.385
          Tue->Wed 157    2.239   1.145            3.896           1.798
          Wed->Thu 155    3.675   2.126            5.692           2.671
          Thu->Fri 155   -6.038  -2.098           -6.449          -2.076
Fri->Mon (weekend) 147   -4.123  -2.171           -4.056          -1.838
Joint Wald chi2(4) all equal: 15.27, p 0.004

By weekday, ex expiry-day auctions:
             night   n  mean_bp  mean_t  minus_others_bp  minus_others_t
          Mon->Tue 157   -0.144  -0.074            1.285           0.523
          Tue->Wed 157    2.239   1.150            4.264           1.918
          Wed->Thu 155    3.675   2.130            6.060           2.746
          Thu->Fri 123   -7.509  -2.074           -7.920          -2.073
Fri->Mon (weekend) 147   -4.123  -2.210           -3.688          -1.634

## B. Offset: on_atc = c + b*a (NW SEs)
                      sample   n  intercept_bp  intercept_t  slope  slope_se  slope_t  pearson_r    r2
non-roll nights (P2 primary) 747         5.490        3.351  0.203     0.178    1.143      0.096 0.009
                  all nights 781         5.687        3.580  0.203     0.178    1.141      0.095 0.009

Decomposition on non-roll nights: on_1429 = a + on_atc (bp; share_a = a / on_1429)
             night   n  on_1429_bp  t_on_1429   a_bp    t_a  on_atc_bp  t_on_atc  share_a
    all (non-roll) 747       4.427      2.366 -0.866 -0.988      5.402     3.304   -0.196
          Mon->Tue 156      11.959      2.486 -0.144 -0.064     12.092     3.042   -0.012
          Tue->Wed 156      14.351      2.061  2.239  1.145     12.149     1.827    0.156
          Wed->Thu 155       8.561      1.562  3.675  2.316      4.886     1.088    0.429
          Thu->Fri 123      -8.207     -1.930 -7.509 -2.601     -0.699    -0.210    0.915
Fri->Mon (weekend) 145      -6.294     -0.967 -4.123 -2.397     -1.570    -0.257    0.655

## C. Matched auction legs, index-intraday window (2025-11-25 .. 2026-11-17, n 243)
POWER LIMIT (stated before the numbers): n ~ 243, Wed n 47. MDE80 = 2.80 x NW SE; cells with MDE80 > 10 bp are POWER-LIMITED.
             night                                            leg   n  mean_bp      t  se_bp  mde80_bp  power_limited
               all                          futures auction leg a 243   -1.013 -0.601  1.686     4.722          False
               all index auction leg (14:25 close -> 14:45 close) 243   -5.075 -3.479  1.459     4.087          False
               all                                futures - index 243    4.062  2.887  1.407     3.942          False
          Mon->Tue                          futures auction leg a  49    6.754  2.191  3.082     8.636          False
          Mon->Tue index auction leg (14:25 close -> 14:45 close)  49   -1.138 -0.418  2.722     7.627          False
          Mon->Tue                                futures - index  49    7.892  4.022  1.962     5.498          False
          Tue->Wed                          futures auction leg a  49    2.073  1.475  1.405     3.937          False
          Tue->Wed index auction leg (14:25 close -> 14:45 close)  49   -0.103 -0.061  1.685     4.720          False
          Tue->Wed                                futures - index  49    2.176  1.445  1.506     4.219          False
          Wed->Thu                          futures auction leg a  47    2.269  0.697  3.257     9.125          False
          Wed->Thu index auction leg (14:25 close -> 14:45 close)  47   -6.027 -2.751  2.191     6.138          False
          Wed->Thu                                futures - index  47    8.297  2.782  2.983     8.356          False
          Thu->Fri                          futures auction leg a  48  -13.819 -2.085  6.628    18.570           True
          Thu->Fri index auction leg (14:25 close -> 14:45 close)  48  -13.025 -3.036  4.291    12.021           True
          Thu->Fri                                futures - index  48   -0.793 -0.220  3.608    10.108           True
Fri->Mon (weekend)                          futures auction leg a  45   -2.679 -0.826  3.241     9.081          False
Fri->Mon (weekend) index auction leg (14:25 close -> 14:45 close)  45   -7.113 -2.582  2.755     7.720          False
Fri->Mon (weekend)                                futures - index  45    4.435  1.802  2.461     6.896          False

Weekday minus-others on (futures - index) auction leg:
             night  n  mean_bp  mean_t  minus_others_bp  minus_others_t
          Mon->Tue 49    7.892   4.039            4.364           1.769
          Tue->Wed 49    2.176   1.250           -2.781          -1.234
          Wed->Thu 47    8.297   3.518            4.869           1.842
          Thu->Fri 48   -0.793  -0.214           -6.493          -1.737
Fri->Mon (weekend) 45    4.435   1.516            0.042           0.015

## D. Competing hypothesis B: index open overshoot (window, n 244)
   night                                                   stat   n  mean_bp      t  mde80_bp  power_limited
     all                   index ON (prior close -> 09:15 open) 244   11.488  3.968     8.112          False
     all                        futures ON (prior ATC -> 09:00) 244    5.038  1.676     8.420          False
     all                               index drift 09:15->09:30 244   -6.263 -1.905     9.208          False
     all                             futures drift 09:15->09:30 244   -1.961 -1.186     4.631          False
     all index symmetric revert -sign(idxON)*drift 09:15->09:30 244    0.102  0.023    12.368           True
     all    futures counterpart -sign(idxON)*drift 09:15->09:30 244    4.155  2.550     4.564          False
     all                               index drift 09:15->10:00 244   -7.278 -1.929    10.573           True
     all                             futures drift 09:15->10:00 244   -1.840 -0.709     7.269          False
     all index symmetric revert -sign(idxON)*drift 09:15->10:00 244   -0.829 -0.179    12.970           True
     all    futures counterpart -sign(idxON)*drift 09:15->10:00 244    2.527  0.937     7.553          False
Wed->Thu                   index ON (prior close -> 09:15 open)  47    4.060  0.827    13.756           True
Wed->Thu                        futures ON (prior ATC -> 09:00)  47   -4.309 -0.556    21.727           True
Wed->Thu                               index drift 09:15->09:30  47   -0.310 -0.073    11.865           True
Wed->Thu                             futures drift 09:15->09:30  47    2.092  0.903     6.491          False
Wed->Thu index symmetric revert -sign(idxON)*drift 09:15->09:30  47    6.386  1.945     9.198          False
Wed->Thu    futures counterpart -sign(idxON)*drift 09:15->09:30  47    6.907  3.052     6.341          False
Wed->Thu                               index drift 09:15->10:00  47   -5.439 -1.126    13.534           True
Wed->Thu                             futures drift 09:15->10:00  47   -2.586 -0.713    10.168           True
Wed->Thu index symmetric revert -sign(idxON)*drift 09:15->10:00  47    8.746  1.596    15.355           True
Wed->Thu    futures counterpart -sign(idxON)*drift 09:15->10:00  47    8.372  1.835    12.781           True

Slope of post-open drift on index ON (NW):
                         y      x   n  slope  slope_t  intercept_bp  intercept_t
  index drift 09:15->09:30 idx_ON 244  0.061    0.744        -6.962       -1.848
futures drift 09:15->09:30 idx_ON 244 -0.084   -2.646        -0.995       -0.634
  index drift 09:15->10:00 idx_ON 244  0.085    1.075        -8.251       -2.019
futures drift 09:15->10:00 idx_ON 244 -0.057   -1.107        -1.184       -0.440

## VERDICTS (pre-registered rule)
- P1 DOES NOT HOLD: mean(a) = -0.85 bp, NW t -1.00, n 786; 95% CI -2.51 .. 0.81 bp (MDE80 2.4 bp). The null is tight: the futures auction adds at most ~1 bp per night on average, against a ~10 bp futures-vs-index ON gap, so rejecting P1 is not a power problem.
- P2 DOES NOT HOLD: slope of on_atc on a = 0.203 (NW t 1.14), Pearson r 0.096, n 747 non-roll nights.
- P3 HOLDS AS PRE-REGISTERED: Wed auction minus other four = 5.69 bp (t 2.67; threshold >= 5 bp and t > 2.576). CAVEAT: the request said 'order ~10 bp'; the pre-registration operationalised that as >= 5 bp. Under a >= 10 bp reading P3 FAILS. Either way the verdict is unchanged because P1 fails.
- **H REJECTED; B reported as the better-supported account (by the pre-registered rule).**
- B independent corroboration (index rev 09:15->10:00 > 0 with t > 2 AND futures counterpart |t| < 2): NO (index -0.83 bp t -0.18; futures 2.53 bp t 0.94; window n 244, MDE80 13.0 bp).
- READING. The rule labels B 'better supported' because H's two conditions both fail (mean a ~ 0, slope ~ 0). The pre-registered corroboration check (SYMMETRIC, gap-proportional reversion) is NO: there is no symmetric reversion of the index open. At the MEAN level D points in B's direction, but only borderline and power-limited: by 10:00 the index gives back -7.28 bp (t -1.93, MDE80 10.6 bp) while futures move -1.84 bp (t -0.71). Combined with the POST HOC index closing-auction dip below, everything that moves is on the INDEX side (its close dips, its open is high, and it drifts down after the open), while futures are flat at all three points (post hoc reading; one-year window). P3 held on its own (Wed auction minus others 5.69 bp, t 2.67), but the pooled auction leg is ~0 because Thu/Fri auctions are negative; under the rule P3 cannot rescue H without P1.
- STEP 2 '5.0 bp quick cut': not reproduced exactly by any cut above. The nearest are keeping the 4 misaligned Thu-close -> Mon-open nights (4.81 bp) and the naive consecutive-day pairing with no roll fix (4.59 bp); the gate set reproduces 2.2a exactly.
- POWER-LIMITED cells (MDE80 > 10 bp): A: year 2023; C: Thu->Fri / futures auction leg a, Thu->Fri / index auction leg (14:25 close -> 14:45 close), Thu->Fri / futures - index; D: all / index symmetric revert -sign(idxON)*drift 09:15->09:30, all / index drift 09:15->10:00, all / index symmetric revert -sign(idxON)*drift 09:15->10:00, Wed->Thu / index ON (prior close -> 09:15 open), Wed->Thu / futures ON (prior ATC -> 09:00), Wed->Thu / index drift 09:15->09:30, Wed->Thu / index drift 09:15->10:00, Wed->Thu / futures drift 09:15->10:00, Wed->Thu / index symmetric revert -sign(idxON)*drift 09:15->10:00, Wed->Thu / futures counterpart -sign(idxON)*drift 09:15->10:00.

## POST HOC (not pre-registered; added after seeing section C; does not change the verdicts above)
The index (not the futures) moves in its closing auction: index leg 14:25 -> 14:45 is negative while the futures leg is ~0. Measured from pre-auction clocks (index 14:25 close, futures 14:29 close), the index-minus-futures ON gap shrinks from the closing-print value to the row below (compare on the same non-roll nights; by construction the difference is test C's futures-minus-index auction leg). That is a MEAN-LEVEL statement: on average, the index's own closing auction lowers the index close relative to the futures close, and that accounts for much of the measured ON gap in this window.
It is NOT a night-by-night recovery of the index: the slope of index ON on the index auction leg is POSITIVE (a bigger auction dip goes with a LOWER next index ON, i.e. continuation). The BASIS does revert night by night (the overnight shortfall rises with the futures-minus-index auction leg).
                                                                  stat   n  mean_bp     t  mde80_bp  power_limited
                                   index ON from 14:45 close (= daily) 243   11.491 3.952     8.146          False
                               index ON from 14:25 close (pre-auction) 243    6.415 1.849     9.722          False
                                             futures ON from 14:45 ATC 243    4.980 1.652     8.448          False
                                futures ON from 14:29 close (non-roll) 232    3.424 0.933    10.275           True
                index - futures ON, closing prints (all window nights) 243    6.511 2.770     6.585          False
index - futures ON, closing prints (non-roll, same nights as next row) 232    6.508 2.697     6.761          False
                     index - futures ON, pre-auction clocks (non-roll) 232    1.863 0.816     6.401          False
                  difference = (futures - index) auction leg, non-roll 232    4.644 3.348     3.886          False
OLS index ON on index auction leg: slope 0.421 (NW t 2.96), n 243. OLS overnight basis shortfall (-dbasis_ON) on (futures - index) auction leg: slope 0.542 (NW t 2.56), n 243.
One year only (window); exploratory; would need its own pre-registered test on a longer index-intraday history.

Provenance: src/atc_drift_test.py on data/raw_intraday/VCI_VN30F1M_1m.csv + VCI_VN30_5m.csv (backup data/snapshots/raw_intraday_20261127T014311Z.tar.gz), frozen daily futures (data/snapshots/frozen_20261117) + data/raw/VN30.csv; cap 2026-11-17; n 787 nights (2023-09-11..2026-11-17), window n 243. Protected files (data/raw, frozen, raw_intraday, track_forward.py, boundary; 78 files) hash-identical before/after.
