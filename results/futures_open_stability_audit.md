# Futures open stability audit (continuous VN30F1M, 2017-2026)

Diagnostic only. Read-only on data/raw/ and results/; no main result re-run, nothing filtered. Script: `src/futures_open_stability_audit.py`.

Question: can the continuous VN30F1M opens before 2022-06-20 be told apart from the verified opens (2022-11-03 onward, 100% match with per-contract tickers) using only data already held?

## Pre-registered rules (written into the script header before the first run; not changed)

- Step 1: a period is flagged on a measure if its equality rate is >= 3x the verified-window rate. Distance is |open - reference| in 0.1-point ticks; `spike` = share at 0 ticks / mean share at 1-2 ticks (a filled or stale open shows as a spike at 0 relative to its neighbours; chance coincidence, which rises at lower price levels, does not). Prior close = same-contract prior close, i.e. `build()` entry (VN30F2M close on roll days).
- Steps 2-3: invested, aligned nights, index open not flagged; fixed-first-row index nights. Quarter departs from the pooled verified window on k if |k_q - k_ver| > 2 NW SE(k_q); on R^2 if Fisher-z distance > 2 sqrt(1/(n_q-3)+1/(n_ver-3)); on residual SD if sd_q/sd_ver is outside 1 +/- 2/sqrt(2 n_q).
- Breaks: Chow-type +/-60 nights at 2022-07-11, 2022-08-25, 2022-11-03 (HAC Wald chi2(2) on intercept and slope shift; log residual-variance ratio z), plus a sup-Wald scan over all dates (15% trim; Andrews 5% critical value ~11.79).
- Primary futures file: `data/raw/VN30F1M.csv` (what published results use). Sensitivity: `VN30F1M_repaired.csv`, night 2021-05-04 excluded.

## 1. Filled-open detector, by year

```
                                  period  n_days prior_close_eq_pct prior_close_spike close_eq_pct close_spike high_eq_pct high_spike low_eq_pct low_spike lock_OHLC_n open_outside_range_n open_whole_point_pct median_price
                                    2017      95               5.26              0.71         3.16        6.00        1.05       1.00       6.32      1.50           0                    0                31.58          816
                                    2018     239               2.51              1.71         0.84        4.00        1.67       1.60       0.84      1.00           0                    0                46.86          964
                                    2019     250               5.20              1.24         1.20        0.50        2.00       1.11       3.60      2.00           0                    0                30.00          885
                                    2020     252               4.37              2.44         0.79        1.33        1.59       4.00       4.76      8.00           0                    0                38.89          829
                                    2021     249               2.41              0.86         0.40        0.33        0.80       1.33       1.61      8.00           0                    0                36.14         1442
                                    2022     247               2.43              2.40         1.21        1.50        4.45       4.40       1.21      1.20           0                    0                41.30         1269
                                    2023     237               4.64              2.75         0.84        4.00        4.64      11.00       5.91      5.60           0                    0                21.94         1099
                                    2024     250               2.40              1.20         0.40        0.29        2.00       5.00       4.00      4.00           0                    0                24.80         1294
                                    2025     249               4.82              2.40         1.20        1.50        4.02       6.67       4.02                     0                    0                38.55         1494
                                    2026     216               0.93              0.36         0.00        0.00        0.93       1.33       0.46      0.50           0                    0                45.37         1957
          episode 2022-07-11..2022-11-02      81               1.23              1.00         1.23        1.00        4.94       2.67       0.00      0.00           0                    0                39.51         1224
          pre-ticker 2017-08..2022-06-19    1196               3.76              1.36         1.09        1.04        1.67       1.82       3.01      2.67           0                    0                37.79          934
BASELINE verified 2022-11-03..2026-11-17     992               3.23              1.60         0.60        0.92        3.02       5.45       3.53      5.00           0                    0                32.56         1321
```

Equality rate as a multiple of baseline:

