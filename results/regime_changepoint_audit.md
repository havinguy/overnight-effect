# Regime change-point audit

Read-only on data/raw/ and results/. Script: `src/regime_changepoint_audit.py`; rules S1-S5 pre-registered in the script header before the first run.

Sample: regime_legs_audit sample (one-day nights, common CW basket / futures dates), n = 1559, 2018-11-22..2026-11-17; EW basket present on all of them. Reproduction gate passed: the plain split at 2022-08-25 gives t = 3.77 (CW ON), -2.62 (CW ID), 0.59 (FUT ON), 5.02 (paired), identical to regime_legs_breaks.csv. Break t = (post - pre mean) / hypot(NW SEs), lag 5. 2022-08-25 = night #739 of 1559.

## 1. Change-point scan (single mean shift, 15% trimming)

1092 candidate dates 2020-02-06..2025-09-12. Best-fit = LS break; sup|t| = max NW break t over candidates; p_boot from a circular block bootstrap of the demeaned series (block 10, B 999), Holm across the 6 series. Date interval: residual block bootstrap around the LS break (B 999), 2.5-97.5%. rank_of_cut_abs_t = rank of |t| at 2022-08-25 among all 1092 candidates. Report-only iid-Gaussian 5% critical value for sup|t|: 2.95. t and break size at every candidate date: `results/regime_changepoint_scan.csv`.

```
          series    ls_date  ls_break_bp  t_at_ls  supt_date  sup_abs_t  boot_crit95  p_boot  p_holm      ci_lo      ci_hi  ci_width_nights  cut_inside  t_at_cut_pointwise  rank_of_cut_abs_t                          interval
           CW ON 2022-11-25       16.707    4.544 2022-11-25      4.544        3.150   0.002   0.012 2021-04-09 2024-08-20              649        True               3.766                147                       informative
           CW ID 2022-08-26      -13.295   -2.658 2022-08-26      2.658        2.871   0.084   0.168 2020-06-04 2025-06-18              979        True              -2.619                  6 UNINFORMATIVE (no detected break)
           EW ON 2022-11-25       18.540    4.915 2022-11-25      4.915        3.234   0.002   0.012 2021-09-01 2024-03-20              490        True               4.099                128                       informative
           EW ID 2022-08-26      -17.366   -3.560 2022-08-26      3.560        2.878   0.006   0.018 2020-12-30 2024-11-20              752        True              -3.517                  7                       informative
          FUT ON 2020-03-17        9.128    2.097 2020-03-20      2.136        2.889   0.309   0.309 2020-02-06 2025-06-03             1034        True               0.594                693 UNINFORMATIVE (no detected break)
PAIRED CW-FUT ON 2022-12-07       14.090    5.770 2022-12-07      5.770        3.455   0.002   0.012 2022-03-25 2024-05-29              414        True               5.018                101                       informative
```

