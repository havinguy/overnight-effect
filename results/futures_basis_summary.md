# VN30F1M overnight = VN30 index overnight + overnight basis change (measurement only)

## Step 0: reproduction gate
                                                           item  target   ours                                                                                               note  diff  pass
                 futures gross ON, all invested nights (simple)    4.99   4.99 n 2284 nights (2300 nights from 2301 bars; the file has 2302 lines incl. header); log mean 4.80 bp  0.00  True
                      futures gross Mon->Tue (simple, non-hold)   10.60  10.62                                                                                n 453; log 10.49 bp  0.02  True
                                    futures gross 2017 (simple)    9.40   9.38                                                                                                    -0.02  True
                                    futures gross 2018 (simple)    2.40   2.40                                                                                                    -0.00  True
                                    futures gross 2019 (simple)    4.10   4.05                                                                                                    -0.05  True
                                    futures gross 2020 (simple)    7.40   7.40                                                                                                    -0.00  True
                                    futures gross 2021 (simple)    8.20   8.22                                                                                                     0.02  True
                                    futures gross 2022 (simple)    1.20   1.18                                                                                                    -0.02  True
                                    futures gross 2023 (simple)    5.00   4.97                                                                                                    -0.03  True
                                    futures gross 2024 (simple)    3.70   3.71                                                                                                     0.01  True
                                    futures gross 2025 (simple)    6.60   6.58                                                                                                    -0.02  True
                                    futures gross 2026 (simple)    4.50   4.51                                                                                                     0.01  True
VN30 index ON pre 2022-08-25 (log, all nights, from 2018-11-21)    0.89   0.89                                                              plain t 0.70 (target 0.70); NW t 0.65  0.00  True
                                  VN30 index ON post 2022-08-25    9.99   9.99                                                              plain t 6.42 (target 6.42); NW t 6.33  0.00  True
                                             VN30 index ON 2018  -10.10 -10.10                                                                                                    -0.00  True
                                             VN30 index ON 2019    0.00   0.02                                                                                                     0.02  True
                                             VN30 index ON 2020   -1.30  -1.33                                                                                                    -0.03  True
                                             VN30 index ON 2021    5.90   5.92                                                                                                     0.02  True
                                             VN30 index ON 2022   -2.50  -2.49                                                                                                     0.01  True
                                             VN30 index ON 2023    9.90   9.86                                                                                                    -0.04  True
                                             VN30 index ON 2024    8.80   8.77                                                                                                    -0.03  True
                                             VN30 index ON 2025   16.60  16.65                                                                                                     0.05  True
                                             VN30 index ON 2026   10.80  10.78                                                                                                    -0.02  True

GATE PASSED

## Step 1: alignment and sample
- Futures nights (invested): 2284, 2017-08-11 .. 2026-11-17. Index nights from 2018-11-21.
- Decomposition sample (intersection, both legs from the same prior trading day): N = 1962, 2018-11-22 .. 2026-11-17; 16 intersection nights dropped because the prior trading day differs between the two series.
- Excluding index-flagged opens: N = 1876. Identity fut_ON = idx_ON + dbasis_ON: max |residual| = 9.50e-16.
- Roll nights in sample: 81; prior-close leg uses the VN30F2M close (build() entry) for both the futures return and the basis.
- Index-flag rate by year (%): 2018 0.0, 2019 11.6, 2020 15.5, 2021 4.4, 2022 1.6, 2023 0.0, 2024 0.4, 2025 0.4, 2026 0.5
- Futures open == prior close (entry): 3.42% of invested nights; degenerate bars (O=H=L=C): 0; zero-volume bars: 0.
- Derivatives session times are UNVERIFIED: the futures 'open' is the vendor daily-bar open, assumed to be the first print of the derivatives session (which has opened 15 minutes before the stock ATO for much of the sample); the index open is the ATO-based index open. If the two opens are struck at different times, dbasis_ON contains the index move over that window by construction.

## Tables, sample a_all_days
A. By year:
                                  year    n  fut_ON_bp  fut_t  idx_ON_bp  idx_t  dbasis_ON_bp  dbasis_t  corr  slope  slope_nw_se   r2  dbasis_ID_bp  idx_flag_pct
