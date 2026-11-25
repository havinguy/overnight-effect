# Level A robustness (src/level_a_robustness.py)

Pre-registered rules and split dates (with sources) are in the script header. bp per night; NW lag 5.

## Test 1: ON minus ID (design doc t-test on the mean difference)

```
       series         nights                              sample   leg    n  mean_bp  nw_t  lo95  hi95                       R1
      VNINDEX     all nights                    full 2011-04-29+ ON-ID    0      NaN   NaN   NaN   NaN no detectable difference
      VNINDEX     all nights                  common 2018-11-21+ ON-ID    0      NaN   NaN   NaN   NaN no detectable difference
      VNINDEX one-day nights                    full 2011-04-29+ ON-ID    0      NaN   NaN   NaN   NaN no detectable difference
      VNINDEX one-day nights                  common 2018-11-21+ ON-ID    0      NaN   NaN   NaN   NaN no detectable difference
   VN30 index     all nights                  common 2018-11-21+ ON-ID    0      NaN   NaN   NaN   NaN no detectable difference
   VN30 index     all nights common ex degraded 2019-01..2021-06 ON-ID    0      NaN   NaN   NaN   NaN no detectable difference
   VN30 index one-day nights                  common 2018-11-21+ ON-ID    0      NaN   NaN   NaN   NaN no detectable difference
   VN30 index one-day nights common ex degraded 2019-01..2021-06 ON-ID    0      NaN   NaN   NaN   NaN no detectable difference
PIT basket CW     all nights                  common 2018-11-21+ ON-ID 1993     7.96  2.62  2.02 13.91         H1 holds (ON>ID)
PIT basket CW one-day nights                  common 2018-11-21+ ON-ID 1574     2.93  0.81 -4.13  9.99 no detectable difference
PIT basket EW     all nights                  common 2018-11-21+ ON-ID 1993     9.04  2.97  3.08 15.00         H1 holds (ON>ID)
PIT basket EW one-day nights                  common 2018-11-21+ ON-ID 1574     3.92  1.08 -3.17 11.01 no detectable difference
```

## Test 2: sub-period splits (VN30 index excludes its degraded window 2019-01..2021-06)

