# Futures basis follow-up (measurement only)

## 1a. Reconcile 2023 index ON (11.1 bp decomposition sample vs 9.9 bp full index)
year                                                                step    n  mean_bp     t
2023                               1 full index nights (gate convention)  249    9.863 4.630
2023                                  2 & futures bar exists on the date  237   10.212 4.603
2023                  3 & futures night invested (roll F2M close exists)  237   10.212 4.603
2023                   4 & same prior trading day (decomposition sample)  225   11.075 5.071
 all                               1 full index nights (gate convention) 1993    5.704 5.259
 all                                  2 & futures bar exists on the date 1978    5.774 5.288
 all                  3 & futures night invested (roll F2M close exists) 1978    5.774 5.288
 all                   4 & same prior trading day (decomposition sample) 1963    5.860 5.335
2023 5 decomposition sample, misaligned nights INCLUDED (step 3 ∩ index)  237   10.212 4.603
2023              6 decomposition sample (misaligned EXCLUDED), = step 4  225   11.075 5.071
 all 5 decomposition sample, misaligned nights INCLUDED (step 3 ∩ index) 1978    5.774 5.288
 all              6 decomposition sample (misaligned EXCLUDED), = step 4 1963    5.860 5.335

Misaligned nights (prior trading day differs between VN30F1M and VN30):
      date  idx_ON_bp  fut_ON_bp fut_prior_day idx_prior_day night_label  idx_flag  idx_gap_calendar_days  fut_gap_calendar_days                                     note
2021-05-04     -1.524     23.502    2021-04-28    2021-04-29     holiday     False                      5                      6 index prior day missing from VN30F1M.csv
2022-11-21     -5.768     64.169    2022-11-17    2022-11-18     holiday     False                      3                      4 index prior day missing from VN30F1M.csv
2022-12-19     -3.290   -136.376    2022-12-15    2022-12-16     holiday     False                      3                      4 index prior day missing from VN30F1M.csv
2023-01-30     15.907     40.062    2023-01-19    2023-01-27     holiday     False                      3                     11 index prior day missing from VN30F1M.csv
2023-02-20    -12.725    -42.766    2023-02-16    2023-02-17     holiday     False                      3                      4 index prior day missing from VN30F1M.csv
2023-03-20    -55.993    -71.857    2023-03-16    2023-03-17     holiday     False                      3                      4 index prior day missing from VN30F1M.csv
2023-04-24     29.207    -86.331    2023-04-20    2023-04-21     holiday     False                      3                      4 index prior day missing from VN30F1M.csv
2023-05-22     14.304      0.000    2023-05-18    2023-05-19     holiday     False                      3                      4 index prior day missing from VN30F1M.csv
2023-06-19      8.562     12.734    2023-06-15    2023-06-16     holiday     False                      3                      4 index prior day missing from VN30F1M.csv
2023-07-24     39.531    203.420    2023-07-20    2023-07-21     holiday     False                      3                      4 index prior day missing from VN30F1M.csv
2023-08-21      4.956   -505.844    2023-08-17    2023-08-18     holiday     False                      3                      4 index prior day missing from VN30F1M.csv
2023-09-25    -19.473   -241.558    2023-09-21    2023-09-22     holiday     False                      3                      4 index prior day missing from VN30F1M.csv
2023-10-23     -8.547    161.563    2023-10-19    2023-10-20     holiday     False                      3                      4 index prior day missing from VN30F1M.csv
2023-11-20   -108.147   -495.820    2023-11-16    2023-11-17     holiday     False                      3                      4 index prior day missing from VN30F1M.csv
2023-12-25     20.663    -19.137    2023-12-21    2023-12-22     holiday     False                      3                      4 index prior day missing from VN30F1M.csv

## 1b. Weekday equality on dbasis_ON (5 night dummies, no intercept, HAC lag 5 over consecutive nights; 'minus others' = beta_k - mean of the other four betas; joint Wald chi2(4) that all five are equal; holiday nights excluded). JOINT row: mean_bp = period grand mean (all five categories).
### pre 2022-08-25 | all days
              night   n  mean_bp  mean_t  minus_others_bp  minus_others_t  wald  wald_p  n_excluded_holiday
           Mon->Tue 184   12.819   3.007           10.043           2.071   NaN     NaN                 NaN
           Tue->Wed 186    1.935   0.610           -3.561          -0.888   NaN     NaN                 NaN
           Wed->Thu 183   -1.023  -0.275           -7.258          -1.860   NaN     NaN                 NaN
           Thu->Fri 187    4.410   1.069           -0.468          -0.098   NaN     NaN                 NaN
 Fri->Mon (weekend) 179    5.778   0.963            1.243           0.204   NaN     NaN                 NaN
JOINT (all 5 equal) 919    4.777   2.318              NaN             NaN 7.084   0.132              18.000

### pre 2022-08-25 | ex index-flagged
              night   n  mean_bp  mean_t  minus_others_bp  minus_others_t  wald  wald_p  n_excluded_holiday
           Mon->Tue 171   12.125   3.045           10.323           2.085   NaN     NaN                 NaN
           Tue->Wed 166    2.194   0.640           -2.090          -0.532   NaN     NaN                 NaN
           Wed->Thu 163   -1.766  -0.445           -7.040          -1.743   NaN     NaN                 NaN
           Thu->Fri 172    3.352   0.746           -0.643          -0.123   NaN     NaN                 NaN
 Fri->Mon (weekend) 167    3.426   0.584           -0.550          -0.091   NaN     NaN                 NaN