2018 (futures only, before index data)  212       2.48   0.69        NaN    NaN           NaN       NaN   NaN    NaN          NaN  NaN           NaN           NaN
2017 (futures only, before index data)   95       9.34   4.17        NaN    NaN           NaN       NaN   NaN    NaN          NaN  NaN           NaN           NaN
                                  2018   27      -0.39  -0.03      -6.40  -0.54          6.01      0.71  0.59   0.84         0.30 0.35         -6.61          0.00
                                  2019  250       3.99   2.00       0.02   0.01          3.97      1.32  0.35   0.36         0.15 0.13         -3.28         11.60
                                  2020  252       6.91   0.96      -1.33  -0.55          8.25      1.38  0.37   0.98         0.11 0.14         -0.86         15.48
                                  2021  248       8.05   2.35       5.95   3.26          2.11      0.60  0.32   0.46         0.09 0.10         -2.96          4.44
                                  2022  245       1.29   0.36      -2.11  -0.51          3.40      1.18  0.74   0.71         0.06 0.54         -0.07          1.63
                                  2023  225       9.66   4.38      11.08   5.07         -1.42     -0.66  0.69   0.76         0.10 0.47          2.27          0.00
                                  2024  250       3.66   1.96       8.77   4.71         -5.11     -3.87  0.72   0.84         0.05 0.51          3.49          0.40
                                  2025  249       6.36   1.95      16.65   4.26        -10.29     -3.71  0.78   0.78         0.15 0.60         11.20          0.40
                                  2026  216       4.28   1.27      10.78   3.63         -6.50     -2.86  0.74   0.99         0.11 0.54          7.59          0.46
                                   all 1962       5.42   4.06       5.92   5.39         -0.50     -0.41  0.58   0.75         0.05 0.33          1.96          4.38

B. By night (entry weekday), NW t lag 5. 6 night types x 4 periods = 24 cells: Bonferroni |t| ~3.1 at 5%; weekday cells are descriptive.
             period              night   n  fut_ON_bp  fut_t  idx_ON_bp  idx_t  dbasis_ON_bp  dbasis_t  dbasis_ID_bp
full (index sample)           Mon->Tue 391      12.14   4.24       8.22   3.19          3.93      1.36         -4.04
full (index sample)           Tue->Wed 394       6.74   2.11       8.05   3.42         -1.31     -0.57          8.48
full (index sample)           Wed->Thu 390       2.75   1.07       6.84   3.12         -4.10     -2.00         -0.86
full (index sample)           Thu->Fri 384       3.58   1.30       2.46   1.07          1.13      0.43          3.95
full (index sample) Fri->Mon (weekend) 366       1.78   0.38       4.15   1.41         -2.37     -0.57          4.05
full (index sample)            holiday  37       3.81   0.31       2.62   0.19          1.19      0.12        -15.81
     pre 2022-08-25           Mon->Tue 184      12.87   2.64       0.06   0.02         12.82      2.58         -9.97
     pre 2022-08-25           Tue->Wed 185       4.25   1.40       2.57   1.16          1.68      0.60          3.77
     pre 2022-08-25           Wed->Thu 183       1.98   0.55       3.01   1.29         -1.02     -0.31         -2.78
     pre 2022-08-25           Thu->Fri 187       2.93   0.62      -1.48  -0.43          4.41      0.90          1.50
     pre 2022-08-25 Fri->Mon (weekend) 179       4.38   0.59      -1.39  -0.45          5.78      0.81         -3.54
     pre 2022-08-25            holiday  18      18.71   1.38      24.06   2.26         -5.35     -0.33         -9.08
    post 2022-08-25           Mon->Tue 207      11.49   3.57      15.47   4.10         -3.98     -1.60          1.24
    post 2022-08-25           Tue->Wed 209       8.94   1.67      12.90   3.40         -3.96     -1.13         12.65
    post 2022-08-25           Wed->Thu 207       3.42   0.94      10.24   2.96         -6.82     -2.73          0.84
    post 2022-08-25           Thu->Fri 197       4.21   1.45       6.20   2.12         -1.99     -1.00          6.28
    post 2022-08-25 Fri->Mon (weekend) 187      -0.72  -0.13       9.45   2.00        -10.17     -2.67         11.32
    post 2022-08-25            holiday  19     -10.31  -0.62     -17.70  -0.93          7.39      0.70        -22.19
          2026 only           Mon->Tue  43      21.48   1.76      21.86   1.88         -0.38     -0.06         -2.65
          2026 only           Tue->Wed  43      27.77   1.53      22.61   2.05          5.15      0.68          9.81
          2026 only           Wed->Thu  42      -6.77  -0.82       4.42   0.79        -11.19     -2.47         -4.42
          2026 only           Thu->Fri  43      -5.78  -0.77       0.49   0.06         -6.27     -1.65         16.57
          2026 only Fri->Mon (weekend)  40     -20.51  -1.11       4.95   0.43        -25.45     -2.12         26.75
          2026 only            holiday   5      32.22   3.90       2.41   0.30         29.81     16.50        -53.14