```
                                  period prior_close_eq_x_baseline close_eq_x_baseline high_eq_x_baseline low_eq_x_baseline
                                    2017                      1.63                5.22               0.35              1.79
                                    2018                      0.78                1.38               0.55              0.24
                                    2019                      1.61                1.98               0.66              1.02
                                    2020                      1.35                1.31               0.52              1.35
                                    2021                      0.75                0.66               0.27              0.46
                                    2022                      0.75                2.01               1.47              0.34
                                    2023                      1.44                1.40               1.53              1.67
                                    2024                      0.74                0.66               0.66              1.13
                                    2025                      1.49                1.99               1.33              1.14
                                    2026                      0.29                0.00               0.31              0.13
          episode 2022-07-11..2022-11-02                      0.38                2.04               1.63              0.00
          pre-ticker 2017-08..2022-06-19                      1.17                1.80               0.55              0.85
BASELINE verified 2022-11-03..2026-11-17                      1.00                1.00               1.00              1.00
```

- Flagged (>= 3x baseline): 2017 [close].
- Baseline (verified window): open = prior close 3.23% (spike 1.60), = close 0.60%, = high 3.02%, = low 3.53%.
- Open outside [low, high]: 0 day(s).
- O=H=L=C lock days: 0 in total ().
- Open = close days in 2017 (the only flag): 2017-09-27 (O 787.0, H 787.6, L 786.4, C 787.0, prior close 787.0), 2017-12-15 (O 935.0, H 939.0, L 927.0, C 935.0, prior close 928.0), 2017-12-29 (O 980.0, H 988.8, L 978.0, C 980.0, prior close 977.9); 3 of 95 days, each with a real intraday range, so the 3x flag rests on 3 days.
- Spike ratio blank = no days at 1-2 ticks in that period (undefined).
- The file's own `open_suspicious` column compares with the naive prior close (expiring contract on roll days); it is not used here (kept in the CSV as `file_open_suspicious_pct`).
- Whole-point prices (decimal .0) are over-represented in every year (round-number clustering, not a grid change: every price is on the 0.1 grid in every year).

## 2-3. Quarterly relation, futures vs VN30 index (original file)

Verified window pooled (2022-11-03..2026-11-17): ON n 974, k 0.805 (NW SE 0.072), a -3.09 bp, R^2 0.533, resid SD 37.4 bp | CC n 974, k 0.999 (SE 0.014), a 0.59 bp, R^2 0.915, resid SD 37.4 bp.

### Overnight: fut_ON on idx_ON (log, bp)

(sd_y = SD of the futures leg, sd_x = SD of the index leg; k_reverse = slope of index on futures.)

