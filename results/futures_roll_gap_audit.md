# VN30F1M roll-gap audit, repair and impact (measurement only)

## Step 0: missing days
Calendar = union of VN30 and VNINDEX daily dates. In the VN30F1M range there are 2316 calendar trading days; VN30F1M.csv has 2301 (missing 15; VN30F1M days not in the calendar: 0). Post-expiry days checked: 111 (expiry = 3rd Thursday, or the last trading day before it).

Missing post-expiry days (all are trading days in both index files):
  month     expiry post_expiry_day  F2M_has_bar                        usable_F2M_as_substitute front_contract  contract_has_bar  in_VN30  in_VNINDEX
2022-11 2022-11-17      2022-11-18         True yes (F2M on this day IS the new front contract)      VN30F2212              True     True        True
2022-12 2022-12-15      2022-12-16         True yes (F2M on this day IS the new front contract)      VN30F2301              True     True        True
2023-01 2023-01-19      2023-01-27        False                                 no (no F2M bar)      VN30F2302              True     True        True
2023-02 2023-02-16      2023-02-17         True yes (F2M on this day IS the new front contract)      VN30F2303              True     True        True
2023-03 2023-03-16      2023-03-17         True yes (F2M on this day IS the new front contract)      VN30F2304              True     True        True
2023-04 2023-04-20      2023-04-21         True yes (F2M on this day IS the new front contract)      VN30F2305              True     True        True
2023-05 2023-05-18      2023-05-19         True yes (F2M on this day IS the new front contract)      VN30F2306              True     True        True
2023-06 2023-06-15      2023-06-16         True yes (F2M on this day IS the new front contract)      VN30F2307              True     True        True
2023-07 2023-07-20      2023-07-21         True yes (F2M on this day IS the new front contract)      VN30F2308              True     True        True
2023-08 2023-08-17      2023-08-18         True yes (F2M on this day IS the new front contract)      VN30F2309              True     True        True
2023-09 2023-09-21      2023-09-22         True yes (F2M on this day IS the new front contract)      VN30F2310              True     True        True
2023-10 2023-10-19      2023-10-20         True yes (F2M on this day IS the new front contract)      VN30F2311              True     True        True
2023-11 2023-11-16      2023-11-17         True yes (F2M on this day IS the new front contract)      VN30F2312              True     True        True
2023-12 2023-12-21      2023-12-22         True yes (F2M on this day IS the new front contract)      VN30F2401              True     True        True

Other missing calendar days (not post-expiry): 2021-04-29 (VN30 bar: yes; VN30F2M bar: no; front contract VN30F2105 not served by VCI).

### Count reconciliation
Index nights from 2018-11-21: 1993. Decomposition sample: 1962. Dropped = 15 nights with no futures bar (2021-04-29, 2022-11-18, 2022-12-16, 2023-01-27, 2023-02-17, 2023-03-17, 2023-04-21, 2023-05-19, 2023-06-16, 2023-07-21, 2023-08-18, 2023-09-22, 2023-10-20, 2023-11-17, 2023-12-22) + 16 misaligned nights (2018-11-21, 2021-05-04, 2022-11-21, 2022-12-19, 2023-01-30, 2023-02-20, 2023-03-20, 2023-04-24, 2023-05-22, 2023-06-19, 2023-07-24, 2023-08-21, 2023-09-25, 2023-10-23, 2023-11-20, 2023-12-25).
- 2023: 12 no-bar + 12 misaligned = 24 index nights (the '24'); 2022: 2 + 2.
- The '16' is the full-sample count of misaligned nights: 14 nights after a missing roll day, 2021-05-04 (after missing 2021-04-29) and 2018-11-21.
- 2018-11-21 is NOT a data gap: VN30.csv starts 2018-11-20 and both series start that night from 2018-11-20. futures_basis_decomp.index_nights() computed prev_date AFTER decompose() dropped the first row, so the first index night lost its prior date (code bug, fixed below as a logged change).
- Correct count of nights affected by DATA gaps: 15 missing futures days -> 15 index nights without a futures bar + 15 contaminated futures nights (14 post-roll + 2021-05-04) = 30.

## Step 1: contract identity on the PRESENT post-expiry days
                                                          test   value                              note
n present post-expiry days with F1M, F2M and VN30 on T and T-1  81.000                                  
 (a) F2M(T)-F1M(T) close spread on roll day T, median bp [IQR]  -3.390                      [-21.2, 9.8]
            (a) same spread on all other days, median bp [IQR] -10.204                      [-29.3, 8.7]
       (b) |ln F1M_open(T)/F2M_close(T-1) - idx ON|, median bp  22.582       F2M(T-1) as the prior close
       (b) |ln F1M_open(T)/F1M_close(T-1) - idx ON|, median bp  46.822      F1M(T-1) = expiring contract
              (b) ordinary nights |fut ON - idx ON|, median bp  18.619                         reference
                   (c) F2M volume(T) / F2M volume(T-1), median   0.013                share < 0.2: 1.000
                   (c) F1M volume(T) / F2M volume(T-1), median   5.434                                  
                  (d) |F2M(T)/F2M(T-1) cc - idx cc|, median bp  31.405 if F2M were one contract across T
                  (d) |F1M(T)/F2M(T-1) cc - idx cc|, median bp  26.121         new front month = old F2M

Reading: on present roll days VN30F2M's volume collapses to ~1% of the prior day (all days < 20%) and F1M(T) opens in line with F2M(T-1), not F1M(T-1). The vendor relabels at expiry: on T, VN30F1M is the old F2M contract and VN30F2M is the next-out contract. The calendar spread is small (median ~-10 bp), so spread levels alone do not identify the contract; volume does.
On the 14 MISSING days the relabel failed differently: VN30F2M's OHLCV on 13 of them is IDENTICAL to the new front contract (from its own ticker), i.e. on those days the vendor's F2M series already carried the new front month and the F1M series carried the expired contract (no bar).

## Step 1: candidate sources
Fetch results (this session):
source    symbol                                                                 status
   KBS   VN30F1M             ok: 149 rows 2026-04-17..2026-11-23 (no contract identity)
   KBS   VN30F2M                                      ok: 2 rows 2026-11-20..2026-11-23
   KBS VN30F2212                                      error (ValueError via RetryError)
   KBS VN30F2302                                                                  error
   KBS VN30F2512                                                                  error
   KBS VN30F2601                                                                  error
   MSN   VN30F1M                                                error (ConnectionError)
   VCI VN30F2601                          error (post-May-2025 contracts use KRX codes)
   VCI 41I1G1000 ok: 38 rows 2025-11-21..2026-01-15 (KRX code of the Jan-2026 contract)
