# Option C: T+2-constrained equity overnight effect (measurement only)

Nothing is selected here, so there is no forward test. Single VN30 stocks, point-in-time membership as of the entry date, date-level baskets for all inference.

## Settlement rule and source
- Cutover constant `CUTOVER = 2022-08-25` (trade date T+0). Trades on/after it: shares credited before 13:00 on T+2, sellable in the T+2 afternoon session -> earliest exit Close[T+2] (ATC). Before it: earliest sale T+3 -> earliest exit Open[T+3] (ATO).
- Source: Thi truong Tai chinh Tien te (SBV-affiliated journal), 'Tu ngay 29/8, chinh thuc rut ngan thoi gian thanh toan giao dich chung khoan xuong con T+2': VSD Decisions 109/QD-VSD (clearing & settlement rules) and 110/QD-VSD (depository members), effective 29/8/2022; trades of 25/8/2022 (T+0) are the first that can be sold in the afternoon of T+2 (29/8) 'instead of waiting until T+3 as before'; VSD settlement moved from 15:30-16:00 to 11:00-11:30 on T+2, members allocate to clients before 13:00. https://thitruongtaichinhtiente.vn/tu-ngay-29-8-chinh-thuc-rut-ngan-thoi-gian-thanh-toan-giao-dich-chung-khoan-xuong-con-t-2-41949.html . Decision 109/QD-VSD is dated 19/8/2022 (luatvietnam.vn listing).
- NOT confirmed from the primary VSD document (full text behind a login). Also not confirmed: that regime-1 shares were sellable at the T+3 ATO (the source says only 'T+3'); that the 25 Aug 2022 entry is the first one in regime 2 is from the news source, not the decision text.
- T+k uses the VNINDEX trading calendar. Period P1 ends the day before the cutover, so P1 = regime 1 exactly; the 5 entry dates 25-31 Aug 2022 are in P2.

## Assumptions (parameters, not facts)
- Sale tax 10 bp on the sell leg; brokerage swept over (10, 15, 25) bp per side; round trip = 2 x brokerage + tax = 30 / 40 / 60 bp.
- Slippage 0: ATC/ATO fills at the official print. This is idealized (no market impact, no queue risk at the ATC).
- One round trip per hold. 'Per overnight' = net per hold / number of overnight legs in the hold (2 in regime 2, 3 in regime 1).
- Headline returns are simple (EW basket P&L); legs are log returns (additive). Log means sit below simple means by about sigma^2/2.
- Limit filters: entry excluded if Close[T] >= +6.9% vs prior close (limit-up, unbuyable); excluded if the exit price is <= -6.9% vs prior close (limit-down, unsellable). Prices are back-adjusted (data-quality flag 8), consistent with the exchange's adjusted reference price on ex-dates. New-listing and ex-right bands are ignored.
- Cap-weighted basket: reuses pit_dayofweek_2x2.build_weights('pit','B') (shares x free float x capping factor, latest-shares variant B) x Close[T]. Back-adjusted prices mix with historical share counts (flag 8), so cap weights are approximate.
- Baskets need >= 10 eligible stocks on the date. Newey-West (Bartlett) lags = hold length for pooled all-days series; within a weekday entries are weekly and non-overlapping, so plain t.

## Filter counts (stock-entries)
      rule  candidates  skip_missing_bar  excl_buy_limit_up  excl_sell_limit_down  eligible_close_set  dropped_suspicious_open  dropped_suspicious_share_%  decomp_set
R2_T2close       59730             12.00             402.00                425.00               58891                 26459.00                       44.93       32432
 R1_T3open       59700             12.00             402.00                103.00               59183                 34408.00                       58.14       24775
R1_T3close       59700             12.00             402.00                426.00               58860                 34281.00                       58.24       24579

By period (stock-entries):
      rule                         period  candidates  eligible_close_set  decomp_set
R2_T2close P1 2018-11..2022-08 (regime 1)       28170               27779       15156
R2_T2close P2 2022-08-25..2025 (regime 2)       25140               24833       13590
R2_T2close        P3 2026-only (regime 2)        6420                6279        3686
R2_T2close           Regime 2 all (P2+P3)       31560               31112       17276
R2_T2close          Full 2018-11..2026-11       59730               58891       32432
 R1_T3open P1 2018-11..2022-08 (regime 1)       28170               27951       11517
 R1_T3open P2 2022-08-25..2025 (regime 2)       25140               24936       10331
 R1_T3open        P3 2026-only (regime 2)        6390                6296        2927
 R1_T3open           Regime 2 all (P2+P3)       31530               31232       13258
 R1_T3open          Full 2018-11..2026-11       59700               59183       24775
R1_T3close P1 2018-11..2022-08 (regime 1)       28170               27780       11425
R1_T3close P2 2022-08-25..2025 (regime 2)       25140               24830       10262
R1_T3close        P3 2026-only (regime 2)        6390                6250        2892
R1_T3close           Regime 2 all (P2+P3)       31530               31080       13154
R1_T3close          Full 2018-11..2026-11       59700               58860       24579

## Executable hold, gross (EW basket, simple returns, all entry dates)
      rule                         period weekday  n_dates  mean_k  mean_bp  mean_log_bp  sd_bp     t  t_nw  hit_pct  net_bp_brk10  net_bp_brk25
