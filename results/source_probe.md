# Data-source continuity probe (src/source_probe.py), run 20261125T202737Z

Installed vnstock 4.0.4. Fetched bars and request log: data/raw_probe/20261125T202737Z/. Rules pre-registered in the header.

## Request log

```
                             utc       probe    symbol   status  rows
2026-11-25T20:27:41.856062+00:00 vnstock-VCI   VN30F1M       ok    25
2026-11-25T20:27:46.151963+00:00  vci-direct   VN30F1M HTTP 400     0
2026-11-25T20:27:52.615825+00:00 vnstock-KBS   VN30F1M       ok    22
2026-11-25T20:27:57.053185+00:00 vnstock-VCI 41I1GC000       ok    25
2026-11-25T20:28:00.863983+00:00  vci-direct 41I1GC000 HTTP 400     0
2026-11-25T20:28:06.803954+00:00 vnstock-KBS 41I1GC000       ok    22
2026-11-25T20:28:10.610722+00:00 vnstock-VCI      VN30       ok    25
2026-11-25T20:28:14.287486+00:00  vci-direct      VN30 HTTP 400     0
2026-11-25T20:28:21.620597+00:00 vnstock-KBS      VN30       ok    23
2026-11-25T20:28:25.445302+00:00 vnstock-VCI   VNINDEX       ok    25
2026-11-25T20:28:29.172077+00:00  vci-direct   VNINDEX HTTP 400     0
2026-11-25T20:28:34.404999+00:00 vnstock-KBS   VNINDEX       ok    22
```

## Last-10-session match rates

```
         probe    symbol   status has_2026_11_24                                       ref  overlap  src_first   src_last missing_in_ref  after_ref_last   ref_last  open_match_pct  high_match_pct  low_match_pct  close_match_pct  volume_match_pct  max_abs_close_diff
P1 vnstock VCI   VN30F1M       ok          False                      data/raw/VN30F1M.csv    10.00 2026-11-11 2026-11-25                           0.00 2026-11-25          100.00          100.00         100.00           100.00            100.00                0.00
P1 vnstock VCI   VN30F1M       ok          False                        frozen/VN30F1M.csv     5.00 2026-11-11 2026-11-25                           5.00 2026-11-17          100.00          100.00         100.00           100.00            100.00                0.00
 P2 VCI direct   VN30F1M HTTP 400            NaN                                         -      NaN        NaN        NaN            NaN             NaN        NaN             NaN             NaN            NaN              NaN               NaN                 NaN
P3 vnstock KBS   VN30F1M       ok          False                      data/raw/VN30F1M.csv    10.00 2026-11-11 2026-11-25                           0.00 2026-11-25           30.00           30.00          30.00            30.00             30.00                7.00
P3 vnstock KBS   VN30F1M       ok          False                        frozen/VN30F1M.csv     5.00 2026-11-11 2026-11-25                           5.00 2026-11-17           40.00            0.00           0.00             0.00              0.00                5.50
P1 vnstock VCI 41I1GC000       ok          False raw_forward_20261125/KBS_41I1GC000_1D.csv     9.00 2026-11-11 2026-11-25     2026-11-23            0.00 2026-11-25           11.11          100.00         100.00           100.00            100.00                0.00
P1 vnstock VCI 41I1GC000       ok          False raw_forward_20261125/VCI_41I1GC000_1D.csv    10.00 2026-11-11 2026-11-25                           0.00 2026-11-25          100.00          100.00         100.00           100.00            100.00                0.00
 P2 VCI direct 41I1GC000 HTTP 400            NaN                                         -      NaN        NaN        NaN            NaN             NaN        NaN             NaN             NaN            NaN              NaN               NaN                 NaN
P3 vnstock KBS 41I1GC000       ok          False raw_forward_20261125/KBS_41I1GC000_1D.csv     9.00 2026-11-11 2026-11-25     2026-11-23            0.00 2026-11-25          100.00          100.00         100.00           100.00            100.00                0.00
P3 vnstock KBS 41I1GC000       ok          False raw_forward_20261125/VCI_41I1GC000_1D.csv    10.00 2026-11-11 2026-11-25                           0.00 2026-11-25           20.00          100.00         100.00           100.00            100.00                0.00
P1 vnstock VCI      VN30       ok          False                         data/raw/VN30.csv     5.00 2026-11-11 2026-11-25                           5.00 2026-11-17          100.00          100.00         100.00           100.00            100.00                0.00
 P2 VCI direct      VN30 HTTP 400            NaN                                         -      NaN        NaN        NaN            NaN             NaN        NaN             NaN             NaN            NaN              NaN               NaN                 NaN
P3 vnstock KBS      VN30       ok          False                         data/raw/VN30.csv     5.00 2026-11-11 2026-11-25                           5.00 2026-11-17          100.00           40.00         100.00           100.00              0.00                0.00
P1 vnstock VCI   VNINDEX       ok          False                      data/raw/VNINDEX.csv     5.00 2026-11-11 2026-11-25                           5.00 2026-11-17          100.00          100.00         100.00           100.00            100.00                0.00
 P2 VCI direct   VNINDEX HTTP 400            NaN                                         -      NaN        NaN        NaN            NaN             NaN        NaN             NaN             NaN            NaN              NaN               NaN                 NaN
P3 vnstock KBS   VNINDEX       ok          False                      data/raw/VNINDEX.csv     5.00 2026-11-11 2026-11-25                           5.00 2026-11-17          100.00           60.00         100.00           100.00              0.00                0.00
```

## Grades (probe statement, not an adoption decision)

- P1 vnstock VCI: NOT replacement-grade on this probe
- P2 VCI direct: NOT replacement-grade on this probe (missing symbols or failed requests)
- P3 vnstock KBS: NOT replacement-grade on this probe

Integrity (data/raw and results unchanged except own outputs): True
