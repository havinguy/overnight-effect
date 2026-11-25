# Regime break by night length, PIT basket (src/regime_nightlength.py)

Definitions and the verdict rule were pre-registered in the script header before the first run. bp per night; NW lag 5.

## Break table (post 2022-08-25 minus pre)

```
scheme           night leg  n_pre  n_post  pre_bp  pre_t  post_bp  post_t  break_bp  break_se_bp  break_t    lo95  hi95  low_n  lt250  mde80_bp
    CW         one-day  ON    741     833   -0.75  -0.26    13.06    5.58     13.81         3.73     3.70    6.49 21.13  False  False     10.46
    CW         one-day  ID    741     833   11.04   2.96    -2.97   -0.89    -14.02         5.01    -2.80  -23.83 -4.20  False  False     14.02
    CW         one-day C2C    741     833   10.29   2.66    10.08    2.78     -0.21         5.30    -0.04  -10.60 10.18  False  False     14.84
    CW    post-weekend  ON    179     201   -2.04  -0.20     5.79    0.86      7.84        12.18     0.64  -16.05 31.72  False   True     34.12
    CW    post-weekend  ID    179     201  -25.88  -2.37   -30.00   -3.52     -4.12        13.86    -0.30  -31.28 23.04  False   True     38.80
    CW    post-weekend C2C    179     201  -27.92  -1.85   -24.21   -2.02      3.71        19.23     0.19  -33.98 41.41  False   True     53.85
    CW      all nights  ON    939    1054   -0.74  -0.25    11.13    5.02     11.87         3.72     3.19    4.57 19.16  False  False     10.43
    CW      all nights  ID    939    1054    4.16   1.23    -8.29   -2.60    -12.45         4.65    -2.68  -21.56 -3.34  False  False     13.02
    CW      all nights C2C    939    1054    3.42   0.78     2.84    0.71     -0.58         5.94    -0.10  -12.22 11.06  False  False     16.62
    CW other multi-day  ON     19      20   12.20   0.87   -15.53   -0.73    -27.73        25.63    -1.08  -77.96 22.50   True   True     71.76
    CW other multi-day  ID     19      20   18.50   0.79   -11.52   -0.46    -30.02        34.13    -0.88  -96.91 36.87   True   True     95.56
    CW other multi-day C2C     19      20   30.70   1.19   -27.05   -0.61    -57.75        51.29    -1.13 -158.29 42.78   True   True    143.62
    EW         one-day  ON    741     833   -2.04  -0.66    13.54    5.89     15.59         3.86     4.04    8.02 23.16  False  False     10.81
    EW         one-day  ID    741     833   11.82   3.18    -6.20   -1.96    -18.02         4.88    -3.69  -27.59 -8.45  False  False     13.67
    EW         one-day C2C    741     833    9.78   2.44     7.35    2.11     -2.43         5.31    -0.46  -12.83  7.97  False  False     14.86
    EW    post-weekend  ON    179     201   -2.51  -0.24     6.70    1.00      9.21        12.52     0.74  -15.33 33.76  False   True     35.06
    EW    post-weekend  ID    179     201  -27.94  -2.62   -29.35   -3.21     -1.41        14.05    -0.10  -28.96 26.13  False   True     39.35
    EW    post-weekend C2C    179     201  -30.45  -2.03   -22.65   -1.82      7.80        19.52     0.40  -30.47 46.06  False   True     54.66
    EW      all nights  ON    939    1054   -1.76  -0.55    11.80    5.30     13.56         3.91     3.47    5.91 21.21  False  False     10.93
    EW      all nights  ID    939    1054    4.22   1.26   -10.63   -3.40    -14.84         4.57    -3.24  -23.81 -5.88  False  False     12.81
    EW      all nights C2C    939    1054    2.45   0.53     1.17    0.30     -1.28         6.09    -0.21  -13.21 10.64  False  False     17.04
    EW other multi-day  ON     19      20   16.25   1.12    -9.76   -0.45    -26.01        26.24    -0.99  -77.44 25.43   True   True     73.48
    EW other multi-day  ID     19      20   10.55   0.55    -6.80   -0.32    -17.35        28.61    -0.61  -73.42 38.72   True   True     80.10
    EW other multi-day C2C     19      20   26.79   1.11   -16.56   -0.41    -43.36        47.17    -0.92 -135.80 49.09   True   True    132.06
```

## Report-only: post-weekend break minus one-day break

```
scheme leg  weekend_break_bp  oneday_break_bp  diff_bp  diff_t
    CW  ON              7.84            13.81    -5.97   -0.47
    CW  ID             -4.12           -14.02     9.89    0.67
    CW C2C              3.71            -0.21     3.92    0.20
    EW  ON              9.21            15.59    -6.38   -0.49
    EW  ID             -1.41           -18.02    16.61    1.12
    EW C2C              7.80            -2.43    10.23    0.51
```

Verdict (CW, primary): V1 RELOCATION STANDS on one-day nights.
Agreement check (EW): V1 RELOCATION STANDS on one-day nights.

Power (rerun 1): post-weekend CW ID break SE 13.9 bp, MDE80 38.8 bp; power to detect a break of the one-day size (-14.0 bp) about 17%. The post-weekend cells therefore cannot distinguish 'no weekend break' from 'the same break on weekends'; V2 could only fire for a weekend ID break below about -27.2 bp. Post-weekend cells have n 179/201 (< 250 under the earlier project rule).

Reading: the post-weekend intraday drop is present in both regimes (a level in each); whether the post-weekend session also relocates at 2022-08-25 is undetermined.

## Summary (5 lines)

1. One-day nights, CW: ON +13.81 bp (t 3.70, CI 6.5..21.1; n 741/833); ID -14.02 bp (t -2.80, CI -23.8..-4.2; n 741/833); C2C -0.21 bp (t -0.04, CI -10.6..10.2; n 741/833).
2. Post-weekend nights, CW: ON +7.84 bp (t 0.64, CI -16.0..31.7; n 179/201); ID -4.12 bp (t -0.30, CI -31.3..23.0; n 179/201); C2C +3.71 bp (t 0.19, CI -34.0..41.4; n 179/201).
3. EW check: one-day ON +15.59 bp (t 4.04, CI 8.0..23.2; n 741/833), ID -18.02 bp (t -3.69, CI -27.6..-8.5; n 741/833); post-weekend ID -1.41 bp (t -0.10, CI -29.0..26.1; n 179/201).
4. Verdict CW: V1 RELOCATION STANDS on one-day nights. EW: V1 RELOCATION STANDS on one-day nights.
5. Weekend-minus-one-day break difference (report only), CW: ON -5.97 bp (t -0.47); ID +9.89 bp (t 0.67); C2C +3.92 bp (t 0.20).

Integrity (checked after all writes; no existing file changed, only regime_nightlength* written): True