R2_T2close P2 2022-08-25..2025 (regime 2)     All      838   29.63    11.72         7.66 179.19  1.89  1.48    57.88        -18.28        -48.28
R2_T2close P2 2022-08-25..2025 (regime 2)     Mon      164   29.71    42.49        39.11 146.25  3.72   NaN    68.90         12.49        -17.51
R2_T2close P2 2022-08-25..2025 (regime 2)     Tue      168   29.64    30.72        27.04 165.57  2.40   NaN    57.74          0.72        -29.28
R2_T2close P2 2022-08-25..2025 (regime 2)     Wed      168   29.72     1.18        -2.94 185.84  0.08   NaN    54.17        -28.82        -58.82
R2_T2close P2 2022-08-25..2025 (regime 2)     Thu      169   29.39   -17.35       -22.31 211.22 -1.07   NaN    52.07        -47.35        -77.35
R2_T2close P2 2022-08-25..2025 (regime 2)     Fri      169   29.71     2.51        -1.59 175.18  0.19   NaN    56.80        -27.49        -57.49
R2_T2close        P3 2026-only (regime 2)     All      214   29.34    -1.58        -6.28 163.35 -0.14 -0.11    48.60        -31.58        -61.58
R2_T2close        P3 2026-only (regime 2)     Mon       42   29.31    78.33        73.20 168.88  3.01   NaN    66.67         48.33         18.33
R2_T2close        P3 2026-only (regime 2)     Tue       43   29.58    31.61        27.33 134.70  1.54   NaN    55.81          1.61        -28.39
R2_T2close        P3 2026-only (regime 2)     Wed       43   29.21   -40.15       -44.13 129.16 -2.04   NaN    39.53        -70.15       -100.15
R2_T2close        P3 2026-only (regime 2)     Thu       43   29.12   -61.54       -67.07 201.79 -2.00   NaN    34.88        -91.54       -121.54
R2_T2close        P3 2026-only (regime 2)     Fri       43   29.49   -14.33       -18.87 138.06 -0.68   NaN    46.51        -44.33        -74.33
R2_T2close           Regime 2 all (P2+P3)     All     1052   29.57     9.01         4.83 176.09  1.66  1.30    55.99        -20.99        -50.99
R2_T2close           Regime 2 all (P2+P3)     Mon      206   29.63    49.80        46.06 151.40  4.72   NaN    68.45         19.80        -10.20
R2_T2close           Regime 2 all (P2+P3)     Tue      211   29.63    30.90        27.10 159.47  2.81   NaN    57.35          0.90        -29.10
R2_T2close           Regime 2 all (P2+P3)     Wed      211   29.62    -7.24       -11.33 176.30 -0.60   NaN    51.18        -37.24        -67.24
R2_T2close           Regime 2 all (P2+P3)     Thu      212   29.33   -26.31       -31.39 209.63 -1.83   NaN    48.58        -56.31        -86.31
R2_T2close           Regime 2 all (P2+P3)     Fri      212   29.67    -0.90        -5.10 168.15 -0.08   NaN    54.72        -30.90        -60.90
 R1_T3open P1 2018-11..2022-08 (regime 1)     All      671   14.27    23.85        16.13 275.97  2.24  1.55    62.44         -6.15        -36.15
 R1_T3open P1 2018-11..2022-08 (regime 1)     Mon      123   14.22    58.34        51.31 250.18  2.59   NaN    66.67         28.34         -1.66
 R1_T3open P1 2018-11..2022-08 (regime 1)     Tue      137   13.91    40.77        32.76 295.41  1.62   NaN    63.50         10.77        -19.23
 R1_T3open P1 2018-11..2022-08 (regime 1)     Wed      140   14.47    32.25        24.43 287.73  1.33   NaN    66.43          2.25        -27.75
 R1_T3open P1 2018-11..2022-08 (regime 1)     Thu      138   14.55   -15.85       -24.20 281.99 -0.66   NaN    54.35        -45.85        -75.85
 R1_T3open P1 2018-11..2022-08 (regime 1)     Fri      133   14.17     6.89        -0.44 256.27  0.31   NaN    61.65        -23.11        -53.11
R1_T3close P1 2018-11..2022-08 (regime 1)     All      938   29.61    19.24        12.51 230.19  2.56  1.67    58.42        -10.76        -40.76
R1_T3close P1 2018-11..2022-08 (regime 1)     Mon      183   29.64    54.87        48.98 203.19  3.65   NaN    61.75         24.87         -5.13
R1_T3close P1 2018-11..2022-08 (regime 1)     Tue      189   29.72    36.81        30.36 228.46  2.22   NaN    62.43          6.81        -23.19
R1_T3close P1 2018-11..2022-08 (regime 1)     Wed      189   29.17    -2.18       -10.17 266.38 -0.11   NaN    59.79        -32.18        -62.18
R1_T3close P1 2018-11..2022-08 (regime 1)     Thu      189   29.72    -1.03        -7.78 222.00 -0.06   NaN    55.56        -31.03        -61.03
R1_T3close P1 2018-11..2022-08 (regime 1)     Fri      188   29.77     8.82         2.25 222.31  0.54   NaN    52.66        -21.18        -51.18

Cap-weighted:
      rule                         period weekday  n_dates  mean_bp     t  t_nw  net_bp_brk10
R2_T2close P2 2022-08-25..2025 (regime 2)     All      838    14.80  2.34  1.82        -15.20
R2_T2close P2 2022-08-25..2025 (regime 2)     Mon      164    47.13  4.13   NaN         17.13
R2_T2close P2 2022-08-25..2025 (regime 2)     Tue      168    32.47  2.43   NaN          2.47
R2_T2close P2 2022-08-25..2025 (regime 2)     Wed      168     5.46  0.37   NaN        -24.54
R2_T2close P2 2022-08-25..2025 (regime 2)     Thu      169   -15.04 -0.89   NaN        -45.04
R2_T2close P2 2022-08-25..2025 (regime 2)     Fri      169     5.00  0.37   NaN        -25.00
R2_T2close        P3 2026-only (regime 2)     All      214    -1.07 -0.10 -0.08        -31.07
R2_T2close        P3 2026-only (regime 2)     Mon       42    81.93  3.04   NaN         51.93
R2_T2close        P3 2026-only (regime 2)     Tue       43    27.03  1.23   NaN         -2.97
R2_T2close        P3 2026-only (regime 2)     Wed       43   -33.96 -1.74   NaN        -63.96
R2_T2close        P3 2026-only (regime 2)     Thu       43   -59.57 -2.05   NaN        -89.57
R2_T2close        P3 2026-only (regime 2)     Fri       43   -18.83 -0.86   NaN        -48.83
R2_T2close           Regime 2 all (P2+P3)     All     1052    11.57  2.09  1.64        -18.43
R2_T2close           Regime 2 all (P2+P3)     Mon      206    54.22  5.10   NaN         24.22
R2_T2close           Regime 2 all (P2+P3)     Tue      211    31.36  2.72   NaN          1.36
R2_T2close           Regime 2 all (P2+P3)     Wed      211    -2.57 -0.21   NaN        -32.57
R2_T2close           Regime 2 all (P2+P3)     Thu      212   -24.08 -1.64   NaN        -54.08
R2_T2close           Regime 2 all (P2+P3)     Fri      212     0.17  0.01   NaN        -29.83
 R1_T3open P1 2018-11..2022-08 (regime 1)     All      671    24.04  2.31  1.62         -5.96
 R1_T3open P1 2018-11..2022-08 (regime 1)     Mon      123    58.87  2.67   NaN         28.87
 R1_T3open P1 2018-11..2022-08 (regime 1)     Tue      137    37.66  1.58   NaN          7.66
 R1_T3open P1 2018-11..2022-08 (regime 1)     Wed      140    34.81  1.45   NaN          4.81
 R1_T3open P1 2018-11..2022-08 (regime 1)     Thu      138   -14.02 -0.58   NaN        -44.02
 R1_T3open P1 2018-11..2022-08 (regime 1)     Fri      133     5.98  0.28   NaN        -24.02
