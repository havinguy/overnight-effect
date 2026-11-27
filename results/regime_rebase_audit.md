# Regime re-basing audit

Read-only on data/raw/ and results/. Step 2 is a clearly labelled RE-BASING RUN (the 'do not recompute regime' restriction is lifted for step 2 only). Script: `src/regime_rebase_audit.py`. KBS index history fetched on 2026-11-24 (`--fetch` re-creates the cache; vendor history can change) through vnstock (source KBS) into the new directory `data/raw_kbs_index/`.

Pre-registered rules: see script header (KBS 'tracks' rule; 'near zero' = |NW t| < 2; flag = |index ON| < 10 bp and |CW basket ON| > 50 bp).

## 1. Independent index open (KBS)

KBS VN30 daily: 2213 rows 2018-01-02..2026-11-17; KBS VNINDEX: 1995 rows 2018-11-19..2026-11-17.
KBS VN30 flat opens (open == own prior close) by year: 2018 13.3%, 2019 20.4%, 2020 54.8%, 2021 47.6%, 2022 1.6%, 2023 0.0%, 2024 0.4%, 2025 17.7%, 2026 0.0%
VCI VN30 flat opens by year: 2018 0.0%, 2019 11.6%, 2020 15.5%, 2021 4.4%, 2022 1.6%, 2023 0.0%, 2024 0.4%, 2025 0.4%, 2026 0.5%

KBS vs VCI VN30 open agreement (|diff| < 0.05 pt) by year: 2018 34%, 2019 30%, 2020 64%, 2021 61%, 2022 99%, 2023 100%, 2024 100%, 2025 82%, 2026 100%

Per quarter, one-day nights, common dates (KBS, VCI with flagged opens kept, CW basket version c). ratio = SD(index ON)/SD(basket ON).

