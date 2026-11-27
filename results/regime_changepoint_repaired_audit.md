# Regime change-point audit

Read-only on data/raw/ and results/. Script: `src/regime_changepoint_audit.py`; rules S1-S5 pre-registered in the script header before the first run.

Sample: regime_legs_audit sample (one-day nights, common CW basket / futures dates), n = 1573, 2018-11-21..2026-11-17; EW basket present on all of them. VARIANT RUN, futures input VN30F1M_repaired (frozen). Reproduction gate NOT APPLIED (different input); plain split at 2022-08-25 gives t = 3.71 (CW ON), -2.78 (CW ID), 0.48 (FUT ON), 5.05 (paired), vs regime_legs_breaks.csv (original input): see regime_changepoint_repaired_compare.md. Break t = (post - pre mean) / hypot(NW SEs), lag 5. 2022-08-25 = night #740 of 1573.

## 1. Change-point scan (single mean shift, 15% trimming)

1102 candidate dates 2020-02-07..2025-09-10. Best-fit = LS break; sup|t| = max NW break t over candidates; p_boot from a circular block bootstrap of the demeaned series (block 10, B 999), Holm across the 6 series. Date interval: residual block bootstrap around the LS break (B 999), 2.5-97.5%. rank_of_cut_abs_t = rank of |t| at 2022-08-25 among all 1102 candidates. Report-only iid-Gaussian 5% critical value for sup|t|: 2.93. t and break size at every candidate date: `results/regime_changepoint_repaired_scan.csv`.

```
          series    ls_date  ls_break_bp  t_at_ls  supt_date  sup_abs_t  boot_crit95  p_boot  p_holm      ci_lo      ci_hi  ci_width_nights  cut_inside  t_at_cut_pointwise  rank_of_cut_abs_t                          interval
           CW ON 2022-11-25       16.554    4.522 2022-11-25      4.522        3.332   0.003   0.012 2021-06-30 2024-10-29              659        True               3.714                162                       informative
           CW ID 2022-08-26      -14.124   -2.820 2022-08-26      2.820        2.860   0.053   0.106 2020-05-21 2025-03-19              952        True              -2.782                  6 UNINFORMATIVE (no detected break)
           EW ON 2022-11-25       18.451    4.907 2022-11-25      4.907        3.257   0.001   0.006 2021-11-10 2024-03-19              464        True               4.053                145                       informative
           EW ID 2022-08-26      -18.197   -3.725 2022-08-26      3.725        2.959   0.004   0.012 2020-11-17 2024-08-28              744        True              -3.683                  8                       informative
          FUT ON 2020-03-17        9.106    2.096 2020-03-20      2.134        2.972   0.327   0.327 2020-02-07 2025-04-24             1027        True               0.480                833 UNINFORMATIVE (no detected break)
PAIRED CW-FUT ON 2022-12-07       14.178    5.824 2022-12-07      5.824        3.438   0.001   0.006 2021-12-08 2023-12-19              402        True               5.051                 98                       informative
```