JOINT (all 5 equal) 839    3.931   1.916              NaN             NaN 6.725   0.151              16.000

### pre 2022-08-25 | all days, ex roll & expiry-1..+1
              night   n  mean_bp  mean_t  minus_others_bp  minus_others_t  wald  wald_p  n_excluded_holiday
           Mon->Tue 184   12.819   3.041           11.101           2.220   NaN     NaN                 NaN
           Tue->Wed 142    1.130   0.286           -3.509          -0.735   NaN     NaN                 NaN
           Wed->Thu 138   -0.547  -0.116           -5.605          -1.204   NaN     NaN                 NaN
           Thu->Fri 142    0.508   0.117           -4.287          -0.854   NaN     NaN                 NaN
 Fri->Mon (weekend) 179    5.778   0.926            2.301           0.364   NaN     NaN                 NaN
JOINT (all 5 equal) 785    4.522   1.894              NaN             NaN 6.627   0.157              17.000

### pre 2022-08-25 | ex flagged, ex roll & expiry-1..+1
              night   n  mean_bp  mean_t  minus_others_bp  minus_others_t  wald  wald_p  n_excluded_holiday
           Mon->Tue 171   12.125   3.061           11.548           2.254   NaN     NaN                 NaN
           Tue->Wed 125    1.449   0.332           -1.797          -0.377   NaN     NaN                 NaN
           Wed->Thu 124   -1.771  -0.357           -5.821          -1.201   NaN     NaN                 NaN
           Thu->Fri 133   -0.796  -0.173           -4.603          -0.864   NaN     NaN                 NaN
 Fri->Mon (weekend) 167    3.426   0.563            0.674           0.109   NaN     NaN                 NaN
JOINT (all 5 equal) 720    3.474   1.449              NaN             NaN 6.730   0.151              15.000

### post 2022-08-25 | all days
              night    n  mean_bp  mean_t  minus_others_bp  minus_others_t  wald  wald_p  n_excluded_holiday
           Mon->Tue  207   -3.978  -1.818            1.757           0.667   NaN     NaN                 NaN
           Tue->Wed  209   -3.960  -1.183            1.780           0.499   NaN     NaN                 NaN
           Wed->Thu  207   -6.817  -3.006           -1.792          -0.652   NaN     NaN                 NaN
           Thu->Fri  197   -1.991  -0.914            4.240           1.827   NaN     NaN                 NaN
 Fri->Mon (weekend)  187  -10.171  -2.942           -5.984          -1.580   NaN     NaN                 NaN
JOINT (all 5 equal) 1007   -5.319  -4.291              NaN             NaN 5.187   0.269              19.000

### post 2022-08-25 | ex index-flagged
              night    n  mean_bp  mean_t  minus_others_bp  minus_others_t  wald  wald_p  n_excluded_holiday
           Mon->Tue  207   -3.978  -1.816            1.724           0.655   NaN     NaN                 NaN
           Tue->Wed  209   -3.960  -1.183            1.747           0.489   NaN     NaN                 NaN
           Wed->Thu  206   -6.585  -2.896           -1.535          -0.555   NaN     NaN                 NaN
           Thu->Fri  196   -1.777  -0.812            4.476           1.927   NaN     NaN                 NaN
 Fri->Mon (weekend)  185  -10.487  -3.007           -6.412          -1.682   NaN     NaN                 NaN
JOINT (all 5 equal) 1003   -5.280  -4.243              NaN             NaN 5.612   0.230              19.000

### post 2022-08-25 | all days, ex roll & expiry-1..+1
              night   n  mean_bp  mean_t  minus_others_bp  minus_others_t  wald  wald_p  n_excluded_holiday
           Mon->Tue 206   -3.926  -1.787            1.680           0.607   NaN     NaN                 NaN
           Tue->Wed 160   -5.935  -1.479           -0.831          -0.200   NaN     NaN                 NaN
           Wed->Thu 159   -5.188  -1.925            0.102           0.032   NaN     NaN                 NaN
           Thu->Fri 162   -1.128  -0.476            5.177           2.148   NaN     NaN                 NaN
 Fri->Mon (weekend) 187  -10.171  -2.922           -6.127          -1.569   NaN     NaN                 NaN
JOINT (all 5 equal) 874   -5.341  -3.845              NaN             NaN 6.051   0.195              16.000

### post 2022-08-25 | ex flagged, ex roll & expiry-1..+1
              night   n  mean_bp  mean_t  minus_others_bp  minus_others_t  wald  wald_p  n_excluded_holiday
           Mon->Tue 206   -3.926  -1.787            1.681           0.607   NaN     NaN                 NaN
           Tue->Wed 160   -5.935  -1.479           -0.831          -0.200   NaN     NaN                 NaN
           Wed->Thu 158   -4.874  -1.803            0.494           0.155   NaN     NaN                 NaN
           Thu->Fri 162   -1.128  -0.475            5.177           2.140   NaN     NaN                 NaN
 Fri->Mon (weekend) 185  -10.487  -2.986           -6.522          -1.661   NaN     NaN                 NaN
JOINT (all 5 equal) 871   -5.340  -3.839              NaN             NaN 6.336   0.175              16.000