R1_T3close P1 2018-11..2022-08 (regime 1)     All      938    20.24  2.78  1.83         -9.76
R1_T3close P1 2018-11..2022-08 (regime 1)     Mon      183    52.13  3.55   NaN         22.13
R1_T3close P1 2018-11..2022-08 (regime 1)     Tue      189    37.36  2.38   NaN          7.36
R1_T3close P1 2018-11..2022-08 (regime 1)     Wed      189     1.74  0.09   NaN        -28.26
R1_T3close P1 2018-11..2022-08 (regime 1)     Thu      189     2.17  0.13   NaN        -27.83
R1_T3close P1 2018-11..2022-08 (regime 1)     Fri      188     8.75  0.56   NaN        -21.25

Clean subset (all nights in the hold are one-day nights). Regime 2 Thu/Fri entries and regime 1 Wed/Thu/Fri entries always span a weekend, so those cells are empty by construction:
      rule                         period weekday  n_dates  mean_bp     t  t_nw
R2_T2close P2 2022-08-25..2025 (regime 2)     All      486    24.72  3.24  3.05
R2_T2close P2 2022-08-25..2025 (regime 2)     Mon      162    42.87  3.71   NaN
R2_T2close P2 2022-08-25..2025 (regime 2)     Tue      162    33.44  2.58   NaN
R2_T2close P2 2022-08-25..2025 (regime 2)     Wed      162    -2.15 -0.15   NaN
R2_T2close P2 2022-08-25..2025 (regime 2)     Thu        0      NaN   NaN   NaN
R2_T2close P2 2022-08-25..2025 (regime 2)     Fri        0      NaN   NaN   NaN
R2_T2close        P3 2026-only (regime 2)     All      126    22.36  1.64  1.51
R2_T2close        P3 2026-only (regime 2)     Mon       42    78.33  3.01   NaN
R2_T2close        P3 2026-only (regime 2)     Tue       42    31.61  1.50   NaN
R2_T2close        P3 2026-only (regime 2)     Wed       42   -42.87 -2.15   NaN
R2_T2close        P3 2026-only (regime 2)     Thu        0      NaN   NaN   NaN
R2_T2close        P3 2026-only (regime 2)     Fri        0      NaN   NaN   NaN
R2_T2close           Regime 2 all (P2+P3)     All      612    24.23  3.63  3.40
R2_T2close           Regime 2 all (P2+P3)     Mon      204    50.17  4.71   NaN
R2_T2close           Regime 2 all (P2+P3)     Tue      204    33.07  2.96   NaN
R2_T2close           Regime 2 all (P2+P3)     Wed      204   -10.54 -0.85   NaN
R2_T2close           Regime 2 all (P2+P3)     Thu        0      NaN   NaN   NaN
R2_T2close           Regime 2 all (P2+P3)     Fri        0      NaN   NaN   NaN
 R1_T3open P1 2018-11..2022-08 (regime 1)     All      249    39.00  2.34  2.24
 R1_T3open P1 2018-11..2022-08 (regime 1)     Mon      119    49.49  2.22   NaN
 R1_T3open P1 2018-11..2022-08 (regime 1)     Tue      130    29.40  1.19   NaN
 R1_T3open P1 2018-11..2022-08 (regime 1)     Wed        0      NaN   NaN   NaN
 R1_T3open P1 2018-11..2022-08 (regime 1)     Thu        0      NaN   NaN   NaN
 R1_T3open P1 2018-11..2022-08 (regime 1)     Fri        0      NaN   NaN   NaN
R1_T3close P1 2018-11..2022-08 (regime 1)     All      354    40.57  3.90  3.47
R1_T3close P1 2018-11..2022-08 (regime 1)     Mon      175    49.78  3.47   NaN
R1_T3close P1 2018-11..2022-08 (regime 1)     Tue      179    31.57  2.09   NaN
R1_T3close P1 2018-11..2022-08 (regime 1)     Wed        0      NaN   NaN   NaN
R1_T3close P1 2018-11..2022-08 (regime 1)     Thu        0      NaN   NaN   NaN
R1_T3close P1 2018-11..2022-08 (regime 1)     Fri        0      NaN   NaN   NaN

## Leg decomposition (EW, log, decomposition subset: all opens in the window not suspicious; hold on the SAME subset)

R2_T2close:
                        period         sample weekday  n_dates  mean_k  ON1_bp  ID1_bp  ON2_bp  ID2_bp  overnight_only_bp  intraday_drag_bp  hold_log_bp  t_overnight_only  t_intraday  t_hold