- CW ON: LS break 2022-11-25 (+16.71 bp), sup|t| 4.54 at 2022-11-25 vs bootstrap 5% critical 3.15 (p 0.002, Holm 0.012); 95% date interval 2021-04-09..2024-08-20 (649 nights) -> 2022-08-25 INSIDE. Pointwise t at 2022-08-25 3.77 (rank 147/1092).
- CW ID: LS break 2022-08-26 (-13.29 bp), sup|t| 2.66 at 2022-08-26 vs bootstrap 5% critical 2.87 (p 0.084, Holm 0.168); 95% date interval 2020-06-04..2025-06-18 (979 nights) -> 2022-08-25 INSIDE; NO DETECTED BREAK, interval uninformative. Pointwise t at 2022-08-25 -2.62 (rank 6/1092).
- EW ON: LS break 2022-11-25 (+18.54 bp), sup|t| 4.92 at 2022-11-25 vs bootstrap 5% critical 3.23 (p 0.002, Holm 0.012); 95% date interval 2021-09-01..2024-03-20 (490 nights) -> 2022-08-25 INSIDE. Pointwise t at 2022-08-25 4.10 (rank 128/1092).
- EW ID: LS break 2022-08-26 (-17.37 bp), sup|t| 3.56 at 2022-08-26 vs bootstrap 5% critical 2.88 (p 0.006, Holm 0.018); 95% date interval 2020-12-30..2024-11-20 (752 nights) -> 2022-08-25 INSIDE. Pointwise t at 2022-08-25 -3.52 (rank 7/1092).
- FUT ON: LS break 2020-03-17 (+9.13 bp), sup|t| 2.14 at 2020-03-20 vs bootstrap 5% critical 2.89 (p 0.309, Holm 0.309); 95% date interval 2020-02-06..2025-06-03 (1034 nights) -> 2022-08-25 INSIDE; NO DETECTED BREAK, interval uninformative. Pointwise t at 2022-08-25 0.59 (rank 693/1092).
- PAIRED CW-FUT ON: LS break 2022-12-07 (+14.09 bp), sup|t| 5.77 at 2022-12-07 vs bootstrap 5% critical 3.46 (p 0.002, Holm 0.012); 95% date interval 2022-03-25..2024-05-29 (414 nights) -> 2022-08-25 INSIDE. Pointwise t at 2022-08-25 5.02 (rank 101/1092).

## 2. Placebo comparison

Primary: local window, 125 one-day nights each side. Random dates (drawn first, seed 20261124, from 488 eligible 2019-2021 nights whose windows end before 2022-08-25): 2019-10-31, 2019-11-14, 2020-01-17, 2020-05-26, 2020-11-04, 2020-12-11, 2021-02-03, 2021-03-05, 2021-11-17, 2021-11-23. The 2022 named dates other than 08-25 have windows that contain the cutover. t_fullsplit is report-only: a pre-cutover split puts the whole post-cutover regime on the 'post' side.

Named-date mapping (first sample night >= date): 2022-07-11 -> 2022-07-12 (07-11 is a Monday open, i.e. a weekend night, not a one-day night); 2022-11-18 -> 2022-11-22: 2022-11-18 is absent from data/raw/VN30F1M.csv (the file regime_legs_audit and this script read), so 11-21 is a 'holiday' hold and 11-18 drops from the common sample. data/raw/VN30F1M_repaired.csv does contain 2022-11-18 (one of 13 inserted post-expiry rows, 2022-11-18..2023-12-22, futures_roll_gap_inserted_rows.csv). Reported, not repaired here: the regime_legs sample (and this one) omits those 13 nights.