VCI contract tickers VN30Fyymm: served for 2207..2512 (38 contracts); contracts expiring before 2022-07 (and 2206) and the post-May-2025 contracts 2507/2508/2510/2511 under the old naming are not served (error).

Validation against VCI VN30F1M on days where VCI is present (price tolerance 0.05 pt):
                                               source                          subset   n      first       last  open_match  high_match  low_match  close_match  volume_exact  volume_within_1pct
          VCI contract tickers (stitched front month)                     all overlap 773 2022-06-20 2025-12-18       0.930       0.929      0.918        1.000         0.899               0.996
          VCI contract tickers (stitched front month)                            2022 136 2022-06-20 2022-12-30       0.610       0.603      0.537        1.000         0.434               0.978
          VCI contract tickers (stitched front month)                     2023 onward 637 2023-01-03 2025-12-18       0.998       0.998      1.000        1.000         0.998               1.000
          VCI contract tickers (stitched front month) present post-expiry (roll) days  23 2022-07-22 2025-11-21       0.913       0.957      0.870        1.000         0.826               1.000
                                    KBS VN30F1M daily                     all overlap 145 2026-04-17 2026-11-17       0.062       0.000      0.055        0.014         0.000               0.000
                                    KBS VN30F1M daily                     2023 onward 145 2026-04-17 2026-11-17       0.062       0.000      0.055        0.014         0.000               0.000
                                    KBS VN30F1M daily present post-expiry (roll) days   7 2026-04-17 2026-10-16       0.000       0.000      0.143        0.000         0.000               0.000
VCI KRX code 41I1G1000 (Jan-2026) in its front window                     all overlap  18 2025-12-19 2026-01-15       1.000       1.000      1.000        1.000         1.000               1.000
VCI KRX code 41I1G1000 (Jan-2026) in its front window                     2023 onward  18 2025-12-19 2026-01-15       1.000       1.000      1.000        1.000         1.000               1.000
VCI KRX code 41I1G1000 (Jan-2026) in its front window present post-expiry (roll) days   1 2025-12-19 2025-12-19       1.000       1.000      1.000        1.000         1.000               1.000

Decision rule (close match >= 99%): VCI contract tickers close match 100.00% -> USABLE. Open/high/low/volume mismatches are concentrated in 2022 (small differences in O/H/L, volume differing by a few hundred contracts); from 2023 every field matches 100%. KBS daily starts 2026-04-17 (no history for the gaps) and fails validation anyway: its 'VN30F1M' (auto-converted to KRX code 41I1GC000) trades ~20 contracts/day vs ~250,000 in VCI VN30F1M (median volume ratio 0.0003), i.e. it is an illiquid non-front contract. The KRX code works only for contracts listed after May 2025; MSN failed. None of these candidates exposes contract identity except the contract tickers themselves.
2023-01-27: VN30F2M absent; recovered from VN30F2302 only (2023 match rate 100%, no second source). 2021-04-29: no source (VN30F2105 not served, no F2M bar, KBS history too short) -> NOT filled; the 2021-05-04 futures night is excluded explicitly.

Values on the missing days, contract ticker vs VN30F2M:
post_expiry_day front_contract   c_open  c_close   c_volume  f2m_open  f2m_close  f2m_volume  F2M_equals_contract_OHLCV
     2022-11-18      VN30F2212  960.100  963.000 525965.000   960.100    963.000  525965.000                       True
     2022-12-16      VN30F2301 1050.000 1060.000 298058.000  1050.000   1060.000  298058.000                       True
     2023-01-27      VN30F2302 1138.900 1127.000 178930.000       NaN        NaN         NaN                      False
     2023-02-17      VN30F2303 1051.000 1049.000 294696.000  1051.000   1049.000  294696.000                       True
     2023-03-17      VN30F2304 1056.200 1045.100 298289.000  1056.200   1045.100  298289.000                       True
     2023-04-21      VN30F2305 1047.800 1040.000 162134.000  1047.800   1040.000  162134.000                       True
     2023-05-19      VN30F2306 1064.900 1062.500 230092.000  1064.900   1062.500  230092.000                       True
     2023-06-16      VN30F2307 1104.200 1102.600 245434.000  1104.200   1102.600  245434.000                       True
     2023-07-21      VN30F2308 1164.900 1184.900 136587.000  1164.900   1184.900  136587.000                       True
     2023-08-18      VN30F2309 1234.300 1188.000 284171.000  1234.300   1188.000  284171.000                       True
     2023-09-22      VN30F2310 1200.700 1192.600 325672.000  1200.700   1192.600  325672.000                       True
     2023-10-20      VN30F2311 1100.800 1117.000 265883.000  1100.800   1117.000  265883.000                       True
     2023-11-17      VN30F2312 1142.000 1105.000 359199.000  1142.000   1105.000  359199.000                       True
     2023-12-22      VN30F2401 1099.900 1097.700 170928.000  1099.900   1097.700  170928.000                       True

## Step 2: repair
Written: data/raw/VN30F1M_repaired.csv (2315 rows = 2301 original + 14 inserted; column `source`). Inserted-row log: results/futures_roll_gap_inserted_rows.csv. VN30F1M.csv untouched. open_suspicious recomputed with fetch_indices' rule on the repaired series; flags that changed on ORIGINAL rows: none.
Reproduction check (original file, original code path level_c_futures.build): all-nights gross 4.99 bp (target 4.99). Replicas used for the repaired file reproduce the originals exactly on the original file: {'build': np.True_, 'futures_nights': np.True_, 'panel': np.True_}.