P2 2022-08-25..2025 (regime 2)            all     All      786   16.75   16.71   -9.06   18.48   -9.29              35.19            -18.35        16.84              6.73       -2.58    1.93
P2 2022-08-25..2025 (regime 2)            all     Mon      154   16.40   21.72   -8.10   21.57    8.29              43.29              0.20        43.48              5.63        0.02    3.31
P2 2022-08-25..2025 (regime 2)            all     Tue      153   17.05   17.07   12.63   23.51  -11.26              40.57              1.37        41.94              6.15        0.10    2.95
P2 2022-08-25..2025 (regime 2)            all     Wed      160   17.03   19.62  -13.27   14.80  -18.70              34.43            -31.97         2.46              3.30       -2.73    0.16
P2 2022-08-25..2025 (regime 2)            all     Thu      158   16.67   12.82  -17.06   12.64  -22.48              25.47            -39.54       -14.07              2.65       -2.68   -0.78
P2 2022-08-25..2025 (regime 2)            all     Fri      161   16.60   12.50  -18.57   20.13   -1.94              32.63            -20.50        12.13              3.59       -1.76    0.78
P2 2022-08-25..2025 (regime 2)          clean     All      453   16.81   19.94   -2.78   19.62   -7.53              39.56            -10.31        29.24              7.41       -1.29    3.29
P2 2022-08-25..2025 (regime 2)          clean     Mon      152   16.41   22.05   -7.36   21.21    8.40              43.27              1.04        44.31              5.56        0.08    3.34
P2 2022-08-25..2025 (regime 2)          clean     Tue      147   17.05   16.94   13.52   24.96   -9.81              41.90              3.71        45.61              6.20        0.27    3.17
P2 2022-08-25..2025 (regime 2)          clean     Wed      154   16.97   20.72  -13.83   12.94  -21.08              33.66            -34.90        -1.24              3.11       -2.90   -0.08
P2 2022-08-25..2025 (regime 2)         ex2021     All      786   16.75   16.71   -9.06   18.48   -9.29              35.19            -18.35        16.84              6.73       -2.58    1.93
P2 2022-08-25..2025 (regime 2)         ex2021     Mon      154   16.40   21.72   -8.10   21.57    8.29              43.29              0.20        43.48              5.63        0.02    3.31
P2 2022-08-25..2025 (regime 2)         ex2021     Tue      153   17.05   17.07   12.63   23.51  -11.26              40.57              1.37        41.94              6.15        0.10    2.95
P2 2022-08-25..2025 (regime 2)         ex2021     Wed      160   17.03   19.62  -13.27   14.80  -18.70              34.43            -31.97         2.46              3.30       -2.73    0.16
P2 2022-08-25..2025 (regime 2)         ex2021     Thu      158   16.67   12.82  -17.06   12.64  -22.48              25.47            -39.54       -14.07              2.65       -2.68   -0.78
P2 2022-08-25..2025 (regime 2)         ex2021     Fri      161   16.60   12.50  -18.57   20.13   -1.94              32.63            -20.50        12.13              3.59       -1.76    0.78
P2 2022-08-25..2025 (regime 2) no_open_filter     All      838   29.63   11.80   -9.17   12.97   -7.94              24.77            -17.11         7.66              5.37       -2.64    0.96
P2 2022-08-25..2025 (regime 2) no_open_filter     Mon      164   29.71   16.21   -2.51   15.35   10.06              31.56              7.55        39.11              5.18        0.69    3.42
P2 2022-08-25..2025 (regime 2) no_open_filter     Tue      168   29.64   11.28   12.20   16.10  -12.55              27.38             -0.34        27.04              4.72       -0.03    2.13
P2 2022-08-25..2025 (regime 2) no_open_filter     Wed      168   29.72   15.68  -12.59   10.03  -16.05              25.70            -28.64        -2.94              2.76       -2.77   -0.21
P2 2022-08-25..2025 (regime 2) no_open_filter     Thu      169   29.39    7.94  -18.19    8.92  -20.98              16.85            -39.16       -22.31              2.06       -2.92   -1.36
P2 2022-08-25..2025 (regime 2) no_open_filter     Fri      169   29.71    8.06  -24.46   14.52    0.29              22.58            -24.17        -1.59              2.99       -2.23   -0.12
       P3 2026-only (regime 2)            all     All      207   17.52   10.63  -13.18   15.44  -15.53              26.07            -28.71        -2.64              3.56       -2.50   -0.17
       P3 2026-only (regime 2)            all     Mon       39   17.38   30.16   -5.19   29.08   23.96              59.24             18.77        78.01              4.08        0.83    2.70
       P3 2026-only (regime 2)            all     Tue       43   16.98   22.95   19.04   12.80  -26.95              35.75             -7.91        27.85              3.30       -0.37    1.21
       P3 2026-only (regime 2)            all     Wed       42   17.69    8.25  -23.18    5.09  -34.55              13.34            -57.73       -44.39              1.16       -3.18   -1.96
       P3 2026-only (regime 2)            all     Thu       42   17.33    2.63  -26.55   -3.08  -41.03              -0.45            -67.58       -68.03             -0.02       -2.97   -2.05
       P3 2026-only (regime 2)            all     Fri       41   18.24  -10.23  -30.66   34.80    4.51              24.57            -26.15        -1.58              1.92       -1.50   -0.07
       P3 2026-only (regime 2)          clean     All      122   17.31   19.98   -2.94   15.29  -14.11              35.27            -17.05        18.22              4.46       -1.22    1.13
       P3 2026-only (regime 2)          clean     Mon       39   17.38   30.16   -5.19   29.08   23.96              59.24             18.77        78.01              4.08        0.83    2.70
       P3 2026-only (regime 2)          clean     Tue       42   16.93   23.76   19.77   11.60  -27.17              35.36             -7.41        27.95              3.19       -0.34    1.19
       P3 2026-only (regime 2)          clean     Wed       41   17.63    6.42  -24.06    5.96  -36.94              12.38            -61.01       -48.62              1.05       -3.34   -2.14
       P3 2026-only (regime 2)         ex2021     All      207   17.52   10.63  -13.18   15.44  -15.53              26.07            -28.71        -2.64              3.56       -2.50   -0.17
       P3 2026-only (regime 2)         ex2021     Mon       39   17.38   30.16   -5.19   29.08   23.96              59.24             18.77        78.01              4.08        0.83    2.70
       P3 2026-only (regime 2)         ex2021     Tue       43   16.98   22.95   19.04   12.80  -26.95              35.75             -7.91        27.85              3.30       -0.37    1.21
       P3 2026-only (regime 2)         ex2021     Wed       42   17.69    8.25  -23.18    5.09  -34.55              13.34            -57.73       -44.39              1.16       -3.18   -1.96
       P3 2026-only (regime 2)         ex2021     Thu       42   17.33    2.63  -26.55   -3.08  -41.03              -0.45            -67.58       -68.03             -0.02       -2.97   -2.05
       P3 2026-only (regime 2)         ex2021     Fri       41   18.24  -10.23  -30.66   34.80    4.51              24.57            -26.15        -1.58              1.92       -1.50   -0.07
       P3 2026-only (regime 2) no_open_filter     All      214   29.34    7.66  -13.27   10.91  -11.57              18.57            -24.85        -6.28              2.88       -2.32   -0.45
       P3 2026-only (regime 2) no_open_filter     Mon       42   29.31   24.67   -1.49   24.54   25.48              49.21             23.98        73.20              3.86        1.23    2.85
       P3 2026-only (regime 2) no_open_filter     Tue       43   29.58   20.32   22.99    7.55  -23.53              27.88             -0.54        27.33              2.81       -0.03    1.34
       P3 2026-only (regime 2) no_open_filter     Wed       43   29.21    3.86  -25.16    1.94  -24.78               5.80            -49.93       -44.13              0.62       -3.00   -2.22
       P3 2026-only (regime 2) no_open_filter     Thu       43   29.12    1.28  -24.27   -8.32  -35.76              -7.03            -60.04       -67.07             -0.41       -2.78   -2.15
       P3 2026-only (regime 2) no_open_filter     Fri       43   29.49  -11.46  -38.14   29.15    1.58              17.69            -36.56       -18.87              1.58       -2.37   -0.89
          Regime 2 all (P2+P3)            all     All      993   16.91   15.44   -9.92   17.85  -10.59              33.29            -20.51        12.78              7.54       -3.34    1.68
          Regime 2 all (P2+P3)            all     Mon      193   16.60   23.43   -7.51   23.09   11.46              46.51              3.95        50.46              6.84        0.36    4.21
          Regime 2 all (P2+P3)            all     Tue      196   17.04   18.36   14.03   21.16  -14.70              39.52             -0.66        38.85              6.98       -0.06    3.19
          Regime 2 all (P2+P3)            all     Wed      202   17.17   17.26  -15.33   12.78  -21.99              30.04            -37.33        -7.28              3.49       -3.72   -0.54
          Regime 2 all (P2+P3)            all     Thu      200   16.81   10.68  -19.05    9.34  -26.37              20.02            -45.43       -25.40              2.34       -3.61   -1.60
          Regime 2 all (P2+P3)            all     Fri      202   16.94    7.89  -21.02   23.11   -0.63              31.00            -21.65         9.35              4.03       -2.18    0.71
          Regime 2 all (P2+P3)          clean     All      575   16.91   19.95   -2.82   18.70   -8.92              38.65            -11.74        26.91              8.54       -1.68    3.45
          Regime 2 all (P2+P3)          clean     Mon      191   16.61   23.71   -6.92   22.82   11.58              46.53              4.66        51.19              6.77        0.43    4.23
          Regime 2 all (P2+P3)          clean     Tue      189   17.03   18.45   14.91   21.99  -13.67              40.44              1.24        41.68              6.98        0.11    3.38
          Regime 2 all (P2+P3)          clean     Wed      195   17.11   17.71  -15.98   11.48  -24.41              29.19            -40.39       -11.20              3.27       -3.93   -0.82
          Regime 2 all (P2+P3)         ex2021     All      993   16.91   15.44   -9.92   17.85  -10.59              33.29            -20.51        12.78              7.54       -3.34    1.68
          Regime 2 all (P2+P3)         ex2021     Mon      193   16.60   23.43   -7.51   23.09   11.46              46.51              3.95        50.46              6.84        0.36    4.21
          Regime 2 all (P2+P3)         ex2021     Tue      196   17.04   18.36   14.03   21.16  -14.70              39.52             -0.66        38.85              6.98       -0.06    3.19
          Regime 2 all (P2+P3)         ex2021     Wed      202   17.17   17.26  -15.33   12.78  -21.99              30.04            -37.33        -7.28              3.49       -3.72   -0.54
          Regime 2 all (P2+P3)         ex2021     Thu      200   16.81   10.68  -19.05    9.34  -26.37              20.02            -45.43       -25.40              2.34       -3.61   -1.60
          Regime 2 all (P2+P3)         ex2021     Fri      202   16.94    7.89  -21.02   23.11   -0.63              31.00            -21.65         9.35              4.03       -2.18    0.71
          Regime 2 all (P2+P3) no_open_filter     All     1052   29.57   10.96  -10.00   12.55   -8.68              23.51            -18.68         4.83              6.03       -3.32    0.69
          Regime 2 all (P2+P3) no_open_filter     Mon      206   29.63   17.94   -2.30   17.22   13.20              35.16             10.90        46.06              6.38        1.14    4.39
          Regime 2 all (P2+P3) no_open_filter     Tue      211   29.63   13.12   14.40   14.36  -14.78              27.48             -0.38        27.10              5.46       -0.04    2.49
          Regime 2 all (P2+P3) no_open_filter     Wed      211   29.62   13.27  -15.15    8.38  -17.83              21.65            -32.98       -11.33              2.82       -3.71   -0.94
          Regime 2 all (P2+P3) no_open_filter     Thu      212   29.33    6.59  -19.42    5.42  -23.97              12.01            -43.40       -31.39              1.62       -3.76   -2.16
          Regime 2 all (P2+P3) no_open_filter     Fri      212   29.67    4.10  -27.24   17.48    0.56              21.59            -26.68        -5.10              3.36       -2.91   -0.44