```
          series   kind       date   k  window_contains_cut  t_window  break_window_bp  t_fullsplit_reportonly  break_fullsplit_bp
           CW ON  named 2022-07-12 713                 True      0.63             5.95                    3.71               14.05
           CW ON  named 2022-08-25 739                 True      1.25            11.40                    3.77               14.13
           CW ON  named 2022-11-03 777                 True      1.11            10.36                    3.58               13.38
           CW ON  named 2022-11-22 786                 True      3.40            27.29                    4.36               15.94
           CW ON random 2019-10-31 185                False     -0.90           -11.53                    2.89               10.16
           CW ON random 2019-11-14 193                False     -0.84           -10.91                    2.82                9.73
           CW ON random 2020-01-17 228                False     -1.01           -13.16                    2.95                9.49
           CW ON random 2020-05-26 292                False      1.61            21.15                    2.93               17.46
           CW ON random 2020-11-04 383                False     -0.12            -1.14                    2.97               14.66
           CW ON random 2020-12-11 405                False     -0.47            -4.16                    2.85               13.66
           CW ON random 2021-02-03 434                False      0.67             6.16                    3.03               15.06
           CW ON random 2021-03-05 447                False      0.85             7.39                    3.05               14.67
           CW ON random 2021-11-17 586                False     -2.12           -12.75                    2.91               11.89
           CW ON random 2021-11-23 589                False     -2.05           -12.15                    2.88               11.76
           CW ID  named 2022-07-12 713                 True     -1.05           -16.91                   -2.45              -12.35
           CW ID  named 2022-08-25 739                 True     -1.69           -26.69                   -2.62              -13.10
           CW ID  named 2022-11-03 777                 True     -0.18            -2.79                   -1.80               -9.04
           CW ID  named 2022-11-22 786                 True     -0.72           -11.17                   -2.16              -10.74
           CW ID random 2019-10-31 185                False      0.78             8.57                    0.32                1.77
           CW ID random 2019-11-14 193                False      0.66             7.09                    0.38                2.04
           CW ID random 2020-01-17 228                False      1.34            14.27                    0.66                3.53
           CW ID random 2020-05-26 292                False     -0.49            -5.50                   -1.03               -5.95
           CW ID random 2020-11-04 383                False      0.92            13.45                   -1.13               -5.89
           CW ID random 2020-12-11 405                False      0.66            10.05                   -1.40               -7.22
           CW ID random 2021-02-03 434                False     -0.16            -2.21                   -1.68               -9.14
           CW ID random 2021-03-05 447                False     -0.88           -13.06                   -1.84              -10.49
           CW ID random 2021-11-17 586                False     -0.02            -0.28                   -2.14              -11.11
           CW ID random 2021-11-23 589                False      0.44             5.83                   -2.04              -10.62
           EW ON  named 2022-07-12 713                 True      0.81             8.25                    4.06               15.91
           EW ON  named 2022-08-25 739                 True      1.42            14.08                    4.10               15.88
           EW ON  named 2022-11-03 777                 True      1.25            12.79                    3.90               15.01
           EW ON  named 2022-11-22 786                 True      3.61            31.42                    4.76               17.83
           EW ON random 2019-10-31 185                False     -0.78           -10.44                    3.83               13.35
           EW ON random 2019-11-14 193                False     -0.65            -8.82                    3.77               12.93
           EW ON random 2020-01-17 228                False     -0.82           -11.26                    3.98               12.84
           EW ON random 2020-05-26 292                False      1.75            24.05                    3.37               20.70
           EW ON random 2020-11-04 383                False      0.12             1.24                    3.39               17.42
           EW ON random 2020-12-11 405                False     -0.39            -3.86                    3.24               16.17
           EW ON random 2021-02-03 434                False      0.59             6.03                    3.28               17.32
           EW ON random 2021-03-05 447                False      0.64             6.15                    3.25               16.53
           EW ON random 2021-11-17 586                False     -2.09           -13.36                    3.18               13.60
           EW ON random 2021-11-23 589                False     -2.04           -12.88                    3.16               13.47
           EW ID  named 2022-07-12 713                 True     -1.20           -19.67                   -3.23              -15.93
           EW ID  named 2022-08-25 739                 True     -2.02           -32.07                   -3.52              -17.15
           EW ID  named 2022-11-03 777                 True     -0.44            -7.15                   -2.70              -13.20
           EW ID  named 2022-11-22 786                 True     -1.08           -16.81                   -3.11              -15.06
           EW ID random 2019-10-31 185                False      0.53             5.81                   -0.38               -1.95
           EW ID random 2019-11-14 193                False      0.27             2.97                   -0.42               -2.09
           EW ID random 2020-01-17 228                False      1.44            15.87                    0.16                0.84
           EW ID random 2020-05-26 292                False     -0.29            -3.48                   -1.41               -7.97
           EW ID random 2020-11-04 383                False      0.73            10.87                   -1.50               -7.70
           EW ID random 2020-12-11 405                False      0.49             7.37                   -1.81               -9.24
           EW ID random 2021-02-03 434                False     -0.24            -3.21                   -2.09              -11.16
           EW ID random 2021-03-05 447                False     -0.85           -12.41                   -2.17              -12.24
           EW ID random 2021-11-17 586                False      0.13             1.73                   -2.59              -13.22
           EW ID random 2021-11-23 589                False      0.63             8.31                   -2.50              -12.75
          FUT ON  named 2022-07-12 713                 True      0.73             3.89                    0.74                1.95
          FUT ON  named 2022-08-25 739                 True      0.44             2.39                    0.59                1.55
          FUT ON  named 2022-11-03 777                 True      0.08             0.44                    0.62                1.59
          FUT ON  named 2022-11-22 786                 True      1.41             7.25                    1.03                2.65
          FUT ON random 2019-10-31 185                False      0.21             2.09                    1.00                2.95
          FUT ON random 2019-11-14 193                False      0.39             3.87                    1.08                3.11
          FUT ON random 2020-01-17 228                False      0.65             6.55                    1.52                4.05
          FUT ON random 2020-05-26 292                False      0.54             5.36                    0.75                3.26
          FUT ON random 2020-11-04 383                False     -1.04            -8.57                    0.54                1.99
          FUT ON random 2020-12-11 405                False     -0.22            -1.51                    0.50                1.76
          FUT ON random 2021-02-03 434                False      1.24             8.08                    0.81                2.92
          FUT ON random 2021-03-05 447                False      1.10             6.64                    0.64                2.23
          FUT ON random 2021-11-17 586                False     -2.30            -8.15                    0.25                0.71
          FUT ON random 2021-11-23 589                False     -1.95            -7.03                    0.28                0.82
PAIRED CW-FUT ON  named 2022-07-12 713                 True      0.31             2.06                    4.76               12.10
PAIRED CW-FUT ON  named 2022-08-25 739                 True      1.45             9.01                    5.02               12.57
PAIRED CW-FUT ON  named 2022-11-03 777                 True      1.50             9.92                    4.72               11.79
PAIRED CW-FUT ON  named 2022-11-22 786                 True      3.47            20.04                    5.43               13.29
PAIRED CW-FUT ON random 2019-10-31 185                False     -1.56           -13.61                    3.37                7.21
PAIRED CW-FUT ON random 2019-11-14 193                False     -1.70           -14.78                    3.09                6.62
PAIRED CW-FUT ON random 2020-01-17 228                False     -2.29           -19.71                    2.43                5.44
PAIRED CW-FUT ON random 2020-05-26 292                False      1.76            15.79                    3.50               14.19
PAIRED CW-FUT ON random 2020-11-04 383                False      1.02             7.43                    3.77               12.67
PAIRED CW-FUT ON random 2020-12-11 405                False     -0.50            -2.65                    3.66               11.90
PAIRED CW-FUT ON random 2021-02-03 434                False     -0.38            -1.92                    3.82               12.15
PAIRED CW-FUT ON random 2021-03-05 447                False      0.15             0.75                    3.96               12.44
PAIRED CW-FUT ON random 2021-11-17 586                False     -0.89            -4.61                    4.10               11.18
PAIRED CW-FUT ON random 2021-11-23 589                False     -1.01            -5.13                    4.02               10.95
```

