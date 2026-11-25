# Level B + 2x2 rebuild, symmetric 7% rule (src/level_b_rebuild.py)

Rules are in the script header (pre-registered). Primary treatment P; L and O are checks.

Treatments: P = no outcome filter; L = drop night if |ON|>7% or |ID|>7%; O = legacy: open_suspicious or |ON|>7%

## 1. Level B per stock (summary across 30 current-VN30 names)

```
treat leg  stocks  pos_mean  t_gt2  t_lt_m2  median_sharpe
    L  ID   30.00     21.00   5.00     3.00           0.27
    L  ON   30.00     25.00  22.00     2.00           2.02
    O  ID   30.00     20.00   4.00     3.00           0.21
    O  ON   30.00     25.00  21.00     2.00           1.81
    P  ID   30.00     22.00   5.00     3.00           0.40
    P  ON   30.00     23.00  19.00     2.00           1.23
```

## 2. 2x2 day-of-week: Mon+Tue minus Wed+Thu, plain Welch t by treatment (mean bp below)

```
treat            L    O    P
leg cell                    
CC  cur30_cap 3.59 3.30 3.54
    cur30_ew  3.89 3.78 3.87
    pit_cap   3.63 3.32 3.57
    pit_ew    3.93 3.61 3.86
ID  cur30_cap 2.83 2.33 2.58
    cur30_ew  3.35 3.05 3.11
    pit_cap   2.86 2.33 2.56
    pit_ew    3.35 2.83 3.06
ON  cur30_cap 2.02 1.99 1.99
    cur30_ew  1.71 1.63 1.67
    pit_cap   2.02 1.98 2.03
    pit_ew    1.69 1.52 1.61

treat             L     O     P
leg cell                       
CC  cur30_cap 20.76 20.60 21.05
    cur30_ew  22.19 23.55 23.11
    pit_cap   20.83 20.37 20.92
    pit_ew    22.22 21.86 22.48
ID  cur30_cap 14.65 13.61 14.49
    cur30_ew  17.11 17.86 17.63
    pit_cap   14.62 13.38 14.16
    pit_ew    16.98 16.41 17.00
ON  cur30_cap  6.11  7.00  6.56
    cur30_ew   5.08  5.69  5.48
    pit_cap    6.20  6.99  6.76
    pit_ew     5.25  5.45  5.49
```

Full weekday table: results/level_b_rebuild_dayofweek.csv. Old (legacy 2x2) vs rebuilt O, PIT CW ON:

```
                night  n_old  mean_bp_old    t  n_rebuild_O  mean_bp_rebuild_O  plain_t
             Mon->Tue    390        15.87 4.89          390              15.87     4.89
             Tue->Wed    394        11.82 3.54          394              11.82     3.54
             Wed->Thu    391        10.92 2.84          391              10.92     2.84
             Thu->Fri    397         2.83 0.78          397               2.83     0.78
Mon+Tue minus Wed+Thu   1572         6.99 1.98         1572               6.99     1.98
```

## 3. Regime split of PIT CW basket at 2022-08-25

```
treat leg  n_pre  n_post  pre_bp  post_bp  pre_nw_t  post_nw_t  diff_bp  break_t
    P  ON    740     833   -0.60    13.06     -0.21       5.58    13.66     3.65
    P  ID    740     833   10.84    -2.97      2.90      -0.89   -13.81    -2.75
    P  CC    740     833   10.24    10.08      2.64       2.78    -0.15    -0.03
    L  ON    740     831   -0.05    15.26     -0.02       8.33    15.31     4.73
    L  ID    740     831   10.80    -4.42      3.06      -1.46   -15.22    -3.27
    L  CC    740     831   10.75    10.83      2.89       3.05     0.09     0.02
    O  ON    739     833    1.69    18.00      0.56       7.77    16.31     4.30
    O  ID    739     833   10.08    -4.59      2.60      -1.34   -14.67    -2.83
    O  CC    739     833   11.77    13.41      2.93       3.54     1.64     0.30
```

R1 verdict on break t: CC TREATMENT-DEPENDENT; ID TREATMENT-ROBUST; ON TREATMENT-ROBUST

## 4. H3 persistence (tercile spread, next-month nights)

```
treat sample leg  months  spread_bp_per_night  nw3_t  top_bp  bot_bp
    P   full  ON      93                18.06  10.31   14.10   -3.96
    P   full  ID      93               -16.31  -5.27   -4.30   12.01
    P    pre  ON      42                18.78   6.43    5.78  -13.00
    P    pre  ID      42               -15.24  -4.60    6.90   22.14
    P   post  ON      51                17.47   8.34   20.95    3.48
    P   post  ID      51               -17.20  -3.48  -13.52    3.67
    L   full  ON      93                17.35  12.73   16.83   -0.52
    L   full  ID      93               -17.78  -6.76   -5.23   12.55
    L    pre  ON      42                17.56   7.18    7.91   -9.64
    L    pre  ID      42               -14.25  -4.84    8.01   22.26
    L   post  ON      51                17.18  11.92   24.18    7.00
    L   post  ID      51               -20.68  -5.18  -16.12    4.56
    O   full  ON      14                 3.49   0.38   24.27   20.78
    O   full  ID      14               -10.36  -1.01  -11.86   -1.51
    O    pre  ON       3                -7.21  -1.97   -3.80    3.41
    O    pre  ID       3               -27.44  -5.21  -10.86   16.58
    O   post  ON      11                 6.41   0.60   31.92   25.52
    O   post  ID      11                -5.70  -0.45  -12.14   -6.44
```

R2 verdict (P, full sample): ON spread t 10.31, ID spread t -5.27 -> H3 SUPPORTED.

## 5. 2018-11-21 check

```
treat basket first_date  has_2018_11_21    n
    P    pit 2018-11-22           False 1573
    P  cur30 2018-11-22           False 1573
    L    pit 2018-11-22           False 1571
    L  cur30 2018-11-22           False 1571
    O    pit 2018-11-22           False 1572
    O  cur30 2018-11-22           False 1568
```

Integrity (no existing file changed, only level_b_rebuild* created): True

## Summary (5 lines)

1. Treatments P/L/O applied identically to Level B, 2x2, regime split and H3; the legacy 2x2 dropped flat opens and |ON|>7% nights on the ON leg only.
2. Level B per stock (P): ID 22/30 positive, 5 with NW t>2, 3 with t<-2; ON 23/30 positive, 19 with NW t>2, 2 with t<-2.
3. Regime break t (PIT CW, post minus pre): CC -0.03/0.02/0.30 (TREATMENT-DEPENDENT); ID -2.75/-3.27/-2.83 (TREATMENT-ROBUST); ON 3.65/4.73/4.30 (TREATMENT-ROBUST) for P/L/O.
4. H3 (P, full): ON spread 18.06 bp (t 10.31), ID spread -16.31 bp (t -5.27) -> SUPPORTED.
5. 2018-11-21 night present in all basket series: False; integrity True. Differences vs old files reported, not reinterpreted.