- CW ON: LS break 2022-11-25 (+16.55 bp), sup|t| 4.52 at 2022-11-25 vs bootstrap 5% critical 3.33 (p 0.003, Holm 0.012); 95% date interval 2021-06-30..2024-10-29 (659 nights) -> 2022-08-25 INSIDE. Pointwise t at 2022-08-25 3.71 (rank 162/1102).
- CW ID: LS break 2022-08-26 (-14.12 bp), sup|t| 2.82 at 2022-08-26 vs bootstrap 5% critical 2.86 (p 0.053, Holm 0.106); 95% date interval 2020-05-21..2025-03-19 (952 nights) -> 2022-08-25 INSIDE; NO DETECTED BREAK, interval uninformative. Pointwise t at 2022-08-25 -2.78 (rank 6/1102).
- EW ON: LS break 2022-11-25 (+18.45 bp), sup|t| 4.91 at 2022-11-25 vs bootstrap 5% critical 3.26 (p 0.001, Holm 0.006); 95% date interval 2021-11-10..2024-03-19 (464 nights) -> 2022-08-25 INSIDE. Pointwise t at 2022-08-25 4.05 (rank 145/1102).
- EW ID: LS break 2022-08-26 (-18.20 bp), sup|t| 3.73 at 2022-08-26 vs bootstrap 5% critical 2.96 (p 0.004, Holm 0.012); 95% date interval 2020-11-17..2024-08-28 (744 nights) -> 2022-08-25 INSIDE. Pointwise t at 2022-08-25 -3.68 (rank 8/1102).
- FUT ON: LS break 2020-03-17 (+9.11 bp), sup|t| 2.13 at 2020-03-20 vs bootstrap 5% critical 2.97 (p 0.327, Holm 0.327); 95% date interval 2020-02-07..2025-04-24 (1027 nights) -> 2022-08-25 INSIDE; NO DETECTED BREAK, interval uninformative. Pointwise t at 2022-08-25 0.48 (rank 833/1102).
- PAIRED CW-FUT ON: LS break 2022-12-07 (+14.18 bp), sup|t| 5.82 at 2022-12-07 vs bootstrap 5% critical 3.44 (p 0.001, Holm 0.006); 95% date interval 2021-12-08..2023-12-19 (402 nights) -> 2022-08-25 INSIDE. Pointwise t at 2022-08-25 5.05 (rank 98/1102).

## 2. Placebo comparison

Primary: local window, 125 one-day nights each side. Random dates (drawn first, seed 20261124, from 489 eligible 2019-2021 nights whose windows end before 2022-08-25): 2019-10-31, 2019-11-13, 2020-01-17, 2020-05-22, 2020-11-04, 2020-12-11, 2021-02-03, 2021-03-05, 2021-11-17, 2021-11-23. The 2022 named dates other than 08-25 have windows that contain the cutover. t_fullsplit is report-only: a pre-cutover split puts the whole post-cutover regime on the 'post' side.

Named-date mapping (first sample night >= date): 2022-07-11 -> 2022-07-12 (07-11 is a Monday open, i.e. a weekend night, not a one-day night); 2022-11-18 -> 2022-11-22: 2022-11-18 is absent from data/raw/VN30F1M.csv (the file regime_legs_audit and this script read), so 11-21 is a 'holiday' hold and 11-18 drops from the common sample. data/raw/VN30F1M_repaired.csv does contain 2022-11-18 (one of 13 inserted post-expiry rows, 2022-11-18..2023-12-22, futures_roll_gap_inserted_rows.csv). Reported, not repaired here: the regime_legs sample (and this one) omits those 13 nights.