Ranking (|t_window| of random dates above the 2022-08-25 value):

```
          series  t_window_cut  n_random_above  max_abs_random  n_random_above_fullsplit_reportonly                                          other_named
           CW ON          1.25               3            2.12                                    0    2022-07-12 0.63, 2022-11-03 1.11, 2022-11-22 3.40
           CW ID         -1.69               0            1.34                                    0 2022-07-12 -1.05, 2022-11-03 -0.18, 2022-11-22 -0.72
           EW ON          1.42               3            2.09                                    0    2022-07-12 0.81, 2022-11-03 1.25, 2022-11-22 3.61
           EW ID         -2.02               0            1.44                                    0 2022-07-12 -1.20, 2022-11-03 -0.44, 2022-11-22 -1.08
          FUT ON          0.44               7            2.30                                    6    2022-07-12 0.73, 2022-11-03 0.08, 2022-11-22 1.41
PAIRED CW-FUT ON          1.45               4            2.29                                    0    2022-07-12 0.31, 2022-11-03 1.50, 2022-11-22 3.47
```

## 3. Sharpness: step vs 3-month linear ramp centred on 2022-08-25

Ramp linear in calendar days 2022-07-11 -> 2022-10-09. Both models 2 parameters; dAIC = AIC_ramp - AIC_step (positive favours the step). Gaussian iid likelihood (caveat: ignores autocorrelation and volatility clustering).