```
                  series               split                     period  ON_bp  ON_t    n  ID_bp  ID_t  ON-ID_bp  ON-ID_t  ONmID_lo95  ONmID_hi95                       R1
                 VNINDEX         COVID 2-way   pre-COVID (< 2020-01-23)    NaN   NaN    0    NaN   NaN       NaN      NaN         NaN         NaN                    LOW N
                 VNINDEX         COVID 2-way post-COVID (>= 2020-01-23)    NaN   NaN    0    NaN   NaN       NaN      NaN         NaN         NaN                    LOW N
                 VNINDEX         COVID 3-way                  pre-COVID    NaN   NaN    0    NaN   NaN       NaN      NaN         NaN         NaN                    LOW N
                 VNINDEX         COVID 3-way     2020-01-23..2022-08-24    NaN   NaN    0    NaN   NaN       NaN      NaN         NaN         NaN                    LOW N
                 VNINDEX         COVID 3-way              >= 2022-08-25    NaN   NaN    0    NaN   NaN       NaN      NaN         NaN         NaN                    LOW N
                 VNINDEX                 KRX     pre-KRX (< 2025-05-05)    NaN   NaN    0    NaN   NaN       NaN      NaN         NaN         NaN                    LOW N
                 VNINDEX                 KRX   post-KRX (>= 2025-05-05)    NaN   NaN    0    NaN   NaN       NaN      NaN         NaN         NaN                    LOW N
                 VNINDEX KRX within regime 2     2022-08-25..2025-05-04    NaN   NaN    0    NaN   NaN       NaN      NaN         NaN         NaN                    LOW N
                 VNINDEX KRX within regime 2   post-KRX (>= 2025-05-05)    NaN   NaN    0    NaN   NaN       NaN      NaN         NaN         NaN                    LOW N
VN30 index (ex degraded)         COVID 2-way   pre-COVID (< 2020-01-23)    NaN   NaN    0    NaN   NaN       NaN      NaN         NaN         NaN                    LOW N
VN30 index (ex degraded)         COVID 2-way post-COVID (>= 2020-01-23)    NaN   NaN    0    NaN   NaN       NaN      NaN         NaN         NaN                    LOW N
VN30 index (ex degraded)         COVID 3-way                  pre-COVID    NaN   NaN    0    NaN   NaN       NaN      NaN         NaN         NaN                    LOW N
VN30 index (ex degraded)         COVID 3-way     2020-01-23..2022-08-24    NaN   NaN    0    NaN   NaN       NaN      NaN         NaN         NaN                    LOW N
VN30 index (ex degraded)         COVID 3-way              >= 2022-08-25    NaN   NaN    0    NaN   NaN       NaN      NaN         NaN         NaN                    LOW N
VN30 index (ex degraded)                 KRX     pre-KRX (< 2025-05-05)    NaN   NaN    0    NaN   NaN       NaN      NaN         NaN         NaN                    LOW N
VN30 index (ex degraded)                 KRX   post-KRX (>= 2025-05-05)    NaN   NaN    0    NaN   NaN       NaN      NaN         NaN         NaN                    LOW N
VN30 index (ex degraded) KRX within regime 2     2022-08-25..2025-05-04    NaN   NaN    0    NaN   NaN       NaN      NaN         NaN         NaN                    LOW N
VN30 index (ex degraded) KRX within regime 2   post-KRX (>= 2025-05-05)    NaN   NaN    0    NaN   NaN       NaN      NaN         NaN         NaN                    LOW N
           PIT basket CW         COVID 2-way   pre-COVID (< 2020-01-23)  -1.04 -0.44  293   1.54  0.38     -2.57    -0.52      -12.28        7.13 no detectable difference
           PIT basket CW         COVID 2-way post-COVID (>= 2020-01-23)   6.67  3.12 1700  -3.11 -1.17      9.78     2.84        3.04       16.52         H1 holds (ON>ID)
           PIT basket CW         COVID 3-way                  pre-COVID  -1.04 -0.44  293   1.54  0.38     -2.57    -0.52      -12.28        7.13 no detectable difference
           PIT basket CW         COVID 3-way     2020-01-23..2022-08-24  -0.60 -0.14  646   5.35  1.17     -5.95    -0.94      -18.31        6.41 no detectable difference
           PIT basket CW         COVID 3-way              >= 2022-08-25  11.13  5.02 1054  -8.29 -2.60     19.42     5.11       11.97       26.87         H1 holds (ON>ID)
           PIT basket CW                 KRX     pre-KRX (< 2025-05-05)   2.89  1.34 1606  -1.08 -0.41      3.97     1.14       -2.85       10.80 no detectable difference
           PIT basket CW                 KRX   post-KRX (>= 2025-05-05)  16.52  5.27  387  -8.00 -1.57     24.52     4.48       13.78       35.25         H1 holds (ON>ID)
           PIT basket CW KRX within regime 2     2022-08-25..2025-05-04   8.00  2.71  667  -8.46 -2.07     16.46     3.24        6.51       26.40         H1 holds (ON>ID)
           PIT basket CW KRX within regime 2   post-KRX (>= 2025-05-05)  16.52  5.27  387  -8.00 -1.57     24.52     4.48       13.78       35.25         H1 holds (ON>ID)
           PIT basket EW         COVID 2-way   pre-COVID (< 2020-01-23)  -4.80 -2.12  293   2.43  0.63     -7.22    -1.53      -16.48        2.03 no detectable difference
           PIT basket EW         COVID 2-way post-COVID (>= 2020-01-23)   7.17  3.21 1700  -4.68 -1.78     11.84     3.44        5.09       18.59         H1 holds (ON>ID)
           PIT basket EW         COVID 3-way                  pre-COVID  -4.80 -2.12  293   2.43  0.63     -7.22    -1.53      -16.48        2.03 no detectable difference
           PIT basket EW         COVID 3-way     2020-01-23..2022-08-24  -0.39 -0.09  646   5.03  1.11     -5.42    -0.85      -17.88        7.04 no detectable difference
           PIT basket EW         COVID 3-way              >= 2022-08-25  11.80  5.30 1054 -10.63 -3.40     22.42     5.99       15.09       29.75         H1 holds (ON>ID)
           PIT basket EW                 KRX     pre-KRX (< 2025-05-05)   3.01  1.31 1606  -2.12 -0.81      5.13     1.45       -1.81       12.07 no detectable difference
           PIT basket EW                 KRX   post-KRX (>= 2025-05-05)  15.37  5.51  387  -9.89 -2.03     25.26     5.10       15.55       34.98         H1 holds (ON>ID)
           PIT basket EW KRX within regime 2     2022-08-25..2025-05-04   9.72  3.14  667 -11.05 -2.73     20.77     4.03       10.66       30.89         H1 holds (ON>ID)
           PIT basket EW KRX within regime 2   post-KRX (>= 2025-05-05)  15.37  5.51  387  -9.89 -2.03     25.26     5.10       15.55       34.98         H1 holds (ON>ID)
```

