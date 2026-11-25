# Level B + 2x2 rebuild, symmetric 7% rule (src/level_b_rebuild.py)

Rules are in the script header (pre-registered). Primary treatment P; L and O are checks.

Treatments: P = no outcome filter; L = drop night if |ON|>7% or |ID|>7%; O = legacy: open_suspicious or |ON|>7%

## 1. Level B per stock (summary across 30 current-VN30 names)

```
treat leg  stocks  pos_mean  t_gt2  t_lt_m2  median_sharpe
    L  ID   30.00     21.00   5.00     3.00           0.28
    L  ON   30.00     26.00  22.00     2.00           2.01
    O  ID   30.00     20.00   4.00     3.00           0.22
    O  ON   30.00     25.00  21.00     1.00           1.79
    P  ID   30.00     23.00   5.00     3.00           0.40
    P  ON   30.00     23.00  19.00     2.00           1.22
```

## 2. 2x2 day-of-week: Mon+Tue minus Wed+Thu, plain Welch t by treatment (mean bp below)

```
treat            L    O    P
leg cell                    
CC  cur30_cap 3.60 3.31 3.54
    cur30_ew  3.89 3.78 3.87
    pit_cap   3.64 3.33 3.58
    pit_ew    3.95 3.62 3.87
ID  cur30_cap 2.87 2.37 2.61
    cur30_ew  3.39 3.08 3.14
    pit_cap   2.90 2.37 2.60
    pit_ew    3.40 2.88 3.11
ON  cur30_cap 1.97 1.94 1.94
    cur30_ew  1.65 1.57 1.62
    pit_cap   1.97 1.93 1.98
    pit_ew    1.63 1.47 1.55

treat             L     O     P
leg cell                       
CC  cur30_cap 20.78 20.63 21.07
    cur30_ew  22.19 23.54 23.11
    pit_cap   20.87 20.43 20.96
    pit_ew    22.28 21.93 22.55
ID  cur30_cap 14.83 13.81 14.66
    cur30_ew  17.28 18.05 17.80
    pit_cap   14.83 13.62 14.37
    pit_ew    17.22 16.68 17.24
ON  cur30_cap  5.95  6.82  6.41
    cur30_ew   4.91  5.49  5.32
    pit_cap    6.04  6.81  6.60
    pit_ew     5.06  5.25  5.30
```

Full weekday table: results/level_b_rebuild_dayofweek.csv. Old (legacy 2x2) vs rebuilt O, PIT CW ON:

```
                night  n_old  mean_bp_old    t  n_rebuild_O  mean_bp_rebuild_O  plain_t
             Mon->Tue    390        15.87 4.89          390              15.87     4.89
             Tue->Wed    394        11.82 3.54          395              11.47     3.43
             Wed->Thu    391        10.92 2.84          391              10.92     2.84
             Thu->Fri    397         2.83 0.78          397               2.83     0.78
Mon+Tue minus Wed+Thu   1572         6.99 1.98         1573               6.81     1.93
```

## 3. Regime split of PIT CW basket at 2022-08-25

```
treat leg  n_pre  n_post  pre_bp  post_bp  pre_nw_t  post_nw_t  diff_bp  break_t
    P  ON    741     833   -0.75    13.06     -0.26       5.58    13.81     3.70
    P  ID    741     833   11.04    -2.97      2.96      -0.89   -14.02    -2.80
    P  CC    741     833   10.29    10.08      2.66       2.78    -0.21    -0.04
    L  ON    741     831   -0.20    15.26     -0.08       8.33    15.46     4.78
    L  ID    741     831   11.00    -4.42      3.12      -1.46   -15.43    -3.32
    L  CC    741     831   10.80    10.83      2.90       3.05     0.03     0.01
    O  ON    740     833    1.52    18.00      0.51       7.77    16.48     4.35
    O  ID    740     833   10.32    -4.59      2.67      -1.34   -14.91    -2.88
    O  CC    740     833   11.84    13.41      2.95       3.54     1.57     0.28
```

R1 verdict on break t: CC TREATMENT-DEPENDENT; ID TREATMENT-ROBUST; ON TREATMENT-ROBUST

## 4. H3 persistence (tercile spread, next-month nights)