## Step 3: impact
### Gross-shift reconciliation (0.50 vs 0.46)
15 contaminated nights: n = 15, sum of simple returns = -1061.3 bp, mean = -70.8 bp. All invested nights N = 2284, mean 4.990 bp. Without them: n = 2269, mean 5.491 bp. Shift = 0.501 bp = (mean_all - mean_15) x 15/(N-15). The earlier 0.46 was sum_15 / N = -0.465 bp, the 15 nights' contribution to the all-nights mean, not the change from removing them (removing also shrinks the denominator). The correct shift from excluding them is 0.50 bp.
Contaminated nights excluded in the 'excluded' variant: 2022-11-21, 2022-12-19, 2023-01-30, 2023-02-20, 2023-03-20, 2023-04-24, 2023-05-22, 2023-06-19, 2023-07-24, 2023-08-21, 2023-09-25, 2023-10-23, 2023-11-20, 2023-12-25, 2021-05-04.

### Before / after (flag = |repaired - before| > 0.5 x SE(before); SE for Sharpe from the Lo formula, for t-stats SE = 1)
                                                                                   metric  before (as reported)  2018-11-21 fix only  original, contaminated nights excluded + fix  repaired file + fix (2021-05-04 excluded)  delta_after_minus_before  moves_gt_half_se
                                                                           all nights | n              2284.000             2284.000                                      2269.000                                   2297.000                    13.000             False
                                                               all nights | gross mean bp                 4.990                4.990                                         5.491                                      5.245                     0.255             False
                                                                all nights | gross Sharpe                 1.287                1.287                                         1.468                                      1.396                     0.110             False
                                                                     all nights | gross t                 3.873                3.873                                         4.404                                      4.216                     0.343             False
                                   all nights | net (12,500 VND + 1bp + 5bp roll) mean bp                 0.585                0.585                                         1.116                                      0.841                     0.256             False
                                    all nights | net (12,500 VND + 1bp + 5bp roll) Sharpe                 0.151                0.151                                         0.298                                      0.224                     0.073             False
                                         all nights | net (12,500 VND + 1bp + 5bp roll) t                 0.454                0.454                                         0.895                                      0.676                     0.222             False
                                          all nights | net 0.021%/side + 5bp roll mean bp                 0.582                0.582                                         1.112                                      0.839                     0.256             False
                                           all nights | net 0.021%/side + 5bp roll Sharpe                 0.150                0.150                                         0.297                                      0.223                     0.073             False
                                                all nights | net 0.021%/side + 5bp roll t                 0.452                0.452                                         0.892                                      0.674                     0.222             False
                                                                Monday full 2017-2026 | n               453.000              453.000                                       453.000                                    453.000                     0.000             False
                                                    Monday full 2017-2026 | gross mean bp                10.620               10.620                                        10.620                                     10.620                     0.000             False
                                                      Monday full 2017-2026 | net mean bp                 6.418                6.418                                         6.418                                      6.418                     0.000             False
                                                       Monday full 2017-2026 | net Sharpe                 0.912                0.912                                         0.912                                      0.912                     0.000             False
                                                            Monday full 2017-2026 | net t                 2.775                2.775                                         2.775                                      2.775                     0.000             False
                                                           Monday ex-2026 (2017-2025) | n               410.000              410.000                                       410.000                                    410.000                     0.000             False
                                               Monday ex-2026 (2017-2025) | gross mean bp                 9.461                9.461                                         9.461                                      9.461                     0.000             False
                                                 Monday ex-2026 (2017-2025) | net mean bp                 5.162                5.162                                         5.162                                      5.162                     0.000             False
                                                  Monday ex-2026 (2017-2025) | net Sharpe                 0.756                0.756                                         0.756                                      0.756                     0.000             False
                                                       Monday ex-2026 (2017-2025) | net t                 2.189                2.189                                         2.189                                      2.189                     0.000             False
                                                               Mon+Tue full 2017-2026 | n               910.000              910.000                                       910.000                                    910.000                     0.000             False
                                                   Mon+Tue full 2017-2026 | gross mean bp                 9.337                9.337                                         9.337                                      9.337                     0.000             False
                                                     Mon+Tue full 2017-2026 | net mean bp                 5.136                5.136                                         5.136                                      5.136                     0.000             False
                                                      Mon+Tue full 2017-2026 | net Sharpe                 0.950                0.950                                         0.950                                      0.950                     0.000             False
                                                           Mon+Tue full 2017-2026 | net t                 2.891                2.891                                         2.891                                      2.891                     0.000             False
                                                          Mon+Tue ex-2026 (2017-2025) | n               824.000              824.000                                       824.000                                    824.000                     0.000             False
                                              Mon+Tue ex-2026 (2017-2025) | gross mean bp                 7.715                7.715                                         7.715                                      7.715                     0.000             False
                                                Mon+Tue ex-2026 (2017-2025) | net mean bp                 3.418                3.418                                         3.418                                      3.418                     0.000             False
                                                 Mon+Tue ex-2026 (2017-2025) | net Sharpe                 0.658                0.658                                         0.658                                      0.658                     0.000             False
                                                      Mon+Tue ex-2026 (2017-2025) | net t                 1.907                1.907                                         1.907                                      1.907                     0.000             False
                                                                   decomposition sample N              1962.000             1963.000                                      1963.000                                   1991.000                    29.000             False
                                                2023 index ON in decomposition sample, bp                11.075               11.075                                        11.075                                      9.863                    -1.212              True
                           dbasis_ON pre 2022-08-25 | all days | Mon->Tue minus others bp                10.108               10.043                                        10.043                                     10.043                    -0.065             False
                            dbasis_ON pre 2022-08-25 | all days | Mon->Tue minus others t                 2.085                2.071                                         2.071                                      2.071                    -0.013             False
                                         dbasis_ON pre 2022-08-25 | all days | Mon->Tue n               184.000              184.000                                       184.000                                    184.000                     0.000             False
                           dbasis_ON pre 2022-08-25 | all days | Tue->Wed minus others bp                -3.820               -3.561                                        -3.561                                     -3.561                     0.259             False
                            dbasis_ON pre 2022-08-25 | all days | Tue->Wed minus others t                -0.953               -0.888                                        -0.888                                     -0.888                     0.064             False
                                         dbasis_ON pre 2022-08-25 | all days | Tue->Wed n               185.000              186.000                                       186.000                                    186.000                     1.000             False
                           dbasis_ON pre 2022-08-25 | all days | Wed->Thu minus others bp                -7.193               -7.258                                        -7.258                                     -7.258                    -0.065             False
                            dbasis_ON pre 2022-08-25 | all days | Wed->Thu minus others t                -1.845               -1.860                                        -1.860                                     -1.860                    -0.015             False
                                         dbasis_ON pre 2022-08-25 | all days | Wed->Thu n               183.000              183.000                                       183.000                                    183.000                     0.000             False
                           dbasis_ON pre 2022-08-25 | all days | Thu->Fri minus others bp                -0.403               -0.468                                        -0.468                                     -0.468                    -0.065             False
                            dbasis_ON pre 2022-08-25 | all days | Thu->Fri minus others t                -0.084               -0.098                                        -0.098                                     -0.098                    -0.014             False
                                         dbasis_ON pre 2022-08-25 | all days | Thu->Fri n               187.000              187.000                                       187.000                                    187.000                     0.000             False
                 dbasis_ON pre 2022-08-25 | all days | Fri->Mon (weekend) minus others bp                 1.308                1.243                                         1.243                                      1.243                    -0.065             False
                  dbasis_ON pre 2022-08-25 | all days | Fri->Mon (weekend) minus others t                 0.214                0.204                                         0.204                                      0.204                    -0.011             False
                               dbasis_ON pre 2022-08-25 | all days | Fri->Mon (weekend) n               179.000              179.000                                       179.000                                    179.000                     0.000             False
                                       dbasis_ON pre 2022-08-25 | all days | joint Wald p                 0.126                0.132                                         0.132                                      0.132                     0.005             False
                                      dbasis_ON pre 2022-08-25 | all days | grand mean bp                 4.728                4.777                                         4.777                                      4.777                     0.049             False
             dbasis_ON pre 2022-08-25 | ex roll & expiry-1..+1 | Mon->Tue minus others bp                11.187               11.101                                        11.101                                     11.101                    -0.086             False
              dbasis_ON pre 2022-08-25 | ex roll & expiry-1..+1 | Mon->Tue minus others t                 2.237                2.220                                         2.220                                      2.220                    -0.017             False
                           dbasis_ON pre 2022-08-25 | ex roll & expiry-1..+1 | Mon->Tue n               184.000              184.000                                       184.000                                    184.000                     0.000             False
             dbasis_ON pre 2022-08-25 | ex roll & expiry-1..+1 | Tue->Wed minus others bp                -3.854               -3.509                                        -3.509                                     -3.509                     0.345             False
              dbasis_ON pre 2022-08-25 | ex roll & expiry-1..+1 | Tue->Wed minus others t                -0.807               -0.735                                        -0.735                                     -0.735                     0.072             False
                           dbasis_ON pre 2022-08-25 | ex roll & expiry-1..+1 | Tue->Wed n               141.000              142.000                                       142.000                                    142.000                     1.000             False
             dbasis_ON pre 2022-08-25 | ex roll & expiry-1..+1 | Wed->Thu minus others bp                -5.519               -5.605                                        -5.605                                     -5.605                    -0.086             False
              dbasis_ON pre 2022-08-25 | ex roll & expiry-1..+1 | Wed->Thu minus others t                -1.187               -1.204                                        -1.204                                     -1.204                    -0.017             False
                           dbasis_ON pre 2022-08-25 | ex roll & expiry-1..+1 | Wed->Thu n               138.000              138.000                                       138.000                                    138.000                     0.000             False
             dbasis_ON pre 2022-08-25 | ex roll & expiry-1..+1 | Thu->Fri minus others bp                -4.201               -4.287                                        -4.287                                     -4.287                    -0.086             False
              dbasis_ON pre 2022-08-25 | ex roll & expiry-1..+1 | Thu->Fri minus others t                -0.837               -0.854                                        -0.854                                     -0.854                    -0.018             False
                           dbasis_ON pre 2022-08-25 | ex roll & expiry-1..+1 | Thu->Fri n               142.000              142.000                                       142.000                                    142.000                     0.000             False
   dbasis_ON pre 2022-08-25 | ex roll & expiry-1..+1 | Fri->Mon (weekend) minus others bp                 2.387                2.301                                         2.301                                      2.301                    -0.086             False
    dbasis_ON pre 2022-08-25 | ex roll & expiry-1..+1 | Fri->Mon (weekend) minus others t                 0.378                0.364                                         0.364                                      0.364                    -0.013             False
                 dbasis_ON pre 2022-08-25 | ex roll & expiry-1..+1 | Fri->Mon (weekend) n               179.000              179.000                                       179.000                                    179.000                     0.000             False
                         dbasis_ON pre 2022-08-25 | ex roll & expiry-1..+1 | joint Wald p                 0.150                0.157                                         0.157                                      0.157                     0.007             False
                        dbasis_ON pre 2022-08-25 | ex roll & expiry-1..+1 | grand mean bp                 4.465                4.522                                         4.522                                      4.522                     0.058             False
                          dbasis_ON post 2022-08-25 | all days | Mon->Tue minus others bp                 1.757                1.757                                         1.757                                      2.015                     0.258             False
                           dbasis_ON post 2022-08-25 | all days | Mon->Tue minus others t                 0.667                0.667                                         0.667                                      0.759                     0.092             False
                                        dbasis_ON post 2022-08-25 | all days | Mon->Tue n               207.000              207.000                                       207.000                                    207.000                     0.000             False
                          dbasis_ON post 2022-08-25 | all days | Tue->Wed minus others bp                 1.780                1.780                                         1.780                                      2.037                     0.258             False
                           dbasis_ON post 2022-08-25 | all days | Tue->Wed minus others t                 0.499                0.499                                         0.499                                      0.577                     0.079             False
                                        dbasis_ON post 2022-08-25 | all days | Tue->Wed n               209.000              209.000                                       209.000                                    209.000                     0.000             False
                          dbasis_ON post 2022-08-25 | all days | Wed->Thu minus others bp                -1.792               -1.792                                        -1.792                                     -1.535                     0.258             False
                           dbasis_ON post 2022-08-25 | all days | Wed->Thu minus others t                -0.652               -0.652                                        -0.652                                     -0.553                     0.099             False
                                        dbasis_ON post 2022-08-25 | all days | Wed->Thu n               207.000              207.000                                       207.000                                    207.000                     0.000             False
                          dbasis_ON post 2022-08-25 | all days | Thu->Fri minus others bp                 4.240                4.240                                         4.240                                      3.980                    -0.260             False
                           dbasis_ON post 2022-08-25 | all days | Thu->Fri minus others t                 1.827                1.827                                         1.827                                      1.711                    -0.116             False
                                        dbasis_ON post 2022-08-25 | all days | Thu->Fri n               197.000              197.000                                       197.000                                    210.000                    13.000             False
                dbasis_ON post 2022-08-25 | all days | Fri->Mon (weekend) minus others bp                -5.984               -5.984                                        -5.984                                     -6.497                    -0.513             False
                 dbasis_ON post 2022-08-25 | all days | Fri->Mon (weekend) minus others t                -1.580               -1.580                                        -1.580                                     -1.792                    -0.212             False
                              dbasis_ON post 2022-08-25 | all days | Fri->Mon (weekend) n               187.000              187.000                                       187.000                                    201.000                    14.000             False
                                      dbasis_ON post 2022-08-25 | all days | joint Wald p                 0.269                0.269                                         0.269                                      0.243                    -0.026             False
                                     dbasis_ON post 2022-08-25 | all days | grand mean bp                -5.319               -5.319                                        -5.319                                     -5.547                    -0.228             False
            dbasis_ON post 2022-08-25 | ex roll & expiry-1..+1 | Mon->Tue minus others bp                 1.680                1.680                                         1.680                                      1.834                     0.154             False
             dbasis_ON post 2022-08-25 | ex roll & expiry-1..+1 | Mon->Tue minus others t                 0.607                0.607                                         0.607                                      0.661                     0.054             False
                          dbasis_ON post 2022-08-25 | ex roll & expiry-1..+1 | Mon->Tue n               206.000              206.000                                       206.000                                    206.000                     0.000             False
            dbasis_ON post 2022-08-25 | ex roll & expiry-1..+1 | Tue->Wed minus others bp                -0.831               -0.831                                        -0.831                                     -0.677                     0.154             False
             dbasis_ON post 2022-08-25 | ex roll & expiry-1..+1 | Tue->Wed minus others t                -0.200               -0.200                                        -0.200                                     -0.163                     0.037             False
                          dbasis_ON post 2022-08-25 | ex roll & expiry-1..+1 | Tue->Wed n               160.000              160.000                                       160.000                                    160.000                     0.000             False
            dbasis_ON post 2022-08-25 | ex roll & expiry-1..+1 | Wed->Thu minus others bp                 0.102                0.102                                         0.102                                      0.256                     0.154             False
             dbasis_ON post 2022-08-25 | ex roll & expiry-1..+1 | Wed->Thu minus others t                 0.032                0.032                                         0.032                                      0.081                     0.048             False
                          dbasis_ON post 2022-08-25 | ex roll & expiry-1..+1 | Wed->Thu n               159.000              159.000                                       159.000                                    159.000                     0.000             False
            dbasis_ON post 2022-08-25 | ex roll & expiry-1..+1 | Thu->Fri minus others bp                 5.177                5.177                                         5.177                                      5.331                     0.154             False
             dbasis_ON post 2022-08-25 | ex roll & expiry-1..+1 | Thu->Fri minus others t                 2.148                2.148                                         2.148                                      2.216                     0.068             False
                          dbasis_ON post 2022-08-25 | ex roll & expiry-1..+1 | Thu->Fri n               162.000              162.000                                       162.000                                    162.000                     0.000             False
  dbasis_ON post 2022-08-25 | ex roll & expiry-1..+1 | Fri->Mon (weekend) minus others bp                -6.127               -6.127                                        -6.127                                     -6.743                    -0.616             False
   dbasis_ON post 2022-08-25 | ex roll & expiry-1..+1 | Fri->Mon (weekend) minus others t                -1.569               -1.569                                        -1.569                                     -1.807                    -0.238             False
                dbasis_ON post 2022-08-25 | ex roll & expiry-1..+1 | Fri->Mon (weekend) n               187.000              187.000                                       187.000                                    201.000                    14.000             False
                        dbasis_ON post 2022-08-25 | ex roll & expiry-1..+1 | joint Wald p                 0.195                0.195                                         0.195                                      0.133                    -0.063             False
                       dbasis_ON post 2022-08-25 | ex roll & expiry-1..+1 | grand mean bp                -5.341               -5.341                                        -5.341                                     -5.556                    -0.216             False
                        dbasis_ON 2023-01-01 onward | all days | Mon->Tue minus others bp                 1.948                1.948                                         1.948                                      2.108                     0.160             False
                         dbasis_ON 2023-01-01 onward | all days | Mon->Tue minus others t                 0.739                0.739                                         0.739                                      0.802                     0.064             False
                                      dbasis_ON 2023-01-01 onward | all days | Mon->Tue n               189.000              189.000                                       189.000                                    189.000                     0.000             False
                        dbasis_ON 2023-01-01 onward | all days | Tue->Wed minus others bp                 1.508                1.508                                         1.508                                      1.668                     0.160             False
                         dbasis_ON 2023-01-01 onward | all days | Tue->Wed minus others t                 0.420                0.420                                         0.420                                      0.469                     0.049             False
                                      dbasis_ON 2023-01-01 onward | all days | Tue->Wed n               191.000              191.000                                       191.000                                    191.000                     0.000             False
                        dbasis_ON 2023-01-01 onward | all days | Wed->Thu minus others bp                -1.094               -1.094                                        -1.094                                     -0.934                     0.160             False
                         dbasis_ON 2023-01-01 onward | all days | Wed->Thu minus others t                -0.408               -0.408                                        -0.408                                     -0.350                     0.058             False
                                      dbasis_ON 2023-01-01 onward | all days | Wed->Thu n               189.000              189.000                                       189.000                                    189.000                     0.000             False
                        dbasis_ON 2023-01-01 onward | all days | Thu->Fri minus others bp                 4.054                4.054                                         4.054                                      4.542                     0.488             False
                         dbasis_ON 2023-01-01 onward | all days | Thu->Fri minus others t                 1.771                1.771                                         1.771                                      2.050                     0.279             False
                                      dbasis_ON 2023-01-01 onward | all days | Thu->Fri n               181.000              181.000                                       181.000                                    192.000                    11.000             False
              dbasis_ON 2023-01-01 onward | all days | Fri->Mon (weekend) minus others bp                -6.416               -6.416                                        -6.416                                     -7.385                    -0.969             False
               dbasis_ON 2023-01-01 onward | all days | Fri->Mon (weekend) minus others t                -1.681               -1.681                                        -1.681                                     -2.007                    -0.326             False
                            dbasis_ON 2023-01-01 onward | all days | Fri->Mon (weekend) n               172.000              172.000                                       172.000                                    184.000                    12.000             False
                                    dbasis_ON 2023-01-01 onward | all days | joint Wald p                 0.250                0.250                                         0.250                                      0.126                    -0.124             False
                                   dbasis_ON 2023-01-01 onward | all days | grand mean bp                -6.176               -6.176                                        -6.176                                     -6.328                    -0.152             False
          dbasis_ON 2023-01-01 onward | ex roll & expiry-1..+1 | Mon->Tue minus others bp                 1.880                1.880                                         1.880                                      2.106                     0.226             False
           dbasis_ON 2023-01-01 onward | ex roll & expiry-1..+1 | Mon->Tue minus others t                 0.689                0.689                                         0.689                                      0.773                     0.084             False
                        dbasis_ON 2023-01-01 onward | ex roll & expiry-1..+1 | Mon->Tue n               188.000              188.000                                       188.000                                    188.000                     0.000             False
          dbasis_ON 2023-01-01 onward | ex roll & expiry-1..+1 | Tue->Wed minus others bp                -0.077               -0.077                                        -0.077                                      0.149                     0.226             False
           dbasis_ON 2023-01-01 onward | ex roll & expiry-1..+1 | Tue->Wed minus others t                -0.018               -0.018                                        -0.018                                      0.035                     0.052             False
                        dbasis_ON 2023-01-01 onward | ex roll & expiry-1..+1 | Tue->Wed n               146.000              146.000                                       146.000                                    146.000                     0.000             False
          dbasis_ON 2023-01-01 onward | ex roll & expiry-1..+1 | Wed->Thu minus others bp                 0.050                0.050                                         0.050                                      0.275                     0.226             False
           dbasis_ON 2023-01-01 onward | ex roll & expiry-1..+1 | Wed->Thu minus others t                 0.016                0.016                                         0.016                                      0.089                     0.073             False
                        dbasis_ON 2023-01-01 onward | ex roll & expiry-1..+1 | Wed->Thu n               145.000              145.000                                       145.000                                    145.000                     0.000             False
          dbasis_ON 2023-01-01 onward | ex roll & expiry-1..+1 | Thu->Fri minus others bp                 4.698                4.698                                         4.698                                      4.924                     0.226             False
           dbasis_ON 2023-01-01 onward | ex roll & expiry-1..+1 | Thu->Fri minus others t                 2.028                2.028                                         2.028                                      2.134                     0.106             False
                        dbasis_ON 2023-01-01 onward | ex roll & expiry-1..+1 | Thu->Fri n               148.000              148.000                                       148.000                                    148.000                     0.000             False
