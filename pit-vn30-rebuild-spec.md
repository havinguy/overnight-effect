# Point-in-Time VN30 Rebuild — Data Manifest, Capping Spec & Build Prompt

Purpose: give the overnight-effect project a *validated* point-in-time VN30 panel (2018–2026) so the day-of-week decomposition can separate composition from weighting with claims backed by data, not assumption. This doc is the data-sourcing + validation spec and the Claude Code build prompt.

Status as of 2026-11-18: source confirmed, capping algorithm extracted, one reliability risk surfaced (quarterly re-capping). Not yet built.

---

## 1. The gold-source document

HOSE publishes, at each reconstitution, **"CBTT – Danh sách thành phần chỉ số VN30"** — the full 30-name basket with columns: ticker, index shares (khối lượng lưu hành tính chỉ số), rounded free-float % (tỷ lệ free-float làm tròn), and cap limit % (giới hạn tỷ trọng vốn hóa). This is the same document type the VN25 Script 1 pipeline already parses. Mirrored on the Vietstock CDN `static2.vietstock.vn`, publicly fetchable.

Note the column caveat: the published cap column is the *limit*, not the applied capping factor. The factor that actually bites is recomputed quarterly (see §3).

### Confirmed URLs (fetched/verified)

| Period | Effective window | URL |
|---|---|---|
| Jan 2018 | 22/01/2018–20/07/2018 | `https://static2.vietstock.vn/vietstock/2018/1/15/20180115_Danh sach HOSE-Index, Chi so VN30 ky 1 2018.pdf` |
| Jul 2021 | from 02/08/2021 | `https://static2.vietstock.vn/vietstock/2021/7/19/20210719_20210719-CBTT - Danh sach thanh phan HOSE-Index_VNSI thang 7 2021.pdf` |
| Jul 2022 | from 01/08/2022 | `https://static2.vietstock.vn/vietstock/2022/7/21/20220718_20220718___cbtt_danh_sach_thanh_phan_hose_index_thang_7_2022.pdf` |
| Jan 2023 | 06/02/2023–04/08/2023 | `https://static2.vietstock.vn/vietstock/2023/1/16/20230116_20230116_cbtt___danh_sach_thanh_phan_hose_index_thang_01_2023.pdf` |
| Jul 2023 | 07/08/2023–02/02/2024 | `https://static2.vietstock.vn/vietstock/2023/7/17/20230717_20230717_cbtt___danh_sach_thanh_phan_hose_index_thang_7_2023.pdf` |
| Jan 2024 | 05/02/2024–02/08/2024 | `https://static2.vietstock.vn/vietstock/2024/1/15/20240115_20240115_cbtt___danh_sach_thanh_phan_hose_index_thang_1_2024.pdf` |
| Jul 2024 | from 05/08/2024 | `https://static2.vietstock.vn/vietstock/2024/7/15/20240715_20240715_cbtt___danh_sach_thanh_phan_hose_index_thang_7_2024_1.pdf` |
| Jan 2025 | 03/02/2025–01/08/2025 | `https://static2.vietstock.vn/vietstock/2025/1/20/20250120_hose_index.pdf` |

The 2023+ periods overlap your existing `vn30_freefloat_history.csv` — use them as a parser cross-check, not new data.

### Gaps to locate (7 periods, 2018–2022)

PDFs not yet pinned to a URL. Naming is inconsistent across years (`YYYYMMDD_Danh sach...`, `YYYYMMDD_YYYYMMDD___cbtt_danh_sach...`, and once just `YYYYMMDD_hose_index.pdf`), and the publish day drifts (15th–21st of Jan/Jul), so URLs can't be guessed — locate each via search.