C. Monday->Tuesday split:
                                       period   n  fut_ON_bp  fut_t  idx_part_bp  idx_t  dbasis_part_bp  dbasis_t  dbasis_share_pct
           full (index sample, 2018-11..2026) 391      12.14   4.24         8.22   3.19            3.93      1.36             32.33
   2017-21 where index exists (2018-11..2021) 154      15.44   2.72         2.78   0.95           12.66      2.21             82.00
                                      2022-25 194       7.46   3.67         9.51   2.65           -2.05     -0.73            -27.50
                                         2026  43      21.48   1.76        21.86   1.88           -0.38     -0.06             -1.76
reference: futures-only Option B full 2017-26 453      10.49   3.91          NaN    NaN             NaN       NaN               NaN
              reference: futures-only 2017-21 216      11.03   2.37          NaN    NaN             NaN       NaN               NaN

D. Wednesday->Thursday (PIT CW basket = one-day nights, filters off):
             period   n  idx_ON_bp  fut_ON_bp  idx_minus_fut_bp  idx_minus_fut_t  dbasis_ON_bp  dbasis_t  basket_minus_fut_bp  basket_minus_fut_t  basket_minus_idx_bp  basket_minus_idx_t
full (index sample) 390       6.84       2.75              4.10             2.00         -4.10     -2.00                 5.01                2.37                 0.91                0.41
     pre 2022-08-25 183       3.01       1.98              1.02             0.31         -1.02     -0.31                -0.56               -0.19                -1.58               -0.36
    post 2022-08-25 207      10.24       3.42              6.82             2.73         -6.82     -2.73                 9.93                3.60                 3.11                2.39
          2026 only  42       4.42      -6.77             11.19             2.47        -11.19     -2.47                10.85                2.20                -0.35               -0.27

E. Basis level and dbasis by days-to-expiry / night:
                  cut                          group   n  b_close_mean_bp  dbasis_ON_bp  dbasis_ON_t  dbasis_ID_bp  dbasis_ID_t
       days-to-expiry                            0-5 570            -8.29          0.84         0.53          2.36         1.06
       days-to-expiry                           6-10 475           -24.56         -1.92        -0.65          3.93         1.35
       days-to-expiry                          11-15 467           -28.26         -0.54        -0.27          0.03         0.01
       days-to-expiry                            16+ 427           -28.47         -0.33        -0.13          1.14         0.39