R1_T3open:
                        period         sample weekday  n_dates  mean_k  ON1_bp  ID1_bp  ON2_bp  ID2_bp  ON3_bp  overnight_only_bp  intraday_drag_bp  hold_log_bp  t_overnight_only  t_intraday  t_hold
P1 2018-11..2022-08 (regime 1)            all     All      671   14.27   -1.81    9.35   -0.38    8.15    0.82              -1.37             17.50        16.13             -0.11        2.08    1.03
P1 2018-11..2022-08 (regime 1)            all     Mon      123   14.22   -1.95   26.75    3.49   20.75    2.27               3.81             47.50        51.31              0.25        2.63    2.23
P1 2018-11..2022-08 (regime 1)            all     Tue      137   13.91    6.22   28.10    4.72    1.09   -7.37               3.56             29.19        32.76              0.22        2.00    1.26
P1 2018-11..2022-08 (regime 1)            all     Wed      140   14.47    3.15   -1.10   -8.94   23.83    7.49               1.70             22.73        24.43              0.09        1.45    1.00
P1 2018-11..2022-08 (regime 1)            all     Thu      138   14.55  -15.61   17.43   -2.42  -26.12    2.52             -15.50             -8.70       -24.20             -0.89       -0.56   -0.99
P1 2018-11..2022-08 (regime 1)            all     Fri      133   14.17   -0.86  -23.46    1.90   22.85   -0.86               0.18             -0.61        -0.44              0.01       -0.04   -0.02
P1 2018-11..2022-08 (regime 1)          clean     All      249   14.03    1.48   24.81    4.21    5.68   -4.42               1.27             30.50        31.77              0.10        2.65    1.75
P1 2018-11..2022-08 (regime 1)          clean     Mon      119   14.24   -3.62   27.49    3.34   13.90    1.56               1.27             41.39        42.66              0.08        2.28    1.87
P1 2018-11..2022-08 (regime 1)          clean     Tue      130   13.84    6.16   22.36    5.01   -1.83   -9.89               1.28             20.53        21.80              0.08        1.44    0.85
P1 2018-11..2022-08 (regime 1)         ex2021     All      453   14.02  -10.38    8.00   -9.15    7.71   -7.14             -26.67             15.71       -10.97             -1.72        1.58   -0.56
P1 2018-11..2022-08 (regime 1)         ex2021     Mon       84   14.26  -14.43   44.09   -1.46   19.66   -3.67             -19.56             63.75        44.20             -1.10        3.14    1.90
P1 2018-11..2022-08 (regime 1)         ex2021     Tue       92   13.40    0.10   23.47   -1.36   -2.75   -8.76             -10.02             20.71        10.69             -0.55        1.13    0.34
P1 2018-11..2022-08 (regime 1)         ex2021     Wed       94   13.99   -2.34   -7.82  -12.29   18.20   -5.47             -20.09             10.38        -9.71             -0.81        0.53   -0.29
P1 2018-11..2022-08 (regime 1)         ex2021     Thu       94   14.14  -21.47   10.27  -19.07  -33.75   -8.66             -49.21            -23.48       -72.69             -2.07       -1.23   -2.28
P1 2018-11..2022-08 (regime 1)         ex2021     Fri       89   14.33  -14.19  -27.76  -10.66   39.96   -8.90             -33.74             12.19       -21.55             -1.51        0.71   -0.76
P1 2018-11..2022-08 (regime 1) no_open_filter     All      939   29.77   -2.27    4.46   -1.37    4.20   -1.07              -4.70              8.65         3.95             -0.58        1.38    0.37
P1 2018-11..2022-08 (regime 1) no_open_filter     Mon      184   29.73   -1.21   15.24    1.79   16.75    1.26               1.83             31.98        33.82              0.20        2.69    2.31
P1 2018-11..2022-08 (regime 1) no_open_filter     Tue      189   29.78    1.34   17.73    0.67    3.62   -5.71              -3.70             21.35        17.65             -0.36        2.13    1.04
P1 2018-11..2022-08 (regime 1) no_open_filter     Wed      189   29.62    0.46    1.00   -7.78   13.91   -0.22              -7.54             14.92         7.38             -0.59        1.36    0.45
P1 2018-11..2022-08 (regime 1) no_open_filter     Thu      189   29.84  -10.78   15.46   -1.65  -26.95    0.49             -11.94            -11.50       -23.44             -0.99       -0.94   -1.29
P1 2018-11..2022-08 (regime 1) no_open_filter     Fri      188   29.86   -1.13  -27.03    0.24   14.04   -1.10              -1.98            -12.99       -14.97             -0.18       -1.23   -1.02