```
                      period   n sd_bas_bp sd_kbs_bp sd_vci_bp ratio_kbs ratio_vci r2_kbs_on_bas r2_vci_on_bas kbs_flat vci_flat corr_kbs_vci  kbs_tracks_vci_not
                      2018Q4  23      70.6      12.7      54.5     0.180     0.772         0.167         0.659    0.043    0.000        0.499               False
                      2019Q1  46      26.8       5.6      22.0     0.208     0.821         0.145         0.635    0.283    0.109        0.403               False
                      2019Q2  48      31.8      11.4      48.4     0.360     1.523         0.506         0.402    0.125    0.042        0.490               False
                      2019Q3  51      38.3      12.2      22.5     0.318     0.587         0.451         0.576    0.255    0.137        0.753               False
                      2019Q4  53      20.1       3.7      14.5     0.185     0.719         0.286         0.571    0.189    0.170        0.574               False
                      2020Q1  45     147.9      13.4      71.6     0.090     0.484         0.394         0.397    0.089    0.089        0.738               False
                      2020Q2  48      93.3      10.5      16.3     0.113     0.175         0.525         0.408    0.188    0.188        0.732               False
                      2020Q3  51      60.5       0.9      40.2     0.015     0.665         0.009         0.329    0.863    0.196        0.021               False
                      2020Q4  53      39.8       7.5      14.0     0.188     0.351         0.111         0.273    0.962    0.189        0.521               False
                      2021Q1  45     117.2       0.0       7.4     0.000     0.063                       0.505    1.000    0.067                            False
                      2021Q2  48      48.4       1.6       6.2     0.033     0.128         0.169         0.273    0.979    0.104        0.250               False
                      2021Q3  51      42.7      41.5      41.5     0.972     0.972         0.942         0.942    0.000    0.020        1.000               False
                      2021Q4  53      25.3      24.9      24.8     0.986     0.981         0.951         0.954    0.000    0.000        0.998               False
                      2022Q1  46      40.8      31.1      30.4     0.763     0.746         0.711         0.719    0.000    0.000        0.995               False
                      2022Q2  49      73.4      63.5      63.5     0.865     0.865         0.801         0.801    0.061    0.061        1.000               False
                      2022Q3  51      50.7      43.0      43.0     0.849     0.849         0.890         0.890    0.000    0.000        1.000               False
                      2022Q4  52     106.3      88.5      88.5     0.832     0.832         0.890         0.890    0.019    0.019        1.000               False
                      2023Q1  46      50.0      39.2      39.2     0.782     0.782         0.782         0.782    0.000    0.000        1.000               False
                      2023Q2  49      17.0      16.6      16.6     0.977     0.977         0.656         0.656    0.000    0.000        1.000               False
                      2023Q3  50      37.3      28.5      28.5     0.764     0.764         0.793         0.793    0.000    0.000        1.000               False
                      2023Q4  52      50.5      41.2      41.2     0.814     0.814         0.789         0.789    0.000    0.000        1.000               False
                      2024Q1  46      26.3      18.1      18.1     0.687     0.687         0.722         0.722    0.000    0.000        1.000               False
                      2024Q2  47      40.4      33.3      33.3     0.824     0.824         0.723         0.723    0.000    0.000        1.000               False
                      2024Q3  50      31.0      27.1      27.1     0.874     0.874         0.803         0.803    0.000    0.000        1.000               False
                      2024Q4  53      24.7      17.3      17.3     0.698     0.698         0.625         0.625    0.000    0.000        1.000               False
                      2025Q1  45      26.9      23.7      23.7     0.880     0.880         0.809         0.809    0.000    0.000        1.000               False
                      2025Q2  48     176.8     111.2     116.1     0.629     0.656         0.651         0.687    0.667    0.000        0.951               False
                      2025Q3  51      47.5      35.6      36.1     0.749     0.758         0.851         0.881    0.039    0.000        0.964               False
                      2025Q4  53      49.8      45.8      45.8     0.920     0.920         0.935         0.935    0.000    0.000        1.000               False
                      2026Q1  45      75.3      61.1      61.1     0.812     0.812         0.807         0.807    0.000    0.000        1.000               False
                      2026Q2  49      57.4      50.0      50.0     0.871     0.871         0.934         0.934    0.000    0.000        1.000               False
                      2026Q3  50      31.4      30.4      30.4     0.969     0.969         0.974         0.973    0.000    0.020        1.000               False
                      2026Q4  27      44.9      43.6      43.6     0.970     0.970         0.977         0.977    0.000    0.000        1.000               False
        POOLED 2020Q1-2021Q2 290      91.9       7.5      34.1     0.082     0.371         0.244         0.275    0.690    0.141        0.549               False
                 POOLED 2019 198      29.9       9.0      29.5     0.300     0.987         0.386         0.423    0.212    0.116        0.526               False
POOLED verified 2022-11-03.. 795      64.6      48.1      48.9     0.745     0.756         0.757         0.769    0.044    0.003        0.981               False
```

- Verified-quarter minima: KBS ratio 0.629, VCI ratio 0.656. Quarters where KBS tracks the basket and VCI does not: none.

VNINDEX (KBS and VCI) vs the same CW VN30 basket. Not a replica pair (VNINDEX is broader), so read each ratio against its own verified quarters.