night (entry weekday)                       Mon->Tue 391           -22.78          3.93         1.36         -4.04        -1.48
night (entry weekday)                       Tue->Wed 394           -16.22         -1.31        -0.57          8.48         2.67
night (entry weekday)                       Wed->Thu 390           -19.67         -4.10        -2.00         -0.86        -0.30
night (entry weekday)                       Thu->Fri 384           -22.55          1.13         0.43          3.95         1.18
night (entry weekday)             Fri->Mon (weekend) 366           -22.11         -2.37        -0.57          4.05         1.01
night (entry weekday)                        holiday  37           -48.32          1.19         0.12        -15.81        -1.90
          night x dte             Mon->Tue | dte 0-5  94              NaN          8.77         1.32           NaN          NaN
          night x dte            Mon->Tue | dte 6-10  97              NaN          4.49         0.88           NaN          NaN
          night x dte           Mon->Tue | dte 11-15  92              NaN          0.02         0.00           NaN          NaN
          night x dte             Mon->Tue | dte 16+ 103              NaN          2.98         0.83           NaN          NaN
          night x dte             Tue->Wed | dte 0-5  96              NaN          2.36         0.69           NaN          NaN
          night x dte            Tue->Wed | dte 6-10 101              NaN         -6.36        -1.07           NaN          NaN
          night x dte           Tue->Wed | dte 11-15 104              NaN         -0.12        -0.03           NaN          NaN
          night x dte             Tue->Wed | dte 16+  89              NaN         -0.97        -0.19           NaN          NaN
          night x dte             Wed->Thu | dte 0-5 187              NaN         -5.03        -1.62           NaN          NaN
          night x dte            Wed->Thu | dte 6-10  83              NaN         -6.49        -1.61           NaN          NaN
          night x dte           Wed->Thu | dte 11-15  87              NaN         -0.21        -0.05           NaN          NaN
          night x dte             Wed->Thu | dte 16+  29              NaN         -1.93        -0.37           NaN          NaN
          night x dte             Thu->Fri | dte 0-5  96              NaN          6.60         1.75           NaN          NaN
          night x dte            Thu->Fri | dte 6-10  90              NaN         -5.63        -0.95           NaN          NaN
          night x dte           Thu->Fri | dte 11-15  89              NaN         -3.16        -1.06           NaN          NaN
          night x dte             Thu->Fri | dte 16+ 104              NaN          5.84         1.10           NaN          NaN
          night x dte   Fri->Mon (weekend) | dte 0-5  94              NaN         -3.75        -0.87           NaN          NaN
          night x dte  Fri->Mon (weekend) | dte 6-10  88              NaN         -1.75        -0.19           NaN          NaN
          night x dte Fri->Mon (weekend) | dte 11-15  80              NaN          7.27         1.18           NaN          NaN
          night x dte   Fri->Mon (weekend) | dte 16+  99              NaN         -9.10        -1.63           NaN          NaN
          night x dte             holiday | dte 6-10  16              NaN         30.99         2.57           NaN          NaN
          night x dte            holiday | dte 11-15  15              NaN        -34.81        -1.54           NaN          NaN

## Tables, sample b_ex_index_flagged
A. By year:
                                  year    n  fut_ON_bp  fut_t  idx_ON_bp  idx_t  dbasis_ON_bp  dbasis_t  corr  slope  slope_nw_se   r2  dbasis_ID_bp  idx_flag_pct
2018 (futures only, before index data)  212       2.48   0.69        NaN    NaN           NaN       NaN   NaN    NaN          NaN  NaN           NaN           NaN
2017 (futures only, before index data)   95       9.34   4.17        NaN    NaN           NaN       NaN   NaN    NaN          NaN  NaN           NaN           NaN
                                  2018   27      -0.39  -0.03      -6.40  -0.54          6.01      0.71  0.59   0.84         0.30 0.35         -6.61          0.00
                                  2019  221       4.11   1.92       0.03   0.01          4.08      1.22  0.36   0.36         0.15 0.13         -3.49          0.00
                                  2020  213       4.32   0.59      -1.58  -0.54          5.90      1.04  0.40   0.98         0.10 0.16          0.97          0.00
                                  2021  237       8.24   2.27       6.22   3.28          2.02      0.54  0.32   0.46         0.09 0.11         -1.04          0.00
                                  2022  241       1.15   0.32      -2.14  -0.51          3.30      1.15  0.74   0.71         0.06 0.55          0.46          0.00
                                  2023  225       9.66   4.38      11.08   5.07         -1.42     -0.66  0.69   0.76         0.10 0.47          2.27          0.00
                                  2024  249       3.68   1.97       8.80   4.74         -5.12     -3.87  0.72   0.84         0.05 0.51          3.40          0.00
                                  2025  248       6.22   1.89      16.71   4.26        -10.50     -3.77  0.78   0.78         0.15 0.60         11.43          0.00
                                  2026  215       4.51   1.35      10.83   3.61         -6.32     -2.74  0.74   0.99         0.11 0.54          7.31          0.00
                                   all 1876       5.14   3.94       6.19   5.40         -1.05     -0.90  0.59   0.75         0.05 0.35          2.61          0.00

B. By night (entry weekday), NW t lag 5. 6 night types x 4 periods = 24 cells: Bonferroni |t| ~3.1 at 5%; weekday cells are descriptive.
             period              night   n  fut_ON_bp  fut_t  idx_ON_bp  idx_t  dbasis_ON_bp  dbasis_t  dbasis_ID_bp
