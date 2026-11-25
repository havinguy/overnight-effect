# Forward-bar audit: missing 2026-11-24 bar and a second futures source

Script `src/forward_bar_audit.py`; rules T, K, S, V, R pre-registered in its header before the first run (`--fetch-only`, 2026-11-25). All vnstock requests are logged in `data/raw_forward_20261125/_fetch_log.csv` (27 requests, 2026-11-25T19:34:16+00:00 .. 2026-11-25T19:37:20+00:00 UTC; 23 ok, 4 failed).

```
                      utc source    symbol      start        end                                                                                 status  rows
2026-11-25T19:34:16+00:00    VCI      VN30 2026-10-01 2026-11-26                                                                                     ok    43
2026-11-25T19:34:24+00:00    VCI   VNINDEX 2026-10-01 2026-11-26                                                                                     ok    43
2026-11-25T19:34:30+00:00    KBS      VN30 2026-10-01 2026-11-26                                                                                     ok    40
2026-11-25T19:34:37+00:00    KBS   VNINDEX 2026-10-01 2026-11-26                                                                                     ok    40
2026-11-25T19:34:43+00:00    VCI   VN30F1M 2026-01-01 2026-11-26                                                                                     ok   238
2026-11-25T19:34:49+00:00    VCI   VN30F2M 2026-01-01 2026-11-26                                                                                     ok   238
2026-11-25T19:34:54+00:00    KBS   VN30F1M 2026-01-01 2026-11-26                                                                                     ok   149
2026-11-25T19:35:01+00:00    KBS   VN30F2M 2026-01-01 2026-11-26                                                                                     ok     4
2026-11-25T19:35:08+00:00    VCI 41I1G1000 2025-05-01 2026-11-26                                                                                     ok    38
2026-11-25T19:35:13+00:00    VCI 41I1G2000 2025-05-01 2026-11-26                                                                                     ok    39
2026-11-25T19:35:18+00:00    VCI 41I1G3000 2025-05-01 2026-11-26                                                                                     ok   166
2026-11-25T19:35:23+00:00    VCI 41I1G4000 2025-05-01 2026-11-26                                                                                     ok    39
2026-11-25T19:35:29+00:00    VCI 41I1G5000 2025-05-01 2026-11-26                                                                                     ok    42
2026-11-25T19:35:34+00:00    VCI 41I1G6000 2025-05-01 2026-11-26                                                                                     ok   165
2026-11-25T19:35:40+00:00    VCI 41I1G7000 2025-05-01 2026-11-26                                                                                     ok    40
2026-11-25T19:35:45+00:00    VCI 41I1G8000 2025-05-01 2026-11-26                                                                                     ok    45
2026-11-25T19:35:50+00:00    VCI 41I1G9000 2025-05-01 2026-11-26                                                                                     ok   164
2026-11-25T19:35:55+00:00    VCI 41I1GA000 2025-05-01 2026-11-26                                                                                     ok    37
2026-11-25T19:36:01+00:00    VCI 41I1GB000 2025-05-01 2026-11-26                                                                                     ok    45
2026-11-25T19:36:06+00:00    VCI 41I1GC000 2025-05-01 2026-11-26                                                                                     ok   151
2026-11-25T19:36:12+00:00    VCI 41I1H1000 2025-05-01 2026-11-26                                                                                     ok     3
2026-11-25T19:36:17+00:00    KBS 41I1G8000 2026-01-01 2026-11-26 error RetryError: RetryError[<Future at 0x10bf99250 state=finished raised ValueError>]     0
2026-11-25T19:36:31+00:00    KBS 41I1G9000 2026-01-01 2026-11-26 error RetryError: RetryError[<Future at 0x10bf98650 state=finished raised ValueError>]     0
2026-11-25T19:36:45+00:00    KBS 41I1GA000 2026-01-01 2026-11-26 error RetryError: RetryError[<Future at 0x10bf98ed0 state=finished raised ValueError>]     0
2026-11-25T19:36:59+00:00    KBS 41I1GB000 2026-01-01 2026-11-26 error RetryError: RetryError[<Future at 0x10bf99550 state=finished raised ValueError>]     0
2026-11-25T19:37:13+00:00    KBS 41I1GC000 2026-01-01 2026-11-26                                                                                     ok   149
2026-11-25T19:37:20+00:00    KBS 41I1H1000 2026-01-01 2026-11-26                                                                                     ok     4
```

## 2a. Was 2026-11-24 a trading day? (rule T)