### 2023-01-01 onward | all days
              night   n  mean_bp  mean_t  minus_others_bp  minus_others_t  wald  wald_p  n_excluded_holiday
           Mon->Tue 189   -4.687  -2.167            1.948           0.739   NaN     NaN                 NaN
           Tue->Wed 191   -5.039  -1.497            1.508           0.420   NaN     NaN                 NaN
           Wed->Thu 189   -7.120  -3.225           -1.094          -0.408   NaN     NaN                 NaN
           Thu->Fri 181   -3.003  -1.438            4.054           1.771   NaN     NaN                 NaN
 Fri->Mon (weekend) 172  -11.378  -3.321           -6.416          -1.681   NaN     NaN                 NaN
JOINT (all 5 equal) 922   -6.176  -5.233              NaN             NaN 5.386   0.250              18.000

### 2023-01-01 onward | ex index-flagged
              night   n  mean_bp  mean_t  minus_others_bp  minus_others_t  wald  wald_p  n_excluded_holiday
           Mon->Tue 189   -4.687  -2.164            1.981           0.750   NaN     NaN                 NaN
           Tue->Wed 191   -5.039  -1.498            1.541           0.429   NaN     NaN                 NaN
           Wed->Thu 189   -7.120  -3.227           -1.061          -0.396   NaN     NaN                 NaN
           Thu->Fri 180   -2.775  -1.326            4.371           1.918   NaN     NaN                 NaN
 Fri->Mon (weekend) 170  -11.737  -3.395           -6.832          -1.777   NaN     NaN                 NaN
JOINT (all 5 equal) 919   -6.190  -5.211              NaN             NaN 6.080   0.193              18.000

### 2023-01-01 onward | all days, ex roll & expiry-1..+1
              night   n  mean_bp  mean_t  minus_others_bp  minus_others_t  wald  wald_p  n_excluded_holiday
           Mon->Tue 188   -4.633  -2.112            1.880           0.689   NaN     NaN                 NaN
           Tue->Wed 146   -6.199  -1.501           -0.077          -0.018   NaN     NaN                 NaN
           Wed->Thu 145   -6.098  -2.361            0.050           0.016   NaN     NaN                 NaN
           Thu->Fri 148   -2.379  -1.077            4.698           2.028   NaN     NaN                 NaN
 Fri->Mon (weekend) 172  -11.378  -3.291           -6.551          -1.644   NaN     NaN                 NaN
JOINT (all 5 equal) 799   -6.220  -4.759              NaN             NaN 5.889   0.208              15.000

### 2023-01-01 onward | ex flagged, ex roll & expiry-1..+1
              night   n  mean_bp  mean_t  minus_others_bp  minus_others_t  wald  wald_p  n_excluded_holiday
           Mon->Tue 188   -4.633  -2.112            1.970           0.720   NaN     NaN                 NaN
           Tue->Wed 146   -6.199  -1.501            0.013           0.003   NaN     NaN                 NaN
           Wed->Thu 145   -6.098  -2.363            0.139           0.045   NaN     NaN                 NaN
           Thu->Fri 148   -2.379  -1.077            4.788           2.069   NaN     NaN                 NaN
 Fri->Mon (weekend) 170  -11.737  -3.364           -6.910          -1.723   NaN     NaN                 NaN
JOINT (all 5 equal) 797   -6.283  -4.790              NaN             NaN 6.262   0.180              15.000

## 1c. Offset vs proportional lag: fut_ON = a + k idx_ON (NW SEs)
          sample                                  period    n   a_bp  a_se_bp    a_t     k  k_se  k_t_vs1    r2  mean_dbasis_bp
        all days                                    2022  245  2.781    2.458  1.132 0.705 0.058   -5.101 0.544           3.403
        all days                                    2023  225  1.190    2.030  0.587 0.765 0.099   -2.369 0.471          -1.416
        all days                                    2024  250 -3.678    1.421 -2.588 0.836 0.047   -3.449 0.515          -5.112
        all days                                    2025  249 -6.681    3.864 -1.729 0.783 0.146   -1.480 0.601         -10.289
        all days                                    2026  216 -6.403    2.431 -2.634 0.991 0.108   -0.082 0.544          -6.498
        all days                  post 2022-08-25 pooled 1026 -3.216    1.338 -2.404 0.820 0.063   -2.838 0.552          -5.084
        all days       pre 2022-08-25 pooled (reference)  937  4.902    2.106  2.328 0.641 0.068   -5.279 0.155           4.583
        all days post 2022-08-25, ex roll & expiry-1..+1  890 -3.175    1.493 -2.126 0.821 0.069   -2.609 0.552          -5.101
ex index-flagged                                    2022  241  2.666    2.439  1.093 0.705 0.058   -5.119 0.548           3.299
ex index-flagged                                    2023  225  1.190    2.030  0.587 0.765 0.099   -2.369 0.471          -1.416
ex index-flagged                                    2024  249 -3.681    1.426 -2.581 0.836 0.048   -3.441 0.515          -5.120
ex index-flagged                                    2025  248 -6.886    3.882 -1.774 0.784 0.146   -1.478 0.602         -10.497
ex index-flagged                                    2026  215 -6.220    2.478 -2.510 0.990 0.108   -0.088 0.544          -6.323
ex index-flagged                  post 2022-08-25 pooled 1022 -3.167    1.342 -2.360 0.820 0.063   -2.838 0.553          -5.044
ex index-flagged       pre 2022-08-25 pooled (reference)  855  4.143    2.044  2.027 0.641 0.070   -5.141 0.173           3.794
ex index-flagged post 2022-08-25, ex roll & expiry-1..+1  887 -3.167    1.496 -2.118 0.821 0.069   -2.609 0.553          -5.100