```
treat        mode sample leg  months  spread_bp_per_night  nw3_t  top_bp  bot_bp
    P        base   full  ON      94                17.94  10.42   13.95   -4.00
    P        base   full  ID      94               -16.85  -5.37   -4.30   12.55
    P        base    pre  ON      43                18.51   6.56    5.65  -12.86
    P        base    pre  ID      43               -16.43  -4.62    6.64   23.07
    P        base   post  ON      51                17.47   8.34   20.95    3.48
    P        base   post  ID      51               -17.20  -3.48  -13.52    3.67
    P D1_demeaned   full  ON      80                 9.22   5.42   12.82    3.60
    P D1_demeaned   full  ID      80               -10.33  -3.32   -2.22    8.11
    P D1_demeaned    pre  ON      29                 4.66   2.84    3.79   -0.87
    P D1_demeaned    pre  ID      29                -3.84  -1.14   15.78   19.62
    P D1_demeaned   post  ON      51                11.82   5.38   17.96    6.14
    P D1_demeaned   post  ID      51               -14.02  -3.34  -12.45    1.56
    P   D2_lag12m   full  ON      81                 9.30   4.24   12.58    3.28
    P   D2_lag12m   full  ID      81                -4.51  -1.52    0.11    4.62
    P   D2_lag12m    pre  ON      30                 9.53   2.64    3.99   -5.54
    P   D2_lag12m    pre  ID      30                -1.24  -0.36   16.13   17.38
    P   D2_lag12m   post  ON      51                 9.17   3.33   17.63    8.46
    P   D2_lag12m   post  ID      51                -6.44  -1.56   -9.31   -2.88
    L        base   full  ON      94                16.96  12.60   16.67   -0.29
    L        base   full  ID      94               -17.99  -6.87   -5.19   12.80
    L        base    pre  ON      43                16.71   6.99    7.77   -8.94
    L        base    pre  ID      43               -14.80  -4.95    7.77   22.58
    L        base   post  ON      51                17.18  11.92   24.18    7.00
    L        base   post  ID      51               -20.68  -5.18  -16.12    4.56
    L D1_demeaned   full  ON      80                 8.50   7.92   15.74    7.24
    L D1_demeaned   full  ID      80               -12.20  -4.27   -4.31    7.89
    L D1_demeaned    pre  ON      29                 5.38   3.50    7.31    1.92
    L D1_demeaned    pre  ID      29                -6.18  -1.85   13.02   19.21
    L D1_demeaned   post  ON      51                10.27   8.49   20.53   10.27
    L D1_demeaned   post  ID      51               -15.62  -4.12  -14.17    1.45
    L   D2_lag12m   full  ON      81                 7.85   4.69   15.15    7.30
    L   D2_lag12m   full  ID      81                -7.79  -3.07   -2.51    5.28
    L   D2_lag12m    pre  ON      30                 8.51   2.73    7.04   -1.46
    L   D2_lag12m    pre  ID      30                -6.94  -1.92   11.00   17.94
    L   D2_lag12m   post  ON      51                 7.46   3.89   19.92   12.46
    L   D2_lag12m   post  ID      51                -8.30  -2.45  -10.46   -2.16
    O        base   full  ON      14                 3.49   0.38   24.27   20.78
    O        base   full  ID      14               -10.36  -1.01  -11.86   -1.51
    O        base    pre  ON       3                -7.21    NaN   -3.80    3.41
    O        base    pre  ID       3               -27.44    NaN  -10.86   16.58
    O        base   post  ON      11                 6.41   0.60   31.92   25.52
    O        base   post  ID      11                -5.70  -0.45  -12.14   -6.44
    O D1_demeaned   full  ON      14                -3.54  -0.53   23.00   26.54
    O D1_demeaned   full  ID      14                -4.14  -0.36  -14.23  -10.09
    O D1_demeaned    pre  ON       3                 3.55    NaN    7.75    4.20
    O D1_demeaned    pre  ID       3               -23.93    NaN  -11.09   12.84
    O D1_demeaned   post  ON      11                -5.48  -0.63   27.16   32.64
    O D1_demeaned   post  ID      11                 1.25   0.09  -15.09  -16.34
    O   D2_lag12m   full  ON      13                 4.93   1.37   23.33   18.40
    O   D2_lag12m   full  ID      13                11.10   1.77   -7.68  -18.78
    O   D2_lag12m    pre  ON       1                -0.18    NaN    0.90    1.08
    O   D2_lag12m    pre  ID       1               -15.60    NaN  -29.17  -13.57
    O   D2_lag12m   post  ON      12                 5.35   1.32   25.20   19.85
    O   D2_lag12m   post  ID      12                13.32   2.02   -5.89  -19.21
```

R2 verdict (P, full sample, base): ON spread t 10.42, ID spread t -5.37 -> H3 SUPPORTED.
Diagnostics (ADDED AFTER RUN 0): D1 demeaned score ON 9.22 bp (t 5.42), ID -10.33 bp (t -3.32); D2 12-month lag ON 9.30 bp (t 4.24), ID -4.51 bp (t -1.52).
Treatment O drops flat opens, which leaves < 40 valid nights per stock in most windows, so its H3 rows have few months and are not comparable (coverage, not a result).

## 5. 2018-11-21 check

```
treat basket first_date  has_2018_11_21    n
    P    pit 2018-11-21            True 1574
    P  cur30 2018-11-21            True 1574
    L    pit 2018-11-21            True 1572
    L  cur30 2018-11-21            True 1572
    O    pit 2018-11-21            True 1573
    O  cur30 2018-11-21            True 1569
```

Integrity (no existing file changed, only level_b_rebuild* created): True

## Summary (5 lines)

1. Treatments P/L/O applied identically to Level B, 2x2, regime split and H3; the legacy 2x2 dropped flat opens and |ON|>7% nights on the ON leg only.
2. Level B per stock (P): ID 23/30 positive, 5 with NW t>2, 3 with t<-2; ON 23/30 positive, 19 with NW t>2, 2 with t<-2.
3. Regime break t (PIT CW, post minus pre): CC -0.04/0.01/0.28 (TREATMENT-DEPENDENT); ID -2.80/-3.32/-2.88 (TREATMENT-ROBUST); ON 3.70/4.78/4.35 (TREATMENT-ROBUST) for P/L/O.
4. H3 (P, full, base): ON spread 17.94 bp (t 10.42), ID -16.85 bp (t -5.37) -> SUPPORTED; D1 demeaned t 5.42/-3.32; D2 lag-12m t 4.24/-1.52 (ON/ID).
5. 2018-11-21 night present in all basket series: True; integrity True. Differences vs old files reported, not reinterpreted.