```
          series    n  step_shift_bp  ramp_shift_bp   ssr_step   ssr_ramp  aic_step  aic_ramp  dAIC_ramp_minus_step             verdict  nights_inside_ramp
           CW ON 1559          14.13          14.37 6752699.51 6751701.11  13058.53  13058.29                 -0.23 NOT DISTINGUISHABLE                  50
           EW ON 1559          15.88          16.18 7088780.79 7087169.45  13134.25  13133.89                 -0.35 NOT DISTINGUISHABLE                  50
PAIRED CW-FUT ON 1559          12.57          12.51 2612704.03 2614612.06  11578.17  11579.30                  1.14 NOT DISTINGUISHABLE                  50
```

- CW ON: dAIC -0.23 -> NOT DISTINGUISHABLE. The two models differ only on the 50 nights inside the ramp, out of 1559.

## 4. VNINDEX legs by year (one-day nights, mean bp, NW t)

VCI primary (flagged opens kept); KBS alongside from 2018-11-19. Caveats per year:

- 2012: VCI only, no KBS cross-check
- 2013: VCI only, no KBS cross-check
- 2014: VCI only, no KBS cross-check
- 2015: VCI only, no KBS cross-check
- 2016: VCI only, no KBS cross-check
- 2017: VCI only, no KBS cross-check
- 2018: KBS only from 2018-11-19 (24 nights)
- 2019: -
- 2020: -
- 2021: VCI flat opens 54% (VCI fills open = prior close); KBS flat opens 5.1%
- 2022: -
- 2023: -
- 2024: -
- 2025: KBS flat opens 17%
- 2026: -

```
 year  vci_n  vci_flat  vci_ON_bp  vci_ON_t  vci_ID_bp  vci_ID_t  vci_C2C_bp  vci_C2C_t  kbs_n  kbs_flat  kbs_ON_bp  kbs_ON_t  kbs_ID_bp  kbs_ID_t  kbs_C2C_bp  kbs_C2C_t
 2012    199      0.01       4.51      0.67       0.53      0.07        5.04       0.54      0       NaN        NaN       NaN        NaN       NaN         NaN        NaN
 2013    198      0.06       9.42      3.78      -1.44     -0.20        7.98       1.06      0       NaN        NaN       NaN        NaN       NaN         NaN        NaN
 2014    193      0.01       6.09      1.52       0.43      0.06        6.52       0.88      0       NaN        NaN       NaN        NaN       NaN         NaN        NaN
 2015    196      0.04       0.28      0.08      12.21      1.80       12.49       1.72      0       NaN        NaN       NaN        NaN       NaN         NaN        NaN
 2016    200      0.06       5.58      1.98       5.39      1.09       10.97       1.86      0       NaN        NaN       NaN        NaN       NaN         NaN        NaN
 2017    197      0.04       3.87      2.40      10.01      2.49       13.88       3.34      0       NaN        NaN       NaN        NaN       NaN         NaN        NaN
 2018    197      0.07      -7.58     -1.80       3.85      0.53       -3.73      -0.44     24      0.00     -16.67     -1.41       4.32      0.34      -12.34      -0.85
 2019    198      0.06       1.61      0.72       1.51      0.35        3.12       0.75    198      0.02       3.95      2.21      -0.74     -0.17        3.21       0.77
 2020    197      0.10      -0.09     -0.01      14.70      2.60       14.61       1.70    197      0.02      -0.25     -0.04      14.85      2.60       14.61       1.70
 2021    197      0.54      -0.03     -0.01      16.95      2.10       16.91       2.03    197      0.05       7.77      1.66       9.14      1.12       16.91       2.03
 2022    198      0.08      -5.85     -1.09      10.64      1.20        4.79       0.57    198      0.01      -5.43     -1.16      10.22      1.20        4.79       0.57
 2023    197      0.00      13.08      5.88     -11.12     -1.89        1.96       0.31    197      0.01      10.22      5.17      -8.26     -1.33        1.96       0.31
 2024    196      0.00      12.49      6.27      -2.16     -0.50       10.33       2.15    196      0.00      11.46      6.08      -1.13     -0.26       10.33       2.15
 2025    197      0.00      17.14      2.81      -0.29     -0.05       16.85       2.33    197      0.17      16.84      3.87       0.01      0.00       16.85       2.33
 2026    171      0.01      12.82      2.75      -1.57     -0.23       11.25       1.33    171      0.00      12.80      2.74      -1.55     -0.22       11.25       1.33
```

