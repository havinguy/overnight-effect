# Intraday feasibility probe (vnstock sources only: VCI, then KBS)

Probe run 2026-11-22; raw responses cached in data/raw_intraday/ (separate from data/raw/). Query: Quote(symbol, source).history(start='2017-01-01', end=today, interval). Community-tier warnings printed by vnstock: '1m limited to 6 months', '5m/15m limited to 1 year'.

## Coverage per source / symbol / interval
source  symbol interval status  rows_raw
   VCI VN30F1M       1m     ok    191874
   VCI VN30F1M       5m     ok    105121
   VCI VN30F1M      15m     ok     35041
   VCI    VN30       1m     ok     28444
   VCI    VN30       5m     ok    105121
   VCI    VN30      15m     ok     35041
   KBS VN30F1M       1m     ok      6198
   KBS VN30F1M       5m     ok      3217
   KBS VN30F1M      15m     ok      1797
   KBS    VN30       1m     ok     28819
   KBS    VN30       5m     ok     11687
   KBS    VN30      15m     ok      4248

source  symbol interval status               first                last  days   rows  median_bars_per_day first_bar_hm_mode  share_first_bar_at_expected  n_bars_before_0900  first_open_eq_daily_open  last_close_eq_daily_close last_bar_hm_mode  days_matched_to_daily
   VCI VN30F1M       1m     ok 2023-09-11 09:00:00 2026-11-23 09:41:00   795 191874                241.0             09:00                     0.986164                   8                  0.997472                   1.000000            14:45                    791
   VCI VN30F1M       5m     ok 2025-11-24 09:00:00 2026-11-23 09:40:00   248  12112                 49.0             09:00                     1.000000                   0                  1.000000                   1.000000            14:45                    244
   VCI VN30F1M      15m     ok 2025-11-24 09:00:00 2026-11-23 09:30:00   248   4202                 17.0             09:00                     1.000000                   0                  1.000000                   1.000000            14:45                    244
   VCI    VN30       1m     ok 2026-05-27 09:42:00 2026-11-23 09:42:00   126  28444                228.0             09:15                     0.992063                   0                  0.983607                   1.000000            14:45                    122
   VCI    VN30       5m     ok 2025-11-24 09:15:00 2026-11-23 09:40:00   248  11805                 48.0             09:15                     1.000000                   0                  0.995902                   1.000000            14:45                    244
   VCI    VN30      15m     ok 2025-11-24 09:15:00 2026-11-23 09:30:00   248   4391                 18.0             09:15                     1.000000                   0                  0.995902                   1.000000            14:45                    244
   KBS VN30F1M       1m     ok 2026-05-25 09:21:00 2026-11-20 14:45:00   129   6198                 30.0             09:00                     0.465116                   0                  0.016260                   0.008130            14:45                    123
   KBS VN30F1M       5m     ok 2026-04-17 09:25:00 2026-11-20 14:45:00   154   3217                 17.0             09:00                     0.532468                   0                  0.013793                   0.013793            14:45                    145
   KBS VN30F1M      15m     ok 2026-04-17 09:15:00 2026-11-20 14:45:00   155   1797                 12.0             09:00                     0.664516                   0                  0.013699                   0.013699            14:45                    146
   KBS    VN30       1m     ok 2026-05-25 09:15:00 2026-11-20 14:45:00   127  28819                227.0             09:15                     1.000000                   0                  0.370968                   1.000000            14:45                    124
   KBS    VN30       5m     ok 2025-11-20 14:45:00 2026-11-20 14:45:00   249  11687                 47.0             09:15                     0.995984                   0                  0.398374                   1.000000            14:45                    246
   KBS    VN30      15m     ok 2025-11-20 14:45:00 2026-11-20 14:45:00   249   4248                 17.0             09:15                     0.995984                   0                  0.398374                   1.000000            14:45                    246