```
                         period   n      k k_nw_se intercept_bp    r2 resid_sd_bp sd_y_bp sd_x_bp k_reverse depart_k depart_r2 depart_sd idx_flag_rate_all_nights
                         2018Q4  28  0.799   0.245         5.54 0.362       54.34   66.79   50.34     0.454        .         .         X                    0.000
                         2019Q1  53  0.439   0.254         9.35 0.104       42.15   44.10   32.37     0.237        .         X         .                    0.086
                         2019Q2  58  0.361   0.170         4.54 0.300       28.45   33.71   51.15     0.831        X         X         X                    0.049
                         2019Q3  55  0.331   0.404         0.95 0.064       37.50   38.40   29.38     0.194        .         X         .                    0.154
                         2019Q4  55 -0.047   0.329         1.83 0.002       18.83   18.67   15.53    -0.033        X         X         X                    0.167
                         2020Q1  53  0.905   0.118       -20.59 0.192      123.59  136.16   65.96     0.212        .         X         X                    0.102
                         2020Q2  51  1.997   0.458        14.72 0.093      109.78  114.10   17.40     0.046        X         X         X                    0.177
                         2020Q3  55  0.921   0.189        14.72 0.209       71.67   79.85   39.65     0.227        .         X         X                    0.154
                         2020Q4  54  0.314   0.316        14.02 0.026       27.87   27.97   14.43     0.084        .         X         X                    0.182
                         2021Q1  54  6.464   1.848         4.86 0.330       69.01   83.54    7.43     0.051        X         .         X                    0.069
                         2021Q2  54  1.869   0.599        15.43 0.201       25.89   28.69    6.88     0.108        .         X         X                    0.097
                         2021Q3  63  0.430   0.108         4.79 0.460       24.46   33.00   52.02     1.069        X         .         X                    0.016
                         2021Q4  66  0.364   0.060        -0.41 0.280       18.97   22.19   32.32     0.771        X         X         X                    0.000
                         2022Q1  58  0.812   0.109         0.31 0.588       24.68   38.14   36.01     0.724        .         .         X                    0.000
                         2022Q2  59  0.571   0.094         0.79 0.481       45.70   62.90   76.46     0.843        X         .         X                    0.048
                         2022Q3  64  0.935   0.079        -0.33 0.718       26.71   49.87   45.20     0.768        .         X         X                    0.000
                         2022Q4  60  0.725   0.096         9.05 0.550       57.26   84.67   86.60     0.759        .         .         X                    0.015
                         2023Q1  53  0.901   0.097        -1.22 0.584       32.01   49.16   41.72     0.649        .         .         .                    0.000
                         2023Q2  56  0.626   0.220        -2.28 0.302       21.60   25.62   22.51     0.483        .         X         X                    0.000
                         2023Q3  57  0.459   0.090         2.40 0.315       18.96   22.70   27.77     0.686        X         X         X                    0.000
                         2023Q4  59  0.884   0.225        10.66 0.556       32.25   47.99   40.50     0.629        .         .         .                    0.000
                         2024Q1  59  0.749   0.110        -4.34 0.378       17.81   22.38   18.36     0.504        .         .         X                    0.000
                         2024Q2  61  0.871   0.065        -6.54 0.568       26.36   39.75   34.38     0.651        .         .         X                    0.000
                         2024Q3  64  0.871   0.081        -2.21 0.651       22.31   37.45   34.68     0.747        .         .         X                    0.000
                         2024Q4  65  0.756   0.116        -1.12 0.253       23.03   26.44   17.59     0.335        .         X         X                    0.015
                         2025Q1  57  0.877   0.095        -4.41 0.622       18.84   30.35   27.28     0.709        .         .         X                    0.017
                         2025Q2  61  0.944   0.091        -3.57 0.704       69.48  126.70  112.66     0.746        .         X         X                    0.000
                         2025Q3  64  0.417   0.071        -3.58 0.385       20.82   26.34   39.18     0.923        X         .         X                    0.000
                         2025Q4  66  0.315   0.071         3.30 0.313       23.83   28.53   50.60     0.993        X         X         X                    0.000
                         2026Q1  57  1.059   0.166       -12.89 0.474       72.52   99.11   64.44     0.448        .         .         X                    0.000
                         2026Q2  62  1.096   0.193        -7.84 0.644       42.29   70.31   51.48     0.588        .         .         .                    0.000
                         2026Q3  62  0.544   0.040        -0.61 0.577       16.29   24.85   34.72     1.062        X         .         X                    0.016
                         2026Q4  34  1.025   0.064        -4.09 0.826       20.11   47.48   42.09     0.806        X         X         X                    0.000
VERIFIED 2022-11-03..2026-11-17 974  0.805   0.072        -3.09 0.533       37.35   54.65   49.60     0.663        .         .         .                         
 episode 2022-07-11..2022-11-02  81  0.948   0.069         1.56 0.721       35.17   66.22   59.30     0.761        X         X         .                         
        pre 2018-11..2022-06-19 808  0.640   0.073         3.78 0.168       58.34   63.90   40.84     0.262        X         X         X                         
```

### Control, close-to-close: fut_CC on idx_CC (same entry as build())

(sd_y = SD of the futures leg, sd_x = SD of the index leg; k_reverse = slope of index on futures.)

