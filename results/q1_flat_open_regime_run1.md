# Q1 at date level: flat-open frequency vs the 2022-08-25 relocation (src/q1_flat_open_regime.py)

Rules and the read are pre-registered in the script header. Units: legs in bp per one-day night; shares in percentage points.

## (i) Flat-open share (open == prior close), PIT members, date-level

```
                            series  n_pre  n_post   pre  pre_t  post  post_t  diff  break_t  diff_lo95  diff_hi95
 flat-open share (ew) [pct points]    741     833 27.30  40.35 26.16   40.12 -1.14    -1.21      -2.98       0.70
flat-open share (cap) [pct points]    741     833 27.42  37.40 26.23   36.26 -1.18    -1.15      -3.20       0.84
```

Pooled stock-day share by calendar year (Q3):

```
universe  PIT members  current-30
year                             
2018             25.5        26.7
2019             35.1        38.2
2020             27.0        31.0
2021             23.6        24.6
2022             20.3        21.0
2023             29.0        30.2
2024             30.2        30.5
2025             23.9        23.1
2026             24.4        24.1
```

## (ii)/(iii) ON and ID by regime: all days (level estimate) vs unflagged only (conditional check, selects on outcome)

```
                                  version scheme leg  n_pre  n_post   pre  pre_t  post  post_t   diff  break_t  diff_lo95  diff_hi95
                           (iii) all days    cap  ON    741     833 -0.75  -0.26 13.06    5.58  13.81     3.70       6.49      21.13
                      (ii) unflagged only    cap  ON    740     833  1.18   0.38 16.75    6.51  15.57     3.85       7.64      23.49
                           (iii) all days    cap  ID    741     833 11.04   2.96 -2.97   -0.89 -14.02    -2.80     -23.83      -4.20
                      (ii) unflagged only    cap  ID    740     833 10.42   2.68 -4.50   -1.32 -14.92    -2.88     -25.06      -4.78
flagged only (ID; ON = 0 by construction)    cap  ID    293     292 10.52   2.04  5.74    1.06  -4.78    -0.64     -19.45       9.89
                           (iii) all days     ew  ON    741     833 -2.04  -0.66 13.54    5.89  15.59     4.04       8.02      23.16
                      (ii) unflagged only     ew  ON    740     833 -0.59  -0.18 17.48    6.93  18.08     4.33       9.89      26.26
                           (iii) all days     ew  ID    741     833 11.82   3.18 -6.20   -1.96 -18.02    -3.69     -27.59      -8.45
                      (ii) unflagged only     ew  ID    740     833 12.02   3.15 -7.64   -2.39 -19.66    -3.95     -29.40      -9.91
flagged only (ID; ON = 0 by construction)     ew  ID    293     292  6.96   1.37  2.87    0.55  -4.09    -0.56     -18.36      10.18
```

## (iv) H3 (C9) on unflagged nights; tercile flag share in the holding month

```
                            version leg  months  spread_bp  nw3_t
all days (= level_b_rebuild P base)  ON      94      17.94  10.42
all days (= level_b_rebuild P base)  ID      94     -16.85  -5.37
all days (= level_b_rebuild P base)  CC      94       1.10   0.41
                     unflagged only  ON      18      14.91   1.91
                     unflagged only  ID      18      -4.31  -0.53
                     unflagged only  CC      18      10.61   1.09
```

Holding-month flag share, top vs bottom tercile (all-days sort): months 94.00, top_flag_pct 25.50, bot_flag_pct 27.86, diff_pp -2.36, nw3_t -4.07

R1: PASS: a flat-open-frequency artifact does not explain the relocation (C4/C5).
R2: (iii) is the level estimate for C4/C5; (ii) supports only the R1 conditional statement.
R3: H3 ON persistence does NOT survive on unflagged nights (t 1.91); ID reversal loses |t|>2 (t -0.53).

Integrity (no existing file changed): True

## Summary (5 lines)

1. Flat-open share (EW, PIT): pre 27.3% vs post 26.2% (diff -1.1 pp, t -1.21); yearly pooled share PIT 20.3-35.1%, current-30 21.0-38.2%.
2. CW ON break: (iii) all days +13.81 bp (t 3.70, CI 6.5..21.1); (ii) unflagged only +15.57 bp (t 3.85, CI 7.6..23.5).
3. CW ID break: (iii) all days -14.02 bp (t -2.80); (ii) unflagged only -14.92 bp (t -2.88); flagged only (ID; ON = 0 by construction) -4.78 bp (t -0.64).
4. R1 -> PASS: a flat-open-frequency artifact does not explain the relocation (C4/C5).
5. R3 -> H3 ON persistence does NOT survive on unflagged nights (t 1.91); ID reversal loses |t|>2 (t -0.53); integrity True.