```
                      period   n sd_bas_bp sd_kbs_bp sd_vci_bp ratio_kbs ratio_vci r2_kbs_on_bas r2_vci_on_bas kbs_flat vci_flat corr_kbs_vci  kbs_tracks_vci_not  vci_tracks_kbs_not
                      2018Q4  23      70.6      65.8      60.6     0.932     0.858         0.973         0.717    0.000    0.130        0.902               False               False
                      2019Q1  46      26.8      29.6      28.8     1.104     1.077         0.888         0.846    0.000    0.022        0.958               False               False
                      2019Q2  48      31.8      28.7      41.5     0.904     1.307         0.743         0.526    0.021    0.062        0.773               False               False
                      2019Q3  51      38.3      36.6      36.5     0.953     0.953         0.947         0.950    0.020    0.059        0.995               False               False
                      2019Q4  53      20.1      16.2      15.5     0.804     0.772         0.792         0.704    0.019    0.075        0.872               False               False
                      2020Q1  45     147.9     113.4     125.3     0.767     0.847         0.860         0.944    0.000    0.111        0.945               False               False
                      2020Q2  48      93.3      84.3      76.3     0.904     0.818         0.947         0.843    0.000    0.083        0.934               False               False
                      2020Q3  51      60.5      48.6      54.5     0.803     0.902         0.923         0.902    0.059    0.078        0.979               False               False
                      2020Q4  53      39.8      34.6      36.3     0.870     0.912         0.887         0.835    0.000    0.113        0.952               False               False
                      2021Q1  45     117.2     104.5     103.5     0.892     0.883         0.987         0.975    0.000    0.044        0.992               False               False
                      2021Q2  48      48.4      37.3      36.1     0.770     0.747         0.842         0.802    0.042    0.083        0.972               False               False
                      2021Q3  51      42.7      39.6       6.7     0.929     0.157         0.898         0.039    0.078    0.961        0.133                True               False
                      2021Q4  53      25.3      26.7       4.7     1.056     0.188         0.756         0.004    0.075    0.981        0.069                True               False
                      2022Q1  46      40.8      39.8      35.4     0.976     0.868         0.763         0.618    0.000    0.326        0.816               False               False
                      2022Q2  49      73.4      74.7      81.1     1.018     1.105         0.874         0.933    0.020    0.020        0.941               False               False
                      2022Q3  51      50.7      46.6      52.5     0.919     1.036         0.812         0.941    0.020    0.000        0.940               False               False
                      2022Q4  52     106.3      86.3      94.7     0.813     0.891         0.952         0.966    0.000    0.000        0.989               False               False
                      2023Q1  46      50.0      32.3      39.1     0.646     0.782         0.771         0.933    0.022    0.000        0.906               False               False
                      2023Q2  49      17.0      15.4      16.0     0.906     0.944         0.757         0.905    0.000    0.000        0.905               False               False
                      2023Q3  50      37.3      32.2      32.8     0.862     0.880         0.843         0.913    0.000    0.000        0.968               False               False
                      2023Q4  52      50.5      40.6      47.8     0.803     0.945         0.828         0.965    0.000    0.000        0.910               False               False
                      2024Q1  46      26.3      20.3      22.1     0.771     0.841         0.778         0.852    0.000    0.000        0.908               False               False
                      2024Q2  47      40.4      30.4      34.2     0.753     0.847         0.785         0.927    0.000    0.000        0.908               False               False
                      2024Q3  50      31.0      25.8      28.4     0.831     0.917         0.788         0.883    0.000    0.000        0.938               False               False
                      2024Q4  53      24.7      19.1      20.6     0.772     0.832         0.912         0.937    0.000    0.000        0.958               False               False
                      2025Q1  45      26.9      19.5      22.1     0.724     0.819         0.748         0.892    0.000    0.000        0.926               False               False
                      2025Q2  48     176.8     117.7     165.0     0.665     0.933         0.761         0.992    0.667    0.000        0.876               False               False
                      2025Q3  51      47.5      33.8      34.1     0.711     0.718         0.856         0.851    0.039    0.000        0.992               False               False
                      2025Q4  53      49.8      48.9      48.9     0.982     0.982         0.866         0.866    0.000    0.000        1.000               False               False
                      2026Q1  45      75.3      59.5      59.5     0.791     0.791         0.631         0.631    0.000    0.000        1.000               False               False
                      2026Q2  49      57.4      51.3      51.3     0.894     0.894         0.853         0.853    0.000    0.000        1.000               False               False
                      2026Q3  50      31.4      36.2      36.2     1.154     1.154         0.877         0.877    0.000    0.020        1.000               False               False
                      2026Q4  27      44.9      41.5      41.5     0.923     0.923         0.957         0.957    0.000    0.000        1.000               False               False
        POOLED 2020Q1-2021Q2 290      91.9      76.4      78.2     0.831     0.851         0.913         0.921    0.017    0.086        0.959               False               False
                 POOLED 2019 198      29.9      28.5      31.9     0.953     1.067         0.856         0.731    0.015    0.056        0.889               False               False
POOLED verified 2022-11-03.. 795      64.6      49.2      58.5     0.761     0.904         0.796         0.928    0.044    0.001        0.926               False               False
```

