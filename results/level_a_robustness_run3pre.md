# Level A robustness (src/level_a_robustness.py)

Pre-registered rules and split dates (with sources) are in the script header. bp per night; NW lag 5.

## Test 1: ON minus ID (design doc t-test on the mean difference)

```
       series         nights                              sample   leg    n  mean_bp  nw_t  lo95  hi95                       R1
      VNINDEX     all nights                    full 2011-04-29+ ON-ID 3884     7.11  3.84  3.48 10.73         H1 holds (ON>ID)
      VNINDEX     all nights                  common 2018-11-21+ ON-ID 1993     9.13  3.37  3.82 14.44         H1 holds (ON>ID)
      VNINDEX one-day nights                    full 2011-04-29+ ON-ID 3069     1.43  0.66 -2.83  5.69 no detectable difference
      VNINDEX one-day nights                  common 2018-11-21+ ON-ID 1574     2.52  0.79 -3.72  8.75 no detectable difference
   VN30 index     all nights                  common 2018-11-21+ ON-ID 1993     7.79  2.77  2.29 13.29   (descriptive only, R4)
   VN30 index     all nights common ex degraded 2019-01..2021-06 ON-ID 1371    16.01  5.30 10.09 21.92         H1 holds (ON>ID)
   VN30 index one-day nights                  common 2018-11-21+ ON-ID 1574     1.69  0.58 -4.01  7.39   (descriptive only, R4)
   VN30 index one-day nights common ex degraded 2019-01..2021-06 ON-ID 1086     9.33  2.76  2.71 15.94         H1 holds (ON>ID)
PIT basket CW     all nights                  common 2018-11-21+ ON-ID 1993     7.96  2.62  2.02 13.91         H1 holds (ON>ID)
PIT basket CW one-day nights                  common 2018-11-21+ ON-ID 1574     2.93  0.81 -4.13  9.99 no detectable difference
PIT basket EW     all nights                  common 2018-11-21+ ON-ID 1993     9.04  2.97  3.08 15.00         H1 holds (ON>ID)
PIT basket EW one-day nights                  common 2018-11-21+ ON-ID 1574     3.92  1.08 -3.17 11.01 no detectable difference
```

## Test 1b (post hoc): legs by night length (VNINDEX full sample; others common 2018-11-21+)

```
                  series    night_length  low_n    n  ON_bp  ON_t  ID_bp  ID_t  ON-ID_bp  ON-ID_t
                 VNINDEX           1-day  False 3069   4.56  3.81   3.13  1.86      1.43     0.66
                 VNINDEX   3-day weekend  False  740   7.71  3.10 -22.34 -4.74     30.05     6.25
                 VNINDEX other multi-day   True   75   7.68  0.95  -5.50 -0.40     13.18     0.94
VN30 index (ex degraded)           1-day  False 1086   9.48  6.34   0.15  0.05      9.33     2.76
VN30 index (ex degraded)   3-day weekend  False  260   5.69  1.41 -38.91 -4.05     44.60     4.65
VN30 index (ex degraded) other multi-day   True   25  -4.01 -0.22 -13.01 -0.69      9.00     0.73
           PIT basket CW           1-day  False 1574   6.55  3.46   3.63  1.43      2.93     0.81
           PIT basket CW   3-day weekend  False  380   2.10  0.35 -28.06 -4.10     30.16     3.48
           PIT basket CW other multi-day   True   39  -2.02 -0.14   3.10  0.19     -5.13    -0.39
           PIT basket EW           1-day  False 1574   6.21  3.17   2.28  0.92      3.92     1.08
           PIT basket EW   3-day weekend  False  380   2.36  0.38 -28.69 -4.11     31.05     3.49
           PIT basket EW other multi-day   True   39   2.91  0.20   1.65  0.13      1.26     0.11
```

## Test 2: sub-period splits (VN30 index excludes its degraded window 2019-01..2021-06)