Search recipe (run in Claude Code's web tool): `site:static2.vietstock.vn cbtt danh sach thanh phan hose index thang <7|1> <year>`, or without the site filter `vietstock CBTT danh sách thành phần HOSE-Index VN30 kỳ tháng <7|1> <year>`. Periods needed: **Jul 2018, Jan 2019, Jul 2019, Jan 2020, Jul 2020, Jan 2021, Jan 2022.** If a period won't surface, fall back to the membership timeline in §2 for composition and interpolate free-float from the nearest bracketing PDFs — but flag it.

---

## 2. Membership-change timeline (news-sourced — cross-check, not primary)

Primary source is the §1 PDFs. This timeline is for (a) filling a gap if a PDF won't load and (b) validating the parser caught the right adds/removes. Confidence flags: ✓ = add and matching remove both confirmed in news; ~ = adds confirmed, removes incomplete (PDF resolves).

| Review | Effective | Added | Removed | Conf |
|---|---|---|---|---|
| Jan 2018 | 22/01/2018 | *(baseline basket — parse PDF)* | — | ✓ |
| Jul 2018 | 23/07/2018 | PNJ, VPB, VRE | *(PDF)* | ~ |
| Jan 2019 | 11/02/2019 (ff/cap re-adj 06/05/2019) | EIB, TCB, HDB, VHM | *(PDF)* | ~ |
| Jul 2019 | 05/08/2019 | BID, BVH | CII, DHG | ✓ |
| Jan 2020 | 03/02/2020 | PLX, POW | DPM, GMD | ✓ |
| Jul 2020 | 03/08/2020 | KDH, TCH | CTD, BVH | ✓ |
| Jan 2021 | 01/02/2021 | BVH, TPB, PDR | SAB, ROS, EIB | ✓ |
| Jul 2021 | 02/08/2021 | ACB, GVR, SAB | REE, SBT, TCH | ✓ |
| Jan 2022 | ~07/02/2022 | *(PDF — not found in news)* | *(PDF)* | — |
| Jul 2022 | 01/08/2022 | VIB | PNJ | ✓ |
| Jan 2023 → | — | *(in existing CSV)* | — | ✓ |

Methodology note (rigor): HOSE reviews **constituents semi-annually** (effective 1st Mondays of Feb and Aug), but there were mid-cycle free-float/cap re-adjustments (e.g. the Jan 2019 basket was re-adjusted effective 06/05/2019, trimming the Vingroup group cap). The panel therefore has two layers: semi-annual membership + quarterly capping/free-float (§3). Build the membership backbone first, add the quarterly layer second.

---

## 3. HOSE capping algorithm (the reliability crux)

From HOSE-Index Ground Rules v4.0 (English translation; the Vietnamese original prevails, and the extracted factor formula was garbled — verify before trusting the exact expression).

**Cap limits (§7.4–7.5):**
- Single stock: **10%**
- Related-stock group (parent + subsidiaries): **15%**
- Same-sector group (GICS Level 1): **40%**

**Weighting (§5.2):** Index = CMV / Divisor, where CMV = Σ(pᵢ · sᵢ · fᵢ · cᵢ) over constituents.
- pᵢ = price, sᵢ = index shares, fᵢ = rounded free-float ratio, cᵢ = capping factor.
- Divisor = total cap / base value; adjusted for non-price events (corporate actions) to keep the series continuous.

**Capping factor (§7.9, verify):** cᵢ = (Z / I) · (pᵢsᵢfᵢ) / Σⱼ(pⱼsⱼfⱼ), summed over the *uncapped* set J; Z = cap, I = total cap ratio of constituents under threshold.

**Iterative procedure (§7.8):**
1. Reduce any stock/group over its cap to the cap.
2. If that pushes another stock/group over threshold, repeat until all constituents are under threshold.
3. If a single stock inside a capped group still exceeds 10%, reallocate the excess proportionally to the other stocks in that group.

**Review cadence (§7.6, §7.10 — the wrinkle):** capping factors are reviewed **quarterly**, effective 1st Mondays of **Feb, May, Aug, Nov**, using data prior to the 3rd Wednesdays of Jan/Apr/Jul/Oct — and recomputed on constituent changes and corporate actions. So capping is quarterly even though membership is semi-annual.

**Free-float rounding:** <15% rounds to 1% steps; ≥15% rounds to 5% steps.

### Why this is the reliability crux
A naive "free-float market cap, 10% single-name clip" reconstruction will diverge from the published VN30 in exactly the periods where the **group caps bind** — the Vingroup bloc (VIC/VHM/VRE, 15%) through 2019–2021 and the financials bloc (40%) throughout. Single-name caps rarely bite (VIC peaked ~9.4% in 2021, under 10%); the group caps and their quarterly resets do. If the reconstruction skips group capping or holds caps fixed semi-annually, the index-tracking validation (§4) will fail — and that failure is the signal, not noise.

---

## 4. Reconstruction + validation design

### The validation gate (do this before any day-of-week analysis)
Reconstruct the basket and check it reproduces the real VN30 before trusting it.

- **Primary gate — daily return tracking.** Compute the reconstructed basket's daily *return* and compare to the published VN30 daily return. Target: correlation ≥ 0.99, mean abs daily return error within a few bp. This is the directly relevant test (the study consumes basket returns) and is robust to divisor/base-level choices, since the divisor is continuous across ordinary days.
- **Stronger secondary check — level tracking.** Reconstruct the index *level* and overlay it on published VN30 closes. Divergence localizes *when* the weights go wrong (expect it to light up on group-cap-binding quarters if capping is mis-implemented).
- Gate rule: no decomposition runs until the primary gate passes. A fail is a finding about the panel, to fix, not to work around.

### The decomposition (after the gate passes)
2×2 day-of-week overnight table, same filters as Level B (open_suspicious removed, |overnight|>7% removed, ordinary one-day nights):

| | Equal-weight | Free-float cap-weight |
|---|---|---|
| Current 30 | Level B (done) | isolates weighting |
| Point-in-time | isolates composition | **futures replica** |

- Recompute cap-weights **daily** within each period (don't freeze at reconstitution — NVL/PDR limit-down runs shift weight on specific weekdays, which is the exact signal under study).
- Bottom-right cell = what VN30F1M tracks. Compare its day-of-week table to the futures. Residual after composition + weighting are both accounted = futures-specific microstructure (ATC-auction pricing / basis / roll).

---

## 5. Claude Code build prompt

> **Task: build and validate a point-in-time VN30 panel, then run the 2×2 day-of-week decomposition.**
>
> Context: overnight-effect project. Level B used the fixed current 30 back to 2018 (equal-weighted); VN30F1M futures track the live point-in-time, free-float cap-weighted VN30. Composition bias is already ruled out as the Wednesday-discrepancy driver (tenure diagnostic). This step tests the remaining confounder — weighting — rigorously, by building the real point-in-time cap-weighted basket and validating it reproduces the published VN30 before drawing any conclusion.
>
> **Step 1 — Acquire membership + free-float, 2018–2026.**
> - Download the HOSE "CBTT Danh sách thành phần VN30" PDFs from the URLs in `pit-vn30-rebuild-spec.md` §1. For the 7 gap periods in §1, locate each URL first via the search recipe there, then download.
> - Put each PDF in its own empty directory; parse with the existing VN25 Script 1 parser (same document format). Extract per constituent: ticker, index shares, rounded free-float %, cap limit %. Watch the multi-line wrapped free-float header — align columns carefully.
> - Build `data/vn30_pit_membership.csv`: one row per (effective_period, ticker) with shares, free_float, cap_limit. Merge the 2018–2022 periods with the existing `vn30_freefloat_history.csv` (2023+). Reconcile the overlap exactly; log any mismatch.
> - Cross-check adds/removes against the timeline in §2. Print a diff of parsed vs expected membership per review; flag discrepancies for me rather than silently accepting.
>
> **Step 2 — Implement HOSE capping (spec in §3).** Single 10%, related-group 15%, same-sector (GICS L1) 40%, iterative per §7.8, factors recomputed quarterly (effective 1st Mondays Feb/May/Aug/Nov). Implement the iterative procedure; verify the factor formula against the Vietnamese ground rules if the English one misbehaves. You'll need a ticker→GICS-sector map and a related-group map (at minimum the Vingroup bloc VIC/VHM/VRE); build these explicitly and keep them in a readable file.
>
> **Step 3 — Reconstruct and VALIDATE (hard gate).** Reconstruct the VN30 from the panel (daily weights = pᵢsᵢfᵢcᵢ renormalized, membership rebalanced at each reconstitution, caps refreshed quarterly). Run the §4 validation: daily-return correlation and mean abs error vs the published VN30, plus a level overlay. **Report the tracking numbers and stop for my review. Do not proceed to Step 4 until the primary gate (corr ≥ 0.99) passes.** If it fails, localize by period and report which capping layer is responsible — don't patch around it.
>
> **Step 4 — 2×2 day-of-week decomposition (only after the gate passes).** Compute the day-of-week overnight table (Level B filters) for all four cells. Report composition effect (down a column), weighting effect (across a row), and the point-in-time cap-weighted cell vs the futures day-of-week table. State what's measured vs residual.
>
> Deliverables: `data/vn30_pit_membership.csv`, `src/pit_reconstruct.py`, `results/vn30_tracking_validation.csv` (+ level overlay plot), `results/pit_dayofweek_2x2.csv`. Flag every data-quality issue rather than smoothing it.

---

## 6. Risk register

1. **Group-cap omission** (most likely tolerance-buster): skip the 15%/40% group caps → reconstructed index over-weights Vingroup and financials, diverges 2019–2021. Mitigation: implement group capping; the level-overlay localizes it.
2. **Quarterly vs semi-annual capping**: holding caps fixed per half-year drifts within each quarter. Mitigation: refresh caps on the Feb/May/Aug/Nov cadence.
3. **Divisor / corporate actions**: dividends and issuance move the divisor; skipping them drifts the *level* on ex-dates (less impact on daily returns, which is why return-tracking is the primary gate). Mitigation: for returns, this mostly cancels; for the level check, expect small ex-date steps.
4. **Formula provenance**: the capping-factor expression is from a garbled English translation. Mitigation: verify against the Vietnamese original before trusting exact numbers.
5. **Gap-period PDFs unlocatable**: Jan 2022 and a few 2018–2020 periods may not surface. Mitigation: §2 timeline fills composition; interpolate free-float from bracketing PDFs and flag those periods as lower-confidence.

Source base: HOSE CBTT disclosures and HOSE-Index Ground Rules v4.0 (both on static2.vietstock.vn); membership changes from VnEconomy, Nhadautu, Vietstock, KBSV/VNDIRECT review notes, 2018–2022.
