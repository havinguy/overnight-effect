# Regime legs audit

Read-only on data/raw/ and results/. Script: `src/regime_legs_audit.py`. Rules R1-R5 are pre-registered in the script header (fixed before the first run).

Sample: one-day nights, common basket/futures dates, n = 1560 (2018-11-21..2026-11-17). Basket = PIT cap-weighted, all stock-days kept. Gap = futures minus basket per date; gap_C2C = gap_ON + gap_ID exactly. Log returns, bp, NW t (lag 5).

## 1. Leg decomposition (mean bp, NW t)

**basket**

```
         period    n            ON            ID          C2C
 pre 2022-08-25  740 -0.82 (-0.28)  10.96 (2.94) 10.13 (2.63)
post 2022-08-25  820  13.46 (5.70) -2.35 (-0.71) 11.11 (3.06)
            all 1560   6.69 (3.50)   3.96 (1.57) 10.65 (4.03)
```

**futures**

```
         period    n          ON          ID          C2C
 pre 2022-08-25  740 5.41 (2.57) 8.16 (1.98) 13.57 (3.14)
post 2022-08-25  820 7.05 (4.53) 5.56 (1.53) 12.61 (3.22)
            all 1560 6.28 (4.86) 6.79 (2.49) 13.07 (4.49)
```

**gap** (futures minus basket)

```
         period    n            ON            ID         C2C
 pre 2022-08-25  740   6.23 (3.18) -2.80 (-1.30) 3.44 (1.83)
post 2022-08-25  820 -6.41 (-4.12)   7.90 (4.58) 1.50 (1.26)
            all 1560 -0.41 (-0.32)   2.83 (2.02) 2.42 (2.22)
```

R1 verdicts: pre 2022-08-25: CONVERGENCE / BASIS DRIFT; post 2022-08-25: OPEN-TIMING SPLIT; all: NO ON GAP

## 2. Relocation test (post minus pre 2022-08-25)

```
     series  pre_bp  pre_t  post_bp  post_t   d_bp  se_bp     t   lo95  hi95  n_pre  n_post
  basket ON   -0.82  -0.28    13.46    5.70  14.28   3.75  3.81   6.94 21.63    740     820
  basket ID   10.96   2.94    -2.35   -0.71 -13.30   5.00 -2.66 -23.10 -3.51    740     820
 basket C2C   10.13   2.63    11.11    3.06   0.98   5.30  0.18  -9.41 11.37    740     820
 futures ON    5.41   2.57     7.05    4.53   1.64   2.61  0.63  -3.48  6.77    740     820
 futures ID    8.16   1.98     5.56    1.53  -2.60   5.48 -0.47 -13.35  8.14    740     820
futures C2C   13.57   3.14    12.61    3.22  -0.96   5.84 -0.16 -12.40 10.48    740     820
     gap ON    6.23   3.18    -6.41   -4.12 -12.64   2.50 -5.05 -17.55 -7.73    740     820
     gap ID   -2.80  -1.30     7.90    4.58  10.70   2.75  3.89   5.31 16.10    740     820
    gap C2C    3.44   1.83     1.50    1.26  -1.94   2.22 -0.87  -6.29  2.41    740     820
```

R2 (stocks): dC2C 0.98 bp (t 0.18), dON 14.28 (t 3.81), dID -13.30 (t -2.66) -> RELOCATION HOLDS.

## 3. Tolerance-based flat-open detector, stocks (report only; not applied)

Share of PIT-member constituent-nights (one-day, common dates) with |ON| exactly 0, < 5 bp (0.05%), < 10 bp (0.1%); basket ON and C2C SD; ON/C2C SD ratio as a volatility-normalised spread.

