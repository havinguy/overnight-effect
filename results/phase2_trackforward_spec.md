# Phase 2 track-forward spec: VN30F1M Monday overnight

**Status: candidate to TRACK, not to trade.** The backtest is a robustness check, not pristine OOS: the Monday/Mon+Tue signal was chosen after seeing the full sample. Its only legitimacy comes from freezing the definition below now and recording live results forward. Do not edit the rule after the first live night.

## Frozen signal
- Instrument: VN30F1M (front month).
- Entry: Monday ATC close (entry-close weekday = Monday). Exit: next trading day (Tuesday) ATO open. 1x notional, flat each morning.
- Only ordinary one-day nights: skip if Tuesday is not the next trading day (Monday holiday-adjacent gaps, Tuesday holiday). Skip if Monday is not a trading day.
- Roll handling (as in the backtest): if Tuesday is a roll day (first trading day after the 3rd-Thursday expiry), enter in the contract that becomes front month (F2M) at Monday ATC, so the roll basis is not booked. Tag these nights `is_roll=1` and report them separately.
- Secondary (shadow only, do not trade on it): Mon+Tue, logged by the same procedure for Tuesday-entry nights.

## Base cost assumption being tested
- Broker fee 12,500 VND per contract per side + slippage 1.0 bp per side (about 4.4 bp round trip all-in at typical prices); roll nights +5 bp placeholder.
- Historical Monday result at this cost: gross 10.6 bp, **net ~6.4 bp/night**, net Sharpe 0.91, t 2.78, n 453 (2017-2026).
- Breakeven slippage (fee 12,500): **4.2 bp per side**. Cost headroom is large; the slippage assumption is not the main risk, the stability of the gross edge is.

## What to log, every Monday (including skipped ones, with reason)
| Field | Meaning |
|---|---|
| date_entry, date_exit | Monday, Tuesday |
| contract | F1M or F2M ticker, is_roll flag |
| signal_ref_close | official VN30F1M ATC close (reference, from data feed) |
| fill_entry | actual fill price at ATC |
| signal_ref_open | official ATO open price |
| fill_exit | actual fill price at ATO |
| fees_vnd | actual fees paid, both legs |
| realized_gross_bp | ln or simple (fill_exit/fill_entry - 1) before fees |
| realized_net_bp | after actual fees |
| ref_net_bp | same night computed from reference prices with assumed costs (12,500 VND + 1 bp/side) |
| slippage_bp_per_side | (|fill - reference|, signed against us) per leg; compare to assumed 1.0 |
| skipped / reason | holiday gap, no fill, etc. |

## Running metrics (update weekly)
1. Cumulative realized net bp vs the ~6.4 bp historical mean; running mean, SD, t-stat, net Sharpe (annualised by n / calendar years).
2. Realized vs assumed slippage: mean per-side slippage with CI. Alarm if mean > 2.5 bp per side (headroom would be roughly half gone), stop if > 4.2 bp (edge gone).
3. Cumulative equity and max drawdown; hit rate.
4. Reference-price net bp vs realized net bp (execution shortfall).

## Sample-size targets
Historical per-night SD of Monday net return is about 49 bp, so the mean is noisy: SE of the mean is 49/sqrt(n) bp.
- **~30 Mondays (~7 months):** enough to check **execution and slippage** (slippage SD per leg is far smaller than return SD). Decision: is realized cost within the 1 bp/side assumption? This is the first gate before any capital.
- **~100 Mondays (~2 years):** SE of mean ~4.9 bp; can only reject "edge is zero or negative" if the true mean is large (a mean of 6.4 bp gives t ~1.3). Interim review, not decision-grade for return.
- **~235 Mondays (~4.5 years):** t >= 2 if the live mean equals the historical 6.4 bp. **Decision-grade for return.**
- If the true edge is closer to the 2022-2025 level (3.5 bp), roughly 1,500 Mondays are needed for 80% power, which is not achievable. So live tracking can validate execution and catch a collapse, but cannot prove a small edge within a practical time.

Pre-registered kill rule: after 100 Mondays, if realized net mean < 0 or mean slippage > 4 bp per side, drop the candidate.

## Caveats carried into the track
- Idea formed after seeing the full sample; the IS/OOS split is a robustness check, not a pristine test.
- OOS-proper (2022-2025, ex-2026) Monday net 3.6 bp, Sharpe 0.79, t 1.57: positive but not significant; the full-sample figure is pulled up by 2026 (18.4 bp over 43 nights, t 1.98). Mon+Tue is weaker ex-2026 (2.2 bp, t 0.92).
- Backtest has no financing, margin, or market-impact costs; 1 bp/side slippage is an assumption, which this tracking is meant to test.

## How to run (weekly operating procedure)
1. Each week, **after Tuesday's open** (the ATO print must be in the feed), run
   `python3 src/track_forward.py --refresh`. This pulls new VN30F1M and VN30F2M bars from vnstock via
   `fetch_indices.update_with_retry` (the same incremental fetcher / CSV schema as `data/raw/VN30F1M.csv`),
   then rebuilds `results/track_forward_log.csv` and `results/track_forward_scorecard.csv`. The new night is
   picked up automatically. Without `--refresh` the script runs off the cached CSV.
2. The log is rebuilt from source on every run (keyed on `tuesday_date`), so re-running never double-counts.
   Manually entered `realized_*` / `note` values are preserved across rebuilds.
3. If you actually traded the night, fill `realized_entry`, `realized_exit`, `realized_fee_bp`,
   `realized_slip_bp` (bp of notional per side) and `realized_net_bp` in the log. Where `realized_net_bp`
   is present the scorecard uses it instead of `modeled_net_bp`. Never edit the modeled columns.
4. `results/track_forward_boundary.txt` is the frozen end of the in-sample backtest. Never edit or delete it:
   only Tuesdays strictly after it are forward observations.
5. Weeks where Monday or Tuesday was a holiday are logged `skipped_hold` and excluded from the scorecard,
   as in the backtest. Check the printed scorecard against the kill rule: n>=30 flag slippage > 1.5 bp/side;
   n>=100 KILL if net mean < 0 or mean slippage > 4 bp/side; decision-grade at 235 Mondays.