R1_T3close:
                        period         sample weekday  n_dates  mean_k  ON1_bp  ID1_bp  ON2_bp  ID2_bp  ON3_bp  ID3_bp  overnight_only_bp  intraday_drag_bp  hold_log_bp  t_overnight_only  t_intraday  t_hold
P1 2018-11..2022-08 (regime 1)            all     All      664   14.21   -1.19   10.27    0.04   10.97    3.55   12.18               2.41             33.41        35.82              0.20        3.07    2.24
P1 2018-11..2022-08 (regime 1)            all     Mon      122   14.13   -1.00   30.09    5.40   23.62    7.16   16.66              11.56             70.36        81.92              0.84        3.66    3.79
P1 2018-11..2022-08 (regime 1)            all     Tue      134   14.01    6.64   27.48    4.94    7.54   -7.39   24.82               4.19             59.84        64.03              0.25        3.78    2.68
P1 2018-11..2022-08 (regime 1)            all     Wed      137   14.25    4.85    1.24   -9.22   27.47   16.27  -15.71              11.89             13.01        24.90              0.63        0.67    0.92
P1 2018-11..2022-08 (regime 1)            all     Thu      138   14.51  -15.70   17.52   -2.41  -25.70    2.25   23.69             -15.86             15.51        -0.36             -0.89        0.88   -0.02
P1 2018-11..2022-08 (regime 1)            all     Fri      133   14.11   -0.41  -23.46    2.28   23.86   -0.48   12.10               1.40             12.50        13.90              0.09        0.72    0.57
P1 2018-11..2022-08 (regime 1)          clean     All      246   14.02    1.99   26.35    4.42   10.13   -2.19   19.15               4.22             55.63        59.84              0.34        4.13    3.60
P1 2018-11..2022-08 (regime 1)          clean     Mon      118   14.14   -2.66   30.95    5.31   16.80    6.61   12.76               9.26             60.51        69.77              0.66        3.22    3.36
P1 2018-11..2022-08 (regime 1)          clean     Tue      128   13.91    6.26   22.12    3.61    3.97  -10.31   25.03              -0.44             51.12        50.69             -0.03        3.49    2.28
P1 2018-11..2022-08 (regime 1)         ex2021     All      447   13.95   -9.62    8.64   -9.11   11.32   -4.58   17.47             -23.31             37.43        14.12             -1.52        2.96    0.70
P1 2018-11..2022-08 (regime 1)         ex2021     Mon       84   14.17  -13.33   44.89   -0.92   20.37   -3.90   18.28             -18.15             83.54        65.39             -1.01        3.82    2.59
P1 2018-11..2022-08 (regime 1)         ex2021     Tue       89   13.54    0.52   22.53   -1.07    6.67   -8.59   25.72              -9.14             54.91        45.77             -0.49        2.84    1.52
P1 2018-11..2022-08 (regime 1)         ex2021     Wed       91   13.68    0.11   -4.46  -12.88   23.75    7.10  -16.31              -5.67              2.99        -2.68             -0.24        0.12   -0.08
P1 2018-11..2022-08 (regime 1)         ex2021     Thu       94   14.13  -21.67   10.22  -19.46  -32.92   -9.15   42.82             -50.27             20.12       -30.15             -2.08        1.03   -1.12
P1 2018-11..2022-08 (regime 1)         ex2021     Fri       89   14.24  -13.51  -27.76  -10.08   41.47   -8.33   16.21             -31.92             29.91        -2.01             -1.45        1.51   -0.07
P1 2018-11..2022-08 (regime 1) no_open_filter     All      938   29.61   -2.10    5.01   -1.21    4.80   -0.17    6.18              -3.48             15.99        12.51             -0.44        1.85    1.08
P1 2018-11..2022-08 (regime 1) no_open_filter     Mon      183   29.64   -0.70   17.15    2.69   18.72    4.36    6.75               6.36             42.62        48.98              0.78        3.20    3.29
P1 2018-11..2022-08 (regime 1) no_open_filter     Tue      189   29.72    1.51   17.60    0.34    4.19   -5.82   12.54              -3.97             34.33        30.36             -0.37        2.80    1.83
P1 2018-11..2022-08 (regime 1) no_open_filter     Wed      189   29.17    0.60    1.84   -7.91   14.05    1.04  -19.78              -6.27             -3.90       -10.17             -0.49       -0.27   -0.52
P1 2018-11..2022-08 (regime 1) no_open_filter     Thu      189   29.72  -10.88   15.45   -1.55  -26.88    0.62   15.48             -11.82              4.04        -7.78             -0.97        0.30   -0.48
P1 2018-11..2022-08 (regime 1) no_open_filter     Fri      188   29.77   -0.98  -26.76    0.49   14.39   -0.90   16.01              -1.39              3.64         2.25             -0.13        0.30    0.14

## Cross-weekday tests (HAC, Bartlett, lags = hold length). 5 weekdays x several periods = many comparisons; descriptive only, no 'best' weekday is selected.
      rule                         period weighting  wald_equal_weekdays  wald_p  montue_minus_wedthu_bp  montue_minus_wedthu_t_hac