```
          series   kind       date   k  window_contains_cut  t_window  break_window_bp  t_fullsplit_reportonly  break_fullsplit_bp
           CW ON  named 2022-07-12 714                 True      0.60             5.58                    3.66               13.82
           CW ON  named 2022-08-25 740                 True      1.12            10.27                    3.71               13.88
           CW ON  named 2022-11-03 778                 True      1.04             9.82                    3.53               13.11
           CW ON  named 2022-11-18 787                 True      3.24            26.30                    4.29               15.63
           CW ON random 2019-10-31 186                False     -0.90           -11.53                    3.02               10.58
           CW ON random 2019-11-13 193                False     -0.84           -10.81                    2.95               10.18
           CW ON random 2020-01-17 229                False     -1.01           -13.16                    3.06                9.79
           CW ON random 2020-05-22 292                False      1.51            19.80                    2.90               17.32
           CW ON random 2020-11-04 384                False     -0.12            -1.14                    2.99               14.70
           CW ON random 2020-12-11 406                False     -0.47            -4.16                    2.87               13.68
           CW ON random 2021-02-03 435                False      0.67             6.16                    3.03               15.05
           CW ON random 2021-03-05 448                False      0.85             7.39                    3.05               14.64
           CW ON random 2021-11-17 587                False     -2.12           -12.75                    2.89               11.77
           CW ON random 2021-11-23 590                False     -2.05           -12.15                    2.86               11.64
           CW ID  named 2022-07-12 714                 True     -1.04           -16.84                   -2.61              -13.18
           CW ID  named 2022-08-25 740                 True     -1.56           -24.28                   -2.78              -13.93
           CW ID  named 2022-11-03 778                 True     -0.16            -2.58                   -1.97               -9.92
           CW ID  named 2022-11-18 787                 True     -0.81           -12.63                   -2.32              -11.61
           CW ID random 2019-10-31 186                False      0.78             8.57                    0.08                0.46
           CW ID random 2019-11-13 193                False      0.55             5.93                    0.04                0.23
           CW ID random 2020-01-17 229                False      1.34            14.27                    0.44                2.36
           CW ID random 2020-05-22 292                False     -0.70            -8.01                   -1.26               -7.29
           CW ID random 2020-11-04 384                False      0.92            13.45                   -1.30               -6.79
           CW ID random 2020-12-11 406                False      0.66            10.05                   -1.57               -8.10
           CW ID random 2021-02-03 435                False     -0.16            -2.21                   -1.84               -9.99
           CW ID random 2021-03-05 448                False     -0.88           -13.06                   -1.98              -11.33
           CW ID random 2021-11-17 587                False     -0.02            -0.28                   -2.29              -11.92
           CW ID random 2021-11-23 590                False      0.44             5.83                   -2.20              -11.44
           EW ON  named 2022-07-12 714                 True      0.71             7.27                    4.02               15.71
           EW ON  named 2022-08-25 740                 True      1.27            12.61                    4.05               15.66
           EW ON  named 2022-11-03 778                 True      1.16            11.96                    3.85               14.76
           EW ON  named 2022-11-18 787                 True      3.42            30.19                    4.69               17.55
           EW ON random 2019-10-31 186                False     -0.78           -10.44                    3.96               13.84
           EW ON random 2019-11-13 193                False     -0.64            -8.68                    3.92               13.47
           EW ON random 2020-01-17 229                False     -0.82           -11.26                    4.09               13.20
           EW ON random 2020-05-22 292                False      1.63            22.48                    3.34               20.56
           EW ON random 2020-11-04 384                False      0.12             1.24                    3.42               17.50
           EW ON random 2020-12-11 406                False     -0.39            -3.86                    3.26               16.24
           EW ON random 2021-02-03 435                False      0.59             6.03                    3.29               17.35
           EW ON random 2021-03-05 448                False      0.64             6.15                    3.26               16.55
           EW ON random 2021-11-17 587                False     -2.09           -13.36                    3.17               13.52
           EW ON random 2021-11-23 590                False     -2.04           -12.88                    3.15               13.38
           EW ID  named 2022-07-12 714                 True     -1.19           -19.52                   -3.39              -16.76
           EW ID  named 2022-08-25 740                 True     -1.85           -28.99                   -3.68              -17.99
           EW ID  named 2022-11-03 778                 True     -0.42            -6.77                   -2.87              -14.08
           EW ID  named 2022-11-18 787                 True     -1.14           -17.77                   -3.27              -15.92
           EW ID random 2019-10-31 186                False      0.53             5.81                   -0.66               -3.32
           EW ID random 2019-11-13 193                False      0.17             1.85                   -0.78               -3.84
           EW ID random 2020-01-17 229                False      1.44            15.87                   -0.07               -0.38
           EW ID random 2020-05-22 292                False     -0.47            -5.61                   -1.66               -9.38
           EW ID random 2020-11-04 384                False      0.73            10.87                   -1.68               -8.63
           EW ID random 2020-12-11 406                False      0.49             7.37                   -1.99              -10.15
           EW ID random 2021-02-03 435                False     -0.24            -3.21                   -2.26              -12.04
           EW ID random 2021-03-05 448                False     -0.85           -12.41                   -2.33              -13.11
           EW ID random 2021-11-17 587                False      0.13             1.73                   -2.76              -14.06
           EW ID random 2021-11-23 590                False      0.63             8.31                   -2.66              -13.59
          FUT ON  named 2022-07-12 714                 True      0.36             1.93                    0.63                1.67
          FUT ON  named 2022-08-25 740                 True      0.14             0.79                    0.48                1.26
          FUT ON  named 2022-11-03 778                 True     -0.09            -0.50                    0.49                1.27
          FUT ON  named 2022-11-18 787                 True      1.05             5.55                    0.90                2.32
          FUT ON random 2019-10-31 186                False      0.21             2.09                    1.03                3.07
          FUT ON random 2019-11-13 193                False      0.34             3.30                    1.07                3.10
          FUT ON random 2020-01-17 229                False      0.65             6.55                    1.53                4.09
          FUT ON random 2020-05-22 292                False      0.59             5.85                    0.77                3.38
          FUT ON random 2020-11-04 384                False     -1.04            -8.57                    0.51                1.90
          FUT ON random 2020-12-11 406                False     -0.22            -1.51                    0.46                1.65
          FUT ON random 2021-02-03 435                False      1.24             8.08                    0.77                2.78
          FUT ON random 2021-03-05 448                False      1.10             6.64                    0.60                2.09
          FUT ON random 2021-11-17 587                False     -2.30            -8.15                    0.17                0.51
          FUT ON random 2021-11-23 590                False     -1.95            -7.03                    0.21                0.61
PAIRED CW-FUT ON  named 2022-07-12 714                 True      0.54             3.66                    4.80               12.15
PAIRED CW-FUT ON  named 2022-08-25 740                 True      1.50             9.48                    5.05               12.62
PAIRED CW-FUT ON  named 2022-11-03 778                 True      1.54            10.32                    4.75               11.84
PAIRED CW-FUT ON  named 2022-11-18 787                 True      3.47            20.74                    5.44               13.32
PAIRED CW-FUT ON random 2019-10-31 186                False     -1.56           -13.61                    3.57                7.51
PAIRED CW-FUT ON random 2019-11-13 193                False     -1.62           -14.11                    3.37                7.08
PAIRED CW-FUT ON random 2020-01-17 229                False     -2.29           -19.71                    2.57                5.70
PAIRED CW-FUT ON random 2020-05-22 292                False      1.54            13.95                    3.46               13.94
PAIRED CW-FUT ON random 2020-11-04 384                False      1.02             7.43                    3.83               12.81
PAIRED CW-FUT ON random 2020-12-11 406                False     -0.50            -2.65                    3.72               12.03
PAIRED CW-FUT ON random 2021-02-03 435                False     -0.38            -1.92                    3.87               12.27
PAIRED CW-FUT ON random 2021-03-05 448                False      0.15             0.75                    4.01               12.55
PAIRED CW-FUT ON random 2021-11-17 587                False     -0.89            -4.61                    4.14               11.27
PAIRED CW-FUT ON random 2021-11-23 590                False     -1.01            -5.13                    4.06               11.04
```