```
                  series               split                     period             dates_used  ON_bp  ON_t    n  ID_bp  ID_t  ON-ID_bp  ON-ID_t  ONmID_lo95  ONmID_hi95                       R1
                 VNINDEX         COVID 2-way   pre-COVID (< 2020-01-23) 2011-04-29..2020-01-22   3.91  2.97 2184  -0.52 -0.25      4.42     1.96        0.01        8.84 no detectable difference
                 VNINDEX         COVID 2-way post-COVID (>= 2020-01-23) 2020-01-30..2026-11-17   6.91  3.75 1700  -3.65 -1.39     10.55     3.44        4.54       16.57         H1 holds (ON>ID)
                 VNINDEX         COVID 3-way                  pre-COVID 2011-04-29..2020-01-22   3.91  2.97 2184  -0.52 -0.25      4.42     1.96        0.01        8.84 no detectable difference
                 VNINDEX         COVID 3-way     2020-01-23..2022-08-24 2020-01-30..2022-08-24  -1.70 -0.49  646   5.62  1.26     -7.33    -1.41      -17.49        2.83 no detectable difference
                 VNINDEX         COVID 3-way              >= 2022-08-25 2022-08-25..2026-11-17  12.19  6.11 1054  -9.33 -2.97     21.52     6.06       14.56       28.47         H1 holds (ON>ID)
                 VNINDEX                 KRX     pre-KRX (< 2025-05-05) 2011-04-29..2025-04-29   3.86  3.30 3497  -1.14 -0.67      5.00     2.58        1.20        8.79         H1 holds (ON>ID)
                 VNINDEX                 KRX   post-KRX (>= 2025-05-05) 2025-05-05..2026-11-17  17.51  6.61  387  -8.67 -1.56     26.18     4.62       15.07       37.29         H1 holds (ON>ID)
                 VNINDEX KRX within regime 2     2022-08-25..2025-05-04 2022-08-25..2025-04-29   9.10  3.36  667  -9.71 -2.58     18.81     4.16        9.95       27.67         H1 holds (ON>ID)
                 VNINDEX KRX within regime 2   post-KRX (>= 2025-05-05) 2025-05-05..2026-11-17  17.51  6.61  387  -8.67 -1.56     26.18     4.62       15.07       37.29         H1 holds (ON>ID)
VN30 index (ex degraded)         COVID 2-way   pre-COVID (< 2020-01-23) 2018-11-21..2018-12-28 -10.10 -0.88   28  -5.47 -0.28     -4.63    -0.20      -48.98       39.73                    LOW N
VN30 index (ex degraded)         COVID 2-way post-COVID (>= 2020-01-23) 2021-07-01..2026-11-17   8.90  6.55 1343  -7.54 -2.52     16.44     5.41       10.48       22.40         H1 holds (ON>ID)
VN30 index (ex degraded)         COVID 3-way                  pre-COVID 2018-11-21..2018-12-28 -10.10 -0.88   28  -5.47 -0.28     -4.63    -0.20      -48.98       39.73                    LOW N
VN30 index (ex degraded)         COVID 3-way     2020-01-23..2022-08-24 2021-07-01..2022-08-24   4.93  1.95  289 -10.64 -1.65     15.58     2.36        2.65       28.51         H1 holds (ON>ID)
VN30 index (ex degraded)         COVID 3-way              >= 2022-08-25 2022-08-25..2026-11-17   9.99  6.33 1054  -6.68 -1.98     16.68     4.87        9.97       23.38         H1 holds (ON>ID)
VN30 index (ex degraded)                 KRX     pre-KRX (< 2025-05-05) 2018-11-21..2025-04-29   5.70  3.61  984  -7.71 -2.23     13.41     3.82        6.53       20.30         H1 holds (ON>ID)
VN30 index (ex degraded)                 KRX   post-KRX (>= 2025-05-05) 2025-05-05..2026-11-17  15.68  6.29  387  -6.94 -1.22     22.62     3.90       11.26       33.97         H1 holds (ON>ID)
VN30 index (ex degraded) KRX within regime 2     2022-08-25..2025-05-04 2022-08-25..2025-04-29   6.69  3.41  667  -6.54 -1.56     13.23     3.15        5.00       21.47         H1 holds (ON>ID)
VN30 index (ex degraded) KRX within regime 2   post-KRX (>= 2025-05-05) 2025-05-05..2026-11-17  15.68  6.29  387  -6.94 -1.22     22.62     3.90       11.26       33.97         H1 holds (ON>ID)
           PIT basket CW         COVID 2-way   pre-COVID (< 2020-01-23) 2018-11-21..2020-01-22  -1.04 -0.44  293   1.54  0.38     -2.57    -0.52      -12.28        7.13 no detectable difference
           PIT basket CW         COVID 2-way post-COVID (>= 2020-01-23) 2020-01-30..2026-11-17   6.67  3.12 1700  -3.11 -1.17      9.78     2.84        3.04       16.52         H1 holds (ON>ID)
           PIT basket CW         COVID 3-way                  pre-COVID 2018-11-21..2020-01-22  -1.04 -0.44  293   1.54  0.38     -2.57    -0.52      -12.28        7.13 no detectable difference
           PIT basket CW         COVID 3-way     2020-01-23..2022-08-24 2020-01-30..2022-08-24  -0.60 -0.14  646   5.35  1.17     -5.95    -0.94      -18.31        6.41 no detectable difference
           PIT basket CW         COVID 3-way              >= 2022-08-25 2022-08-25..2026-11-17  11.13  5.02 1054  -8.29 -2.60     19.42     5.11       11.97       26.87         H1 holds (ON>ID)
           PIT basket CW                 KRX     pre-KRX (< 2025-05-05) 2018-11-21..2025-04-29   2.89  1.34 1606  -1.08 -0.41      3.97     1.14       -2.85       10.80 no detectable difference
           PIT basket CW                 KRX   post-KRX (>= 2025-05-05) 2025-05-05..2026-11-17  16.52  5.27  387  -8.00 -1.57     24.52     4.48       13.78       35.25         H1 holds (ON>ID)
           PIT basket CW KRX within regime 2     2022-08-25..2025-05-04 2022-08-25..2025-04-29   8.00  2.71  667  -8.46 -2.07     16.46     3.24        6.51       26.40         H1 holds (ON>ID)
           PIT basket CW KRX within regime 2   post-KRX (>= 2025-05-05) 2025-05-05..2026-11-17  16.52  5.27  387  -8.00 -1.57     24.52     4.48       13.78       35.25         H1 holds (ON>ID)
           PIT basket EW         COVID 2-way   pre-COVID (< 2020-01-23) 2018-11-21..2020-01-22  -4.80 -2.12  293   2.43  0.63     -7.22    -1.53      -16.48        2.03 no detectable difference
           PIT basket EW         COVID 2-way post-COVID (>= 2020-01-23) 2020-01-30..2026-11-17   7.17  3.21 1700  -4.68 -1.78     11.84     3.44        5.09       18.59         H1 holds (ON>ID)
           PIT basket EW         COVID 3-way                  pre-COVID 2018-11-21..2020-01-22  -4.80 -2.12  293   2.43  0.63     -7.22    -1.53      -16.48        2.03 no detectable difference
           PIT basket EW         COVID 3-way     2020-01-23..2022-08-24 2020-01-30..2022-08-24  -0.39 -0.09  646   5.03  1.11     -5.42    -0.85      -17.88        7.04 no detectable difference
           PIT basket EW         COVID 3-way              >= 2022-08-25 2022-08-25..2026-11-17  11.80  5.30 1054 -10.63 -3.40     22.42     5.99       15.09       29.75         H1 holds (ON>ID)
           PIT basket EW                 KRX     pre-KRX (< 2025-05-05) 2018-11-21..2025-04-29   3.01  1.31 1606  -2.12 -0.81      5.13     1.45       -1.81       12.07 no detectable difference
           PIT basket EW                 KRX   post-KRX (>= 2025-05-05) 2025-05-05..2026-11-17  15.37  5.51  387  -9.89 -2.03     25.26     5.10       15.55       34.98         H1 holds (ON>ID)
           PIT basket EW KRX within regime 2     2022-08-25..2025-05-04 2022-08-25..2025-04-29   9.72  3.14  667 -11.05 -2.73     20.77     4.03       10.66       30.89         H1 holds (ON>ID)
           PIT basket EW KRX within regime 2   post-KRX (>= 2025-05-05) 2025-05-05..2026-11-17  15.37  5.51  387  -9.89 -2.03     25.26     5.10       15.55       34.98         H1 holds (ON>ID)
```