```
         period  nights  constituent_nights  share_exact0  share_lt_5bp  share_lt_10bp  share_5_10bp_band  basket_ON_sd_bp  basket_C2C_sd_bp  ON_sd_over_C2C_sd
           2018      23                 678         0.255         0.257          0.265              0.009           70.627            64.281              1.099
           2019     198                5940         0.351         0.353          0.381              0.028           29.872            66.076              0.452
           2020     197                5910         0.270         0.271          0.285              0.015           93.648           121.571              0.770
           2021     196                5880         0.235         0.236          0.264              0.028           66.289           139.851              0.474
           2022     196                5880         0.203         0.204          0.228              0.024           73.610           153.386              0.480
           2023     186                5580         0.287         0.288          0.300              0.012           39.551           105.491              0.375
           2024     196                5880         0.302         0.302          0.317              0.015           31.107            81.966              0.380
           2025     197                5910         0.239         0.240          0.254              0.015           95.277           132.313              0.720
           2026     171                5130         0.244         0.245          0.258              0.013           56.925           105.226              0.541
 pre 2022-08-25     740               22188         0.273         0.274          0.298              0.024           66.808           114.304              0.584
post 2022-08-25     820               24600         0.261         0.262          0.276              0.014           65.067           117.823              0.552
 window 2018-19     221                6618         0.341         0.343          0.369              0.026           36.543            66.194              0.552
 window 2023-25     579               17370         0.276         0.276          0.290              0.014           62.549           108.648              0.576
```

- Comparable-volatility windows: basket C2C SD 2018-19 66.2 bp vs 2023-25 108.6 bp; basket ON SD 36.5 vs 62.5 bp; ON/C2C SD ratio 0.552 vs 0.576. Near-flat (< 10 bp) share 0.369 vs 0.290; exact-zero 0.341 vs 0.276; the 5-10 bp band (near-flat but not exact) 0.026 vs 0.014.

## 4. REPLACEMENT of the 82% Monday claim: basket (not index) as the reference leg

This replaces futures_basis_summary.md R1 ('Monday dbasis share 82%, t 2.21, 2018-11..2021', computed against the VN30 index open). fut_ON = basket_ON + gap_ON on one-day nights; share = mean(gap)/mean(fut_ON), Fieller 95% CI.

```
         period    night   n  fut_ON_bp  fut_t  basket_ON_bp  basket_t  gap_ON_bp  gap_t  basis_share_pct  fieller_lo_pct  fieller_hi_pct                                 fieller  R4_mostly_basis
  2018-11..2021 Mon->Tue 154      15.44   2.72          8.05      1.31       7.39   1.04            47.86          -87.91          137.70                                 bounded            False
  2018-11..2021 Tue->Wed 154       3.18   0.91          0.32      0.09       2.86   1.14            90.02            -inf             inf unbounded (denominator not significant)            False
  2018-11..2021 Wed->Thu 151       1.63   0.42          0.04      0.01       1.58   0.47            97.28            -inf             inf unbounded (denominator not significant)            False
  2018-11..2021 Thu->Fri 155       3.29   0.59         -7.81     -1.14      11.10   2.29           337.53            -inf             inf unbounded (denominator not significant)             True
      2022-2026 Mon->Tue 237      10.00   3.45         14.49      3.15      -4.49  -1.46           -44.85         -131.79           18.29                                 bounded            False
      2022-2026 Tue->Wed 241       8.74   1.85         12.56      2.64      -3.82  -1.36           -43.72            -inf             inf unbounded (denominator not significant)            False
      2022-2026 Wed->Thu 239       3.45   1.02         12.63      3.79      -9.18  -3.66          -265.89            -inf             inf unbounded (denominator not significant)            False
      2022-2026 Thu->Fri 229       3.78   1.42          3.80      1.04      -0.02  -0.01            -0.41            -inf             inf unbounded (denominator not significant)            False
 pre 2022-08-25 Mon->Tue 184      12.87   2.64          2.86      0.50      10.01   1.60            77.78          -30.85          223.52                                 bounded            False
 pre 2022-08-25 Tue->Wed 186       3.90   1.28          0.99      0.30       2.91   1.24            74.72            -inf             inf unbounded (denominator not significant)            False
 pre 2022-08-25 Wed->Thu 183       1.98   0.55          1.43      0.28       0.56   0.19            28.09            -inf             inf unbounded (denominator not significant)            False
 pre 2022-08-25 Thu->Fri 187       2.93   0.62         -8.44     -1.43      11.37   2.63           388.19            -inf             inf unbounded (denominator not significant)             True
post 2022-08-25 Mon->Tue 207      11.49   3.57         20.03      4.56      -8.54  -3.39           -74.31         -171.39          -30.66                                 bounded            False
post 2022-08-25 Tue->Wed 209       8.94   1.67         13.83      2.60      -4.89  -1.60           -54.66            -inf             inf unbounded (denominator not significant)            False
post 2022-08-25 Wed->Thu 207       3.42   0.94         13.35      3.79      -9.93  -3.60          -290.47            -inf             inf unbounded (denominator not significant)            False
post 2022-08-25 Thu->Fri 197       4.21   1.45          6.28      1.66      -2.07  -0.76           -49.30            -inf             inf unbounded (denominator not significant)            False
```