## 1d. Weekday equality on the intraday basis change dbasis_ID = fut_ID - idx_ID
### post 2022-08-25 | all days
              night    n  mean_bp  mean_t  minus_others_bp  minus_others_t  wald  wald_p  n_excluded_holiday
           Mon->Tue  207    1.240   0.464           -6.533          -1.960   NaN     NaN                 NaN
           Tue->Wed  209   12.652   2.741            7.732           1.519   NaN     NaN                 NaN
           Wed->Thu  207    0.843   0.259           -7.030          -1.830   NaN     NaN                 NaN
           Thu->Fri  197    6.283   2.030           -0.230          -0.064   NaN     NaN                 NaN
 Fri->Mon (weekend)  187   11.315   2.762            6.061           1.287   NaN     NaN                 NaN
JOINT (all 5 equal) 1007    6.385   4.509              NaN             NaN 7.214   0.125              19.000

### post 2022-08-25 | all days, ex roll & expiry-1..+1
              night   n  mean_bp  mean_t  minus_others_bp  minus_others_t  wald  wald_p  n_excluded_holiday
           Mon->Tue 206    1.612   0.601           -6.511          -1.894   NaN     NaN                 NaN
           Tue->Wed 160   13.450   2.324            8.286           1.325   NaN     NaN                 NaN
           Wed->Thu 159    1.893   0.517           -6.160          -1.425   NaN     NaN                 NaN
           Thu->Fri 162    5.834   1.760           -1.233          -0.322   NaN     NaN                 NaN
 Fri->Mon (weekend) 187   11.315   2.829            5.618           1.190   NaN     NaN                 NaN
JOINT (all 5 equal) 874    6.689   4.293              NaN             NaN 5.835   0.212              16.000

### 2023-01-01 onward | all days
              night   n  mean_bp  mean_t  minus_others_bp  minus_others_t  wald  wald_p  n_excluded_holiday
           Mon->Tue 189    2.849   1.115           -4.933          -1.565   NaN     NaN                 NaN
           Tue->Wed 191   11.003   2.325            5.260           1.027   NaN     NaN                 NaN
           Wed->Thu 189    1.919   0.651           -6.095          -1.717   NaN     NaN                 NaN
           Thu->Fri 181    6.185   2.267           -0.762          -0.240   NaN     NaN                 NaN
 Fri->Mon (weekend) 172   12.019   3.174            6.530           1.493   NaN     NaN                 NaN
JOINT (all 5 equal) 922    6.713   4.844              NaN             NaN 5.980   0.201              18.000

### 2023-01-01 onward | all days, ex roll & expiry-1..+1
              night   n  mean_bp  mean_t  minus_others_bp  minus_others_t  wald  wald_p  n_excluded_holiday
           Mon->Tue 188    3.265   1.268           -4.575          -1.402   NaN     NaN                 NaN
           Tue->Wed 146   11.863   2.014            6.173           0.976   NaN     NaN                 NaN
           Wed->Thu 145    3.085   0.943           -4.800          -1.197   NaN     NaN                 NaN
           Thu->Fri 148    4.392   1.529           -3.166          -0.916   NaN     NaN                 NaN
 Fri->Mon (weekend) 172   12.019   3.167            6.368           1.430   NaN     NaN                 NaN
JOINT (all 5 equal) 799    6.897   4.643              NaN             NaN 4.677   0.322              15.000

## 2.0 Probe outcome (full text: results/intraday_probe.md)
- **VN30F1M 1m (VCI) goes back to 2023-09-11 (~3.2 years, ~241 bars/day), despite vnstock's stated 6-month community cap** for 1m. That cap may be enforced later, so the data is cached now. Earlier than 2023-09-11 nothing is returned (no row cap observed: the response is not a round number). VCI VN30F1M 5m/15m and VCI VN30 5m/15m return 1 year on a padded 24h grid (NaN rows outside the session; dropped). KBS VN30F1M intraday is sparse (1m starts 2026-05-25 with ~6,200 rows; many minutes missing) and is not used.
- **VN30 index intraday exists**: VCI/KBS 1m from 2026-05-25 (~6 months), VCI/KBS 5m from 2025-11-20 (1 year). The first index bar of each day is 09:15 (the stock ATO result); there is no index print between 09:00 and 09:15. The 1m/5m windows roll (on this run VCI 5m starts 2025-11-24, VCI 1m 2026-05-27).
- **KBS index 09:15 bar disagrees with the daily open**: KBS's first index bar open equals the (VCI) daily open on only ~40% of days, by up to ~39 points, while VCI 5m/1m match it on 99.6%/98%; at 09:30 and 10:00 KBS and VCI agree exactly. VCI 5m is used, KBS is a cross-check only.
- The response includes the current, incomplete session (2026-11-23 VN time) and 2026-11-18..20, after the daily files end; analysis only uses dates present in the daily files.
- **Timezone**: timestamps are naive and run 09:00..14:45 (futures) / 09:15..14:45 (index), i.e. Vietnam local time (UTC+7); no conversion applied.
- **Daily-bar check**: first intraday bar open vs daily open and last bar close vs daily close are in the table (columns first_open_eq_daily_open, last_close_eq_daily_close).
- **How the futures ATO appears**: there is no separate 08:45 bar. The ATO match (struck at 09:00) is folded into the bar labelled 09:00: its open equals the daily open on ~99.7% of days and its median volume (2996 contracts) is >2x the 09:01 bar (1286). Only 8 stray bars before 09:00 exist in 3 years (dates 2023-09-20, 2023-09-21, 2023-11-03, 2024-08-19, 2024-11-26, 2025-04-24); they are ignored. The ATC appears as a single bar labelled 14:45 whose close equals the daily close on every day.
- Bars labelled 11:30 exist on 399 of 795 futures days and 14:30 on 353; there are no 12:59 or 14:31..14:44 bars. Consistent with bar-START labels (prints stamped exactly at 11:30:00 / 14:30:00 fall in a minute of their own).