```
                         period   n     k k_nw_se intercept_bp    r2 resid_sd_bp sd_y_bp sd_x_bp k_reverse depart_k depart_r2 depart_sd idx_flag_rate_all_nights
                         2018Q4  28 0.936   0.043         2.33 0.791       44.98   96.50   91.70     0.845        .         X         .                    0.000
                         2019Q1  53 0.987   0.090         6.10 0.723       60.21  113.23   97.49     0.732        .         X         X                    0.086
                         2019Q2  58 0.969   0.109        -0.21 0.686       44.45   78.68   67.24     0.708        .         X         X                    0.049
                         2019Q3  55 0.924   0.126         0.86 0.650       42.03   70.34   61.37     0.703        .         X         .                    0.154
                         2019Q4  55 0.860   0.057        -3.78 0.772       26.04   54.05   55.23     0.898        X         X         X                    0.167
                         2020Q1  53 1.087   0.052         6.27 0.846       95.66  241.62  204.56     0.779        .         X         X                    0.102
                         2020Q2  51 1.219   0.130        10.88 0.689      121.37  215.44  146.65     0.565        .         X         X                    0.177
                         2020Q3  55 1.187   0.034         6.19 0.907       54.16  175.83  141.10     0.764        X         .         X                    0.154
                         2020Q4  54 0.979   0.051         1.73 0.866       35.61   96.41   91.62     0.884        .         .         .                    0.182
                         2021Q1  54 1.151   0.052        -3.92 0.898       79.22  245.38  201.99     0.780        X         .         X                    0.069
                         2021Q2  54 1.183   0.064        -3.48 0.896       50.05  153.39  122.72     0.757        X         .         X                    0.097
                         2021Q3  63 0.986   0.057         1.33 0.928       37.53  138.93  135.76     0.941        .         .         .                    0.016
                         2021Q4  66 0.959   0.050        -0.45 0.902       28.96   91.89   91.02     0.941        .         .         X                    0.000
                         2022Q1  58 0.802   0.034        -1.77 0.908       27.63   90.18  107.17     1.132        X         .         X                    0.000
                         2022Q2  59 0.949   0.035         1.22 0.931       52.61  198.16  201.46     0.981        .         .         X                    0.048
                         2022Q3  64 0.803   0.059         1.51 0.801       36.91   82.06   91.44     0.997        X         X         .                    0.000
                         2022Q4  60 1.081   0.048        10.30 0.873       99.10  275.28  237.78     0.807        .         .         X                    0.015
                         2023Q1  53 1.014   0.026        -1.83 0.942       33.46  138.08  132.14     0.929        .         .         .                    0.000
                         2023Q2  56 0.889   0.045         4.95 0.870       23.74   65.23   68.43     0.978        X         .         X                    0.000
                         2023Q3  57 0.994   0.044         0.49 0.922       25.26   89.41   86.38     0.927        .         .         X                    0.000
                         2023Q4  59 1.037   0.030         0.90 0.946       32.70  139.69  131.02     0.912        .         .         .                    0.000
                         2024Q1  59 1.014   0.042        -3.27 0.918       27.15   94.22   89.04     0.906        .         .         X                    0.000
                         2024Q2  61 0.964   0.037         0.42 0.940       26.84  108.94  109.59     0.975        .         .         X                    0.000
                         2024Q3  64 0.931   0.024         0.25 0.930       23.12   86.56   89.62     0.998        X         .         X                    0.000
                         2024Q4  65 0.994   0.043        -4.04 0.911       22.31   74.24   71.32     0.917        .         .         X                    0.015
                         2025Q1  57 0.960   0.037        -1.50 0.912       19.11   63.98   63.63     0.950        .         .         X                    0.017
                         2025Q2  61 0.951   0.036         1.00 0.929       48.64  181.58  184.10     0.977        .         .         X                    0.000
                         2025Q3  64 1.010   0.024         3.33 0.959       28.59  139.57  135.25     0.949        .         X         X                    0.000
                         2025Q4  66 1.008   0.022         0.85 0.946       36.35  155.65  150.13     0.938        .         .         .                    0.000
                         2026Q1  57 1.003   0.038         0.98 0.933       44.61  171.26  164.96     0.931        .         .         X                    0.000
                         2026Q2  62 1.006   0.055         3.03 0.851       41.98  107.81   98.88     0.846        .         X         .                    0.000
                         2026Q3  62 0.940   0.045        -0.19 0.903       33.26  106.16  107.35     0.961        .         .         .                    0.016
                         2026Q4  34 0.956   0.030        -1.85 0.950       20.99   92.54   94.34     0.994        .         .         X                    0.000
VERIFIED 2022-11-03..2026-11-17 974 0.999   0.014         0.59 0.915       37.45  128.74  123.29     0.916        .         .         .                         
 episode 2022-07-11..2022-11-02  81 1.031   0.070         5.80 0.876       57.30  161.62  146.70     0.849        .         .         X                         
        pre 2018-11..2022-06-19 808 1.055   0.024         2.31 0.847       59.41  151.94  132.55     0.803        X         X         X                         
```