- NEW Mon->Tue basis share 2018-11..2021: 48% (gap 7.39 bp, t 1.04; futures 15.44 bp, basket 8.05 bp; Fieller -88..138%; n 154) -> R4 mostly basis: False.
- 2022-2026: -45% (gap -4.49 bp, t -1.46; futures 10.00, basket 14.49; Fieller -132..18%, bounded) -> R4 mostly basis: False.
- Differences from the original: one-day nights only, CW PIT basket instead of the index, common basket/futures dates; the original used all Mon->Tue nights with an index leg.

## 5. Futures break CI and paired stock-minus-futures break

```
                                              test  pre_bp  pre_t  post_bp  post_t  d_bp  se_bp    t  lo95  hi95  n_pre  n_post
                     futures ON break (post - pre)    5.41   2.57     7.05    4.53  1.64   2.61 0.63 -3.48  6.77    740     820
                      basket ON break (post - pre)   -0.82  -0.28    13.46    5.70 14.28   3.75 3.81  6.94 21.63    740     820
paired: break of (basket ON - futures ON) per date   -6.23  -3.18     6.41    4.12 12.64   2.50 5.05  7.73 17.55    740     820
```

- Futures ON break 1.64 bp, 95% CI -3.48..6.77 bp. Paired date-level break (basket - futures) 12.64 bp, t 5.05 (CI 7.73..17.55).

## Reading

**Where the futures-basket gap sits.** Pre-cutover the gap is in ON (6.23 bp, t 3.18); ID is negative but not significant (-2.80, t -1.30), so R1 returns CONVERGENCE / BASIS DRIFT. The C2C gap is only 3.44 bp (t 1.83), about half the ON gap: R1 is met because the intraday offset is not significant, not because C2C clearly equals ON - borderline between the two rows. Post-cutover R1 returns OPEN-TIMING SPLIT: ON -6.41 (t -4.12), ID 7.90 (t 4.58), C2C 1.50 (t 1.26). That verdict is the stock relocation seen from the other side: no futures leg moves across the cutover (all |t| < 0.6), so the post-cutover gap pattern comes entirely from the basket's own shift and carries no information about futures open timing (the same applies to the significant 2022-26 Mon->Tue gap, basket above futures).
Pre-cutover, about half of the ON excess (3.4 of 6.2 bp) carries to the close and about half reverses intraday without reaching significance; the convergence verdict rests on that absence of evidence.

**Relocation (stocks).** Holds under R2: basket C2C is unchanged across the cutover (+0.98 bp, t 0.18) while ON rises +14.28 (t 3.81) and ID falls -13.30 (t -2.66). The stock 'regime' is a move of return from the trading day to the night with the daily total unchanged. Futures show no change in any leg (all |t| < 0.6). Power: the C2C 'unchanged' result has a 95% CI of -9.4..11.4 bp, so a C2C change smaller than about 10 bp could not be detected.

