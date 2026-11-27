# Backend switch validation (run 20261127T034849Z)

Switch: `src/fetch_indices.py` sends VN30F1M, VN30F2M, VN30, VNINDEX (source VCI) to `src/fetch_vci_direct.py`; all other symbols stay on vnstock. Gate pre-registered in `src/backend_switch_validate.py`. Fetched files in `data/raw_probe/backend_switch_20261127T034849Z/`. Today (2026-11-27) excluded.

## VERDICT: GATE PASS  G1 PASS  G2 PASS  G3 PASS  G4 PASS

Rollback: `export OVERNIGHT_FETCH_BACKEND=vnstock` (or put it in the launchd job / scripts/weekly_refresh.sh) restores vnstock for every symbol with no code change. Full revert: remove the FETCH BACKEND SWITCH block in `src/fetch_indices.py` (backend_for / _download_vci_direct and the 4-line dispatch at the top of _download).

## G1: full-history refetch via the new backend vs references (today excluded)

| symbol | ref | fetched rows | overlap | span | open | high | low | close | volume | open_suspicious | only fetch | only ref |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| VN30F1M | data/raw | 2307 | 2306 | 2017-08-10..2026-11-25 | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% | 0  | 0  |
| VN30F1M | frozen_20261117 | 2307 | 2301 | 2017-08-10..2026-11-17 | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% | 0  | 0  |
| VN30F2M | data/raw | 2320 | 1997 | 2018-11-20..2026-11-25 | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% | 0  | 0  |
| VN30F2M | frozen_20261117 | 2320 | 1992 | 2018-11-20..2026-11-17 | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% | 0  | 0  |
| VN30 | data/raw | 3695 | 1994 | 2018-11-20..2026-11-17 | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% | 0  | 0  |
| VNINDEX | data/raw | 4150 | 3885 | 2011-04-28..2026-11-17 | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% | 0  | 0  |

Mismatches: none.

## G2: same-run A/B, new backend vs OVERNIGHT_FETCH_BACKEND=vnstock (output CSV bytes)

| symbol | direct rows | vnstock rows | vnstock first date | byte-identical | overlap | O/H/L/C/V/flag match | only vnstock | REV1 window pass |
|---|---|---|---|---|---|---|---|---|
| VN30F1M | 2307 | 2307 | 2017-08-10 | True | 2306 | 100/100/100/100/100/100% | 0 | True |
| VN30F2M | 2320 | 1991 | 2018-11-29 | False | 1990 | 100/100/100/100/100/100% | 0 | True |
| VN30 | 3695 | 1993 | 2018-11-29 | False | 1992 | 100/100/100/100/100/100% | 0 | True |
| VNINDEX | 4150 | 1993 | 2018-11-29 | False | 1992 | 100/100/100/100/100/100% | 0 | True |

## G3: track_forward dry runs in throwaway repo copies

copy       env  rc_norefresh  norefresh_identical  rc_refresh  backend_lines  backend_ok  boundary_same  rows_le_cap_unchanged                   rows_added  scorecard_same  guard
   D (default)             0                 True           0              2        True           True                   True {'VN30F1M': 1, 'VN30F2M': 1}            True passed
   V   vnstock             0                 True           0              2        True           True                   True {'VN30F1M': 1, 'VN30F2M': 1}            True passed

D vs V byte-identical after --refresh: {'VN30F1M': True, 'VN30F2M': True, 'log': True, 'scorecard': True}
Scorecard after --refresh: identical to live in both copies

## G4: integrity
67 protected files (data/raw/*, frozen_20261117/*, track_forward boundary/log/scorecard, src/track_forward.py): unchanged (sha256 before == after)