Ranking (|t_window| of random dates above the 2022-08-25 value):

```
          series  t_window_cut  n_random_above  max_abs_random  n_random_above_fullsplit_reportonly                                          other_named
           CW ON          1.12               3            2.12                                    0    2022-07-12 0.60, 2022-11-03 1.04, 2022-11-18 3.24
           CW ID         -1.56               0            1.34                                    0 2022-07-12 -1.04, 2022-11-03 -0.16, 2022-11-18 -0.81
           EW ON          1.27               3            2.09                                    1    2022-07-12 0.71, 2022-11-03 1.16, 2022-11-18 3.42
           EW ID         -1.85               0            1.44                                    0 2022-07-12 -1.19, 2022-11-03 -0.42, 2022-11-18 -1.14
          FUT ON          0.14              10            2.30                                    7   2022-07-12 0.36, 2022-11-03 -0.09, 2022-11-18 1.05
PAIRED CW-FUT ON          1.50               4            2.29                                    0    2022-07-12 0.54, 2022-11-03 1.54, 2022-11-18 3.47
```

## 3. Sharpness: step vs 3-month linear ramp centred on 2022-08-25

Ramp linear in calendar days 2022-07-11 -> 2022-10-09. Both models 2 parameters; dAIC = AIC_ramp - AIC_step (positive favours the step). Gaussian iid likelihood (caveat: ignores autocorrelation and volatility clustering).

