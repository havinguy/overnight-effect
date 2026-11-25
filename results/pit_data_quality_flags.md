# Point-in-time VN30 rebuild: data-quality flags

Window: price data start 2018-11-21 (VCI feed limit), so the testable window is 2018-11-21 .. 2026-11-18.

## Sources and confidence
| Periods | Membership | Shares / free-float | Cap factor (published) |
|---|---|---|---|
| Jan 2018 | HOSE PDF | PDF | PDF (before price window; not used in tests) |
| Jul 2018, Jan 2019, Jul 2019, Jul 2020, Jan 2021, Jan 2022 | set algebra + news (below) | **interpolated** from bracketing VN30 PDFs / VNAllShare tables (flat outside range) | none |
| Jan 2020 | KBSV copy of HOSE table ("Nguon: HOSE"), equals the set-algebra chain | mirror | mirror |
| Jul 2021, Jul 2022, Jan 2023 - Jan 2025 | HOSE PDF | PDF | PDF |
| 2023+ quarterly (May/Aug/Nov) updates | vn30_freefloat_history.csv | CSV | none |
| 2018-2022 quarterly (May/Nov) updates | unchanged | interpolated | none |

## Flags
1. **Script 1 was not in the repo** (only 02-04 exist in the VN25 project). A new parser (`src/pit_parse.py`) was written; it returns exactly 30 rows for all 8 PDFs. NT2 share count (name ends in "2") parsed from the right to avoid a 2,287,876,029 error.
2. **7 gap PDFs not located** (Jul 2018, Jan 2019, Jul 2019, Jan 2020, Jul 2020, Jan 2021, Jan 2022). Searches on the Vietstock CDN returned nothing. Jan 2020 was recovered from a faithful KBSV copy of the HOSE table. The other 6 use the fallback. Free-float for PNJ/VPB/VRE at Jul 2018 comes from news (70/60/45).
3. **Membership closure holds**: Jan-2018 PDF chained with the news timeline reproduces both the Jan-2020 mirror and the Jul-2021 PDF exactly (30 names at every step). The Jul-2018 removals (BID, BVH, NT2) are confirmed by VnEconomy. The Jan-2019 removals (PLX, KDC, BMP, HSG) are forced by closure and consistent with a BSC note. The spec's Jan-2019 adds (EIB, TCB, HDB, VHM) are consistent. Jan 2022: no net change (Jul-2022 PDF minus VIB plus PNJ equals Jul-2021 PDF), so Jan 2022 = Jul 2021; confidence "inferred".
4. **CSV overlap reconciliation**: 5 PDFs vs CSV quarter-start snapshots, 0 membership differences; 1 value mismatch (TCB shares Jan 2024: PDF 3,522,510,811 vs CSV 3,522,410,935). The CSV's Apr/Oct snapshots are the quarterly May/Nov updates, which is why they differ from the PDFs.
5. **The spec's cap-column caveat is wrong**: the CBTT "gioi han ty trong von hoa" column is the *applied capping factor* (e.g. VIC 77.20% Jan 2018, Vin trio 80.44% Jul 2021, FPT 78.70% Jul 2024), not a limit.
6. **The 40% same-sector cap is NOT applied to the published VN30 factors**: financials are 50-57% of raw free-float cap in 2024-25 yet every bank has c = 100%. The spec's s7.5 / risk-register item 1 is therefore wrong for VN30; the sector cap is off in the model (`use_sector=False`).
7. **Related groups share ONE common factor** (Vin trio 0.4538 in Jan 2020, 0.8044 in Jul 2021). Group-first clipping, then a within-group 10% check, reproduces this. Group map is hand-built (`data/vn30_sector_groups.csv`: Vingroup, Masan, Techcom); GICS sector column is approximate and unused in the final model.
8. **Prices are back-adjusted** (VCI and KBS both): SAB 84.61 in Nov 2018 vs a real price of about 200k VND. Cap-weights p*s*f*c therefore mix adjusted prices with historical share counts. Two bracketing conventions are reported: A = share count at the date (understates mcap of names with later bonus/splits); B = latest share count (overstates names with later non-bonus issuance). Cash dividends are also adjusted away from returns, so reconstructed returns have small ex-date residuals.
9. **Cap-factor accuracy**: model vs published (mirror/PDF dates, B): 2024-08 max |diff| 0.007, 2025-02 0.007, 2021-08 0.056, 2020-02 0.165 (VNM 0.80 vs 0.63; adjusted-price distortion largest where later bonus issues are largest).
10. **First three effective dates (2018-07-23, 2018-08-06, 2018-11-05)** predate the price data; caps use 2018-11-21 prices as the cutoff-price proxy. A first version silently used c = 1 here (VIC +7.7pp over-weight, window corr 0.964/0.981); fixed.
11. **2025-2026 tracking is the weakest** (variant B MAE 11.5-12 bp, window corr 0.992-0.993). Constituent-weight errors explain 68% of 2025 error variance (largest: VHM about 4pp under-weight vs published). Cause not isolated.
12. **Quarterly cap refresh for 2018-2022 May/Nov uses interpolated shares**; real quarterly updates for those years (the `cbtt_cap_nhat_thong_tin_bcs` files) were not collected.
13. **Current-30 cap-weighted cell** excludes names with no price at the cap cutoff (SSB, TCX, VPL before listing); the weighting effect is measured against equal-weight on that identical name set (`cur30_ew`), while composition effects use the exact Level B series (`cur30_ew_levelB`).