```
source  symbol   last_bar  bar_2026_11_24  volume_2026_11_24              bars_2026_11_20_to_25
   VCI    VN30 2026-11-25           False                NaN 2026-11-20, 2026-11-23, 2026-11-25
   VCI VNINDEX 2026-11-25           False                NaN 2026-11-20, 2026-11-23, 2026-11-25
   KBS    VN30 2026-11-25           False                NaN 2026-11-20, 2026-11-23, 2026-11-25
   KBS VNINDEX 2026-11-25           False                NaN 2026-11-20, 2026-11-23, 2026-11-25
```

- Rule T (VN30 and VNINDEX each have an 11-24 bar with volume > 0 in VCI or KBS): FAIL. Fetched files with an 11-24 bar: 0 of 23 (index, continuous futures and every contract code, both vendors). No allowed feed shows a session on 2026-11-24, so it is NOT confirmed as a trading day. Whether the market was closed (holiday / halt) or every vendor lost the day cannot be told from these feeds.

## K. Contract identity (VCI KRX codes)

```
     code   month     expiry      first       last   n identity
41I1G1000 2026-01 2026-01-15 2025-11-21 2026-01-15  38     PASS
41I1G2000 2026-02 2026-02-13 2025-12-19 2026-02-13  39     PASS
41I1G3000 2026-03 2026-03-19 2025-07-18 2026-03-19 166     PASS
41I1G4000 2026-04 2026-04-16 2026-02-23 2026-04-16  39     PASS
41I1G5000 2026-05 2026-05-21 2026-03-20 2026-05-21  42     PASS
41I1G6000 2026-06 2026-06-18 2025-10-17 2026-06-18 165     PASS
41I1G7000 2026-07 2026-07-16 2026-05-22 2026-07-16  40     PASS
41I1G8000 2026-08 2026-08-20 2026-06-19 2026-08-20  45     PASS
41I1G9000 2026-09 2026-09-17 2026-01-16 2026-09-17 164     PASS
41I1GA000 2026-10 2026-10-15 2026-08-21 2026-10-15  37     PASS
41I1GB000 2026-11 2026-11-19 2026-09-18 2026-11-19  45     PASS
41I1GC000 2026-12 2026-11-25 2026-04-17 2026-11-25 151     PASS
41I1H1000 2027-01 2026-11-25 2026-11-20 2026-11-25   3     PASS
```