- ON: quarters departing on k 12/33 (2019Q2, 2019Q4, 2020Q2, 2021Q1, 2021Q3, 2021Q4, 2022Q2, 2023Q3, 2025Q3, 2025Q4, 2026Q3, 2026Q4); on R^2 17/33 (2019Q1, 2019Q2, 2019Q3, 2019Q4, 2020Q1, 2020Q2, 2020Q3, 2020Q4, 2021Q2, 2021Q4, 2022Q3, 2023Q2, 2023Q3, 2024Q4, 2025Q2, 2025Q4, 2026Q4); on resid SD 28/33 (2018Q4, 2019Q2, 2019Q4, 2020Q1, 2020Q2, 2020Q3, 2020Q4, 2021Q1, 2021Q2, 2021Q3, 2021Q4, 2022Q1, 2022Q2, 2022Q3, 2022Q4, 2023Q2, 2023Q3, 2024Q1, 2024Q2, 2024Q3, 2024Q4, 2025Q1, 2025Q2, 2025Q3, 2025Q4, 2026Q1, 2026Q3, 2026Q4).
- CC: quarters departing on k 8/33 (2019Q4, 2020Q3, 2021Q1, 2021Q2, 2022Q1, 2022Q3, 2023Q2, 2024Q3); on R^2 10/33 (2018Q4, 2019Q1, 2019Q2, 2019Q3, 2019Q4, 2020Q1, 2020Q2, 2022Q3, 2025Q3, 2026Q2); on resid SD 23/33 (2019Q1, 2019Q2, 2019Q4, 2020Q1, 2020Q2, 2020Q3, 2021Q1, 2021Q2, 2021Q4, 2022Q1, 2022Q2, 2022Q4, 2023Q2, 2023Q3, 2024Q1, 2024Q2, 2024Q3, 2024Q4, 2025Q1, 2025Q2, 2025Q3, 2026Q1, 2026Q4).

Noise floor: share of quarters departing, verified quarters (2023Q1-2026Q4) vs pre-ticker quarters (2018Q4-2022Q2). Verified quarters are compared with their own pooled window, so their departure rate is what the rule produces on opens known to be right.

```
leg      rule verified   pre
 ON  depart_k     5/16  7/15
 ON depart_r2     6/16 10/15
 ON depart_sd    13/16 13/15
 CC  depart_k     2/16  5/15
 CC depart_r2     2/16  7/15
 CC depart_sd    11/16 11/15
```

- Departures in ON but not in CC (the open-specific signal): k 2019Q2, 2020Q2, 2021Q3, 2021Q4, 2022Q2, 2023Q3, 2025Q3, 2025Q4, 2026Q3, 2026Q4; R^2 2020Q3, 2020Q4, 2021Q2, 2021Q4, 2023Q2, 2023Q3, 2024Q4, 2025Q2, 2025Q4, 2026Q4; resid SD 2018Q4, 2020Q4, 2021Q3, 2022Q3, 2025Q4, 2026Q3.

### Repaired-file sensitivity (quarters that differ from the original file only)

```
                         period leg  n_orig  n_rep k_orig k_rep r2_orig r2_rep sd_orig sd_rep dep_rep
                         2022Q4  ON      60     64  0.725 0.746   0.550  0.530   57.26  59.63     ..X
                         2022Q4  CC      60     64  1.081 1.086   0.873  0.871   99.10  97.23     ..X
                         2023Q1  ON      53     59  0.901 0.962   0.584  0.584   32.01  34.10     ...
                         2023Q1  CC      53     59  1.014 1.025   0.942  0.949   33.46  32.97     ...
                         2023Q2  ON      56     62  0.626 0.587   0.302  0.247   21.60  22.31     .XX
                         2023Q2  CC      56     62  0.889 0.881   0.870  0.870   23.74  23.12     X.X
                         2023Q3  ON      57     63  0.459 0.705   0.315  0.474   18.96  22.98     ..X
                         2023Q3  CC      57     63  0.994 0.985   0.922  0.952   25.26  25.76     .XX
                         2023Q4  ON      59     65  0.884 1.007   0.556  0.595   32.25  34.49     ...
                         2023Q4  CC      59     65  1.037 1.035   0.946  0.949   32.70  32.00     ...
VERIFIED 2022-11-03..2026-11-17  ON     974   1002  0.805 0.820   0.533  0.535   37.35  37.79     ...
VERIFIED 2022-11-03..2026-11-17  CC     974   1002  0.999 1.001   0.915  0.918   37.45  37.38     ...
```
(dep_rep = departure flags k/R^2/SD on the repaired file, vs the repaired verified window.)