full (index sample)           Mon->Tue 378      11.81   4.40       8.50   3.20          3.31      1.25         -4.05
full (index sample)           Tue->Wed 374       7.11   2.11       8.48   3.44         -1.37     -0.56          8.54
full (index sample)           Wed->Thu 369       2.78   1.02       7.23   3.13         -4.46     -2.09          0.85
full (index sample)           Thu->Fri 368       3.19   1.13       2.57   1.07          0.62      0.23          4.09
full (index sample) Fri->Mon (weekend) 352       0.43   0.09       4.31   1.42         -3.89     -0.91          5.97
full (index sample)            holiday  35       5.22   0.41       2.77   0.19          2.46      0.26        -19.95
     pre 2022-08-25           Mon->Tue 171      12.18   2.72       0.06   0.02         12.12      2.71        -10.46
     pre 2022-08-25           Tue->Wed 165       4.79   1.38       2.88   1.17          1.91      0.60          3.33
     pre 2022-08-25           Wed->Thu 163       1.61   0.41       3.38   1.28         -1.77     -0.49          0.62
     pre 2022-08-25           Thu->Fri 172       1.74   0.35      -1.61  -0.43          3.35      0.65          1.96
     pre 2022-08-25 Fri->Mon (weekend) 167       1.93   0.24      -1.49  -0.45          3.43      0.44         -0.20
     pre 2022-08-25            holiday  16      23.66   1.73      27.07   2.38         -3.40     -0.21        -17.30
    post 2022-08-25           Mon->Tue 207      11.49   3.57      15.47   4.10         -3.98     -1.60          1.24
    post 2022-08-25           Tue->Wed 209       8.94   1.67      12.90   3.40         -3.96     -1.13         12.65
    post 2022-08-25           Wed->Thu 206       3.70   1.00      10.29   2.95         -6.58     -2.62          1.04
    post 2022-08-25           Thu->Fri 196       4.45   1.53       6.23   2.13         -1.78     -0.88          5.97
    post 2022-08-25 Fri->Mon (weekend) 185      -0.93  -0.17       9.55   2.01        -10.49     -2.71         11.55
    post 2022-08-25            holiday  19     -10.31  -0.62     -17.70  -0.93          7.39      0.70        -22.19
          2026 only           Mon->Tue  43      21.48   1.76      21.86   1.88         -0.38     -0.06         -2.65
          2026 only           Tue->Wed  43      27.77   1.53      22.61   2.05          5.15      0.68          9.81
          2026 only           Wed->Thu  42      -6.77  -0.82       4.42   0.79        -11.19     -2.47         -4.42
          2026 only           Thu->Fri  42      -4.87  -0.63       0.50   0.06         -5.37     -1.28         15.34
          2026 only Fri->Mon (weekend)  40     -20.51  -1.11       4.95   0.43        -25.45     -2.12         26.75
          2026 only            holiday   5      32.22   3.90       2.41   0.30         29.81     16.50        -53.14

C. Monday->Tuesday split:
                                       period   n  fut_ON_bp  fut_t  idx_part_bp  idx_t  dbasis_part_bp  dbasis_t  dbasis_share_pct
           full (index sample, 2018-11..2026) 378      11.81   4.40         8.50   3.20            3.31      1.25             28.01
   2017-21 where index exists (2018-11..2021) 141      14.84   2.83         3.03   0.96           11.80      2.29             79.55
                                      2022-25 194       7.46   3.67         9.51   2.65           -2.05     -0.73            -27.50
                                         2026  43      21.48   1.76        21.86   1.88           -0.38     -0.06             -1.76
reference: futures-only Option B full 2017-26 453      10.49   3.91          NaN    NaN             NaN       NaN               NaN
              reference: futures-only 2017-21 216      11.03   2.37          NaN    NaN             NaN       NaN               NaN

D. Wednesday->Thursday (PIT CW basket = one-day nights, filters off):
             period   n  idx_ON_bp  fut_ON_bp  idx_minus_fut_bp  idx_minus_fut_t  dbasis_ON_bp  dbasis_t  basket_minus_fut_bp  basket_minus_fut_t  basket_minus_idx_bp  basket_minus_idx_t
full (index sample) 369       7.23       2.78              4.46             2.09         -4.46     -2.09                 4.88                2.16                 0.42                0.17
     pre 2022-08-25 163       3.38       1.61              1.77             0.49         -1.77     -0.49                -1.35               -0.40                -3.12               -0.59
    post 2022-08-25 206      10.29       3.70              6.58             2.62         -6.58     -2.62                 9.80                3.56                 3.22                2.42
          2026 only  42       4.42      -6.77             11.19             2.47        -11.19     -2.47                10.85                2.20                -0.35               -0.27

