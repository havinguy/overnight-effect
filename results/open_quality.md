# Open-price quality: VCI vs KBS (checked 2026-11-17)

TCBS is not available in vnstock 4.x (Quote accepts kbs, vci, msn, dnse, binance, fmp, fmarket;
DNSE listed but no provider; MSN failed to resolve index symbols). Cross-check used KBS.

Flag: open == prior close exactly (`open_suspicious`).
- VNINDEX (VCI): 7.0% flagged overall; 3.8% pre-2015, 8.0% 2015+ (3.8% excluding 2021);
  2021 alone is 53% (133/250 days).
- VN30 (VCI): 4.3% flagged; 2019-2020 heavy (11.6%, 15.5%).
- VNINDEX: on 252 VCI-flagged days KBS shows a different open on 225 -> VCI fills these.
- VN30: on 86 VCI-flagged days KBS has the same value on 77 -> shared gap in upstream data.
  KBS itself flags 18% of VN30 days (2019-2021, 2025) and 2.9% of VNINDEX (43 days in 2025),
  so KBS is not cleaner overall. VCI kept as primary; rows flagged, not repaired.
- Opens agree within 0.05 pts on only 72% (VNINDEX) / 78% (VN30) of days across sources.

## Known data artifact: 2021 (VNINDEX)
133 of 250 VNINDEX sessions in 2021 (53%) are flagged (open == prior close) in the VCI feed,
against 1-8% in every other year. This is likely a VCI feed issue, not a market event. Any
paper or analysis built on this data must either exclude 2021 or treat those results with a
caveat. Robustness check with 2021 excluded entirely: see section below.

### Robustness: 2021 excluded entirely (full-sample, VCI)
| series | set | overnight mean | overnight Sharpe (ann) | overnight t |
|---|---|---|---|---|
| VNINDEX | all | 0.052% | 1.45 | 5.70 |
| VNINDEX | ex-2021 | 0.054% | 1.48 | 5.64 |
| VNINDEX | ex-2021 + flagged dropped | 0.056% | 1.51 | 5.64 |
| VN30 | all | 0.057% | 1.99 | 5.58 |
| VN30 | ex-2021 | 0.057% | 1.91 | 5.01 |
| VN30 | ex-2021 + flagged dropped | 0.059% | 1.95 | 5.02 |

Overnight result is not driven by 2021. VN30's lower t is mechanical (250 fewer obs; mean unchanged).
Intraday leg is less stable: VN30 intraday t goes -0.77 -> -1.28 (ex-2021) -> -1.63 (also drop flagged).

## Over-limit overnight gaps (|ln(open/prev close)| > 7%), VN30 constituents, checked 2026-11-17
153 rows across 29 tickers (list in results/overlimit_gaps.csv). Conclusion: NOT unadjusted corporate
actions; no `corp_action_suspected` flag added, no rows removed from primary Level B stats.
- 101 rows: HOSE limit-down opens (-6.8% to -7.0%, never beyond the band). 84% fall on market-wide
  selloff days (e.g. 2025-04-04: 15 tickers, 2026-03-09: 16, 2020-03-13: 9). ~90% of the gap persists to
  the close (locked at the floor). Genuine.
- 39 rows: ACB and SHB, <=10% (HNX band, before their moves to HOSE). Mostly reverse by the close
  (median retained 0.0), unlike a stock dividend. The "1:10 ratio" matches are the HNX 10% limit-down edge.
- 13 rows: 10-16% on MCH, BSR, LPB, GVR (UPCoM-band periods). Mostly reverse.
- Largest-gap size per ticker tracks the venue band (7% / 10% / ~15%); no clustering at -20/-25/-33/-50%.
- Residual oddities, not resolved: GVR 2019-01-02 (-8.7%, 7,900 shares), GVR 2020-03-17 (-16%),
  BSR 2021-01-28 (-12.8%, persistent). Could be thin first prints or real events; 3 rows of 153.
Caveat: ACB/SHB/MCH/BSR/LPB/GVR traded on HNX/UPCoM for part of the sample, so their overnight
stats mix exchange regimes (HNX has no opening auction).
Sensitivity (`level_b.py --exclude-large-gaps`): t-stats RISE for most names because dropping
limit-down opens removes negative overnight returns (selection on outcome, so not used as primary).
No ticker crosses the t=1.5 threshold; VRE's mean flips sign (-0.02% -> +0.01%) but stays insignificant
(t=0.51). Rank correlation of overnight Sharpe 0.97.