```
                  series               split  break_t_ONmID                                                                                             sides                    R2
                 VNINDEX         COVID 2-way       1.610155 pre-COVID (< 2020-01-23): no detectable difference | post-COVID (>= 2020-01-23): H1 holds (ON>ID) CHANGES H1 conclusion
                 VNINDEX                 KRX       3.536062             pre-KRX (< 2025-05-05): H1 holds (ON>ID) | post-KRX (>= 2025-05-05): H1 holds (ON>ID)    same H1 conclusion
                 VNINDEX KRX within regime 2       1.016974             2022-08-25..2025-05-04: H1 holds (ON>ID) | post-KRX (>= 2025-05-05): H1 holds (ON>ID)    same H1 conclusion
VN30 index (ex degraded)         COVID 2-way       0.922760                    pre-COVID (< 2020-01-23): LOW N | post-COVID (>= 2020-01-23): H1 holds (ON>ID)                 LOW N
VN30 index (ex degraded)                 KRX       1.358527             pre-KRX (< 2025-05-05): H1 holds (ON>ID) | post-KRX (>= 2025-05-05): H1 holds (ON>ID)    same H1 conclusion
VN30 index (ex degraded) KRX within regime 2       1.311545             2022-08-25..2025-05-04: H1 holds (ON>ID) | post-KRX (>= 2025-05-05): H1 holds (ON>ID)    same H1 conclusion
           PIT basket CW         COVID 2-way       2.048672 pre-COVID (< 2020-01-23): no detectable difference | post-COVID (>= 2020-01-23): H1 holds (ON>ID) CHANGES H1 conclusion
           PIT basket CW                 KRX       3.164963     pre-KRX (< 2025-05-05): no detectable difference | post-KRX (>= 2025-05-05): H1 holds (ON>ID) CHANGES H1 conclusion
           PIT basket CW KRX within regime 2       1.079209             2022-08-25..2025-05-04: H1 holds (ON>ID) | post-KRX (>= 2025-05-05): H1 holds (ON>ID)    same H1 conclusion
           PIT basket EW         COVID 2-way       3.262805 pre-COVID (< 2020-01-23): no detectable difference | post-COVID (>= 2020-01-23): H1 holds (ON>ID) CHANGES H1 conclusion
           PIT basket EW                 KRX       3.305599     pre-KRX (< 2025-05-05): no detectable difference | post-KRX (>= 2025-05-05): H1 holds (ON>ID) CHANGES H1 conclusion
           PIT basket EW KRX within regime 2       0.627594             2022-08-25..2025-05-04: H1 holds (ON>ID) | post-KRX (>= 2025-05-05): H1 holds (ON>ID)    same H1 conclusion
```