- VNINDEX verified-quarter minima: KBS 0.646, VCI 0.718. KBS tracks and VCI does not: 2021Q3, 2021Q4; VCI tracks and KBS does not: none.

10 largest |futures ON| nights in 2020-03 (from index_open_degradation_covid.csv) with KBS added (VN30 and VNINDEX; overnight vs each source's own prior close):

```
      date weekday  fut_ON_bp  f2m_ON_bp  basket_cw_all_nights_bp  vci_vn30_ON_bp  vci_flag  kbs_prev_close  kbs_open  kbs_ON_bp  vci_vnindex_ON_bp  kbs_vnindex_ON_bp
2020-03-09     Mon     -443.4     -368.1                   -520.1            -3.8     False           836.0     835.6       -3.8             -177.0             -177.0
2020-03-12     Thu     -369.1     -416.2                   -495.3            -3.4     False           758.2     757.9       -3.4             -419.0             -419.0
2020-03-13     Fri     -381.8     -506.8                   -613.5          -452.7     False           719.2     715.3      -54.0             -447.3             -246.0
2020-03-16     Mon     -188.5     -225.0                    -62.5             0.0      True           716.6     716.6        0.0              -46.1              -46.1
2020-03-17     Tue      104.7      133.4                   -325.1            -2.6     False           698.2     698.0       -2.6             -323.3             -323.3
2020-03-23     Mon     -458.2     -429.5                   -424.0           -39.4     False           673.7     671.0      -39.4             -213.0             -213.0
2020-03-24     Tue      149.3      145.3                   -125.2            -3.6     False           632.9     632.6       -3.6                0.0             -167.9
2020-03-25     Wed      219.6      226.1                    258.6             6.4     False           625.4     625.8        6.4              158.8              158.8
2020-03-30     Mon     -165.6     -167.0                   -522.6            -4.8     False           642.2     641.9       -4.8             -472.9             -472.9
2020-03-31     Tue      153.2      173.5                     68.2             5.1     False           611.8     613.3       25.1              112.3              112.3
```

- Index registered >= half the basket move: KBS VN30 on 0/10 (none), VCI VN30 on 1/10 (2020-03-13).

## 2. RE-BASING RUN: regime evidence with no index open (one-day nights, common dates, stock flat opens kept)

```
                 period cw_n cw_mean_bp cw_nw_t ew_n ew_mean_bp ew_nw_t fut_n fut_mean_bp fut_nw_t flat_share_cw flat_share_ew
                   2018   23     -19.88   -1.52   23     -22.48   -1.80    23       -6.25    -0.53         0.240         0.252
                   2019  198       0.14    0.07  198      -3.04   -1.52   198        3.38     1.63         0.350         0.351
                   2020  197      -4.78   -0.56  197      -5.65   -0.63   197        7.98     1.28         0.273         0.270
                   2021  196       7.43    1.41  196       7.78    1.36   196        7.78     2.21         0.239         0.235
                   2022  196      -2.89   -0.51  196      -3.94   -0.64   196        3.34     1.02         0.206         0.203
                   2023  186      14.06    6.11  186      16.33    7.09   186        8.46     3.93         0.303         0.287
                   2024  196      11.66    4.93  196      13.71    6.10   196        4.03     2.02         0.300         0.302
                   2025  197      18.01    2.71  197      15.53    2.38   197        7.94     2.37         0.226         0.239
                   2026  171      14.42    2.97  171      14.98    3.59   171        9.27     2.07         0.245         0.244
         pre 2022-08-25  740      -0.82   -0.28  740      -2.11   -0.68   740        5.41     2.57         0.274         0.273
        post 2022-08-25  820      13.46    5.70  820      13.94    6.03   820        7.05     4.53         0.262         0.261
pre excl. 2020Q1-2021Q2  451       0.81    0.39  451      -1.05   -0.47   451        3.84     2.54         0.285         0.284
                    all 1560       6.69    3.50 1560       6.32    3.21  1560        6.28     4.86         0.268         0.267
```

Futures on all its own one-day nights from 2018-11-21 (not restricted to basket dates):

```
         period   n  mean_bp  nw_t
           2018  23    -6.25 -0.53
           2019 198     3.38  1.63
           2020 197     7.98  1.28
           2021 196     7.78  2.21
           2022 196     3.34  1.02
           2023 186     8.46  3.93
           2024 196     4.03  2.02
           2025 197     7.94  2.37
           2026 171     9.27  2.07
 pre 2022-08-25 740     5.41  2.57
post 2022-08-25 820     7.05  4.53
```

- Pre-cutover: CW -0.82 bp (t -0.28), EW -2.11 bp (t -0.68), futures 5.41 bp (t 2.57), n 740. Post: CW 13.46 (t 5.70), EW 13.94 (t 6.03), futures 7.05 (t 4.53), n 820.
- Near zero pre-cutover (|NW t| < 2): CW True, EW True, futures False.
- Reference only, quoted not recomputed: published VCI VN30 index overnight pre 0.89 bp (t 0.70), post 9.99 bp (t 6.42), all nights (open_audit_summary.md).

Post minus pre (ADDED AFTER THE FIRST RUN; NW SE combined across the two independent subsamples):

```
   series  pre_bp  post_bp  post_minus_pre_bp  nw_se    t
CW basket   -0.82    13.46              14.28   3.75 3.81
EW basket   -2.11    13.94              16.05   3.87 4.15
  futures    5.41     7.05               1.64   2.61 0.63
```

Impossible stock gaps (ADDED AFTER THE FIRST RUN): stock-days in the baskets with |open/prior close - 1| > 7.5% (beyond the +/-7% limit; usually unadjusted corporate actions or bad prints), and their contribution to the basket means (basket minus the same basket with those returns set to 0, denominators unchanged):

```
         period  stock_days_beyond_7_5pct  dates_affected  cw_contribution_bp  ew_contribution_bp
 pre 2022-08-25                        45              42                0.00                0.00
post 2022-08-25                         6               6                0.00                0.00
```

Counts are over the whole stock universe; stock-days that are PIT VN30 members on their date: 0. Hence the exact-zero contribution: no impossible gap enters either basket.

Largest such stock-days (all non-members on the date): 2024-01-30 MCH -1618 bp; 2022-11-16 BSR -1504 bp; 2021-01-28 BSR -1373 bp; 2020-03-03 GVR 1360 bp; 2021-06-29 MCH 1309 bp; 2020-03-04 LPB 1297 bp; 2025-04-10 MCH 1236 bp; 2020-03-24 BSR 1232 bp

## 3. Degraded-index flag (report only; applied nowhere)

Flag = |index ON| < 10 bp and |CW basket ON| > 50 bp, one-day nights, common dates. Shown for VCI VN30 (with the subset already VCI-flagged as open == prior close) and KBS VN30.

```
quarter  n  basket_big  flag_vci  flag_vci_not_flat  flag_kbs  rate_vci_given_big
 2018Q4 23           7         2                  2         6                0.29
 2019Q1 46           2         1                  1         2                0.50
 2019Q2 48           8         0                  0         4                0.00
 2019Q3 51           4         0                  0         1                0.00
 2019Q4 53           2         1                  1         2                0.50
 2020Q1 45          21        16                 14        15                0.76
 2020Q2 48          19        11                  7        12                0.58
 2020Q3 51          13         9                  7        13                0.69
 2020Q4 53           7         3                  3         6                0.43
 2021Q1 45          20        14                 13        20                0.70
 2021Q2 48          13        10                  9        12                0.77
 2021Q3 51          14         1                  1         1                0.07
 2021Q4 53           6         0                  0         0                0.00
 2022Q1 46           9         1                  1         1                0.11
 2022Q2 49          17         2                  1         2                0.12
 2022Q3 51          17         2                  2         2                0.12
 2022Q4 52          30         3                  3         3                0.10
 2023Q1 46          15         0                  0         0                0.00
 2023Q2 49           2         0                  0         0                0.00
 2023Q3 50           6         0                  0         0                0.00
 2023Q4 52          14         3                  3         3                0.21
 2024Q1 46           4         0                  0         0                0.00
 2024Q2 47          12         3                  3         3                0.25
 2024Q3 50           6         0                  0         0                0.00
 2024Q4 53           2         1                  1         1                0.50
 2025Q1 45           3         0                  0         0                0.00
 2025Q2 48          14         0                  0         5                0.00
 2025Q3 51          19         0                  0         0                0.00
 2025Q4 53          12         0                  0         0                0.00
 2026Q1 45          15         0                  0         0                0.00
 2026Q2 49          11         0                  0         0                0.00
 2026Q3 50           5         0                  0         0                0.00
 2026Q4 27           4         0                  0         0                0.00
```

```
               period   n  basket_big  flag_vci  flag_vci_not_flat  flag_kbs  flag_vci_per_100  flag_vci_share_of_big
  2018-11..2022-11-02 779         187        73                 62        99              9.37                   0.39
verified 2022-11-03.. 795         166        10                 10        15              1.26                   0.06
        2020Q1-2021Q2 290          93        63                 53        78             21.72                   0.68
```

## 4. Pre-cutover claims that would need rewording

No memory file exists for this project (the Claude memory directory is empty and the repo has no notes file), so the claims below are taken from the published results summaries. Outcomes of step 2: A = baskets and futures both near zero pre-cutover; B = baskets near zero, futures positive (OBSERVED); C = baskets positive.

| Claim (source) | A | B (observed) | C |
|---|---|---|---|
| 'Regime 1: published VN30 overnight ~0 before 2022-08-25 (0.89 bp, t 0.70); positive after' (open_audit_summary.md) | keep, re-source to stocks+futures | reword: 'stock overnight ~0 pre-cutover (CW -0.82 bp, t -0.28); futures overnight positive (5.41 bp, t 2.57); the index number is index-open-dependent; the claim is now carried by stock-only evidence' | reword: regime-1 zero is an index artifact |
| 'Level A full-sample positive overnight comes from outside 2018-11..2022-08' (open_audit_summary.md) | keep | keep for stocks; not true for futures | drop |
| 'Levels A/B unfiltered overnight positive after, not before (Level A VN30 0.89 bp; Level B 1.95 bp, t 0.79)' (open_audit_summary.md) | keep | keep for Level B (stocks); Level A VN30 pre value flagged as index-open-dependent | reword both |
| 'Index positive, stocks ~0 hypothesis rejected: basket minus index regime 1 = -3.63 bp' (open_audit_summary.md) | keep, caveat index | keep conclusion (stocks ~0 confirmed without the index); the -3.63 bp gap itself is index-open-dependent | reword |
| R1 'Monday futures edge is mostly basis, 82% in 2018-11..2021' (futures_basis_summary.md) | reword: basis vs ~0 stocks | reword: 'futures minus stocks' is positive on average pre-cutover (one-day nights; not tested for Mon->Tue here), but the 82% share is computed against a degraded index open; Monday share not recomputed here | reword: share overstated |
| Pre-cutover Mon->Tue dbasis +12.82 bp; follow-up pre-cutover weekday tests t 2.09 / 2.24 | caveat | caveat: index leg degraded 2020-21Q2; sign plausibly survives vs stocks (not tested by weekday here) | caveat |
| Option C P1 'regime 1' holds (option_c_summary.md) | none (stock prices, CUTOVER is the T+2 rule date) | none | none |
| R3 slopes 2019-21, pre-cutover offset k 0.64 | flag | flag (index-open-dependent; no rebase done) | flag |

## Reading

**KBS.** KBS VN30 is not an independent open: identical to VCI from 2021Q3 (corr ~1.00) and worse before (flat opens 69% pooled 2020Q1-2021Q2 vs VCI 14%; SD ratio 0.08 vs VCI 0.37). Under the pre-registered rule no quarter has KBS VN30 tracking the basket while VCI does not. On the COVID nights KBS VN30 registered the move on 0/10. VNINDEX is different: both vendors' VNINDEX opens track the VN30 basket through 2019-2021Q2 (pooled 2020Q1-2021Q2 ratio KBS 0.83, VCI 0.85; R^2 0.91 / 0.92; verified 0.76 / 0.90), and register the COVID moves (e.g. 2020-03-30: VNINDEX -473 bp both vendors, VN30 -5 bp both vendors). KBS VNINDEX tracks where VCI VNINDEX does not only in 2021Q3-Q4 (VCI's known 2021 VNINDEX fill). So the 2020-21Q2 degradation is specific to the VN30 index open: both vendors' VN30 opens are degraded (in different forms - KBS mostly exact-flat, VCI mostly near-flat; KBS-VCI corr 0.02-0.74 in several quarters), while both vendors' VNINDEX opens and the constituent opens are normal. Whether it originates in the exchange's VN30 calculation or in common vendor processing cannot be determined from these data.