dbasis_ON 2023-01-01 onward | ex roll & expiry-1..+1 | Fri->Mon (weekend) minus others bp                -6.551               -6.551                                        -6.551                                     -7.455                    -0.903             False
 dbasis_ON 2023-01-01 onward | ex roll & expiry-1..+1 | Fri->Mon (weekend) minus others t                -1.644               -1.644                                        -1.644                                     -1.944                    -0.300             False
              dbasis_ON 2023-01-01 onward | ex roll & expiry-1..+1 | Fri->Mon (weekend) n               172.000              172.000                                       172.000                                    184.000                    12.000             False
                      dbasis_ON 2023-01-01 onward | ex roll & expiry-1..+1 | joint Wald p                 0.208                0.208                                         0.208                                      0.121                    -0.086             False
                     dbasis_ON 2023-01-01 onward | ex roll & expiry-1..+1 | grand mean bp                -6.220               -6.220                                        -6.220                                     -6.501                    -0.281             False
                                                                       offset 2022 | a bp                 2.781                2.781                                         2.781                                      2.260                    -0.521             False
                                                                        offset 2022 | a t                 1.132                1.132                                         1.132                                      0.889                    -0.243             False
                                                                          offset 2022 | k                 0.705                0.705                                         0.705                                      0.714                     0.009             False
                                                                          offset 2022 | n               245.000              245.000                                       245.000                                    249.000                     4.000             False
                                                                       offset 2023 | a bp                 1.190                1.190                                         1.190                                     -0.711                    -1.902              True
                                                                        offset 2023 | a t                 0.587                0.587                                         0.587                                     -0.326                    -0.912              True
                                                                          offset 2023 | k                 0.765                0.765                                         0.765                                      0.867                     0.102              True
                                                                          offset 2023 | n               225.000              225.000                                       225.000                                    249.000                    24.000             False
                                                                       offset 2024 | a bp                -3.678               -3.678                                        -3.678                                     -3.678                     0.000             False
                                                                        offset 2024 | a t                -2.588               -2.588                                        -2.588                                     -2.588                     0.000             False
                                                                          offset 2024 | k                 0.836                0.836                                         0.836                                      0.836                     0.000             False
                                                                          offset 2024 | n               250.000              250.000                                       250.000                                    250.000                     0.000             False
                                                                       offset 2025 | a bp                -6.681               -6.681                                        -6.681                                     -6.681                     0.000             False
                                                                        offset 2025 | a t                -1.729               -1.729                                        -1.729                                     -1.729                     0.000             False
                                                                          offset 2025 | k                 0.783                0.783                                         0.783                                      0.783                     0.000             False
                                                                          offset 2025 | n               249.000              249.000                                       249.000                                    249.000                     0.000             False
                                                                       offset 2026 | a bp                -6.403               -6.403                                        -6.403                                     -6.403                     0.000             False
                                                                        offset 2026 | a t                -2.634               -2.634                                        -2.634                                     -2.634                     0.000             False
                                                                          offset 2026 | k                 0.991                0.991                                         0.991                                      0.991                     0.000             False
                                                                          offset 2026 | n               216.000              216.000                                       216.000                                    216.000                     0.000             False
                                                     offset post 2022-08-25 pooled | a bp                -3.216               -3.216                                        -3.216                                     -3.556                    -0.340             False
                                                      offset post 2022-08-25 pooled | a t                -2.404               -2.404                                        -2.404                                     -2.731                    -0.327             False
                                                        offset post 2022-08-25 pooled | k                 0.820                0.820                                         0.820                                      0.834                     0.014             False
                                                        offset post 2022-08-25 pooled | n              1026.000             1026.000                                      1026.000                                   1054.000                    28.000             False