## 2.x Reproduction gate: exit at the 09:00 bar open vs build() (same nights, base costs incl. 5 bp roll placeholder)
n 791; max |gross diff| 40.917 bp, mean gross diff 0.0264 bp, mean net diff 0.0264 bp; nights where the 09:00 bar open != daily open: 12.
Forward-fills (no print in minute h): futures {'09:00': 0, '09:15': 1, '09:30': 0, '10:00': 2} of 795 days; index {'09:15': 0, '09:30': 0, '10:00': 1} of 248 days. Index 09:15 bar open == daily index open on 99.6% of basis-window nights; basis window (Timestamp('2025-11-24 00:00:00'), Timestamp('2026-11-17 00:00:00'), 244).

2.2a uses aligned decomposition nights only (4 misaligned Thu-close -> Mon-open nights in the intraday window dropped).

## 2.2a futures cum ln return prior ATC -> h
                          period     subset     h   n  mean_bp     t
                            2023 all nights 09:00  71   13.230 2.914
                            2023 all nights 09:15  72   11.951 2.137
                            2023 all nights 09:30  72    5.910 0.945
                            2023 all nights 10:00  72    4.060 0.604
                            2023   Mon->Tue 09:00  15   17.637 2.468
                            2023   Mon->Tue 09:15  16   22.755 2.623
                            2023   Mon->Tue 09:30  16   16.404 1.544
                            2023   Mon->Tue 10:00  16   13.194 1.474
                            2024 all nights 09:00 247    3.886 2.060
                            2024 all nights 09:15 250    5.301 2.296
                            2024 all nights 09:30 250    5.354 2.229
                            2024 all nights 10:00 250    6.123 2.053
                            2024   Mon->Tue 09:00  49    7.613 2.441
                            2024   Mon->Tue 09:15  49   10.308 3.311
                            2024   Mon->Tue 09:30  49    8.854 2.762
                            2024   Mon->Tue 10:00  49    7.856 1.495
                            2025 all nights 09:00 248    6.261 1.923
                            2025 all nights 09:15 249    6.710 1.601
                            2025 all nights 09:30 249    6.550 1.435
                            2025 all nights 10:00 249    9.529 2.073
                            2025   Mon->Tue 09:00  49    6.639 1.764
                            2025   Mon->Tue 09:15  49   10.637 1.756
                            2025   Mon->Tue 09:30  49   12.822 1.589
                            2025   Mon->Tue 10:00  49   22.194 2.152
                            2026 all nights 09:00 216    4.284 1.275
                            2026 all nights 09:15 216    4.081 1.058
                            2026 all nights 09:30 216    1.622 0.376
                            2026 all nights 10:00 216    0.944 0.191
                            2026   Mon->Tue 09:00  43   21.477 1.765
                            2026   Mon->Tue 09:15  43   25.582 1.651
                            2026   Mon->Tue 09:30  43   27.392 1.746
                            2026   Mon->Tue 10:00  43   32.702 1.983
2023-09-11 onward (all intraday) all nights 09:00 782    5.597 3.535
2023-09-11 onward (all intraday) all nights 09:15 787    6.020 3.126
2023-09-11 onward (all intraday) all nights 09:30 787    4.759 2.259
2023-09-11 onward (all intraday) all nights 10:00 787    5.590 2.424
2023-09-11 onward (all intraday)   Mon->Tue 09:00 156   12.092 3.042
2023-09-11 onward (all intraday)   Mon->Tue 09:15 157   15.862 3.150
2023-09-11 onward (all intraday)   Mon->Tue 09:30 157   15.939 2.948
2023-09-11 onward (all intraday)   Mon->Tue 10:00 157   19.680 3.208

## 2.2b futures catch-up from 09:00 by index-ON tercile (2023-09-11 onward)
           period             subset            h   n  mean_bp      t  idx_ON_mean_bp  dbasis_ON_mean_bp