E. Basis level and dbasis by days-to-expiry / night:
                  cut                          group   n  b_close_mean_bp  dbasis_ON_bp  dbasis_ON_t  dbasis_ID_bp  dbasis_ID_t
       days-to-expiry                            0-5 543            -5.69          0.93         0.60          3.68         1.43
       days-to-expiry                           6-10 453           -24.19         -3.80        -1.47          4.87         1.70
       days-to-expiry                          11-15 447           -27.79         -0.78        -0.37          0.56         0.23
       days-to-expiry                            16+ 410           -29.66         -0.62        -0.24          0.74         0.24
night (entry weekday)                       Mon->Tue 378           -22.61          3.31         1.25         -4.05        -1.47
night (entry weekday)                       Tue->Wed 374           -15.32         -1.37        -0.56          8.54         2.66
night (entry weekday)                       Wed->Thu 369           -18.01         -4.46        -2.09          0.85         0.29
night (entry weekday)                       Thu->Fri 368           -22.65          0.62         0.23          4.09         1.11
night (entry weekday)             Fri->Mon (weekend) 352           -21.11         -3.89        -0.91          5.97         1.39
night (entry weekday)                        holiday  35           -48.43          2.46         0.26        -19.95        -2.40
          night x dte             Mon->Tue | dte 0-5  91              NaN          8.13         1.34           NaN          NaN
          night x dte            Mon->Tue | dte 6-10  91              NaN          2.51         0.51           NaN          NaN
          night x dte           Mon->Tue | dte 11-15  92              NaN          0.02         0.00           NaN          NaN
          night x dte             Mon->Tue | dte 16+  99              NaN          3.17         0.85           NaN          NaN
          night x dte             Tue->Wed | dte 0-5  93              NaN          2.27         0.64           NaN          NaN
          night x dte            Tue->Wed | dte 6-10  95              NaN         -6.56        -1.03           NaN          NaN
          night x dte           Tue->Wed | dte 11-15  95              NaN          0.24         0.05           NaN          NaN
          night x dte             Tue->Wed | dte 16+  87              NaN         -1.38        -0.26           NaN          NaN
          night x dte             Wed->Thu | dte 0-5 174              NaN         -5.17        -1.53           NaN          NaN
          night x dte            Wed->Thu | dte 6-10  81              NaN         -7.66        -1.96           NaN          NaN
          night x dte           Wed->Thu | dte 11-15  84              NaN          0.27         0.06           NaN          NaN
          night x dte             Wed->Thu | dte 16+  26              NaN         -3.93        -0.73           NaN          NaN
          night x dte             Thu->Fri | dte 0-5  93              NaN          5.92         1.59           NaN          NaN
          night x dte            Thu->Fri | dte 6-10  87              NaN         -5.88        -0.95           NaN          NaN
          night x dte           Thu->Fri | dte 11-15  86              NaN         -4.34        -1.36           NaN          NaN
          night x dte             Thu->Fri | dte 16+  97              NaN          6.00         1.08           NaN          NaN
          night x dte   Fri->Mon (weekend) | dte 0-5  90              NaN         -2.40        -0.60           NaN          NaN
          night x dte  Fri->Mon (weekend) | dte 6-10  83              NaN         -8.32        -1.04           NaN          NaN
          night x dte Fri->Mon (weekend) | dte 11-15  76              NaN          6.47         1.01           NaN          NaN
          night x dte   Fri->Mon (weekend) | dte 16+  98              NaN         -9.30        -1.65           NaN          NaN
          night x dte             holiday | dte 6-10  16              NaN         30.99         2.57           NaN          NaN
          night x dte            holiday | dte 11-15  14              NaN        -36.90        -1.42           NaN          NaN

