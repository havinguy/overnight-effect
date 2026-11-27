# Direct VCI fetcher validation (run 20261127T004647Z)

Script: `src/vci_direct_validate.py` (gate pre-registered in its header). Fetcher: `src/fetch_vci_direct.py`. vnstock (A/B only): 4.0.4.
Bars written to `data/raw_probe/vci_direct_20261127T004647Z/` only. Today (2026-11-27) excluded from every comparison.

## VERDICT: GATE FAIL

- G1 (direct vs frozen/data/raw, 100% field match, overlap >= 20): **FAIL**  -- **STOP: opens differ**
- G2 (same-run A/B vs vnstock 4.0.4 VCI, 34 symbols): **PASS**
- Integrity (sha256 of data/raw/ + frozen_20261117/, 63 files, before == after): **OK**

## Headers

Taken verbatim from the live wire capture in `results/vci_headers_captured.json`. vnstock 4.0.4 sends **no Device-Id**, no cookie and no auth header; its `_generate_vci_device_id()` is never called. What gets past the HTTP 400 that `source_probe.py` got is the browser UA plus the browser Accept/Sec-Fetch/sec-ch-ua headers.

## Symbol mapping

| repo symbol | VCI code | asset type | price scaling |
|---|---|---|---|
| VNINDEX | VNINDEX | index | none, round 2 |
| VN30 | VN30 | index | none, round 2 |
| VN30F1M | VN30F1M | derivative | none, round 2 |
| VN30F2M | VN30F2M | derivative | none, round 2 |
| stocks (3-letter) | same | stock | /1000, round 2 |

No code differences: index and futures codes pass through unchanged (confirmed by G2).

## G1: direct vs frozen reference

| symbol | ref | overlap | span | open | high | low | close | volume | flag agree | only direct | only ref |
|---|---|---|---|---|---|---|---|---|---|---|---|
| VN30F1M | frozen_20261117 | 34 | 2026-10-01..2026-11-17 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | - | - |
| VN30F1M | data/raw | 39 | 2026-10-01..2026-11-25 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | - | - |
| VN30F2M | frozen_20261117 | 34 | 2026-10-01..2026-11-17 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | - | - |
| VN30F2M | data/raw | 39 | 2026-10-01..2026-11-25 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | - | - |
| VN30 | data/raw | 34 | 2026-10-01..2026-11-17 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | - | - |
| VNINDEX | data/raw | 34 | 2026-10-01..2026-11-17 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | - | - |
| VCB | data/raw | 34 | 2026-10-01..2026-11-17 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | - | - |
| FPT | data/raw | 34 | 2026-10-01..2026-11-17 | 0.0% | 0.0% | 0.0% | 0.0% | 2.9% | 100.0% | - | - |
| HPG | data/raw | 34 | 2026-10-01..2026-11-17 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | - | - |

Mismatches:
- FPT vs data/raw: 2026-10-01 open: direct=61.58 ref=63.0
- FPT vs data/raw: 2026-10-02 open: direct=61.29 ref=62.7
- FPT vs data/raw: 2026-10-05 open: direct=60.8 ref=62.2
- FPT vs data/raw: 2026-10-06 open: direct=60.6 ref=62.0
- FPT vs data/raw: 2026-10-07 open: direct=59.04 ref=60.4
- FPT vs data/raw: 2026-10-08 open: direct=58.16 ref=59.5
- FPT vs data/raw: 2026-10-09 open: direct=58.36 ref=59.7
- FPT vs data/raw: 2026-10-12 open: direct=56.79 ref=58.1
- FPT vs data/raw: 2026-10-13 open: direct=55.82 ref=57.1
- FPT vs data/raw: 2026-10-14 open: direct=55.03 ref=56.3
- FPT vs data/raw: 2026-10-15 open: direct=56.21 ref=57.5
- FPT vs data/raw: 2026-10-16 open: direct=57.38 ref=58.7
- FPT vs data/raw: 2026-10-19 open: direct=57.28 ref=58.6
- FPT vs data/raw: 2026-10-20 open: direct=55.72 ref=57.0
- FPT vs data/raw: 2026-10-21 open: direct=56.99 ref=58.3
- FPT vs data/raw: 2026-10-22 open: direct=56.7 ref=58.0
- FPT vs data/raw: 2026-10-23 open: direct=55.91 ref=57.2
- FPT vs data/raw: 2026-10-26 open: direct=55.82 ref=57.1
- FPT vs data/raw: 2026-10-27 open: direct=54.74 ref=56.0
- FPT vs data/raw: 2026-10-28 open: direct=54.35 ref=55.6
- FPT vs data/raw: 2026-10-29 open: direct=53.27 ref=54.5
- FPT vs data/raw: 2026-10-30 open: direct=51.22 ref=52.4
- FPT vs data/raw: 2026-11-02 open: direct=51.22 ref=52.4
- FPT vs data/raw: 2026-11-03 open: direct=49.17 ref=50.3
- FPT vs data/raw: 2026-11-04 open: direct=49.46 ref=50.6
- FPT vs data/raw: 2026-11-05 open: direct=53.27 ref=54.5
- FPT vs data/raw: 2026-11-06 open: direct=50.24 ref=51.4
- FPT vs data/raw: 2026-11-09 open: direct=50.15 ref=51.3
- FPT vs data/raw: 2026-11-10 open: direct=50.44 ref=51.6
- FPT vs data/raw: 2026-11-11 open: direct=49.85 ref=51.0
- FPT vs data/raw: 2026-11-12 open: direct=49.85 ref=51.0
- FPT vs data/raw: 2026-11-13 open: direct=48.39 ref=49.5
- FPT vs data/raw: 2026-11-16 open: direct=48.88 ref=50.0
- FPT vs data/raw: 2026-11-17 open: direct=48.29 ref=49.4
- FPT vs data/raw: 2026-10-01 high: direct=61.68 ref=63.1
- FPT vs data/raw: 2026-10-02 high: direct=61.78 ref=63.2
- FPT vs data/raw: 2026-10-05 high: direct=61.39 ref=62.8
- FPT vs data/raw: 2026-10-06 high: direct=60.8 ref=62.2
- FPT vs data/raw: 2026-10-07 high: direct=59.92 ref=61.3
- FPT vs data/raw: 2026-10-08 high: direct=60.12 ref=61.5
- FPT vs data/raw: 2026-10-09 high: direct=58.65 ref=60.0
- FPT vs data/raw: 2026-10-12 high: direct=57.48 ref=58.8
- FPT vs data/raw: 2026-10-13 high: direct=56.11 ref=57.4
- FPT vs data/raw: 2026-10-14 high: direct=56.4 ref=57.7
- FPT vs data/raw: 2026-10-15 high: direct=56.89 ref=58.2
- FPT vs data/raw: 2026-10-16 high: direct=57.38 ref=58.7
- FPT vs data/raw: 2026-10-19 high: direct=57.28 ref=58.6
- FPT vs data/raw: 2026-10-20 high: direct=56.5 ref=57.8
- FPT vs data/raw: 2026-10-21 high: direct=56.99 ref=58.3
- FPT vs data/raw: 2026-10-22 high: direct=57.38 ref=58.7
- FPT vs data/raw: 2026-10-23 high: direct=55.91 ref=57.2
- FPT vs data/raw: 2026-10-26 high: direct=56.5 ref=57.8
- FPT vs data/raw: 2026-10-27 high: direct=54.94 ref=56.2
- FPT vs data/raw: 2026-10-28 high: direct=54.84 ref=56.1
- FPT vs data/raw: 2026-10-29 high: direct=53.57 ref=54.8
- FPT vs data/raw: 2026-10-30 high: direct=52.49 ref=53.7
- FPT vs data/raw: 2026-11-02 high: direct=51.32 ref=52.5
- FPT vs data/raw: 2026-11-03 high: direct=50.54 ref=51.7
- FPT vs data/raw: 2026-11-04 high: direct=52.69 ref=53.9
- FPT vs data/raw: 2026-11-05 high: direct=53.37 ref=54.6

## G2: same-run A/B vs vnstock 4.0.4 (all returned rows)