```
                  series               split                                                                                             sides                    R2
                 VNINDEX         COVID 2-way                               pre-COVID (< 2020-01-23): LOW N | post-COVID (>= 2020-01-23): LOW N                 LOW N
                 VNINDEX                 KRX                                   pre-KRX (< 2025-05-05): LOW N | post-KRX (>= 2025-05-05): LOW N                 LOW N
                 VNINDEX KRX within regime 2                                   2022-08-25..2025-05-04: LOW N | post-KRX (>= 2025-05-05): LOW N                 LOW N
VN30 index (ex degraded)         COVID 2-way                               pre-COVID (< 2020-01-23): LOW N | post-COVID (>= 2020-01-23): LOW N                 LOW N
VN30 index (ex degraded)                 KRX                                   pre-KRX (< 2025-05-05): LOW N | post-KRX (>= 2025-05-05): LOW N                 LOW N
VN30 index (ex degraded) KRX within regime 2                                   2022-08-25..2025-05-04: LOW N | post-KRX (>= 2025-05-05): LOW N                 LOW N
           PIT basket CW         COVID 2-way pre-COVID (< 2020-01-23): no detectable difference | post-COVID (>= 2020-01-23): H1 holds (ON>ID) CHANGES H1 conclusion
           PIT basket CW                 KRX     pre-KRX (< 2025-05-05): no detectable difference | post-KRX (>= 2025-05-05): H1 holds (ON>ID) CHANGES H1 conclusion
           PIT basket CW KRX within regime 2             2022-08-25..2025-05-04: H1 holds (ON>ID) | post-KRX (>= 2025-05-05): H1 holds (ON>ID)    same H1 conclusion
           PIT basket EW         COVID 2-way pre-COVID (< 2020-01-23): no detectable difference | post-COVID (>= 2020-01-23): H1 holds (ON>ID) CHANGES H1 conclusion
           PIT basket EW                 KRX     pre-KRX (< 2025-05-05): no detectable difference | post-KRX (>= 2025-05-05): H1 holds (ON>ID) CHANGES H1 conclusion
           PIT basket EW KRX within regime 2             2022-08-25..2025-05-04: H1 holds (ON>ID) | post-KRX (>= 2025-05-05): H1 holds (ON>ID)    same H1 conclusion
```

## Test 3: EW vs CW basket vs published index (common dates, all nights)