R2_T2close P1 2018-11..2022-08 (regime 1)        EW                10.14    0.04                   36.75                       2.67
R2_T2close P1 2018-11..2022-08 (regime 1)       cap                 8.60    0.07                   30.79                       2.30
R2_T2close P2 2022-08-25..2025 (regime 2)        EW                10.35    0.03                   44.69                       3.00
R2_T2close P2 2022-08-25..2025 (regime 2)       cap                10.61    0.03                   44.59                       2.90
R2_T2close        P3 2026-only (regime 2)        EW                15.60    0.00                  105.81                       3.77
R2_T2close        P3 2026-only (regime 2)       cap                14.62    0.01                  101.24                       3.64
R2_T2close           Regime 2 all (P2+P3)        EW                20.75    0.00                   57.13                       4.32
R2_T2close           Regime 2 all (P2+P3)       cap                21.01    0.00                   56.12                       4.14
R2_T2close          Full 2018-11..2026-11        EW                28.98    0.00                   47.51                       4.98
R2_T2close          Full 2018-11..2026-11       cap                27.46    0.00                   44.17                       4.62
 R1_T3open P1 2018-11..2022-08 (regime 1)        EW                 7.30    0.12                   41.36                       1.64
 R1_T3open P1 2018-11..2022-08 (regime 1)       cap                 7.52    0.11                   37.87                       1.52
 R1_T3open P2 2022-08-25..2025 (regime 2)        EW                 4.61    0.33                   48.94                       2.07
 R1_T3open P2 2022-08-25..2025 (regime 2)       cap                 3.60    0.46                   41.85                       1.70
 R1_T3open        P3 2026-only (regime 2)        EW                 8.93    0.06                  108.64                       2.77
 R1_T3open        P3 2026-only (regime 2)       cap                 9.66    0.05                  117.84                       3.04
 R1_T3open           Regime 2 all (P2+P3)        EW                 9.67    0.05                   62.62                       3.08
 R1_T3open           Regime 2 all (P2+P3)       cap                 8.82    0.07                   59.35                       2.83
 R1_T3open          Full 2018-11..2026-11        EW                14.20    0.01                   52.91                       3.30
 R1_T3open          Full 2018-11..2026-11       cap                14.20    0.01                   49.53                       3.07
R1_T3close P1 2018-11..2022-08 (regime 1)        EW                 9.56    0.05                   47.45                       2.82
R1_T3close P1 2018-11..2022-08 (regime 1)       cap                 8.49    0.08                   42.80                       2.61
R1_T3close P2 2022-08-25..2025 (regime 2)        EW                 7.55    0.11                   42.02                       2.45
R1_T3close P2 2022-08-25..2025 (regime 2)       cap                 6.81    0.15                   42.59                       2.39
R1_T3close        P3 2026-only (regime 2)        EW                12.25    0.02                   96.36                       3.06
R1_T3close        P3 2026-only (regime 2)       cap                12.59    0.01                   96.52                       3.10
R1_T3close           Regime 2 all (P2+P3)        EW                14.78    0.01                   53.08                       3.51
R1_T3close           Regime 2 all (P2+P3)       cap                13.66    0.01                   53.56                       3.43
R1_T3close          Full 2018-11..2026-11        EW                21.30    0.00                   50.42                       4.48
R1_T3close          Full 2018-11..2026-11       cap                19.76    0.00                   48.48                       4.28

## Cost grid: breakeven round-trip cost = gross mean (executable, EW)
      rule                         period weekday  n_dates  gross_bp  gross_t  breakeven_roundtrip_bp
R2_T2close P2 2022-08-25..2025 (regime 2)     All      838     11.72     1.48                   11.72
R2_T2close P2 2022-08-25..2025 (regime 2)     Mon      164     42.49     3.72                   42.49
R2_T2close P2 2022-08-25..2025 (regime 2)     Tue      168     30.72     2.40                   30.72
R2_T2close P2 2022-08-25..2025 (regime 2)     Wed      168      1.18     0.08                    1.18
R2_T2close P2 2022-08-25..2025 (regime 2)     Thu      169    -17.35    -1.07                  -17.35
R2_T2close P2 2022-08-25..2025 (regime 2)     Fri      169      2.51     0.19                    2.51
R2_T2close        P3 2026-only (regime 2)     All      214     -1.58    -0.11                   -1.58
R2_T2close        P3 2026-only (regime 2)     Mon       42     78.33     3.01                   78.33
R2_T2close        P3 2026-only (regime 2)     Tue       43     31.61     1.54                   31.61
R2_T2close        P3 2026-only (regime 2)     Wed       43    -40.15    -2.04                  -40.15
R2_T2close        P3 2026-only (regime 2)     Thu       43    -61.54    -2.00                  -61.54
R2_T2close        P3 2026-only (regime 2)     Fri       43    -14.33    -0.68                  -14.33
R2_T2close           Regime 2 all (P2+P3)     All     1052      9.01     1.30                    9.01
R2_T2close           Regime 2 all (P2+P3)     Mon      206     49.80     4.72                   49.80
R2_T2close           Regime 2 all (P2+P3)     Tue      211     30.90     2.81                   30.90
R2_T2close           Regime 2 all (P2+P3)     Wed      211     -7.24    -0.60                   -7.24
R2_T2close           Regime 2 all (P2+P3)     Thu      212    -26.31    -1.83                  -26.31
R2_T2close           Regime 2 all (P2+P3)     Fri      212     -0.90    -0.08                   -0.90
 R1_T3open P1 2018-11..2022-08 (regime 1)     All      671     23.85     1.55                   23.85
 R1_T3open P1 2018-11..2022-08 (regime 1)     Mon      123     58.34     2.59                   58.34
 R1_T3open P1 2018-11..2022-08 (regime 1)     Tue      137     40.77     1.62                   40.77
 R1_T3open P1 2018-11..2022-08 (regime 1)     Wed      140     32.25     1.33                   32.25
 R1_T3open P1 2018-11..2022-08 (regime 1)     Thu      138    -15.85    -0.66                  -15.85
 R1_T3open P1 2018-11..2022-08 (regime 1)     Fri      133      6.89     0.31                    6.89
R1_T3close P1 2018-11..2022-08 (regime 1)     All      938     19.24     1.67                   19.24
R1_T3close P1 2018-11..2022-08 (regime 1)     Mon      183     54.87     3.65                   54.87
R1_T3close P1 2018-11..2022-08 (regime 1)     Tue      189     36.81     2.22                   36.81
R1_T3close P1 2018-11..2022-08 (regime 1)     Wed      189     -2.18    -0.11                   -2.18
R1_T3close P1 2018-11..2022-08 (regime 1)     Thu      189     -1.03    -0.06                   -1.03
R1_T3close P1 2018-11..2022-08 (regime 1)     Fri      188      8.82     0.54                    8.82

Net per hold at each brokerage level (All days, EW):
      rule                         period  brokerage_bp_side  roundtrip_cost_bp  gross_bp  net_bp_per_hold  net_t  net_bp_per_overnight
R2_T2close P2 2022-08-25..2025 (regime 2)                 10              30.00     11.72           -18.28  -2.31                 -9.14
R2_T2close P2 2022-08-25..2025 (regime 2)                 15              40.00     11.72           -28.28  -3.57                -14.14
R2_T2close P2 2022-08-25..2025 (regime 2)                 25              60.00     11.72           -48.28  -6.09                -24.14
R2_T2close        P3 2026-only (regime 2)                 10              30.00     -1.58           -31.58  -2.25                -15.79
R2_T2close        P3 2026-only (regime 2)                 15              40.00     -1.58           -41.58  -2.96                -20.79
R2_T2close        P3 2026-only (regime 2)                 25              60.00     -1.58           -61.58  -4.38                -30.79
R2_T2close           Regime 2 all (P2+P3)                 10              30.00      9.01           -20.99  -3.02                -10.49
R2_T2close           Regime 2 all (P2+P3)                 15              40.00      9.01           -30.99  -4.46                -15.49
R2_T2close           Regime 2 all (P2+P3)                 25              60.00      9.01           -50.99  -7.35                -25.49
 R1_T3open P1 2018-11..2022-08 (regime 1)                 10              30.00     23.85            -6.15  -0.40                 -2.05
 R1_T3open P1 2018-11..2022-08 (regime 1)                 15              40.00     23.85           -16.15  -1.05                 -5.38
 R1_T3open P1 2018-11..2022-08 (regime 1)                 25              60.00     23.85           -36.15  -2.36                -12.05