### Candidate break dates and scan

```
    feed leg                                          test       date n_before n_after k_before k_after r2_before r2_after sd_before sd_after wald_chi2_2 p_wald logvar_z p_var
original  ON                Chow 2022-07-11 (+/-60 nights) 2022-07-11       60      60    0.587   0.906     0.490    0.726    45.278   27.644       7.316  0.026   -3.758 0.000
original  ON                Chow 2022-08-25 (+/-60 nights) 2022-08-25       60      60    0.666   0.851     0.600    0.704    31.289   47.228       2.848  0.241    3.136 0.002
original  ON                Chow 2022-11-03 (+/-60 nights) 2022-11-03       60      60    0.968   0.590     0.729    0.440    39.041   49.193      12.501  0.002    1.760 0.078
original  ON                 sup-Wald scan (a,k), 15% trim 2023-12-29                                                                              16.224                      
original  ON max |z| residual-variance split (descriptive) 2021-03-09                                                                                             -17.946      
original  CC                Chow 2022-07-11 (+/-60 nights) 2022-07-11       60      60    0.938   0.884     0.923    0.864    54.374   36.538       0.872  0.646   -3.028 0.002
original  CC                Chow 2022-08-25 (+/-60 nights) 2022-08-25       60      60    0.843   1.110     0.827    0.869    44.948   83.709      15.597  0.000    4.736 0.000
original  CC                Chow 2022-11-03 (+/-60 nights) 2022-11-03       60      60    1.064   1.057     0.891    0.870    60.705   85.182       0.168  0.919    2.580 0.010
original  CC                 sup-Wald scan (a,k), 15% trim 2021-06-28                                                                              17.601                      
original  CC max |z| residual-variance split (descriptive) 2023-01-05                                                                                             -20.162      
repaired  ON                Chow 2022-07-11 (+/-60 nights) 2022-07-11       60      60    0.587   0.906     0.490    0.726    45.278   27.644       7.316  0.026   -3.758 0.000
repaired  ON                Chow 2022-08-25 (+/-60 nights) 2022-08-25       60      60    0.666   0.853     0.600    0.710    31.289   46.665       2.983  0.225    3.044 0.002
repaired  ON                Chow 2022-11-03 (+/-60 nights) 2022-11-03       60      60    0.968   0.641     0.729    0.412    39.041   56.663       9.340  0.009    2.837 0.005
repaired  ON                 sup-Wald scan (a,k), 15% trim 2023-12-25                                                                              15.438                      
repaired  ON max |z| residual-variance split (descriptive) 2021-03-09                                                                                             -17.701      
repaired  CC                Chow 2022-07-11 (+/-60 nights) 2022-07-11       60      60    0.938   0.884     0.923    0.864    54.374   36.538       0.872  0.646   -3.028 0.002
repaired  CC                Chow 2022-08-25 (+/-60 nights) 2022-08-25       60      60    0.843   1.109     0.827    0.869    44.948   83.720      15.385  0.000    4.737 0.000
repaired  CC                Chow 2022-11-03 (+/-60 nights) 2022-11-03       60      60    1.064   1.067     0.891    0.867    60.705   86.720       1.132  0.568    2.716 0.007
repaired  CC                 sup-Wald scan (a,k), 15% trim 2021-06-28                                                                              17.329                      
repaired  CC max |z| residual-variance split (descriptive) 2023-01-05                                                                                             -20.415      
```

### Power: positive control on the known episode (continuous vs ticker opens; closes identical)

```
                                     period open_source  n     k  k_nw_se    r2  resid_sd_bp  depart_k  depart_r2  depart_sd
                                     2022Q3  continuous 64 0.935    0.079 0.718       26.707     False       True       True
                                     2022Q3      ticker 64 0.931    0.095 0.676       29.414     False      False       True
                                     2022Q4  continuous 60 0.725    0.096 0.550       57.260     False      False       True
                                     2022Q4      ticker 60 0.870    0.208 0.389       95.310     False      False       True
                                    episode  continuous 81 0.948    0.069 0.721       35.169      True       True      False
                                    episode      ticker 81 1.181    0.235 0.494       71.280     False      False       True
episode excl. 2022-10-10 (sensitivity only)  continuous 80 0.902    0.056 0.705       33.806     False       True      False
episode excl. 2022-10-10 (sensitivity only)      ticker 80 0.904    0.064 0.680       35.950     False       True      False
```