- 13 of 13 codes pass (last bar on that month's expiry; live contract through 2026-11-25).

## 2b. Validation of the VCI KRX-coded contracts (rule V)

Premise check: the earlier 100% KRX match (futures_roll_gap_audit.md) covered ONE contract (41I1G1000, Jan-2026) over 18 days, not every contract listed after May 2025. This run tests every 2026 contract on the fixed range 2025-12-19..2026-11-25.

```
                                          source   n      first       last  open_match  high_match  low_match  close_match  volume_exact  volume_within_1pct
VCI KRX codes stitched vs VCI VN30F1M (data/raw) 230 2025-12-19 2026-11-25      1.0000      1.0000     1.0000       1.0000        1.0000              1.0000
                                       41I1G1000  18 2025-12-19 2026-01-15      1.0000      1.0000     1.0000       1.0000        1.0000              1.0000
                                       41I1G2000  21 2026-01-16 2026-02-13      1.0000      1.0000     1.0000       1.0000        1.0000              1.0000
                                       41I1G3000  19 2026-02-23 2026-03-19      1.0000      1.0000     1.0000       1.0000        1.0000              1.0000
                                       41I1G4000  20 2026-03-20 2026-04-16      1.0000      1.0000     1.0000       1.0000        1.0000              1.0000
                                       41I1G5000  22 2026-04-17 2026-05-21      1.0000      1.0000     1.0000       1.0000        1.0000              1.0000
                                       41I1G6000  20 2026-05-22 2026-06-18      1.0000      1.0000     1.0000       1.0000        1.0000              1.0000
                                       41I1G7000  20 2026-06-19 2026-07-16      1.0000      1.0000     1.0000       1.0000        1.0000              1.0000
                                       41I1G8000  25 2026-07-17 2026-08-20      1.0000      1.0000     1.0000       1.0000        1.0000              1.0000
                                       41I1G9000  17 2026-08-21 2026-09-17      1.0000      1.0000     1.0000       1.0000        1.0000              1.0000
                                       41I1GA000  20 2026-09-18 2026-10-15      1.0000      1.0000     1.0000       1.0000        1.0000              1.0000
                                       41I1GB000  25 2026-10-16 2026-11-19      1.0000      1.0000     1.0000       1.0000        1.0000              1.0000
                                       41I1GC000   3 2026-11-20 2026-11-25      1.0000      1.0000     1.0000       1.0000        1.0000              1.0000
```

V3 bars (11-18, 11-19 = Nov contract; 11-20, 11-23, 11-25 = Dec contract):

```
      date  contract   open   high    low  close   volume  open_v  high_v  low_v  close_v  volume_v  all_fields_match
2026-11-18 41I1GB000 1834.0 1836.9 1806.1 1815.0 172252.0  1834.0  1836.9 1806.1   1815.0    172252              True
2026-11-19 41I1GB000 1811.3 1812.2 1784.3 1787.9 187495.0  1811.3  1812.2 1784.3   1787.9    187495              True
2026-11-20 41I1GC000 1765.9 1780.2 1761.7 1780.2 185882.0  1765.9  1780.2 1761.7   1780.2    185882              True
2026-11-23 41I1GC000 1775.0 1799.5 1753.1 1789.3 254042.0  1775.0  1799.5 1753.1   1789.3    254042              True
2026-11-25 41I1GC000 1791.6 1799.5 1769.9 1769.9 198238.0  1791.6  1799.5 1769.9   1769.9    198238              True
```

- V1 pass; V2 pass; V3 pass; V4 FAIL; V5 pass -> NOT VALIDATED.
- Overlap n 230: close 1.0000, open 1.0000, high 1.0000, low 1.0000, volume exact 1.0000. The source itself reproduces VCI VN30F1M on every field; it fails only because it has no 2026-11-24 bar (V4), consistent with 2a.

## 2c. Outcome

NOT VALIDATED (failing: V4). `data/raw/VN30F1M_repaired_forward.csv` was NOT written and the logger was not rerun. The Monday 2026-11-23 stays `skipped_hold` in the official log: the logger saw a Monday-close -> Wednesday-open night (no 11-24 bar), which its rule excludes, as in the backtest.

## 3. Second source (rule R): KBS through vnstock

No broker API key is available in this environment, and an HNX/HOSE website download would be scraping (project rule: no scraping, no unofficial endpoints), so KBS via vnstock is the only second source tried.

```
                                                        source   n      first       last  open_match  high_match  low_match  close_match  volume_exact  volume_within_1pct
           KBS KRX codes stitched (front month) vs VCI VN30F1M   2 2026-11-20 2026-11-25      0.0000      1.0000     1.0000       1.0000        1.0000              1.0000
                        KBS 'VN30F1M' as served vs VCI VN30F1M  58 2026-09-03 2026-11-25      0.0690      0.0345     0.1034       0.0517        0.0345              0.0345
report-only: KBS vs VCI, same contract 41I1GC000, all its days 149 2026-04-17 2026-11-25      0.3087      1.0000     1.0000       1.0000        1.0000              1.0000
report-only: KBS vs VCI, same contract 41I1H1000, all its days   3 2026-11-20 2026-11-25      0.3333      1.0000     1.0000       1.0000        1.0000              1.0000
```

- KBS served only 41I1GC000, 41I1H1000; it refused 41I1G8000, 41I1G9000, 41I1GA000, 41I1GB000 (RetryError/ValueError), so the Sep-Nov 2026 front months cannot be stitched from KBS: stitched overlap n = 2 (needs >= 50). KBS 'VN30F1M' is the fixed Dec-2026 contract, not a rolling front month (it matches VCI VN30F1M only from the 11-20 roll).
- Rule R ('could replace VCI'): NO - insufficient coverage, not a price disagreement. Report-only same-contract check: KBS vs VCI 41I1GC000 close 1.0000, open 0.3087, volume exact 1.0000 over 149 days.
- Continuity: KBS is reached through the same vnstock v4 library whose sunset was announced (v4/v5 'stop operating' from 2026-11-10, Decree 363/2026 from 2026-11-11). Agreement today is not a continuity answer. A true second path needs something the user supplies: a broker API key (the v6 model) or an official exchange file.

Integrity: sha256 of every pre-existing file in data/raw/ and results/ identical before and after: True (178 files).

## Summary (5 lines)

1. 2026-11-24: no bar in VCI or KBS for VN30 or VNINDEX, nor in any futures series or contract code (0/23 files) -> rule T FAIL, not confirmed as a trading day.
2. VCI KRX contract codes: identity 13/13 pass; stitched vs VCI VN30F1M on 230 days: close 100.0%, open 100.0%, high 100.0%, low 100.0%, volume exact 100.0%; the 11-18..11-25 bars all match.
3. Rule V: NOT VALIDATED (failing: V4): the source has no 11-24 bar either; nothing inserted, no repaired_forward file, the Monday stays skipped_hold.
4. Second source KBS: only 2 KRX codes served (Sep-Nov front months refused), stitched overlap n 2 -> cannot replace VCI (rule R NO, coverage); same-contract 41I1GC000 KBS vs VCI close 100.0%, volume exact 100.0% (report-only).
5. Continuity is not established: KBS rides the same vnstock v4 path; a replacement needs a user-supplied broker API key or an official exchange file.