## 2018-11-21 bug fix (logged)
grep: index_nights() is defined only in futures_basis_decomp.py and called by futures_basis_decomp.py and futures_basis_followup.py (not by level_c_phase2.py or track_forward.py, which do not use the index). The same first-row pattern (`decompose()` then `date.diff()`/`shift(1)`, so the first remaining night has no gap and fails a gap == 1 filter) exists in level_b_dayofweek.py, pit_dayofweek_2x2.py, pit_residual_split.py, open_filter_audit.py (one_day filter) and composition_diagnostic.py: each drops the first night of each series. In pit_residual_split.py the index series is cut at 2018-11-21, so the same night is lost there. These scripts were NOT changed.
Fixed outputs written next to the old ones as results/<name>_fix20181121.csv; decomposition N 1,962 -> 1,963. Changed cells at 2-decimal precision: 356 (full list: results/futures_roll_gap_fix20181121_changes.csv). The intraday tables (2023-09 onward) cannot change.

                                file  n_changed
                futures_basis_expiry         36
       futures_basis_followup_offset         10
    futures_basis_followup_reconcile          1
futures_basis_followup_weekday_tests        143
            futures_basis_robustness         80
               futures_basis_weekday         36
                  futures_basis_year         50

Changed cells in headline tables (year 'all', Monday, Wednesday, offset, weekday tests):
                    file                                                 row               column     old     new
      futures_basis_year 2018 (futures only, before index data) | a_all_days                    n     212     211
      futures_basis_year                                   2018 | a_all_days                    n      27      28
      futures_basis_year                                    all | a_all_days                    n    1962    1963
      futures_basis_year                            all | b_ex_index_flagged                    n    1876    1877
      futures_basis_year 2018 (futures only, before index data) | a_all_days            fut_ON_bp   2.482   2.779
      futures_basis_year                                   2018 | a_all_days            fut_ON_bp  -0.385  -2.526
      futures_basis_year                                    all | a_all_days            fut_ON_bp   5.424   5.390
      futures_basis_year                            all | b_ex_index_flagged            fut_ON_bp   5.145   5.110
      futures_basis_year 2018 (futures only, before index data) | a_all_days                fut_t   0.688   0.774
      futures_basis_year                                   2018 | a_all_days                fut_t  -0.034  -0.225
      futures_basis_year                                    all | a_all_days                fut_t   4.061   4.036
      futures_basis_year                            all | b_ex_index_flagged                fut_t   3.941   3.914
      futures_basis_year                                   2018 | a_all_days            idx_ON_bp  -6.396 -10.100
      futures_basis_year                                    all | a_all_days            idx_ON_bp   5.919   5.860
      futures_basis_year                            all | b_ex_index_flagged            idx_ON_bp   6.190   6.128
      futures_basis_year                                   2018 | a_all_days                idx_t  -0.543  -0.883
      futures_basis_year                                    all | a_all_days                idx_t   5.395   5.335
      futures_basis_year                            all | b_ex_index_flagged                idx_t   5.400   5.340
      futures_basis_year                                   2018 | a_all_days         dbasis_ON_bp   6.011   7.574
      futures_basis_year                                    all | a_all_days         dbasis_ON_bp  -0.495  -0.470
      futures_basis_year                            all | b_ex_index_flagged         dbasis_ON_bp  -1.045  -1.018
      futures_basis_year                                   2018 | a_all_days             dbasis_t   0.705   0.936
      futures_basis_year                                    all | a_all_days             dbasis_t  -0.408  -0.387
      futures_basis_year                            all | b_ex_index_flagged             dbasis_t  -0.897  -0.874
      futures_basis_year                                   2018 | a_all_days                 corr   0.590   0.602
      futures_basis_year                                   2018 | a_all_days                slope   0.838   0.799
      futures_basis_year                                   2018 | a_all_days          slope_nw_se   0.295   0.245
      futures_basis_year                                   2018 | a_all_days                   r2   0.349   0.362
      futures_basis_year                                   2018 | a_all_days         dbasis_ID_bp  -6.611  -4.244
      futures_basis_year                                    all | a_all_days         dbasis_ID_bp   1.960   1.989
      futures_basis_year                            all | b_ex_index_flagged         dbasis_ID_bp   2.605   2.635
      futures_basis_year                                   2018 | a_all_days          dbasis_ID_t  -0.857  -0.556
      futures_basis_year                                    all | a_all_days          dbasis_ID_t   1.509   1.533
      futures_basis_year                            all | b_ex_index_flagged          dbasis_ID_t   1.907   1.931
   futures_basis_weekday         full (index sample) | Tue->Wed | a_all_days                    n     394     395
   futures_basis_weekday              pre 2022-08-25 | Tue->Wed | a_all_days                    n     185     186
   futures_basis_weekday         full (index sample) | Tue->Wed | a_all_days            fut_ON_bp   6.738   6.568
   futures_basis_weekday              pre 2022-08-25 | Tue->Wed | a_all_days            fut_ON_bp   4.245   3.898
   futures_basis_weekday         full (index sample) | Tue->Wed | a_all_days                fut_t   2.106   2.053
   futures_basis_weekday              pre 2022-08-25 | Tue->Wed | a_all_days                fut_t   1.396   1.276
   futures_basis_weekday         full (index sample) | Tue->Wed | a_all_days            idx_ON_bp   8.051   7.752
   futures_basis_weekday              pre 2022-08-25 | Tue->Wed | a_all_days            idx_ON_bp   2.569   1.963
   futures_basis_weekday         full (index sample) | Tue->Wed | a_all_days                idx_t   3.420   3.265
   futures_basis_weekday              pre 2022-08-25 | Tue->Wed | a_all_days                idx_t   1.164   0.858
   futures_basis_weekday         full (index sample) | Tue->Wed | a_all_days         dbasis_ON_bp  -1.313  -1.184
   futures_basis_weekday              pre 2022-08-25 | Tue->Wed | a_all_days         dbasis_ON_bp   1.676   1.935
   futures_basis_weekday         full (index sample) | Tue->Wed | a_all_days             dbasis_t  -0.569  -0.514
   futures_basis_weekday              pre 2022-08-25 | Tue->Wed | a_all_days             dbasis_t   0.598   0.692
   futures_basis_weekday         full (index sample) | Tue->Wed | a_all_days         dbasis_ID_bp   8.484   8.613
   futures_basis_weekday              pre 2022-08-25 | Tue->Wed | a_all_days         dbasis_ID_bp   3.774   4.075
   futures_basis_weekday         full (index sample) | Tue->Wed | a_all_days          dbasis_ID_t   2.670   2.714
   futures_basis_weekday              pre 2022-08-25 | Tue->Wed | a_all_days          dbasis_ID_t   0.777   0.841
    futures_basis_expiry                   days-to-expiry | 16+ | a_all_days                    n     427     428
    futures_basis_expiry       night (entry weekday) | Tue->Wed | a_all_days                    n     394     395
    futures_basis_expiry       night x dte | Tue->Wed | dte 16+ | a_all_days                    n      89      90
    futures_basis_expiry                   days-to-expiry | 16+ | a_all_days      b_close_mean_bp -28.473 -28.462
    futures_basis_expiry       night (entry weekday) | Tue->Wed | a_all_days      b_close_mean_bp -16.217 -16.235
    futures_basis_expiry                   days-to-expiry | 16+ | a_all_days        b_close_sd_bp  87.994  87.892
    futures_basis_expiry       night (entry weekday) | Tue->Wed | a_all_days        b_close_sd_bp  70.365  70.277
    futures_basis_expiry                   days-to-expiry | 16+ | a_all_days         dbasis_ON_bp  -0.333  -0.216
    futures_basis_expiry       night (entry weekday) | Tue->Wed | a_all_days         dbasis_ON_bp  -1.313  -1.184
    futures_basis_expiry       night x dte | Tue->Wed | dte 16+ | a_all_days         dbasis_ON_bp  -0.965  -0.402
    futures_basis_expiry                   days-to-expiry | 16+ | a_all_days          dbasis_ON_t  -0.132  -0.086
    futures_basis_expiry       night (entry weekday) | Tue->Wed | a_all_days          dbasis_ON_t  -0.569  -0.514
    futures_basis_expiry       night x dte | Tue->Wed | dte 16+ | a_all_days          dbasis_ON_t  -0.186  -0.077
    futures_basis_expiry                   days-to-expiry | 16+ | a_all_days         dbasis_ID_bp   1.138   1.275
    futures_basis_expiry       night (entry weekday) | Tue->Wed | a_all_days         dbasis_ID_bp   8.484   8.613
    futures_basis_expiry                   days-to-expiry | 16+ | a_all_days          dbasis_ID_t   0.389   0.437
    futures_basis_expiry       night (entry weekday) | Tue->Wed | a_all_days          dbasis_ID_t   2.670   2.714
    futures_basis_expiry       night (entry weekday) | Tue->Wed | a_all_days prev_b_close_mean_bp -23.387 -23.664