- Episode open-error in return units (ticker minus continuous fut_ON, sample nights): n 81, SD 53.82 bp, SD excluding 2022-10-10 10.56 bp, non-zero on 53 nights.
- The residual-SD rule has no specificity (it flags 13/16 verified quarters on opens known to be right), so power comes only from the k and R^2 rules.

### Power simulation (ADDED AFTER THE FIRST RUN; threshold fixed before running it)

i.i.d. N(0, sigma) bp added to fut_ON on verified nights only (index and close-to-close untouched); each verified quarter re-tested with the pre-registered rules against the clean pooled verified window; 20 seeds. 'Detectable' = mean R^2-rule flags >= 12 of 16 quarters (floor with sigma = 0 is the first row).

```
 sigma_bp  seeds  quarters  mean_flag_r2  mean_flag_k  mean_pass_both  detectable
        0      1        16          6.00         5.00            8.00       False
       10     20        16          6.65         4.95            7.80       False
       25     20        16          7.25         4.60            7.70       False
       50     20        16         11.40         3.95            3.35       False
      100     20        16         14.65         2.60            0.85        True
```

## Reading

**Step 1.** No period reaches 3x baseline on open = prior close (max 1.63x); the pre-ticker spike ratio (1.36) is not above baseline (1.60); no open outside [low, high] and no O=H=L=C day in any year. The only flag is 2017 open = close, on 3 of 95 days with real ranges. No sign of filled or stale futures opens in the form the 2021 index feed showed.

**Steps 2-3.** The quarterly rules flag many verified quarters too (noise floor above), so a single departing quarter means little. Pre-ticker quarters depart more often than verified ones on R^2, in BOTH legs (ON 10/15 vs 6/16; CC 7/15 vs 2/16): the futures-index relation itself was looser before 2022, not only at the open.
The ON-specific weakness sits in 2019Q1-2021Q2. In 2020Q1-2021Q2 it coincides with the index leg collapsing (fut/idx ON SD ratio 1.9-11.2 vs 0.6-1.5 in verified quarters): idx_ON SD 2020Q2 17.4 bp, 2021Q1 7.4, 2021Q2 6.9 (verified ~37) while fut_ON SD stays 114, 84, 29 bp and index close-to-close SD is normal. Forward k blows up (2021Q1 6.5) and reverse k collapses: the pattern a shrunken/stale index open produces, even on days the index flag passes. Read with caution: it points at the index open, but the data cannot prove the futures open is clean in those quarters, because the reference itself is degraded. 2019Q1, 2019Q3 and 2019Q4 are different: ON R^2 0.10, 0.06, 0.002 with a normal SD ratio (1.4, 1.3, 1.2) and index-flag rates of 9-17%: the two overnight legs are nearly unrelated there and nothing here says which leg is at fault. Unexplained.
Pre-registered rules, quarters passing BOTH k and R^2: verified 8/16, pre-ticker 2/15 (2018Q4, 2022Q1). On these rules the pre-ticker overnight relation IS distinguishable from the verified window; part of that is explained by the index leg (2020Q1-2021Q2) and by the looser close-to-close relation, part (2019) is not explained.
POST-HOC and lenient (added after seeing results, not a test): pre-ticker quarters whose ON k and R^2 both lie inside the range spanned by the 16 verified quarters (k 0.32-1.10, R^2 0.25-0.83): 2018Q4, 2019Q2, 2021Q3, 2021Q4, 2022Q1, 2022Q2.