Check: VCI with flagged (open == prior close) days dropped:

```
 year  vcidrop_ON_bp  vcidrop_ON_t  vcidrop_ID_bp  vcidrop_ID_t  vcidrop_C2C_bp  vcidrop_C2C_t
 2012           4.55          0.67           0.78          0.11            5.34           0.57
 2013           9.97          3.75           2.87          0.46           12.84           1.84
 2014           6.15          1.52           1.24          0.18            7.40           1.00
 2015           0.29          0.08          11.17          1.58           11.46           1.57
 2016           5.94          1.93           6.91          1.40           12.85           2.15
 2017           4.03          2.36           9.39          2.29           13.42           3.14
 2018          -8.16         -1.83           4.50          0.62           -3.66          -0.43
 2019           1.70          0.72          -0.07         -0.02            1.63           0.39
 2020          -0.10         -0.01          21.86          3.71           21.76           2.37
 2021          -0.08         -0.01          22.05          1.50           21.97           1.41
 2022          -6.36         -1.10           9.20          0.98            2.84           0.32
 2023          13.08          5.88         -11.12         -1.89            1.96           0.31
 2024          12.49          6.27          -2.16         -0.50           10.33           2.15
 2025          17.14          2.81          -0.29         -0.05           16.85           2.33
 2026          12.90          2.75          -1.40         -0.20           11.49           1.36
```

Adjacent-year relocation test (R2 verbatim: |t(dC2C)| < 2, t(dON) >= 2, t(dID) <= -2; d = later - earlier):