```
         regime                                       series  n  ON_bp  ON_t  ID_bp  ID_t  ONmID_bp  ONmID_t                       R1  corr_ON
 pre 2022-08-25                                      VNINDEX  0    NaN   NaN    NaN   NaN       NaN      NaN no detectable difference      NaN
 pre 2022-08-25                     VN30 index (ex degraded)  0    NaN   NaN    NaN   NaN       NaN      NaN no detectable difference      NaN
 pre 2022-08-25                                PIT basket CW  0    NaN   NaN    NaN   NaN       NaN      NaN no detectable difference      NaN
 pre 2022-08-25                                PIT basket EW  0    NaN   NaN    NaN   NaN       NaN      NaN no detectable difference      NaN
 pre 2022-08-25            PIT basket EW minus PIT basket CW  0    NaN   NaN    NaN   NaN       NaN      NaN                      NaN      NaN
 pre 2022-08-25            PIT basket EW minus PIT basket CW  0    NaN   NaN    NaN   NaN       NaN      NaN                      NaN      NaN
 pre 2022-08-25 PIT basket CW minus VN30 index (ex degraded)  0    NaN   NaN    NaN   NaN       NaN      NaN                      NaN      NaN
 pre 2022-08-25 PIT basket CW minus VN30 index (ex degraded)  0    NaN   NaN    NaN   NaN       NaN      NaN                      NaN      NaN
 pre 2022-08-25 PIT basket EW minus VN30 index (ex degraded)  0    NaN   NaN    NaN   NaN       NaN      NaN                      NaN      NaN
 pre 2022-08-25 PIT basket EW minus VN30 index (ex degraded)  0    NaN   NaN    NaN   NaN       NaN      NaN                      NaN      NaN
 pre 2022-08-25                  PIT basket CW minus VNINDEX  0    NaN   NaN    NaN   NaN       NaN      NaN                      NaN      NaN
 pre 2022-08-25                  PIT basket CW minus VNINDEX  0    NaN   NaN    NaN   NaN       NaN      NaN                      NaN      NaN
post 2022-08-25                                      VNINDEX  0    NaN   NaN    NaN   NaN       NaN      NaN no detectable difference      NaN
post 2022-08-25                     VN30 index (ex degraded)  0    NaN   NaN    NaN   NaN       NaN      NaN no detectable difference      NaN
post 2022-08-25                                PIT basket CW  0    NaN   NaN    NaN   NaN       NaN      NaN no detectable difference      NaN
post 2022-08-25                                PIT basket EW  0    NaN   NaN    NaN   NaN       NaN      NaN no detectable difference      NaN
post 2022-08-25            PIT basket EW minus PIT basket CW  0    NaN   NaN    NaN   NaN       NaN      NaN                      NaN      NaN
post 2022-08-25            PIT basket EW minus PIT basket CW  0    NaN   NaN    NaN   NaN       NaN      NaN                      NaN      NaN
post 2022-08-25 PIT basket CW minus VN30 index (ex degraded)  0    NaN   NaN    NaN   NaN       NaN      NaN                      NaN      NaN
post 2022-08-25 PIT basket CW minus VN30 index (ex degraded)  0    NaN   NaN    NaN   NaN       NaN      NaN                      NaN      NaN
post 2022-08-25 PIT basket EW minus VN30 index (ex degraded)  0    NaN   NaN    NaN   NaN       NaN      NaN                      NaN      NaN
post 2022-08-25 PIT basket EW minus VN30 index (ex degraded)  0    NaN   NaN    NaN   NaN       NaN      NaN                      NaN      NaN
post 2022-08-25                  PIT basket CW minus VNINDEX  0    NaN   NaN    NaN   NaN       NaN      NaN                      NaN      NaN
post 2022-08-25                  PIT basket CW minus VNINDEX  0    NaN   NaN    NaN   NaN       NaN      NaN                      NaN      NaN
     all common                                      VNINDEX  0    NaN   NaN    NaN   NaN       NaN      NaN no detectable difference      NaN
     all common                     VN30 index (ex degraded)  0    NaN   NaN    NaN   NaN       NaN      NaN no detectable difference      NaN
     all common                                PIT basket CW  0    NaN   NaN    NaN   NaN       NaN      NaN no detectable difference      NaN
     all common                                PIT basket EW  0    NaN   NaN    NaN   NaN       NaN      NaN no detectable difference      NaN
     all common            PIT basket EW minus PIT basket CW  0    NaN   NaN    NaN   NaN       NaN      NaN                      NaN      NaN
     all common            PIT basket EW minus PIT basket CW  0    NaN   NaN    NaN   NaN       NaN      NaN                      NaN      NaN
     all common PIT basket CW minus VN30 index (ex degraded)  0    NaN   NaN    NaN   NaN       NaN      NaN                      NaN      NaN
     all common PIT basket CW minus VN30 index (ex degraded)  0    NaN   NaN    NaN   NaN       NaN      NaN                      NaN      NaN
     all common PIT basket EW minus VN30 index (ex degraded)  0    NaN   NaN    NaN   NaN       NaN      NaN                      NaN      NaN
     all common PIT basket EW minus VN30 index (ex degraded)  0    NaN   NaN    NaN   NaN       NaN      NaN                      NaN      NaN
     all common                  PIT basket CW minus VNINDEX  0    NaN   NaN    NaN   NaN       NaN      NaN                      NaN      NaN
     all common                  PIT basket CW minus VNINDEX  0    NaN   NaN    NaN   NaN       NaN      NaN                      NaN      NaN
```

R3 weighting-robust (EW label == CW label): post 2022-08-25: True, pre 2022-08-25: True; index-consistent (VN30 index ex degraded == CW): post 2022-08-25: True, pre 2022-08-25: True

Integrity (no existing file changed): True

## Summary (5 lines)

1. ON-ID (all nights): VNINDEX full 2011-04-29+ +nan bp (NW t nan, CI nan..nan); VNINDEX common 2018-11-21+ +nan bp (NW t nan, CI nan..nan); VN30 index common 2018-11-21+ +nan bp (NW t nan, CI nan..nan); VN30 index common ex degraded 2019-01..2021-06 +nan bp (NW t nan, CI nan..nan); PIT basket CW common 2018-11-21+ +7.96 bp (NW t 2.62, CI 2.0..13.9); PIT basket EW common 2018-11-21+ +9.04 bp (NW t 2.97, CI 3.1..15.0).
2. COVID split: VNINDEX: LOW N; VN30 index (ex degraded): LOW N; PIT basket CW: CHANGES H1 conclusion; PIT basket EW: CHANGES H1 conclusion. KRX split: VNINDEX: LOW N; VN30 index (ex degraded): LOW N; PIT basket CW: CHANGES H1 conclusion; PIT basket EW: CHANGES H1 conclusion.
3. KRX within regime 2: VNINDEX: LOW N; VN30 index (ex degraded): LOW N; PIT basket CW: same H1 conclusion; PIT basket EW: same H1 conclusion. Post-KRX n = 0 nights (VNINDEX).
4. Weighting (R3): post 2022-08-25 robust, pre 2022-08-25 robust; index-consistent: post 2022-08-25 True, pre 2022-08-25 True.
5. VN30 index numbers inside 2019-01..2021-06 are descriptive only (R4); integrity True.