**Breaks.** 2022-07-11 (episode start): ON intercept/slope shift, Wald p 0.026 (k 0.59 -> 0.91, R^2 0.49 -> 0.73); CC none (p 0.65); both legs show a variance drop (market volatility). 2022-08-25: CC breaks (p < 0.001), ON does not (p 0.24): an instrument/market change, not an open one. 2022-11-03: ON-only break (Wald 12.5, p 0.002; repaired file 9.3, p 0.009; CC p 0.92), k 0.97 -> 0.59, R^2 0.73 -> 0.44: so both edges of the mismatch episode carry an ON-only coefficient shift, and the futures-index overnight fit was TIGHTER inside the episode than on either side (the episode window departs from the verified window on k and R^2, toward a better fit). This is not attributable to the open definition: ticker opens reproduce it (episode excl. 2022-10-10: k 0.90 / R^2 0.68 vs continuous 0.90 / 0.71, positive-control table). CC does not shift at either edge, so the cause is unidentified (a change in how the futures and index overnight moves relate over that period, whichever open is used). The sup-Wald maxima (ON 2023-12-29, CC 2021-06-28) exceed ~11.8 but are at neither candidate date.

**Power.** The residual-SD rule cannot discriminate (13/16 verified quarters flagged). In the simulation (added after the first run), an i.i.d. futures-open error is detectable by the R^2 rule only at sigma = 100 bp (mean flags 14.7/16); at 50 bp it is 11.4/16, at 25 bp 7.2/16, at 10 bp 6.7/16 vs a floor of 6/16. The known 2022 episode's open error, excluding 2022-10-10, is about 11 bp SD, and continuous vs ticker opens give practically the same quarterly k / R^2 once 2022-10-10 is set aside: this audit could not have detected the one episode we know about. The pre-ticker R^2 flag rate (10/15) is in the range the simulation produces for a 25-50+ bp error, but the close-to-close control is also degraded pre-2022, so that rate cannot be attributed to the futures open.

**What this can and cannot establish.** It can show that the pre-2022-06 futures opens have no filled- or stale-open signature (Step 1), and that the 2022 edge shifts are not caused by the open definition (ticker opens reproduce them). It cannot show the opens are right, and on the pre-registered k/R^2 rules the 2019-2021 overnight relation is NOT indistinguishable from the verified window. The data cannot assign that difference to the futures open: the index open is degraded in 2020Q1-2021Q2, close-to-close is looser too, and 2019 is unexplained. The test sees only i.i.d. errors of roughly 100 bp SD (50 bp is borderline), and 2017-08..2018-11-19 is covered by Step 1 only (the VN30 index file starts 2018-11-20). Passing Step 1 is not proof; failing Steps 2-3 is not proof of a bad open.

## Summary (5 lines)

1. Filled-open rates: no year >= 3x baseline on open = prior close / high / low (pre-ticker 1.17x, spike 1.36 vs 1.60); only flag 2017 open = close (3 of 95 days); no out-of-range or locked opens.
2. Break dates: ON-only coefficient shifts at both edges of the 2022 episode, 2022-07-11 (p 0.026) and 2022-11-03 (p 0.002; repaired 0.009), with a tighter fit inside it (R^2 0.72 vs 0.53 verified), but ticker opens reproduce it (0.68 excl. 2022-10-10), so the shifts are not attributable to the open definition (cause unidentified; CC does not shift); 2022-08-25 breaks in close-to-close too, so it is not an open break; the all-date sup-Wald scan peaks at 2023-12-29 (ON) and 2021-06-28 (CC), not at any candidate date.
3. Control: close-to-close is also looser before 2022 (R^2 departures 7/15 vs 2/16), and the ON weakness in 2020Q1-2021Q2 tracks a collapse in index-open variance (points at the index open); 2019Q1/Q3/Q4 ON R^2 0.00-0.10 is unexplained and could be either leg.
4. Indistinguishable: on Step 1 every year except 2017 (3 open = close days); on Steps 2-3 (pre-registered k and R^2) only 2018Q4, 2022Q1 pass, vs 8/16 verified quarters, so the 2019-2021 overnight relation IS distinguishable (2020Q1-2021Q2 explained by the index leg, 2019 unexplained); 2017-08..2018-11 has Step 1 only.
5. Open question: are the 2019-2021H1 futures opens right? Step 2 used the VCI index open, which is degraded there; the PIT constituent-open basket (`pit_basket()`, from data/raw/ stock files, from 2018-11) is held but was not run because the brief specified the index. It is the natural next run; even then the test detects only i.i.d. errors of ~100 bp SD, far above the ~11 bp 2022 episode.

Raw files unchanged (md5 before = after): True.