| symbol | direct rows | vnstock rows | overlap | open | high | low | close | volume | only direct | only vnstock |
|---|---|---|---|---|---|---|---|---|---|---|
| VN30F1M | 40 | 43 | 40 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | - | - |
| VN30F2M | 40 | 43 | 40 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | - | - |
| VN30 | 40 | 43 | 40 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | - | - |
| VNINDEX | 40 | 43 | 40 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | - | - |
| VCB | 40 | 43 | 40 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | - | - |
| FPT | 40 | 43 | 40 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | - | - |
| HPG | 40 | 43 | 40 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | - | - |
| ACB | 40 | 43 | 40 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | - | - |
| BID | 40 | 43 | 40 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | - | - |
| BSR | 40 | 43 | 40 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | - | - |
| CTG | 40 | 43 | 40 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | - | - |
| GAS | 40 | 43 | 40 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | - | - |
| GVR | 40 | 43 | 40 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | - | - |
| HDB | 40 | 43 | 40 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | - | - |
| LPB | 40 | 43 | 40 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | - | - |
| MBB | 40 | 43 | 40 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | - | - |
| MCH | 40 | 43 | 40 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | - | - |
| MSN | 40 | 43 | 40 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | - | - |
| MWG | 40 | 43 | 40 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | - | - |
| SAB | 40 | 43 | 40 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | - | - |
| SHB | 40 | 43 | 40 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | - | - |
| SSB | 40 | 43 | 40 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | - | - |
| SSI | 40 | 43 | 40 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | - | - |
| STB | 40 | 43 | 40 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | - | - |
| TCB | 40 | 43 | 40 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | - | - |
| TCX | 40 | 43 | 40 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | - | - |
| VHM | 40 | 43 | 40 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | - | - |
| VIB | 40 | 43 | 40 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | - | - |
| VIC | 40 | 43 | 40 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | - | - |
| VJC | 40 | 43 | 40 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | - | - |
| VNM | 40 | 43 | 40 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | - | - |
| VPB | 40 | 43 | 40 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | - | - |
| VPL | 40 | 43 | 40 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | - | - |
| VRE | 40 | 43 | 40 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | - | - |

A/B mismatches: none.

## Coverage notes

- 2026-11-24 in direct futures fetch: VN30F1M=absent, VN30F2M=absent (data/raw futures lack it; known feed gap).
- Fetch errors: none
## POST HOC diagnostics (added after the run; the verdict above is unchanged; wording revised after the fresh-reviewer pass)

- **FPT G1 mismatch: VCI revised FPT's history; the fetcher is not at fault.** On all 34 overlap rows, direct/raw price ratios are
  open 0.97742-0.97760, high 0.97741-0.97758, low 0.97741-0.97760, close 0.97741-0.97760. A single factor k ~ 0.97753 reproduces
  every overlapping price to within 0.01 (2-dp rounding), and vnstock's earlier rows 09-28..10-01 carry the same factor. That fits a
  corporate-action price back-adjustment with an ex-date between 2026-11-18 and 2026-11-27 (the run was ~07:46 HCM on 11-27).
  The ex-date and action type have NOT been checked against an HOSE/FPT disclosure.
- **FPT volumes were revised separately and the price adjustment does not explain them.** The direct/raw volume ratio is 1.000-1.011,
  varies day to day, and is exactly 1 on 10-01. The reviewer found that data/raw/FPT.csv volumes are all multiples of 100 from
  10-02 onward but not before, while every direct FPT volume is non-round-lot (VCB/HPG are round-lot on both sides). So
  data/raw/FPT.csv already has a volume-convention break between 10-01 and 10-02. Cause unknown.
- vnstock 4.0.4 returns the same revised values in this run (G2 FPT 100%), so data/raw/FPT.csv would no longer match a fresh vnstock pull either.
- Under the pre-registered rule this is still **GATE FAIL / STOP (opens differ)**. Step 4 (integration) was NOT done.
- Wider consequence for the existing pipeline (pre-existing, not caused by this fetcher): VCI stock prices are back-adjusted and can be
  revised retroactively. `fetch_indices.update` re-downloads only a 7-day overlap with keep='last'. An incremental stock refresh after
  an adjustment would therefore splice adjusted new rows onto unadjusted old rows, creating a false overnight gap at the splice and
  a wrong open_suspicious flag there. The 6 index/futures comparisons in G1 (VN30F1M x2, VN30F2M x2, VN30, VNINDEX) are exact on this
  7-week window, so the live futures logger shows no such revision here. That says nothing about futures revisions outside the window.
- G2 detail: vnstock sizes countBack from business days and ignores `start`, so it returned 3 rows before the direct window
  (2026-09-28..30). Every one of the 40 direct rows per symbol matched (overlap 40/40 for all 34 symbols), so G2 passes under the
  stricter REV 1 rule (overlap == direct rows) too. Run 0 fetched all direct bars first and the vnstock bars ~2 min later per symbol,
  not back-to-back as the header said. REV 1 interleaves them. Neither change was rerun, because the verdict cannot change: G1 fails on FPT.
- 2026-11-24 is absent from VCI itself (all 34 direct files), so the gap is not a vnstock artefact.
- Reviewer-driven fetcher edits after the run (none affect the validated symbols): removed VNI/HNX/UPCOM aliases, which vnstock 4.0.4 does
  not map that way; network errors, non-numeric and non-positive values now raise VCIDirectError.