**Re-based regime (stocks and futures only).** Pre-cutover, both baskets are near zero (CW -0.82 bp, t -0.28; EW -2.11, t -0.68; n 740) and strongly positive after (CW 13.46, t 5.70). The near-zero pre-cutover overnight is therefore NOT only an index artifact for stocks. It does not hold for futures: 5.41 bp, t 2.57 pre vs 7.05, t 4.53 post. Excluding 2020Q1-2021Q2 changes nothing material (CW 0.81, futures 3.84 bp, t 2.54). Flat-open share is similar pre and post (cw 0.274 vs 0.262), so differential constituent anchoring does not explain the stock pre/post gap. Caveats: the futures window (prior 14:45 close -> 08:45/09:00 open) differs from the stock window (prior close -> stock ATO); pre-2022-06 futures opens are unverified (open-definition and stability audits); one-day nights only (Mondays and holidays excluded).

**Flag (report only).** 73 VCI-VN30 nights flagged in 2018-11..2022-11-02 (9.4 per 100 one-day nights; 62 not already VCI-flagged), 63 of them in 2020Q1-2021Q2 (68% of large-basket nights); verified window 10 (1.3 per 100, 6% of large-basket nights) - that is the flag's floor on good opens. KBS VN30: 99 vs 15.

## Summary (5 lines)