T1 small/negative idx_ON -309..-0 bp 09:00->09:15 260  -12.259 -7.785         -28.816              0.478
T1 small/negative idx_ON -309..-0 bp 09:00->09:30 260   -9.093 -3.744         -28.816              0.478
T1 small/negative idx_ON -309..-0 bp 09:00->10:00 260   -9.030 -2.679         -28.816              0.478
        T2 middle   idx_ON -0..21 bp 09:00->09:15 260    1.599  1.775           9.598             -1.138
        T2 middle   idx_ON -0..21 bp 09:00->09:30 260   -1.582 -1.127           9.598             -1.138
        T2 middle   idx_ON -0..21 bp 09:00->10:00 260   -1.818 -0.810           9.598             -1.138
  T3 large gap-up  idx_ON 21..664 bp 09:00->09:15 262   11.993  8.240          53.244            -16.916
  T3 large gap-up  idx_ON 21..664 bp 09:00->09:30 262    8.113  4.265          53.244            -16.916
  T3 large gap-up  idx_ON 21..664 bp 09:00->10:00 262   10.676  3.986          53.244            -16.916
              all                    09:00->09:15 782    0.474  0.577          11.396             -5.873
              all                    09:00->09:30 782   -0.831 -0.725          11.396             -5.873
              all                    09:00->10:00 782   -0.030 -0.019          11.396             -5.873

## 2.2e recovery legs: futures 09:00->h and index 09:15->h
                                   period      subset     h   n  mean_bp      t
index-intraday window (2025-11-24 onward) futures leg 09:15 244   -0.300 -0.202
index-intraday window (2025-11-24 onward)   index leg 09:15 244    0.000    NaN
                        Wed->Thu (window) futures leg 09:15  47   -6.229 -1.918
                        Wed->Thu (window)   index leg 09:15  47    0.000    NaN
              Fri->Mon (weekend) (window) futures leg 09:15  46    2.497  0.690
              Fri->Mon (weekend) (window)   index leg 09:15  46    0.000    NaN
index-intraday window (2025-11-24 onward) futures leg 09:30 244   -2.261 -1.046
index-intraday window (2025-11-24 onward)   index leg 09:30 244   -6.263 -1.905
                        Wed->Thu (window) futures leg 09:30  47   -4.137 -0.923
                        Wed->Thu (window)   index leg 09:30  47   -0.310 -0.073
              Fri->Mon (weekend) (window) futures leg 09:30  46   -6.570 -0.997
              Fri->Mon (weekend) (window)   index leg 09:30  46  -29.230 -1.675
index-intraday window (2025-11-24 onward) futures leg 10:00 244   -2.140 -0.724
index-intraday window (2025-11-24 onward)   index leg 10:00 244   -7.278 -1.929
                        Wed->Thu (window) futures leg 10:00  47   -8.815 -1.785
                        Wed->Thu (window)   index leg 10:00  47   -5.439 -1.126
              Fri->Mon (weekend) (window) futures leg 10:00  46   -4.848 -0.433
              Fri->Mon (weekend) (window)   index leg 10:00  46  -28.784 -1.512

## 2.2c basis change from prior close
                                   period subset                                          h   n  mean_bp      t
index-intraday window (2025-11-24 onward)        daily open (F 09:00 / I 09:15) = dbasis_ON 244   -6.451 -2.754
index-intraday window (2025-11-24 onward)                                     09:15 matched 244   -6.815 -2.905
index-intraday window (2025-11-24 onward)                                     09:30 matched 244   -2.513 -1.506
index-intraday window (2025-11-24 onward)                                     10:00 matched 244   -1.377 -0.823
                                2026 only        daily open (F 09:00 / I 09:15) = dbasis_ON 216   -6.498 -2.865
                                2026 only                                     09:15 matched 216   -6.774 -2.795
                                2026 only                                     09:30 matched 216   -2.950 -1.769
                                2026 only                                     10:00 matched 216   -1.535 -0.910
                        Mon->Tue (window)        daily open (F 09:00 / I 09:15) = dbasis_ON  49   -3.735 -0.604
                        Mon->Tue (window)                                     09:15 matched  49    0.706  0.111
                        Mon->Tue (window)                                     09:30 matched  49   -2.529 -0.615
                        Mon->Tue (window)                                     10:00 matched  49   -0.076 -0.020
                        Tue->Wed (window)        daily open (F 09:00 / I 09:15) = dbasis_ON  49    3.768  0.548
                        Tue->Wed (window)                                     09:15 matched  49    2.578  0.455
                        Tue->Wed (window)                                     09:30 matched  49    2.527  0.887
                        Tue->Wed (window)                                     10:00 matched  49    3.284  1.140
                        Wed->Thu (window)        daily open (F 09:00 / I 09:15) = dbasis_ON  47   -8.369 -1.827
                        Wed->Thu (window)                                     09:15 matched  47  -14.598 -2.369
                        Wed->Thu (window)                                     09:30 matched  47  -12.196 -3.119
                        Wed->Thu (window)                                     10:00 matched  47  -11.745 -2.077
                        Thu->Fri (window)        daily open (F 09:00 / I 09:15) = dbasis_ON  48   -2.938 -0.724
                        Thu->Fri (window)                                     09:15 matched  48   -4.345 -1.121
                        Thu->Fri (window)                                     09:30 matched  48    1.849  0.404
                        Thu->Fri (window)                                     10:00 matched  48    2.993  0.754
              Fri->Mon (weekend) (window)        daily open (F 09:00 / I 09:15) = dbasis_ON  46  -25.875 -2.468
              Fri->Mon (weekend) (window)                                     09:15 matched  46  -23.377 -1.909
              Fri->Mon (weekend) (window)                                     09:30 matched  46   -3.215 -0.662
              Fri->Mon (weekend) (window)                                     10:00 matched  46   -1.939 -0.431