**Tolerance detector.** Stock flat opens are exact, not near-flat: the 5-10 bp band adds only 0.009-0.028 of constituent-nights on top of the exact-zero share. Near-flat share pre 0.298 vs post 0.276; 2019 is the highest year (0.381). The 2018-19 and 2023-25 windows are NOT comparable in volatility (basket C2C SD 66 vs 109 bp), so the volatility-normalised ON/C2C SD ratio is the comparison: 0.552 vs 0.576, i.e. no compression of the stock overnight between the two windows. 2019 has both the lowest stock ON/C2C ratio (0.452) and the highest near-flat share (0.381), consistent with the degradation audit's 'both references degraded' reading for 2019.

**Monday split, replaced.** With the basket as reference, the 2018-11..2021 Mon->Tue futures edge 15.44 bp splits into basket 8.05 bp (t 1.31) and futures-minus-basket 7.39 bp (t 1.04): basis share 48% (Fieller -88..138%), not 'mostly basis' under R4. The 82% claim is no longer supported: the share is undetermined (gap t 1.04; the Fieller interval covers 0%, 48%, 82% and 100%), so the data cannot distinguish 48% from 82%. The replacement is clean: the futures leg reproduces the original exactly (15.44 bp, n 154), so the whole change comes from the reference leg (basket 8.05 bp vs index 2.78 bp). In 2022-2026 the basket exceeds the futures on Mon->Tue (share -45%, Fieller -132..18%). The only R4 'mostly basis' rows are pre-cutover Thu->Fri (gap 11.4 bp, t 2.63) with a futures mean that is not significant, so the share (>300%) is not meaningful.

**Breaks.** Futures ON break 1.64 bp, 95% CI -3.48..6.77. Paired date-level break of (basket - futures) 12.64 bp, t 5.05: the stock break is significantly larger than the futures break.

Caveats: pre-2022-06 futures opens are unverified (open-definition / stability audits); one-day nights only; stock flat opens kept (exact-zero ON on ~27% of constituent-nights, both periods).

## Summary (5 lines)

1. Futures-basket gap: pre-cutover in ON (6.2 bp, t 3.2) with an insignificant ID offset (-2.8, t -1.3) and C2C 3.4 (t 1.8) -> R1 CONVERGENCE/BASIS DRIFT (borderline: half the ON excess reverses intraday, n.s.); post-cutover R1 says OPEN-TIMING SPLIT (ON -6.4, ID +7.9, C2C 1.5 n.s.), but that is the stock relocation seen from the futures side (no futures leg moves), not evidence on futures open timing.
2. Relocation holds for stocks: C2C unchanged (+1.0 bp, t 0.18), ON +14.3 (t 3.8), ID -13.3 (t -2.7); futures break 1.6 bp (95% CI -3.5..6.8); paired stock-minus-futures break 12.6 bp (t 5.1); C2C CI -9.4..11.4 bp, so changes < ~10 bp undetectable.
3. Flat-open tolerance: stock flat opens are exact (5-10 bp band <= 0.028); near-flat share pre 0.298 vs post 0.276; ON/C2C SD ratio 2018-19 0.55 vs 2023-25 0.58 (windows differ in volatility, C2C SD 66 vs 109 bp): no compression of stock overnight between the windows; 2019 alone combines the lowest ratio and highest near-flat share.
4. New Monday split (REPLACES 82%): 2018-11..2021 Mon->Tue futures 15.4 bp = basket 8.0 + gap 7.4 (t 1.04); basis share 48% (Fieller -88..138%): the 82% claim is no longer supported, the share is undetermined (cannot distinguish 48% from 82%); futures leg identical to the original (15.44 bp, n 154), change comes from the reference (basket 8.05 vs index 2.78 bp); 2022-26 -45% (basket above futures).
5. Open question: does the half of the pre-cutover futures ON excess that reverses intraday come from how pre-2022 futures opens were defined (needs verified opens to answer)? Second: what moved stock return from intraday to overnight at 2022-08-25 with futures unchanged - consistent with the T+2 afternoon-sale rule, mechanism not identified here.

Integrity: md5 of every pre-existing file in data/raw/ and results/ identical before and after: True (249 files).