```
          series    n  step_shift_bp  ramp_shift_bp   ssr_step   ssr_ramp  aic_step  aic_ramp  dAIC_ramp_minus_step             verdict  nights_inside_ramp
           CW ON 1573          13.88          14.11 6814992.29 6814036.46  13176.14  13175.92                 -0.22 NOT DISTINGUISHABLE                  50
           EW ON 1573          15.66          15.95 7156770.15 7155205.17  13253.11  13252.77                 -0.34 NOT DISTINGUISHABLE                  50
PAIRED CW-FUT ON 1573          12.62          12.56 2636545.71 2638455.43  11682.33  11683.47                  1.14 NOT DISTINGUISHABLE                  50
```

- CW ON: dAIC -0.22 -> NOT DISTINGUISHABLE. The two models differ only on the 50 nights inside the ramp, out of 1573.

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
 2018-11..2021               8.05              1.31    154            -2.51           -0.71      460               10.56               1.49 -3.38 24.50            False           0.14          0.04                               1.28
pre 2022-08-25               2.86              0.50    184            -2.04           -0.67      556                4.90               0.75 -7.91 17.70            False          -0.82         -0.28                               0.64
```

- 2018-11-21..2022-08-24: basket Mon->Tue 2.86 bp (t 0.50, n 184); minus other one-day nights +4.90 bp (t 0.75) -> NOT distinguishable. All-night mean -0.82 bp.
- 2018-11..2021: basket Mon->Tue 8.05 bp (t 1.31, n 154); minus other nights +10.56 bp (t 1.49) -> NOT distinguishable.

Caveats: pre-2022-06 futures opens unverified; one-day nights only; stock flat opens kept; VNINDEX opens per the caveat list.

Variant of regime_changepoint_audit.py: only the futures input changed (see src/regime_changepoint_repaired.py for the exact substitutions).

Integrity: md5 of every pre-existing file in data/raw/, data/raw_kbs_index/ and results/ identical before and after: True (252 files).

## Summary (5 lines)

1. Break date: CW ON LS break 2022-11-25, 95% interval 2021-06-30..2024-10-29 (659 nights; 2022-08-25 inside, but the interval does not single it out: cutover |t| ranks 162/1102); sup|t| 4.52 vs block-bootstrap 5% critical 3.33 (Holm p 0.012). ON legs: LS dates 2022-11-25 (CW), 2022-11-25 (EW), paired 2022-12-07; ID legs: LS date 2022-08-26 (CW, rank of cutover 6) and 2022-08-26 (EW, rank 8). Holm p < 0.05: CW ON, EW ON, EW ID, PAIRED CW-FUT ON; not detected (interval uninformative): CW ID, FUT ON.
2. Placebo (±125 nights, local window): random 2019-21 dates with |t| above the 08-25 value: CW ON 3/10, CW ID 0/10, EW ON 3/10, EW ID 0/10, FUT ON 10/10, PAIRED CW-FUT ON 4/10; CW ON t at 08-25 only 1.12 (max random 2.12) vs 3.24 at the 2022-11-18 named date (mapped to 2022-11-18).
3. Sharpness (CW ON): dAIC ramp - step -0.22 -> NOT DISTINGUISHABLE; EW ON -0.34, paired +1.14 (50 nights inside the ramp).
4. Earlier relocations (VNINDEX, R2 rule, Y-1 vs Y): 2017->2018 no - ON FELL (-11.4 bp, t -2.54), the opposite direction; 2022->2023 NOT ROBUST: R2 met only in VCI with flagged opens kept (dID t -2.05), not with flagged dropped (t -1.84) or KBS (t -1.76); ON up (t > 3) and C2C flat in all three. 2022->2023 straddles the cutover, so it is not an independent event; background KBS 0/7, VCI 1/14, VCI flagged dropped 0/12 adjacent pairs.
5. Monday basket: 2018-11-21..2022-08-24 Mon->Tue 2.86 bp (t 0.50), minus other nights +4.90 (t 0.75) -> not distinguishable; the 8.05 bp figure is the 2018-11..2021 row (t 1.31; vs other nights t 1.49).