R1_T3close P1 2018-11..2022-08 (regime 1)                 10              30.00     19.24           -10.76  -0.93                 -3.59
R1_T3close P1 2018-11..2022-08 (regime 1)                 15              40.00     19.24           -20.76  -1.80                 -6.92
R1_T3close P1 2018-11..2022-08 (regime 1)                 25              60.00     19.24           -40.76  -3.53                -13.59

## Secondary: Level B 1-night day-of-week, date-level EW baskets
                night  pooled_mean_bp  pooled_naive_t  levelb_csv_ew_mean_bp  levelb_csv_ew_t  cur30_ew_mean_bp  cur30_ew_t  pit_ew_dates  pit_ew_mean_bp  pit_ew_t
             Mon->Tue           18.35           14.64                  17.19             5.50             17.19        5.50           390           14.32      4.42
             Tue->Wed           14.65           11.85                  13.42             3.98             13.42        3.98           395           11.52      3.35
             Wed->Thu           15.87           12.36                  14.56             3.86             14.56        3.86           391           12.18      3.16
             Thu->Fri            4.57            3.70                   5.01             1.37              5.01        1.37           397            3.23      0.86
Mon+Tue minus Wed+Thu             NaN             NaN                    NaN              NaN               NaN         NaN          1573            5.25      1.47

PIT EW by period:
                        period                 night  pit_ew_dates  pit_ew_mean_bp  pit_ew_t
P1 2018-11..2022-08 (regime 1)              Mon->Tue           183            2.06      0.37
P1 2018-11..2022-08 (regime 1)              Tue->Wed           186            2.26      0.47
P1 2018-11..2022-08 (regime 1)              Wed->Thu           184            4.04      0.68
P1 2018-11..2022-08 (regime 1)              Thu->Fri           187           -7.32     -1.24
P1 2018-11..2022-08 (regime 1) Mon+Tue minus Wed+Thu           740            3.85      0.69
P2 2022-08-25..2025 (regime 2)              Mon->Tue           164           23.49      6.50
P2 2022-08-25..2025 (regime 2)              Tue->Wed           166           17.62      3.14
P2 2022-08-25..2025 (regime 2)              Wed->Thu           165           21.88      3.66
P2 2022-08-25..2025 (regime 2)              Thu->Fri           167           14.57      2.67
P2 2022-08-25..2025 (regime 2) Mon+Tue minus Wed+Thu           662            2.34      0.45
       P3 2026-only (regime 2)              Mon->Tue            43           31.54      3.40
       P3 2026-only (regime 2)              Tue->Wed            43           28.04      3.07
       P3 2026-only (regime 2)              Wed->Thu            42            9.73      1.35
       P3 2026-only (regime 2)              Thu->Fri            43            5.03      0.64
       P3 2026-only (regime 2) Mon+Tue minus Wed+Thu           171           22.44      2.68

## Verdict
VERDICT (current regime 2, T+2 ATC exit, EW, 1052 entry dates 2022-08-25..): gross 9.0 bp per 2-night hold (NW t 1.30; log 4.8 bp), breakeven round trip 9.0 bp vs cost 30/40/60 bp -> brokerage 10 bp/side: (b) positive gross, consumed by costs (net -21.0 bp); brokerage 15 bp/side: (b) positive gross, consumed by costs (net -31.0 bp); brokerage 25 bp/side: (b) positive gross, consumed by costs (net -51.0 bp). The gross mean is not distinguishable from zero (|t| 1.30 < 2). Give-back (same decomposition subset, n 993): overnight-only ON1+ON2 33.3 bp (t 7.54), intraday ID1+ID2 -20.5 bp (t -3.34), executable hold 12.8 bp (log); the intraday legs give back 62% of the overnight edge. (Regime 2 has no 2021 entries, so its ex-2021 cut equals the full cut.) Regime 1 (T+3, 938 dates): close-to-close T+3 gross 19.2 bp (NW t 1.67); ATO T+3 exit on the open-clean subset 23.9 bp (n 671). Decomposition ON1+ON2+ON3 -1.4 bp vs intraday 17.5 bp (n 671); ex-2021 ON -26.7 / ID 15.7 bp (n 453). Filter sensitivity: single-stock 'open == prior close' flags run 20-38% in EVERY year (mostly genuine ATO-at-reference prints, not the 2021 feed artifact), so the open filter removes ~45% of regime-2 stock-entries and is selective: on the filtered subset the hold is 12.8 bp log vs 4.8 bp on the close-only set. Without the open filter (same close-only set as the headline) ON1+ON2 23.5 bp (t 6.03), ID1+ID2 -18.7 bp (t -3.32), give-back 79%. Clean (no weekend/holiday in the hold) filtered subset: give-back 30%; the weekend-spanning Thu/Fri entries carry much of the intraday drag. So 'the intraday legs give back most of the overnight edge' is robust; the exact share is filter-sensitive. Regime 1 is not read as a give-back: there is no overnight edge to give back. ON1+ON2+ON3 is about zero filtered (-1.4 bp) and unfiltered (-3.5 bp, close-exit variant), negative ex-2021, consistent with the 1-night PIT basket for P1 (2-4 bp, t < 0.7); the T+3 hold's return came from intraday legs. Opens in 2019-2021 are the least reliable in the data, so treat the regime-1 split as unreliable. The regime-1 close-to-close hold does not use opens. Per period (regime 2, 30 bp lowest round trip): P2 2022-08-25..2025 gross 11.7 bp (NW t 1.48) -> (b) positive gross, consumed by costs; P3 2026 gross -1.6 bp (NW t -0.11) -> (c) not positive even gross; cap-weighted regime 2 gross 11.6 bp (NW t 1.64) -> (b) positive gross, consumed by costs. Weekday pattern (descriptive; 5 weekdays x 3 periods = 15 cells, Bonferroni |t| ~2.9; no weekday is selected): the pre-specified Mon+Tue minus Wed+Thu contrast carried over from Level B / futures is 57.1 bp per hold in regime 2 (HAC t 4.32); equal-weekday Wald p 0.000. Per-weekday net figures are in option_c_cost_grid.csv and are not a strategy.