## F. Robustness: excluding roll nights and nights whose open date is expiry-1, expiry or expiry+1 (all days sample)
A:
year    n  fut_ON_bp  fut_t  idx_ON_bp  idx_t  dbasis_ON_bp  dbasis_t  corr  slope  slope_nw_se   r2  dbasis_ID_bp  idx_flag_pct
2018   24       4.88   0.47      -2.56  -0.24          7.44      0.98  0.57   0.81         0.25 0.32         -7.68          0.00
2019  214       3.95   1.74      -0.37  -0.11          4.33      1.32  0.34   0.35         0.16 0.11         -3.59         10.75
2020  216       4.79   0.55      -1.67  -0.59          6.46      0.91  0.37   0.97         0.09 0.14         -2.28         14.81
2021  212       7.44   1.88       5.97   2.88          1.47      0.37  0.35   0.51         0.09 0.12         -3.20          4.25
2022  211       2.89   0.72      -0.99  -0.22          3.87      1.16  0.72   0.72         0.07 0.51          0.85          1.90
2023  201      10.02   4.24      11.81   4.89         -1.78     -0.80  0.68   0.71         0.09 0.46          2.19          0.00
2024  214       2.72   1.49       7.22   3.77         -4.49     -3.34  0.74   0.82         0.05 0.54          4.09          0.47
2025  213       6.83   1.79      17.67   3.88        -10.84     -3.36  0.78   0.79         0.15 0.61         12.40          0.47
2026  186       4.02   1.07      10.59   3.25         -6.56     -2.62  0.74   1.00         0.11 0.55          6.67          0.00
 all 1691       5.31   3.44       6.03   4.95         -0.72     -0.52  0.57   0.76         0.06 0.33          1.92          4.14

B:
             period              night   n  fut_ON_bp  fut_t  idx_ON_bp  idx_t  dbasis_ON_bp  dbasis_t  dbasis_ID_bp
full (index sample)           Mon->Tue 390      12.20   4.26       8.23   3.19          3.97      1.38         -3.85
full (index sample)           Tue->Wed 301       5.95   1.61       8.74   3.25         -2.79     -1.05          9.17
full (index sample)           Wed->Thu 297       5.02   1.68       8.05   3.21         -3.03     -1.19         -2.46
full (index sample)           Thu->Fri 304       0.91   0.30       1.27   0.48         -0.36     -0.15          5.55
full (index sample) Fri->Mon (weekend) 366       1.78   0.38       4.15   1.41         -2.37     -0.57          4.05
full (index sample)            holiday  33       0.57   0.05       2.15   0.15         -1.58     -0.16        -13.42
     pre 2022-08-25           Mon->Tue 184      12.87   2.64       0.06   0.02         12.82      2.58         -9.97
     pre 2022-08-25           Tue->Wed 141       1.49   0.38       0.70   0.24          0.79      0.24          4.31
     pre 2022-08-25           Wed->Thu 138       4.22   1.02       4.77   2.12         -0.55     -0.13         -7.47
     pre 2022-08-25           Thu->Fri 142      -1.58  -0.30      -2.09  -0.51          0.51      0.11          5.23
     pre 2022-08-25 Fri->Mon (weekend) 179       4.38   0.59      -1.39  -0.45          5.78      0.81         -3.54
     pre 2022-08-25            holiday  17      14.52   1.10      25.11   2.25        -10.59     -0.71         -5.12
    post 2022-08-25           Mon->Tue 206      11.60   3.59      15.53   4.10         -3.93     -1.57          1.61
    post 2022-08-25           Tue->Wed 160       9.89   1.67      15.82   4.12         -5.93     -1.48         13.45
    post 2022-08-25           Wed->Thu 159       5.70   1.35      10.89   2.62         -5.19     -1.68          1.89
    post 2022-08-25           Thu->Fri 162       3.09   0.91       4.22   1.25         -1.13     -0.48          5.83
    post 2022-08-25 Fri->Mon (weekend) 187      -0.72  -0.13       9.45   2.00        -10.17     -2.67         11.32
    post 2022-08-25            holiday  16     -14.26  -0.97     -22.24  -1.10          7.99      0.65        -22.25
          2026 only           Mon->Tue  43      21.48   1.76      21.86   1.88         -0.38     -0.06         -2.65
          2026 only           Tue->Wed  34      31.23   1.62      25.12   2.16          6.11      0.73          7.75
          2026 only           Wed->Thu  32      -5.32  -0.96       6.27   1.18        -11.60     -3.25         -1.08
          2026 only           Thu->Fri  33     -10.37  -1.10      -5.94  -0.62         -4.43     -1.25          9.40
          2026 only Fri->Mon (weekend)  40     -20.51  -1.11       4.95   0.43        -25.45     -2.12         26.75
          2026 only            holiday   4      23.99   3.16      -6.83  -0.91         30.83     12.84        -63.70

C:
                                       period   n  fut_ON_bp  fut_t  idx_part_bp  idx_t  dbasis_part_bp  dbasis_t  dbasis_share_pct
           full (index sample, 2018-11..2026) 390      12.20   4.26         8.23   3.19            3.97      1.38             32.57
   2017-21 where index exists (2018-11..2021) 154      15.44   2.72         2.78   0.95           12.66      2.21             82.00
                                      2022-25 193       7.56   3.70         9.54   2.65           -1.99     -0.70            -26.28
                                         2026  43      21.48   1.76        21.86   1.88           -0.38     -0.06             -1.76