## Findings
- **VN30F1M 1m (VCI) goes back to 2023-09-11 (~3.2 years, ~241 bars/day), despite vnstock's stated 6-month community cap** for 1m. That cap may be enforced later, so the data is cached now. Earlier than 2023-09-11 nothing is returned (no row cap observed: the response is not a round number). VCI VN30F1M 5m/15m and VCI VN30 5m/15m return 1 year on a padded 24h grid (NaN rows outside the session; dropped). KBS VN30F1M intraday is sparse (1m starts 2026-05-25 with ~6,200 rows; many minutes missing) and is not used.
- **VN30 index intraday exists**: VCI/KBS 1m from 2026-05-25 (~6 months), VCI/KBS 5m from 2025-11-20 (1 year). The first index bar of each day is 09:15 (the stock ATO result); there is no index print between 09:00 and 09:15. The 1m/5m windows roll (on this run VCI 5m starts 2025-11-24, VCI 1m 2026-05-27).
- **KBS index 09:15 bar disagrees with the daily open**: KBS's first index bar open equals the (VCI) daily open on only ~40% of days, by up to ~39 points, while VCI 5m/1m match it on 99.6%/98%; at 09:30 and 10:00 KBS and VCI agree exactly. VCI 5m is used, KBS is a cross-check only.
- The response includes the current, incomplete session (2026-11-23 VN time) and 2026-11-18..20, after the daily files end; analysis only uses dates present in the daily files.
- **Timezone**: timestamps are naive and run 09:00..14:45 (futures) / 09:15..14:45 (index), i.e. Vietnam local time (UTC+7); no conversion applied.
- **Daily-bar check**: first intraday bar open vs daily open and last bar close vs daily close are in the table (columns first_open_eq_daily_open, last_close_eq_daily_close).
- **How the futures ATO appears**: there is no separate 08:45 bar. The ATO match (struck at 09:00) is folded into the bar labelled 09:00: its open equals the daily open on ~99.7% of days and its median volume (2996 contracts) is >2x the 09:01 bar (1286). Only 8 stray bars before 09:00 exist in 3 years (dates 2023-09-20, 2023-09-21, 2023-11-03, 2024-08-19, 2024-11-26, 2025-04-24); they are ignored. The ATC appears as a single bar labelled 14:45 whose close equals the daily close on every day.
- Bars labelled 11:30 exist on 399 of 795 futures days and 14:30 on 353; there are no 12:59 or 14:31..14:44 bars. Consistent with bar-START labels (prints stamped exactly at 11:30:00 / 14:30:00 fall in a minute of their own).

## Bar-timestamp convention test (5m bars vs 1m bars, VCI)
If labels are bar-start, a 5m bar labelled t has the open of the 1m bar t and the close of the 1m bar t+4min.
 symbol    n  open5_eq_open1_same_label  close5_eq_close1_label_plus4m  close5_eq_close1_same_label
   VN30 3125                        1.0                       0.999680                     0.016000
VN30F1M 6180                        1.0                       0.999838                     0.028641

Result: **labels are bar-start times**. Price at time h is therefore taken as the open of the bar labelled h (first print at or after h).

## Index 5m (VCI, used) vs KBS 5m and VCI 1m at the sampling times (open of bar labelled h)
    h     vs   n  share_equal  max_abs_diff
09:15 KBS 5m 247     0.396761         39.33
09:15 VCI 1m 125     1.000000          0.00
09:30 KBS 5m 247     1.000000          0.00
09:30 VCI 1m 125     1.000000          0.00
10:00 KBS 5m 247     1.000000          0.00
10:00 VCI 1m 125     1.000000          0.00

## Decision
VN30F1M intraday history is >1 month (3.2 years), so Part 2 runs. Basis at matched times is limited to the index-intraday window (5m, 2025-11-20 onward). No trackforward addendum is required by the stop rule; track_forward.py and the frozen boundary are untouched.
