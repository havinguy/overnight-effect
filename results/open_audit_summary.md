# Open-filter audit (Phase 1, Levels A + B): measurement only

## Step 0: reproduction gate
Pass criterion: every return statistic (n, means, Sharpe, t, flag share) within 1e-8 of the saved file, using the original script's own convention.
  level                                 file                                                                                     convention  rows  max_abs_diff  reproduced
      A                  level_a_summary.csv                                         all nights, exclude_suspicious=False, exclude_years=[]    12          0.00        True
      A            level_a_summary_clean.csv                                          all nights, exclude_suspicious=True, exclude_years=[]    12          0.00        True
      A           level_a_summary_ex2021.csv                                     all nights, exclude_suspicious=False, exclude_years=[2021]    12          0.00        True
      A     level_a_summary_ex2021_clean.csv                                      all nights, exclude_suspicious=True, exclude_years=[2021]    12          0.00        True
      B            level_b_cross_section.csv     all nights per stock, exclude_suspicious=False, exclude_years=[], exclude_large_gaps=False    30          0.00        True
      B      level_b_cross_section_clean.csv      all nights per stock, exclude_suspicious=True, exclude_years=[], exclude_large_gaps=False    30          0.00        True
      B     level_b_cross_section_ex2021.csv all nights per stock, exclude_suspicious=False, exclude_years=[2021], exclude_large_gaps=False    30          0.00        True
      B level_b_cross_section_nolargegap.csv      all nights per stock, exclude_suspicious=False, exclude_years=[], exclude_large_gaps=True    30          0.00        True
PIT 2x2    pit_dayofweek_2x2.csv [pit_ew, B]                                       one-day nights, open_suspicious & |ON|>7% dropped, k>=10     5          0.00        True
PIT 2x2   pit_dayofweek_2x2.csv [pit_cap, B]                                       one-day nights, open_suspicious & |ON|>7% dropped, k>=10     5          0.00        True
- level_b_cross_section_ex2021.csv: return stats exact; diagnostic count n_gap_gt_limit differs by up to 4: file (2026-11-18 03:47) predates the last edit of src/level_b.py (2026-11-18 03:53), which counts gaps before the year exclusion

## Step 1: benchmark (published VN30 overnight, one-day nights; index-flagged opens dropped)
pit_dayofweek_2x2.py DID apply open_suspicious: `flag = open_suspicious | |r_overnight| > 7%`, nights kept only if gap == 1 and not flagged.
Note the 7% rule is asymmetric in log terms: a limit-down open is ln(0.93) = -7.26% (dropped), a limit-up open ln(1.07) = +6.77% (kept).

Mean absolute weekday difference, basket minus index (bp):
version    a    b    c
scheme                
cap     3.90 2.22 2.20
ew      3.87 2.08 2.04

All-nights mean difference (bp):
version    a    b     c
scheme                 
cap     3.80 0.83  0.07
ew      3.85 0.89 -0.26

Correlation with index overnight (all nights):
version    a    b    c
scheme                
cap     0.78 0.78 0.77
ew      0.76 0.76 0.75