## Per-review membership diff (spec s2 expected vs built)
| Review (effective) | Spec adds | Spec removes | Built adds | Built removes | Source / status |
|---|---|---|---|---|---|
| Jan 2018 (2018-01-22) | baseline | - | 30 names | - | HOSE PDF (parsed, 30 rows) |
| Jul 2018 (2018-07-23) | PNJ VPB VRE | (PDF) | PNJ VPB VRE | BID BVH NT2 | removes from VnEconomy Jul-2018 article; closure-consistent |
| Jan 2019 (2019-02-11) | EIB TCB HDB VHM | (PDF) | EIB TCB HDB VHM | PLX KDC BMP HSG | removes forced by closure (7 removals needed over Jul18+Jan19; 3 confirmed Jul18) and match a BSC note. Spec says EIB, BSC says VPB; VPB already joined Jul 2018, so EIB. BSC says effective 4 Feb; VN30.csv has no trading day 4-8 Feb 2019 (Tet), so 4 Feb vs 11 Feb is equivalent and the extra 2019-02-04 entry is inert |
| Jul 2019 (2019-08-05) | BID BVH | CII DHG | BID BVH | CII DHG | matches |
| Jan 2020 (2020-02-03) | PLX POW | DPM GMD | PLX POW | DPM GMD | matches; full table from KBSV mirror equals chain |
| Jul 2020 (2020-08-03) | KDH TCH | CTD BVH | KDH TCH | CTD BVH | matches |
| Jan 2021 (2021-02-01) | BVH TPB PDR | SAB ROS EIB | BVH TPB PDR | SAB ROS EIB | matches |
| Jul 2021 (2021-08-02) | ACB GVR SAB | REE SBT TCH | ACB GVR SAB | REE SBT TCH | chain equals HOSE PDF exactly |
| Jan 2022 (2022-02-07) | not found | not found | none | none | inferred: Jul-2022 PDF minus VIB plus PNJ equals Jul-2021 PDF; a KBSV forecast (SAB, PNJ out) is contradicted by the Jul-2022 PDF |
| Jul 2022 (2022-08-01) | VIB | PNJ | VIB | PNJ | HOSE PDF |

## Residual split (see results/pit_residual_split.csv)
Published VN30 index overnight return (ln open / prev close, index open not flagged) is the missing middle link between the stock replica and VN30F1M. Index open_suspicious shares: 2019 12%, 2020 15%, 2021 4%, 2022 2% (others 0%).