## Test 3: EW vs CW basket vs published index (common dates, all nights)

```
         regime                                       series    n  ON_bp  ON_t  ID_bp  ID_t  ONmID_bp  ONmID_t                       R1  corr_ON
 pre 2022-08-25                                      VNINDEX  939  -0.63 -0.26   4.14  1.25     -4.77    -1.24 no detectable difference      NaN
 pre 2022-08-25                     VN30 index (ex degraded)  317   3.61  1.39 -10.19 -1.67     13.79     2.17         H1 holds (ON>ID)      NaN
 pre 2022-08-25                                PIT basket CW  939  -0.74 -0.25   4.16  1.23     -4.89    -1.06 no detectable difference      NaN
 pre 2022-08-25                                PIT basket EW  939  -1.76 -0.55   4.22  1.26     -5.98    -1.29 no detectable difference      NaN
 pre 2022-08-25            PIT basket EW minus PIT basket CW  939  -1.03 -1.82    NaN   NaN       NaN      NaN                      NaN     0.98
 pre 2022-08-25            PIT basket EW minus PIT basket CW  939    NaN   NaN   0.06  0.08       NaN      NaN                      NaN      NaN
 pre 2022-08-25 PIT basket CW minus VN30 index (ex degraded)  317  -2.19 -1.60    NaN   NaN       NaN      NaN                      NaN     0.92
 pre 2022-08-25 PIT basket CW minus VN30 index (ex degraded)  317    NaN   NaN   1.56  1.15       NaN      NaN                      NaN      NaN
 pre 2022-08-25 PIT basket EW minus VN30 index (ex degraded)  317  -2.61 -1.61    NaN   NaN       NaN      NaN                      NaN     0.90
 pre 2022-08-25 PIT basket EW minus VN30 index (ex degraded)  317    NaN   NaN   4.85  2.63       NaN      NaN                      NaN      NaN
 pre 2022-08-25                  PIT basket CW minus VNINDEX  939  -0.10 -0.09    NaN   NaN       NaN      NaN                      NaN     0.91
 pre 2022-08-25                  PIT basket CW minus VNINDEX  939    NaN   NaN   0.02  0.01       NaN      NaN                      NaN      NaN
post 2022-08-25                                      VNINDEX 1054  12.19  6.11  -9.33 -2.97     21.52     6.06         H1 holds (ON>ID)      NaN
post 2022-08-25                     VN30 index (ex degraded) 1054   9.99  6.33  -6.68 -1.98     16.68     4.87         H1 holds (ON>ID)      NaN
post 2022-08-25                                PIT basket CW 1054  11.13  5.02  -8.29 -2.60     19.42     5.11         H1 holds (ON>ID)      NaN
post 2022-08-25                                PIT basket EW 1054  11.80  5.30 -10.63 -3.40     22.42     5.99         H1 holds (ON>ID)      NaN
post 2022-08-25            PIT basket EW minus PIT basket CW 1054   0.67  1.32    NaN   NaN       NaN      NaN                      NaN     0.98
post 2022-08-25            PIT basket EW minus PIT basket CW 1054    NaN   NaN  -2.34 -2.86       NaN      NaN                      NaN      NaN
post 2022-08-25 PIT basket CW minus VN30 index (ex degraded) 1054   1.14  0.95    NaN   NaN       NaN      NaN                      NaN     0.86
post 2022-08-25 PIT basket CW minus VN30 index (ex degraded) 1054    NaN   NaN  -1.60 -1.33       NaN      NaN                      NaN      NaN
post 2022-08-25 PIT basket EW minus VN30 index (ex degraded) 1054   1.81  1.37    NaN   NaN       NaN      NaN                      NaN     0.85
post 2022-08-25 PIT basket EW minus VN30 index (ex degraded) 1054    NaN   NaN  -3.94 -2.90       NaN      NaN                      NaN      NaN
post 2022-08-25                  PIT basket CW minus VNINDEX 1054  -1.06 -1.64    NaN   NaN       NaN      NaN                      NaN     0.94
post 2022-08-25                  PIT basket CW minus VNINDEX 1054    NaN   NaN   1.04  1.10       NaN      NaN                      NaN      NaN
     all common                                      VNINDEX 1993   6.15  3.82  -2.98 -1.29      9.13     3.37         H1 holds (ON>ID)      NaN
     all common                     VN30 index (ex degraded) 1371   8.52  6.24  -7.49 -2.54     16.01     5.30         H1 holds (ON>ID)      NaN
     all common                                PIT basket CW 1993   5.54  2.97  -2.42 -1.03      7.96     2.62         H1 holds (ON>ID)      NaN
     all common                                PIT basket EW 1993   5.41  2.77  -3.63 -1.57      9.04     2.97         H1 holds (ON>ID)      NaN
     all common            PIT basket EW minus PIT basket CW 1993  -0.13 -0.34    NaN   NaN       NaN      NaN                      NaN     0.98
     all common            PIT basket EW minus PIT basket CW 1993    NaN   NaN  -1.21 -2.11       NaN      NaN                      NaN      NaN
     all common PIT basket CW minus VN30 index (ex degraded) 1371   0.37  0.38    NaN   NaN       NaN      NaN                      NaN     0.88
     all common PIT basket CW minus VN30 index (ex degraded) 1371    NaN   NaN  -0.87 -0.89       NaN      NaN                      NaN      NaN
     all common PIT basket EW minus VN30 index (ex degraded) 1371   0.78  0.72    NaN   NaN       NaN      NaN                      NaN     0.86
     all common PIT basket EW minus VN30 index (ex degraded) 1371    NaN   NaN  -1.91 -1.65       NaN      NaN                      NaN      NaN
     all common                  PIT basket CW minus VNINDEX 1993  -0.61 -0.96    NaN   NaN       NaN      NaN                      NaN     0.92
     all common                  PIT basket CW minus VNINDEX 1993    NaN   NaN   0.56  0.65       NaN      NaN                      NaN      NaN
```