Basket level by weekday (bp); index (cap a rows' dates): Mon->Tue 8.54, Tue->Wed 8.17, Wed->Thu 7.23, Thu->Fri 2.17
version             a     b     c
scheme group                     
cap    Mon->Tue 16.61 12.98 12.53
       Thu->Fri  2.00 -0.58 -1.92
       Tue->Wed 11.85  8.71  8.02
       Wed->Thu 10.89  8.32  7.77
ew     Mon->Tue 15.11 11.74 10.93
       Thu->Fri  2.45 -0.18 -1.98
       Tue->Wed 11.90  8.76  7.75
       Wed->Thu 12.11  9.35  8.38

Basket minus index by weekday (bp):
version             a     b     c
scheme group                     
cap    Mon->Tue  8.08  4.48  4.03
       Thu->Fri -0.17 -2.76 -4.09
       Tue->Wed  3.69  0.55 -0.14
       Wed->Thu  3.66  1.09  0.54
ew     Mon->Tue  6.58  3.24  2.43
       Thu->Fri  0.28 -2.35 -4.15
       Tue->Wed  3.74  0.60 -0.41
       Wed->Thu  4.88  2.13  1.15

Wed->Thu vs VN30F1M (paired by date):
version scheme   n  basket_bp  index_bp  diff_bp  paired_t
      a    cap 390      10.78      2.92     7.86      3.49
      a     ew 390      12.02      2.92     9.10      4.16
      b    cap 390       8.28      2.92     5.36      2.64
      b     ew 390       9.35      2.92     6.43      3.28
      c    cap 390       7.76      2.92     4.83      2.37
      c     ew 390       8.42      2.92     5.50      2.74

Decision rule outcome (cap-weighted, fixed in advance): C (neither tracks within ~2 bp: another data or method issue)

## Step 2: flag diagnostics
(a) flag rate % by year:
series  VN30  VNINDEX  stock panel PIT members  stock panel pooled (all tickers)
group                                                                           
2011     NaN    10.40                      NaN                               NaN
2012     NaN     0.80                      NaN                               NaN
2013     NaN     4.80                      NaN                               NaN
2014     NaN     1.21                      NaN                               NaN
2015     NaN     3.23                      NaN                               NaN
2016     NaN     6.37                      NaN                               NaN
2017     NaN     3.60                      NaN                               NaN
2018    0.00     6.40                    26.21                             28.83
2019   11.60     6.00                    34.05                             37.95
2020   15.48     7.54                    25.89                             30.05
2021    4.40    53.20                    22.84                             24.36
2022    1.61     7.63                    20.19                             20.14
2023    0.00     0.00                    27.91                             26.94
2024    0.40     0.00                    30.17                             29.78
2025    0.40     0.00                    23.69                             24.44
2026    0.46     0.46                    23.95                             25.75

(b) flagged vs unflagged, PIT member stock-days (pooled, descriptive):
                             section                           group     n  overnight_bp  intraday_bp  intraday_t  cc_bp  cc_t
              b_flagged_vs_unflagged             all | flagged=False 44159          7.36        -3.51       -3.65   3.85  3.68
              b_flagged_vs_unflagged              all | flagged=True 15619          0.00        -4.13       -3.03  -4.13 -3.03
              b_flagged_vs_unflagged  pre 2022-08-25 | flagged=False 20700         -2.32         5.77        4.07   3.45  2.23
              b_flagged_vs_unflagged   pre 2022-08-25 | flagged=True  7458          0.00        -0.39       -0.19  -0.39 -0.19
              b_flagged_vs_unflagged post 2022-08-25 | flagged=False 23459         15.90       -11.70       -8.96   4.21  2.97
              b_flagged_vs_unflagged  post 2022-08-25 | flagged=True  8161          0.00        -7.55       -4.09  -7.55 -4.09
b_date_level_flagged_minus_unflagged                             all  1940           NaN         0.65        0.36 -11.66 -5.77
b_date_level_flagged_minus_unflagged                  pre 2022-08-25   911           NaN        -4.00       -1.45 -10.14 -3.35
b_date_level_flagged_minus_unflagged                 post 2022-08-25  1029           NaN         4.77        1.96 -13.00 -4.80

(c) observed vs expected genuine flat-open rate (%). tickrule: density of ON near 0 from non-zero days x relative tick (HOSE rule 10/50/100 VND applied to the BACK-ADJUSTED price, so the tick band can be understated for names with large later bonus issues). ccscaled: observed close==prior-close rate (closes are reliable) x ratio of ON to CC mass in (0, h]; scale-free and consistent with the price rounding.
group    n  flag_rate_pct  cc_zero_pct  exp_tickrule_h0.5_pct  exp_tickrule_h1_pct  exp_ccscaled_h0.5_pct  exp_ccscaled_h1_pct  excess_tickrule_pct  excess_ccscaled_pct
 2018  828          26.21         9.54                   5.82                 5.23                  10.94                 9.96                20.38                15.27
 2019 7500          34.05        11.29                   7.29                 5.64                  13.95                11.88                26.77                20.11
 2020 7560          25.89         9.51                   6.08                 5.10                  12.78                11.15                19.80                13.11
 2021 7500          22.84         5.72                   7.14                 5.82                   9.70                 7.99                15.70                13.14
 2022 7470          20.19         6.64                   6.32                 5.45                  10.91                 9.48                13.87                 9.28
 2023 7470          27.91         7.97                   8.02                 6.38                  12.13                 9.94                19.90                15.79
 2024 7500          30.17        10.17                   9.65                 7.01                  15.08                11.93                20.53                15.10
 2025 7470          23.69         8.19                   8.31                 6.25                  13.85                11.09                15.39                 9.85
 2026 6480          23.95         7.73                   7.25                 5.40                  14.56                11.22                16.70                 9.39

(d) KBS spot check (VCI-flagged days):
series group  n  kbs_coverage_pct  kbs_differs_gt1tick_pct  kbs_on_on_vci_flagged_bp  kbs_close_ratio_med
   FPT  2018  9             88.89                     0.00                      0.00                 1.00
   FPT  2019 76            100.00                     1.32                     -1.97                 1.00
   FPT  2020 53            100.00                     0.00                     -0.15                 1.00
   FPT  2021 52            100.00                     1.92                     -1.11                 1.00
   FPT  2022 49            100.00                     0.00                      0.00                 1.00
   FPT  2023 60            100.00                     0.00                      0.00                 1.00
   FPT  2024 56            100.00                     0.00                      0.00                 1.00
   FPT  2025 49            100.00                     0.00                      0.00                 1.00
   FPT  2026 39            100.00                     0.00                      0.00                 1.00
   HPG  2018  5            100.00                     0.00                      0.00                 1.00
   HPG  2019 85            100.00                     0.00                      0.00                 1.00
   HPG  2020 44            100.00                     4.55                      1.21                 1.00
   HPG  2021 51            100.00                     5.88                     -1.02                 1.00
   HPG  2022 35            100.00                     2.86                      0.62                 1.00
   HPG  2023 78            100.00                     0.00                      0.00                 1.00
   HPG  2024 83            100.00                     0.00                      0.00                 1.00
   HPG  2025 49            100.00                     0.00                      0.00                 1.00
   HPG  2026 69            100.00                     0.00                      0.00                 1.00
   MBB  2018  6            100.00                     0.00                      0.00                 1.00
   MBB  2019 81            100.00                     1.23                      1.60                 1.00
   MBB  2020 46            100.00                     0.00                      0.92                 1.00
   MBB  2021 54            100.00                     3.70                      0.32                 1.00
   MBB  2022 41            100.00                     0.00                      0.00                 1.00
   MBB  2023 86            100.00                     0.00                      0.00                 1.00
   MBB  2024 83            100.00                     0.00                      0.00                 1.00
   MBB  2025 47            100.00                     0.00                      0.00                 1.00
   MBB  2026 73            100.00                     0.00                      0.00                 1.00
   SSI  2018  5             80.00                     0.00                      0.00                 1.01
   SSI  2019 70            100.00                     1.43                      1.04                 1.01
   SSI  2020 49            100.00                     4.08                      1.41                 1.00
   SSI  2021 43            100.00                     4.65                     -0.36                 1.00
   SSI  2022 28            100.00                     0.00                      0.00                 1.00
   SSI  2023 54            100.00                     0.00                      0.00                 1.00
   SSI  2024 65            100.00                     0.00                      0.00                 1.00
   SSI  2025 31            100.00                     0.00                      0.00                 1.00
   SSI  2026 41            100.00                     0.00                      0.00                 1.00
   VCB  2018  6            100.00                     0.00                      0.00                 1.00
   VCB  2019 86            100.00                     3.49                      0.54                 1.00
   VCB  2020 78            100.00                     3.85                      3.14                 1.00
   VCB  2021 63            100.00                     0.00                      0.00                 1.00
   VCB  2022 64            100.00                     0.00                      0.00                 1.00
   VCB  2023 90            100.00                     0.00                      0.00                 1.00
   VCB  2024 72            100.00                     0.00                      0.00                 1.00
   VCB  2025 56            100.00                     0.00                      0.00                 1.00
   VCB  2026 54            100.00                     0.00                      0.00                 1.00
   VIC  2018  9            100.00                     0.00                      0.00                 1.00
   VIC  2019 84            100.00                     3.57                     -1.78                 1.00
   VIC  2020 86            100.00                     2.33                      1.25                 1.00
   VIC  2021 79            100.00                     2.53                      1.20                 1.00
   VIC  2022 49            100.00                     0.00                      0.00                 1.00
   VIC  2023 69            100.00                     0.00                      0.00                 1.00
   VIC  2024 79            100.00                     0.00                      0.00                 1.00
   VIC  2025 49            100.00                     0.00                      0.00                 1.00
   VIC  2026 42            100.00                     0.00                      0.00                 1.00

## Step 3: regime and year split (date-level, one obs per date)
                                       series     filter            group  n_dates  mean_bp     t  hit_pct note
          VNINDEX index (Level A, all nights)   filtered   pre 2022-08-25   750.00    -0.79 -0.31    60.27  NaN
          VNINDEX index (Level A, all nights)   filtered  post 2022-08-25  1053.00    12.20  6.79    70.37  NaN
          VNINDEX index (Level A, all nights)   filtered full 2018-11-21+  1803.00     6.80  4.51    66.17  NaN
          VNINDEX index (Level A, all nights) unfiltered   pre 2022-08-25   939.00    -0.63 -0.31    48.14  NaN
          VNINDEX index (Level A, all nights) unfiltered  post 2022-08-25  1054.00    12.19  6.79    70.30  NaN
          VNINDEX index (Level A, all nights) unfiltered full 2018-11-21+  1993.00     6.15  4.51    59.86  NaN
             VN30 index (Level A, all nights)   filtered   pre 2022-08-25   857.00     0.98  0.70    56.94  NaN
             VN30 index (Level A, all nights)   filtered  post 2022-08-25  1050.00    10.03  6.42    65.52  NaN
             VN30 index (Level A, all nights)   filtered full 2018-11-21+  1907.00     5.96  5.59    61.67  NaN
             VN30 index (Level A, all nights) unfiltered   pre 2022-08-25   939.00     0.89  0.70    51.97  NaN
             VN30 index (Level A, all nights) unfiltered  post 2022-08-25  1054.00     9.99  6.42    65.28  NaN
             VN30 index (Level A, all nights) unfiltered full 2018-11-21+  1993.00     5.70  5.58    59.01  NaN
Level B date-level EW current-30 (all nights)   filtered   pre 2022-08-25   934.00     5.71  2.03    62.74  NaN
Level B date-level EW current-30 (all nights)   filtered  post 2022-08-25  1053.00    15.90  7.38    70.18  NaN
Level B date-level EW current-30 (all nights)   filtered full 2018-11-21+  1987.00    11.11  6.35    66.68  NaN
Level B date-level EW current-30 (all nights) unfiltered   pre 2022-08-25   939.00     1.95  0.79    62.62  NaN
Level B date-level EW current-30 (all nights) unfiltered  post 2022-08-25  1054.00    12.16  6.19    70.21  NaN
Level B date-level EW current-30 (all nights) unfiltered full 2018-11-21+  1993.00     7.35  4.70    66.63  NaN
               PIT EW basket (one-day nights)  version a   pre 2022-08-25   740.00     0.23  0.08    57.03  NaN
               PIT EW basket (one-day nights)  version a  post 2022-08-25   833.00    19.22  8.50    72.75  NaN
               PIT EW basket (one-day nights)  version a full 2018-11-21+  1573.00    10.28  5.75    65.35  NaN
              PIT CAP basket (one-day nights)  version a   pre 2022-08-25   740.00     1.52  0.57    58.38  NaN
              PIT CAP basket (one-day nights)  version a  post 2022-08-25   833.00    18.00  7.72    70.47  NaN
              PIT CAP basket (one-day nights)  version a full 2018-11-21+  1573.00    10.25  5.80    64.78  NaN
               PIT EW basket (one-day nights)  version b   pre 2022-08-25   741.00    -1.36 -0.54    56.95  NaN
               PIT EW basket (one-day nights)  version b  post 2022-08-25   833.00    15.07  7.23    72.75  NaN
               PIT EW basket (one-day nights)  version b full 2018-11-21+  1574.00     7.34  4.50    65.31  NaN
              PIT CAP basket (one-day nights)  version b   pre 2022-08-25   741.00    -0.46 -0.19    58.30  NaN
              PIT CAP basket (one-day nights)  version b  post 2022-08-25   833.00    14.18  6.61    70.47  NaN
              PIT CAP basket (one-day nights)  version b full 2018-11-21+  1574.00     7.29  4.53    64.74  NaN
               PIT EW basket (one-day nights)  version c   pre 2022-08-25   741.00    -2.04 -0.78    56.82  NaN
               PIT EW basket (one-day nights)  version c  post 2022-08-25   833.00    13.54  6.11    72.27  NaN
               PIT EW basket (one-day nights)  version c full 2018-11-21+  1574.00     6.21  3.63    64.99  NaN
              PIT CAP basket (one-day nights)  version c   pre 2022-08-25   741.00    -0.75 -0.31    58.30  NaN
              PIT CAP basket (one-day nights)  version c  post 2022-08-25   833.00    13.06  5.80    70.35  NaN
              PIT CAP basket (one-day nights)  version c full 2018-11-21+  1574.00     6.55  3.93    64.68  NaN

By year (mean bp):
group                                                      2018  2019  2020  2021  2022  2023  2024  2025  2026
series                                        filter                                                           
Level B date-level EW current-30 (all nights) filtered   -27.70  8.20  0.90 16.40  0.50 19.30 16.30 19.30 12.40
                                              unfiltered -20.50  4.20 -4.60 11.40 -0.20 14.60 12.30 15.20  9.50
PIT CAP basket (one-day nights)               version a  -21.20  1.20 -1.10 11.60 -0.60 18.00 16.00 24.50 16.90
                                              version b  -19.80  0.20 -4.10  7.90 -0.70 13.10 11.70 19.70 14.60
                                              version c  -19.90  0.10 -4.80  7.60 -3.50 13.10 11.70 18.00 14.40
PIT EW basket (one-day nights)                version a  -23.80 -3.40 -1.30 12.80 -1.00 21.20 18.40 22.30 18.60
                                              version b  -21.70 -2.60 -4.10  8.50 -1.10 15.60 13.70 17.70 15.50
                                              version c  -22.50 -3.00 -5.70  8.00 -4.80 15.50 13.70 15.50 15.00
VN30 index (Level A, all nights)              filtered   -10.10  0.00 -1.60  6.20 -2.50  9.90  8.80 16.70 10.80
                                              unfiltered -10.10  0.00 -1.30  5.90 -2.50  9.90  8.80 16.60 10.80
VNINDEX index (Level A, all nights)           filtered    -7.00  2.60 -2.70  6.60 -6.80 13.70 12.60 16.50 11.80
                                              unfiltered  -6.20  2.40 -2.50  3.10 -6.20 13.70 12.60 16.50 11.80

## Step 4: reconcile with Option C regime 1 (entries/nights before 2022-08-25)
                                                                                 item  value_bp                                              note
                                      Option C D (window dropped if ANY open flagged)     -1.37                 ON1 -1.81, ON2 -0.38, ON3 0.82 bp
                                                          Option C E (no open filter)     -4.70                ON1 -2.27, ON2 -1.37, ON3 -1.07 bp
                                         per-night PIT EW, unfiltered (all nights) x3     -5.29               per-night -1.76 bp x 3, n 939 dates
                                         per-night PIT EW, open_suspicious dropped x3      0.19                per-night 0.06 bp x 3, n 938 dates
                               per-night PIT EW, open_suspicious & |ON|>7% dropped x3      3.08                per-night 1.03 bp x 3, n 938 dates
                                            per-night PIT EW, |ON|>7% dropped only x3     -2.81               per-night -0.94 bp x 3, n 939 dates
                                    Option C ON1 on E with only ITS OWN open filtered     -0.61          vs ON1 under the window filter (D) above
   VN30 index per-night overnight x3, same calendar (unfiltered / index-flag dropped)      2.67    filtered x3 = 2.93 bp; t unf 0.70, t filt 0.70
VNINDEX index per-night overnight x3, same calendar (unfiltered / index-flag dropped)     -1.90 filtered x3 = -2.37 bp; t unf -0.31, t filt -0.31
            regime 1: pit_unf minus VN30 index overnight (paired, index-flag dropped)     -3.63                  paired t -1.58, n 856, corr 0.56
              regime 1: pit_f minus VN30 index overnight (paired, index-flag dropped)     -1.91                  paired t -0.77, n 856, corr 0.57
               regime 1 year 2018: VN30 index / PIT EW unf / PIT EW filt per-night bp    -10.10             PIT unf -19.59, PIT filt -22.44, n 28
               regime 1 year 2019: VN30 index / PIT EW unf / PIT EW filt per-night bp      0.03              PIT unf -2.80, PIT filt -3.72, n 221
               regime 1 year 2020: VN30 index / PIT EW unf / PIT EW filt per-night bp     -1.58            PIT unf -14.11, PIT filt -11.17, n 213
               regime 1 year 2021: VN30 index / PIT EW unf / PIT EW filt per-night bp      6.24              PIT unf 10.38, PIT filt 14.79, n 238
               regime 1 year 2022: VN30 index / PIT EW unf / PIT EW filt per-night bp     -0.19              PIT unf -3.63, PIT filt -3.08, n 156

## Level A / Level B checks (unfiltered date-level overnight, pre and post 2022-08-25)
- Level A VNINDEX index (Level A, all nights): pre 2022-08-25: unfiltered -0.63 bp (t -0.31) vs filtered -0.79 bp -> positive & t>=3: False, >=50% of filtered: False; post 2022-08-25: unfiltered 12.19 bp (t 6.79) vs filtered 12.20 bp -> positive & t>=3: True, >=50% of filtered: True
- Level A VN30 index (Level A, all nights): pre 2022-08-25: unfiltered 0.89 bp (t 0.70) vs filtered 0.98 bp -> positive & t>=3: False, >=50% of filtered: True; post 2022-08-25: unfiltered 9.99 bp (t 6.42) vs filtered 10.03 bp -> positive & t>=3: True, >=50% of filtered: True
- Level B (date-level EW, current 30, all nights): pre 2022-08-25: unfiltered 1.95 bp (t 0.79) vs filtered 5.71 bp -> positive & t>=3: False, >=50% of filtered: False; post 2022-08-25: unfiltered 12.16 bp (t 6.19) vs filtered 15.90 bp -> positive & t>=3: True, >=50% of filtered: True
## Caveats
- HOSE tick rule (10 / 50 / 100 VND at <10k / 10k-<50k / >=50k) is from memory, not verified from a primary source in this run, and is applied to back-adjusted prices.
- The cc-scaled expected rate assumes ON and close-to-close have locally flat densities over (0, h]; two h values are shown.
- KBS covers the six names fully from 2018-11-22; it agrees with VCI almost everywhere, so it is not an independent check of the open (shared upstream source).
- If the flagged open is the reference price after no ATO match, the unfiltered overnight is the right LEVEL measure but is not executable at that price.
- Level B 'date-level' = EW across the current-30 per date, all nights, k >= 10; the Level B cross-section itself is per stock (reproduced above).

## Verdict
VERDICT. Filter: the open_suspicious filter is mainly truncation bias for levels. Against the published VN30 overnight, the cap-weighted PIT basket's all-nights gap is 3.80 bp with the filter and 0.07 bp without it, and the mean absolute weekday gap falls from 3.90 to 2.20 bp (correlation unchanged, ~0.78). Fixed rule outcome: C by a 0.20 bp margin over the ~2 bp threshold, so I read it as borderline A/C (ambiguous, D) on weekday shape; the residual is a shape mismatch (Mon->Tue +4.0, Thu->Fri -4.1 bp), not a level gap. Flags run 20-34% a year against an expected genuine flat-open rate of about 10-15% (cc-scaled) or 6-10% (tick rule), but KBS shows the same open on 99% of VCI-flagged days, so the excess is not a VCI fill that another vendor corrects; it looks like the exchange-reported open equal to the reference price (plausibly no ATO match), which the index also uses. Flagged names close 11.7 bp below unflagged names on the same date (t -5.77), so the filter selects on the outcome: harmless for the overnight leg (zeros), but it biases any hold that spans the flagged day (the Option C 12.8 vs 4.8 bp). Regime 1: there is no inconsistency to explain. The published VN30 overnight is itself ~0 before 2022-08-25 (0.89 bp/night, t 0.70) and strongly positive after (9.99 bp, t 6.42); the Level A full-sample positive overnight comes from outside 2018-11..2022-08. Option C's unfiltered three-leg sum (-4.70 bp) matches 3 x the per-night PIT mean (-5.29 bp); the filtered version differs (-1.37 vs 0.19 bp) because Option C drops the whole window. The 'index positive, stocks ~0' hypothesis is rejected: stock basket minus index in regime 1 is -3.63 bp (not significant). Wednesday: the Wed->Thu replica-minus-VN30F1M gap shrinks from 7.86 bp (t 3.49) to 4.83 bp (t 2.37) unfiltered; about 38% of it was filter, the rest persists. Levels A/B: unfiltered overnight is positive with t >= 3 after 2022-08-25 for both, but not before (Level A VN30 0.89 bp, Level B 1.95 bp, t 0.79); Level B's unfiltered mean is 34% (pre) and 77% (post) of the filtered mean; Level A is essentially unaffected by the filter after 2018.
