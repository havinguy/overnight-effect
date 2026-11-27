# Fetch backend: rollback note (switch made 2026-11-27, uncommitted for review)

**What changed.** In `src/fetch_indices.py`, `_download` now sends **VN30F1M, VN30F2M, VN30, VNINDEX** (source `VCI`) to `src/fetch_vci_direct.py`, a direct VCI POST that sends the same request vnstock 4.0.4 sends. Every other symbol (all 3-letter stocks) and every other source still uses vnstock. Each fetch prints `[fetch] <SYM>: backend=...`. `track_forward.py` is unchanged; it reaches the switch through `update_with_retry`. Validation: `results/backend_switch_validation.md`.

**Rollback, no code change.** Set the environment variable `OVERNIGHT_FETCH_BACKEND=vnstock`:
- one run: `OVERNIGHT_FETCH_BACKEND=vnstock python3 src/track_forward.py --refresh`
- the weekly launchd job: add `export OVERNIGHT_FETCH_BACKEND=vnstock` after the other `export` lines in `scripts/weekly_refresh.sh`.

**Full revert.** `git checkout src/fetch_indices.py` (the only modified tracked file), or delete the `FETCH BACKEND SWITCH` block and the 4-line dispatch at the top of `_download`.

**Caveat found during validation.** vnstock 4.0.4 now caps 1D history at 8 years (community tier). A `--full` refetch through vnstock would start 2018-11-29 for VN30F2M/VN30/VNINDEX. Incremental refreshes (7-day overlap) are unaffected on either backend.