```
             source                                    pair  dON_bp   tON  dID_bp   tID  dC2C_bp  tC2C  relocation
                VCI                              2012->2013    4.91  0.69   -1.97 -0.20     2.94  0.24       False
                VCI                              2013->2014   -3.33 -0.70    1.86  0.19    -1.47 -0.14       False
                VCI                              2014->2015   -5.81 -1.10   11.78  1.20     5.97  0.57       False
                VCI                              2015->2016    5.30  1.19   -6.82 -0.81    -1.52 -0.16       False
                VCI                              2016->2017   -1.71 -0.53    4.62  0.72     2.91  0.40       False
                VCI                              2017->2018  -11.45 -2.54   -6.16 -0.74   -17.60 -1.87       False
                VCI                              2018->2019    9.19  1.93   -2.34 -0.28     6.85  0.73       False
                VCI                              2019->2020   -1.70 -0.22   13.19  1.86    11.49  1.20       False
                VCI                              2020->2021    0.06  0.01    2.25  0.23     2.31  0.19       False
                VCI                              2021->2022   -5.82 -0.85   -6.31 -0.53   -12.12 -1.02       False
                VCI                              2022->2023   18.93  3.27  -21.76 -2.05    -2.83 -0.27        True
                VCI                              2023->2024   -0.60 -0.20    8.96  1.23     8.37  1.05       False
                VCI                              2024->2025    4.66  0.72    1.87  0.25     6.53  0.75       False
                VCI                              2025->2026   -4.32 -0.56   -1.29 -0.14    -5.61 -0.50       False
                VCI cutover year (report-only) 21/22->22/23   16.25  2.88  -29.16 -2.91   -12.90 -1.30        True
VCI flagged dropped                              2012->2013    5.42  0.75    2.09  0.22     7.50  0.64       False
VCI flagged dropped                              2013->2014   -3.82 -0.79   -1.63 -0.17    -5.45 -0.54       False
VCI flagged dropped                              2014->2015   -5.86 -1.07    9.92  0.99     4.07  0.39       False
VCI flagged dropped                              2015->2016    5.65  1.17   -4.25 -0.49     1.39  0.15       False
VCI flagged dropped                              2016->2017   -1.91 -0.54    2.48  0.39     0.57  0.08       False
VCI flagged dropped                              2017->2018  -12.19 -2.55   -4.89 -0.59   -17.08 -1.81       False
VCI flagged dropped                              2018->2019    9.86  1.96   -4.57 -0.54     5.29  0.56       False
VCI flagged dropped                              2019->2020   -1.81 -0.21   21.93  3.00    20.13  1.99       False
VCI flagged dropped                              2022->2023   19.45  3.13  -20.33 -1.84    -0.88 -0.08       False
VCI flagged dropped                              2023->2024   -0.60 -0.20    8.96  1.23     8.37  1.05       False
VCI flagged dropped                              2024->2025    4.66  0.72    1.87  0.25     6.53  0.75       False
VCI flagged dropped                              2025->2026   -4.24 -0.55   -1.12 -0.12    -5.36 -0.48       False
VCI flagged dropped cutover year (report-only) 21/22->22/23   21.12  2.83  -28.42 -2.22    -7.30 -0.58        True
                KBS                              2019->2020   -4.20 -0.61   15.59  2.18    11.39  1.19       False
                KBS                              2020->2021    8.02  0.99   -5.71 -0.57     2.31  0.19       False
                KBS                              2021->2022  -13.20 -1.99    1.08  0.09   -12.12 -1.02       False
                KBS                              2022->2023   15.65  3.07  -18.48 -1.76    -2.83 -0.27       False
                KBS                              2023->2024    1.24  0.45    7.13  0.94     8.37  1.05       False
                KBS                              2024->2025    5.38  1.14    1.14  0.15     6.53  0.75       False
                KBS                              2025->2026   -4.05 -0.63   -1.56 -0.17    -5.61 -0.50       False
                KBS cutover year (report-only) 21/22->22/23    8.10  1.47  -21.01 -2.09   -12.90 -1.30       False
```

Reading of '2018' and '2023': adjacent calendar years Y-1 vs Y (stated in the header; the project defines no other dates for them). 2023 is AFTER the 2022-08-25 cutover, and 2022 contains about four months of the post-cutover regime, so 2022->2023 straddles the cutover and is not an independent event.

- VCI 2017->2018: dON -11.4 (t -2.54), dID -6.2 (t -0.74), dC2C -17.6 (t -1.87) -> no relocation signature
- VCI flagged dropped 2017->2018: dON -12.2 (t -2.55), dID -4.9 (t -0.59), dC2C -17.1 (t -1.81) -> no relocation signature
- VCI 2022->2023: dON +18.9 (t 3.27), dID -21.8 (t -2.05), dC2C -2.8 (t -0.27) -> RELOCATION
- KBS 2022->2023: dON +15.6 (t 3.07), dID -18.5 (t -1.76), dC2C -2.8 (t -0.27) -> no relocation signature
- Cutover year, report-only: VCI cutover year (report-only) 21/22->22/23: dON +16.3 (t 2.88), dID -29.2 (t -2.91), dC2C -12.9 (t -1.30) -> RELOCATION; KBS cutover year (report-only) 21/22->22/23: dON +8.1 (t 1.47), dID -21.0 (t -2.09), dC2C -12.9 (t -1.30) -> no relocation signature
- Background: relocation signature in KBS 0/7, VCI 1/14, VCI flagged dropped 0/12 adjacent-year pairs; pairs flagged: VCI 2022->2023.