futures_basis_robustness                         2018 | A | a_all_days | nan                    n      24      25
futures_basis_robustness                          all | A | a_all_days | nan                    n    1691    1692
futures_basis_robustness          nan | B | a_all_days | full (index sample)                    n     301     302
futures_basis_robustness               nan | B | a_all_days | pre 2022-08-25                    n     141     142
futures_basis_robustness                  all | A | b_ex_index_flagged | nan                    n    1621    1622
futures_basis_robustness                         2018 | A | a_all_days | nan            fut_ON_bp   4.879   2.271
futures_basis_robustness                          all | A | a_all_days | nan            fut_ON_bp   5.314   5.275
futures_basis_robustness          nan | B | a_all_days | full (index sample)            fut_ON_bp   5.953   5.733
futures_basis_robustness               nan | B | a_all_days | pre 2022-08-25            fut_ON_bp   1.486   1.051
futures_basis_robustness                  all | A | b_ex_index_flagged | nan            fut_ON_bp   4.932   4.892

## Conclusions checked (not reinterpreted)
- Monday edge: unchanged to every decimal (Monday full net 6.42 bp, t 2.78; Mon+Tue likewise). All 14 missing days are Fridays, so no Monday- or Tuesday-entry night touches them; the contaminated nights are weekend/holiday nights.
- Wednesday gap: Wed->Thu nights are not touched by the repair or the 2018 fix (2018-11-21 is a Tue->Wed night); futures_basis_decomp Tables C/D are unchanged. W1 post-cutover Wed->Thu minus others -1.79 -> -1.53 bp (t -0.55): conclusion unchanged.
- Offset: post-cutover a -3.22 -> -3.56 bp (t -2.40 -> -2.73); O1 still holds. 2023 a moves 1.19 -> -0.71 bp and k 0.765 -> 0.867 (flagged, > 0.5 SE).
- 2023 index ON: 11.08 -> 9.86 bp, equal to the full-index 9.86 bp: the discrepancy is removed.
- Cells crossing |t| = 2 after the repair (below the Bonferroni bar 3.1, no pre-registered read involves them): 2023-on all-days Thu->Fri minus others 1.77 -> 2.05, weekend -1.68 -> -2.01.