1. KBS: VN30 history exists (2018-01+) but is not independent - identical to VCI from 2021Q3 and more degraded before (flat 69% in 2020Q1-2021Q2); no quarter where KBS VN30 tracks the basket and VCI does not; VNINDEX (both vendors) tracks the basket normally in 2019-2021Q2, so the degradation is specific to the VN30 index open (both vendors, different forms; exchange vs vendor origin not determinable).
2. Pre-cutover weakness survives in stocks (CW -0.82 bp, t -0.28; EW -2.11, t -0.68) but not in futures (5.41 bp, t 2.57); post-cutover all three positive (CW 13.5, futures 7.1 bp); the break is in stocks only (post minus pre CW 14.3 bp, t 3.8; futures 1.6 bp, t 0.6); impossible stock gaps contribute 0 (none on PIT members).
3. Flag counts (|index ON| < 10 bp, |basket ON| > 50 bp): VCI VN30 73 nights 2018-11..2022 (63 in 2020Q1-2021Q2) vs 10 in the verified window (9.4 vs 1.3 per 100 nights); not applied anywhere.
4. Reword (outcome B): the regime-1 claim and any 'change at the cutover' claim must name stocks only (stock overnight ~0 pre holds without the index; futures were positive pre and show no break); Level A VN30 pre value and the -3.63 bp basket-minus-index gap flagged as index-open-dependent; R1 82% Monday basis share and pre-cutover dbasis tests caveated (computed against a degraded index open). No memory file exists; claims taken from results summaries.
5. Open question: why were futures overnight returns positive pre-cutover while stocks were ~0 - the timing difference (08:45 futures open vs stock ATO), basis convergence (the earlier decomposition put the pre-cutover excess in dbasis), or unverified pre-2022-06 futures opens? Next run (not done): pre-cutover futures close-to-close minus basket close-to-close - an excess at a similar daily rate points to carry/convergence, an excess confined to the overnight points to the open.

Integrity: md5 of every file in data/raw/ and results/ (excluding this audit's and the degradation audit's outputs) identical before and after: True (248 files).