reference: futures-only Option B full 2017-26 451      10.42   3.87          NaN    NaN             NaN       NaN               NaN
              reference: futures-only 2017-21 215      10.77   2.31          NaN    NaN             NaN       NaN               NaN

D:
             period   n  idx_ON_bp  fut_ON_bp  idx_minus_fut_bp  idx_minus_fut_t  dbasis_ON_bp  dbasis_t  basket_minus_fut_bp  basket_minus_fut_t  basket_minus_idx_bp  basket_minus_idx_t
full (index sample) 297       8.05       5.02              3.03             1.19         -3.03     -1.19                 4.79                2.04                 1.76                0.70
     pre 2022-08-25 138       4.77       4.22              0.55             0.13         -0.55     -0.13                 0.09                0.03                -0.45               -0.09
    post 2022-08-25 159      10.89       5.70              5.19             1.68         -5.19     -1.68                 8.87                2.72                 3.68                2.30
          2026 only  32       6.27      -5.32             11.60             3.25        -11.60     -3.25                11.54                3.17                -0.06               -0.04

## Step 3: pre-registered reads (as written, before results)
- R1: Monday futures edge is mostly basis if dbasis_ON accounts for >50% of Monday futures ON with |t| > 2 in the periods where the index exists.
- R2: Wednesday gap is an overnight-basis effect if mean dbasis_ON on Wed->Thu is negative, within ~1.5 bp of -(index ON - futures ON), with |t| > 2.
- R3: Futures track the index overnight only if the slope in table A is within +/-0.25 of 1 in most years.
- Between thresholds = ambiguous.

## Verdicts
[a_all_days] R1 MIXED/AMBIGUOUS (holds only in: 2017-21 where index exists (2018-11..2021)) (full (index sample, 2018-11..2026): share 32%, t 1.36; 2017-21 where index exists (2018-11..2021): share 82%, t 2.21; 2022-25: share -28%, t -0.73; 2026: share -2%, t -0.06). R2 HOLDS: Wed->Thu dbasis_ON -4.10 bp (NW t -2.001; excluding roll/near-expiry nights -3.03 bp, t -1.19, n 297); -(idx-fut) on the same nights is -4.10 bp, identical by construction, so the 1.5 bp condition is automatic; the substantive check is against the earlier PIT-basket-minus-futures gap of 4.83 bp: -dbasis_ON = 4.10 bp, 0.73 bp away; on the basket's own dates the basket-minus-futures gap is 5.01 bp = basket-minus-index 0.91 bp + index-minus-futures 4.10 bp. R3 HOLDS (futures track the index overnight): slope within 1 +/- 0.25 in 6 of 9 years (slopes 2018: 0.84, 2019: 0.36, 2020: 0.98, 2021: 0.46, 2022: 0.71, 2023: 0.76, 2024: 0.84, 2025: 0.78, 2026: 0.99).
[b_ex_index_flagged] R1 MIXED/AMBIGUOUS (holds only in: 2017-21 where index exists (2018-11..2021)) (full (index sample, 2018-11..2026): share 28%, t 1.25; 2017-21 where index exists (2018-11..2021): share 80%, t 2.29; 2022-25: share -28%, t -0.73; 2026: share -2%, t -0.06). R2 HOLDS: Wed->Thu dbasis_ON -4.46 bp (NW t -2.087; excluding roll/near-expiry nights -3.51 bp, t -1.34, n 282); -(idx-fut) on the same nights is -4.46 bp, identical by construction, so the 1.5 bp condition is automatic; the substantive check is against the earlier PIT-basket-minus-futures gap of 4.83 bp: -dbasis_ON = 4.46 bp, 0.37 bp away; on the basket's own dates the basket-minus-futures gap is 4.88 bp = basket-minus-index 0.42 bp + index-minus-futures 4.46 bp. R3 HOLDS (futures track the index overnight): slope within 1 +/- 0.25 in 6 of 9 years (slopes 2018: 0.84, 2019: 0.36, 2020: 0.98, 2021: 0.46, 2022: 0.71, 2023: 0.76, 2024: 0.84, 2025: 0.78, 2026: 0.99).