## 2.3 Monday exit-time sensitivity (simple, descriptive)
                                           period            subset     h   n  mean_bp     t
2023-09-11 onward (post-cutover, intraday window)             gross 09:00 156   12.181 3.041
2023-09-11 onward (post-cutover, intraday window) net of base costs 09:00 156    8.495 2.115
                                             2026             gross 09:00  43   21.679 1.765
                                             2026 net of base costs 09:00  43   18.387 1.498
2023-09-11 onward (post-cutover, intraday window)             gross 09:15 157   16.007 3.151
2023-09-11 onward (post-cutover, intraday window) net of base costs 09:15 157   12.318 2.419
                                             2026             gross 09:15  43   25.882 1.653
                                             2026 net of base costs 09:15  43   22.590 1.443
2023-09-11 onward (post-cutover, intraday window)             gross 09:30 157   16.099 2.954
2023-09-11 onward (post-cutover, intraday window) net of base costs 09:30 157   12.410 2.269
                                             2026             gross 09:30  43   27.699 1.746
                                             2026 net of base costs 09:30  43   24.407 1.539

DESCRIPTIVE ONLY, NO EXIT SELECTION. Exits after 09:00 are fills in the continuous session and carry intraday price risk over the extra 15-30 minutes; the base costs (12,500 VND/side + 1 bp slippage/side + 5 bp roll placeholder) are applied unchanged although continuous-session fills are not auction fills. These rows cannot be mixed into the pre-registered rule (exit = Tuesday ATO, results/phase2_trackforward_spec.md), which is unchanged.

## 2.2d Recovery: mean(b_h - b_open) / mean(-dbasis_ON) on the same nights (b_open = ln F_0900 - ln I_0915, the daily decomposition's open basis). From daily open -> 09:15 the index term is zero (I_0915 is the index open), so that ratio is pure futures movement.
                                   period                   h   n  num_bp  den_bp  ratio  fieller_lo  fieller_hi                                 fieller  delta_se  delta_lo  delta_hi  shortfall_t  num_t
index-intraday window (2025-11-24 onward) daily open -> 09:15 244  -0.365   6.451 -0.057      -1.048       0.398                                 bounded     0.241    -0.528     0.415        2.754 -0.242
index-intraday window (2025-11-24 onward) daily open -> 09:30 244   3.937   6.451  0.610      -0.286       1.166                                 bounded     0.253     0.115     1.106        2.754  1.633
index-intraday window (2025-11-24 onward) daily open -> 10:00 244   5.074   6.451  0.787       0.099       1.479                                 bounded     0.247     0.302     1.271        2.754  2.086
                                2026 only daily open -> 09:15 216  -0.277   6.498 -0.043      -0.953       0.468                                 bounded     0.254    -0.540     0.455        2.865 -0.171
                                2026 only daily open -> 09:30 216   3.547   6.498  0.546      -0.596       1.055                                 bounded     0.284    -0.010     1.102        2.865  1.345
                                2026 only daily open -> 10:00 216   4.963   6.498  0.764      -0.093       1.349                                 bounded     0.264     0.247     1.280        2.865  1.857
                        Mon->Tue (window) daily open -> 09:15  49   4.441   3.735  1.189        -inf         inf unbounded (denominator not significant)     1.959    -2.650     5.028        0.604  1.138
                        Mon->Tue (window) daily open -> 09:30  49   1.206   3.735  0.323        -inf         inf unbounded (denominator not significant)     0.850    -1.342     1.988        0.604  0.276
                        Mon->Tue (window) daily open -> 10:00  49   3.659   3.735  0.980        -inf         inf unbounded (denominator not significant)     1.002    -0.984     2.944        0.604  0.812
                        Tue->Wed (window) daily open -> 09:15  49  -1.190  -3.768  0.316        -inf         inf unbounded (denominator not significant)     0.571    -0.804     1.436       -0.548 -0.452
                        Tue->Wed (window) daily open -> 09:30  49  -1.241  -3.768  0.329        -inf         inf unbounded (denominator not significant)     1.076    -1.781     2.439       -0.548 -0.206
                        Tue->Wed (window) daily open -> 10:00  49  -0.484  -3.768  0.128        -inf         inf unbounded (denominator not significant)     1.410    -2.636     2.892       -0.548 -0.079
                        Wed->Thu (window) daily open -> 09:15  47  -6.229   8.369 -0.744        -inf         inf unbounded (denominator not significant)     0.498    -1.721     0.232        1.827 -1.918
                        Wed->Thu (window) daily open -> 09:30  47  -3.827   8.369 -0.457        -inf         inf unbounded (denominator not significant)     0.562    -1.558     0.644        1.827 -1.189
                        Wed->Thu (window) daily open -> 10:00  47  -3.376   8.369 -0.403        -inf         inf unbounded (denominator not significant)     0.522    -1.427     0.620        1.827 -0.892
                        Thu->Fri (window) daily open -> 09:15  48  -1.407   2.938 -0.479        -inf         inf unbounded (denominator not significant)     1.377    -3.177     2.220        0.724 -0.496
                        Thu->Fri (window) daily open -> 09:30  48   4.788   2.938  1.629        -inf         inf unbounded (denominator not significant)     2.233    -2.748     6.007        0.724  1.346
                        Thu->Fri (window) daily open -> 10:00  48   5.932   2.938  2.019        -inf         inf unbounded (denominator not significant)     2.520    -2.920     6.957        0.724  1.817
              Fri->Mon (weekend) (window) daily open -> 09:15  46   2.497  25.875  0.097      -0.162       1.103                                 bounded     0.158    -0.213     0.406        2.468  0.690
              Fri->Mon (weekend) (window) daily open -> 09:30  46  22.660  25.875  0.876      -0.376       1.236                                 bounded     0.208     0.468     1.284        2.468  1.772
              Fri->Mon (weekend) (window) daily open -> 10:00  46  23.936  25.875  0.925       0.067       1.321                                 bounded     0.181     0.571     1.279        2.468  1.998