## 5. Basket Mon->Tue overnight (read-out from regime_legs_monday.csv)

Note: in regime_legs_monday.csv the 8.05 bp basket figure is the **2018-11..2021** row, not 2018-11..2022-08-24. Both rows are shown; recomputed values equal the CSV exactly.

```
        window  csv_basket_mon_bp  csv_basket_mon_t  n_mon  other_nights_bp  other_nights_t  n_other  mon_minus_other_bp  mon_minus_other_t  lo95  hi95  distinguishable  all_nights_bp  all_nights_t  onesample_vs_allmean_t_reportonly
 2018-11..2021               8.05              1.31    154            -2.27           -0.64      459               10.32               1.45 -3.63 24.26            False           0.32          0.10                               1.25
pre 2022-08-25               2.86              0.50    184            -1.84           -0.60      555                4.70               0.72 -8.11 17.50            False          -0.67         -0.23                               0.61
```

- 2018-11-21..2022-08-24: basket Mon->Tue 2.86 bp (t 0.50, n 184); minus other one-day nights +4.70 bp (t 0.72) -> NOT distinguishable. All-night mean -0.67 bp.
- 2018-11..2021: basket Mon->Tue 8.05 bp (t 1.31, n 154); minus other nights +10.32 bp (t 1.45) -> NOT distinguishable.

Caveats: pre-2022-06 futures opens unverified; one-day nights only; stock flat opens kept; VNINDEX opens per the caveat list.

Rerun 1: text only (summary wording, date-mapping note, scan-CSV pointer); statistics and seeds unchanged, CSV md5 identical to run 0 (checked outside the script).

Integrity: md5 of every pre-existing file in data/raw/, data/raw_kbs_index/ and results/ identical before and after: True (172 files).

## Summary (5 lines)

1. Break date: CW ON LS break 2022-11-25, 95% interval 2021-04-09..2024-08-20 (649 nights; 2022-08-25 inside, but the interval does not single it out: cutover |t| ranks 147/1092); sup|t| 4.54 vs block-bootstrap 5% critical 3.15 (Holm p 0.012). ON legs: LS dates 2022-11-25 (CW), 2022-11-25 (EW), paired 2022-12-07; ID legs: LS date 2022-08-26 (CW, rank of cutover 6) and 2022-08-26 (EW, rank 7). Holm p < 0.05: CW ON, EW ON, EW ID, PAIRED CW-FUT ON; not detected (interval uninformative): CW ID, FUT ON.
2. Placebo (±125 nights, local window): random 2019-21 dates with |t| above the 08-25 value: CW ON 3/10, CW ID 0/10, EW ON 3/10, EW ID 0/10, FUT ON 7/10, PAIRED CW-FUT ON 4/10; CW ON t at 08-25 only 1.25 (max random 2.12) vs 3.40 at the 2022-11-18 named date (mapped to 2022-11-22).
3. Sharpness (CW ON): dAIC ramp - step -0.23 -> NOT DISTINGUISHABLE; EW ON -0.35, paired +1.14 (50 nights inside the ramp).
4. Earlier relocations (VNINDEX, R2 rule, Y-1 vs Y): 2017->2018 no - ON FELL (-11.4 bp, t -2.54), the opposite direction; 2022->2023 NOT ROBUST: R2 met only in VCI with flagged opens kept (dID t -2.05), not with flagged dropped (t -1.84) or KBS (t -1.76); ON up (t > 3) and C2C flat in all three. 2022->2023 straddles the cutover, so it is not an independent event; background KBS 0/7, VCI 1/14, VCI flagged dropped 0/12 adjacent pairs.
5. Monday basket: 2018-11-21..2022-08-24 Mon->Tue 2.86 bp (t 0.50), minus other nights +4.70 (t 0.72) -> not distinguishable; the 8.05 bp figure is the 2018-11..2021 row (t 1.31; vs other nights t 1.45).