## Summary
1. Missing: 15 trading days in VN30F1M.csv: 14 consecutive roll days 2022-11-18..2023-12-22 plus 2021-04-29; 30 nights affected (15 index nights without a futures bar, 15 contaminated futures nights).
2. Validated source: yes. VCI contract tickers (close 100% vs VCI VN30F1M; all fields 100% from 2023) fill all 14 roll days; 13 are cross-confirmed by identical VN30F2M bars; 2021-04-29 has no source and its night is excluded.
3. Moved (> 0.5 SE): 2023 index ON in the decomposition sample (11.08 -> 9.86 bp, discrepancy removed) and the 2023 offset fit (a, k). All-nights gross 4.99 -> 5.25 bp (Sharpe 1.29 -> 1.40) moved, but < 0.5 SE.
4. Did not move: Monday and Mon+Tue (identical), Wednesday tables, W1/W2/O1 verdicts; the 2018-11-21 fix changes only 2018 / pooled / Tue->Wed cells (N 1,962 -> 1,963).
5. Open: the same first-row pattern drops the first night in five other scripts (not changed); the 2022 contract-ticker O/H/L/volume differences vs the continuous feed are unexplained; the fallback 'excluded' variant (5.49 bp) and the repaired file (5.25 bp) differ because the repair adds 14 roll and 14 weekend nights back.