R3 weighting-robust (EW label == CW label): post 2022-08-25: True, pre 2022-08-25: True; index-consistent on the same dates (VN30 index ex degraded vs CW): pre 2022-08-25: False [same 317 dates: VN30 'H1 holds (ON>ID)' vs CW 'no detectable difference' (CW ON-ID 10.05 bp, t 1.57)]; post 2022-08-25: True [same 1054 dates: VN30 'H1 holds (ON>ID)' vs CW 'H1 holds (ON>ID)' (CW ON-ID 19.42 bp, t 5.11)]

Note: CIs use 1.96 x NW SE; R1 uses |t| > 2, so a CI excluding 0 with t in (1.96, 2) is labelled 'no detectable difference' (VNINDEX pre-COVID: t 1.96). Break t of ON-ID across each split is in the verdict table; Test 1b cells with n < 250 are tagged LOW N.

Integrity (no existing file changed): True

## Summary (5 lines)

1. ON-ID (all nights): VNINDEX full 2011-04-29+ +7.11 bp (NW t 3.84, CI 3.5..10.7); VNINDEX common 2018-11-21+ +9.13 bp (NW t 3.37, CI 3.8..14.4); VN30 index common 2018-11-21+ +7.79 bp (NW t 2.77, CI 2.3..13.3) [descriptive, R4]; VN30 index common ex degraded 2019-01..2021-06 +16.01 bp (NW t 5.30, CI 10.1..21.9); PIT basket CW common 2018-11-21+ +7.96 bp (NW t 2.62, CI 2.0..13.9); PIT basket EW common 2018-11-21+ +9.04 bp (NW t 2.97, CI 3.1..15.0); on one-day nights ON-ID is not significant for VNINDEX or either basket (|t| <= 1.08); the VN30 index ex degraded is the exception (t 2.76, n 1086). Test 1b: much of the all-nights difference comes from the post-weekend intraday session (VNINDEX Monday ID -22.3 bp, t -4.74).
2. COVID split: VNINDEX: CHANGES H1 conclusion (break t 1.61); VN30 index (ex degraded): LOW N (break t 0.92); PIT basket CW: CHANGES H1 conclusion (break t 2.05); PIT basket EW: CHANGES H1 conclusion (break t 3.26). KRX split: VNINDEX: same H1 conclusion (break t 3.54); VN30 index (ex degraded): same H1 conclusion (break t 1.36); PIT basket CW: CHANGES H1 conclusion (break t 3.16); PIT basket EW: CHANGES H1 conclusion (break t 3.31).
3. KRX within regime 2: VNINDEX: same H1 conclusion; VN30 index (ex degraded): same H1 conclusion; PIT basket CW: same H1 conclusion; PIT basket EW: same H1 conclusion. Post-KRX n = 387 nights (VNINDEX).
4. Weighting (R3): post 2022-08-25 robust, pre 2022-08-25 robust; index-consistent on same dates: pre 2022-08-25 False, post 2022-08-25 True.
5. VN30 index numbers inside 2019-01..2021-06 are descriptive only (R4); integrity True.