## Pre-registered reads (as written)
- W1: Wednesday is special if Wed->Thu dbasis minus the other weekdays is negative with |t| > 2 post-2022-08-25 and still |t| > 2 excluding roll and near-expiry nights. Otherwise the Wednesday 'puzzle' is a uniform post-2022 basis shortfall.
- W2: Monday is special if Mon->Tue minus others is positive with |t| > 2 under the same two conditions.
- T1 (mechanical timing): holds if, post-2022-08-25, the 09:00->09:30 basis change recovers >= 50% of the mean overnight basis shortfall, with a CI excluding zero. T2 (systematic offset): holds if recovery is < 25% or the CI includes zero while the shortfall is significant. Between 25% and 50% is ambiguous.
- O1: offset in the daily fit, a is significantly negative (|t| > 2) post-2022-08-25.
- Between thresholds = ambiguous. Bonferroni: 5 weekday cells x 3 periods x 2 variables = 30 'minus others' cells -> |t| ~3.1.

## Verdicts
[all days] W1 DOES NOT HOLD: Wed->Thu minus others -1.79 bp (t -0.65); ex roll/near-expiry 0.10 bp (t 0.03, n 159).
[all days] W2 DOES NOT HOLD: Mon->Tue minus others 1.76 bp (t 0.67); ex roll/near-expiry 1.68 bp (t 0.61, n 206).
[ex index-flagged] W1 DOES NOT HOLD: Wed->Thu minus others -1.53 bp (t -0.55); ex roll/near-expiry 0.49 bp (t 0.15, n 158).
[ex index-flagged] W2 DOES NOT HOLD: Mon->Tue minus others 1.72 bp (t 0.65); ex roll/near-expiry 1.68 bp (t 0.61, n 206).
[all days] O1 HOLDS: post-2022-08-25 a = -3.22 bp (NW t -2.40), k = 0.820 (SE 0.063; t vs 1 -2.84), n 1026.
[ex index-flagged] O1 HOLDS: post-2022-08-25 a = -3.17 bp (NW t -2.36), k = 0.820 (SE 0.063; t vs 1 -2.84), n 1022.
T1/T2 [window 2025-11-24..2026-11-17, n 244, NOT the full post-2022-08-25 period]: T2 HOLDS as written (CI includes zero while the shortfall is significant). Shortfall -dbasis_ON 6.45 bp (NW t 2.75); basis change daily open -> 09:30 3.94 bp (t 1.63); recovery point estimate 61%, Fieller 95% CI -29% .. 117% (contains 0 because |t_num| < 1.96; the delta-method CI 11%..111% understates the uncertainty near zero and is not used). The point estimate is above 50%, so the evidence leans toward a transient shortfall but is not conclusive on one year of data. MECHANISM (point estimates): the movement is mostly on the INDEX side after its 09:15 open (index leg 09:15->09:30 -6.26 bp, t -1.91) rather than futures catching up (futures leg 09:00->09:30 -2.26 bp, t -1.05); on matched clocks at 09:15 the shortfall is unchanged. The post-open index move does not scale with the overnight gap (corr(idx_ON, index 09:15->09:30) = 0.055, slope 0.061), so it looks more like a roughly constant post-open index drift than a gap-proportional overshoot or a futures lag.

## Notes
- 1a: the 2023 gap (9.86 -> 11.08 bp) is entirely the 24 index nights around the 12 2023 roll days that are MISSING from data/raw/VN30F1M.csv (the first trading day after each 3rd-Thursday expiry is absent for 14 consecutive months, 2022-11 .. 2023-12; the VCI 1m feed omits the same days). Each missing day removes the index Thu->Fri night (no futures bar) and makes the next Monday misaligned (futures night spans Thu close -> Mon open, including Friday's session and a contract change). Those futures-only nights remain in level_c_futures.build() as 'holiday' nights (e.g. 2023-08-21 fut ON -506 bp); they do not enter Monday statistics. Including 2021-05-04 (VN30F1M.csv also lacks 2021-04-29), the 15 nights whose prior futures day is missing sum to -1,061 bp of simple futures ON, i.e. -0.46 bp on the 2,284-night all-nights futures mean (4.99 bp with them, 5.49 bp without). Reported only; existing files were not changed.
- 2.x gate: the 12 nights where the 09:00 bar open differs from the daily open are 5 days with stray pre-09:00 prints (the daily open is the first stray print), 5 days with no 09:00 bar (dropped, no fill possible) and 2 days with a 0.1-0.8 point difference; mean difference 0.03 bp.
- The weekday HAC t-stats differ from futures_basis_decomp Table B because lags here run over consecutive nights, not consecutive same-weekday nights.
