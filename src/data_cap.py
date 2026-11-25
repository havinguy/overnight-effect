"""Single data cap for the analysis scripts (added 2026-11-25).

DATA_CAP = 2026-11-17, the frozen forward boundary (results/track_forward_boundary.txt).
Analysis scripts read the futures files (VN30F1M, VN30F2M, VN30F1M_repaired) from the frozen snapshot
data/snapshots/frozen_20261117/, never from data/raw/, which only the forward logger appends to.

LIVE MODE: when the entry point is src/track_forward.py (or OVERNIGHT_LIVE=1 is set), the futures files
resolve to data/raw/ so the logger keeps seeing new bars. Launching the logger in any other way (a wrapper,
`python -m`, an import) reads the FROZEN files and the logger would silently stop seeing new bars.
OVERRIDE maps a file name to an explicit path, for wrappers that rerun logic against a candidate file.
Every other raw file (stocks, indices) keeps resolving to data/raw/; none of them extends past DATA_CAP.
No project imports here.
"""
from __future__ import annotations
import os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
DATA_CAP = "2026-11-17"
FROZEN_DIR = ROOT / "data" / "snapshots" / "frozen_20261117"
CAPPED = ("VN30F1M", "VN30F2M", "VN30F1M_repaired")
OVERRIDE: dict[str, Path] = {}
_checked: set[str] = set()


def live() -> bool:
    main = sys.modules.get("__main__")
    return Path(getattr(main, "__file__", "") or "").name == "track_forward.py" or os.environ.get("OVERNIGHT_LIVE") == "1"


def futures_csv(name: str) -> Path:
    if name in OVERRIDE:
        return Path(OVERRIDE[name])
    if name in CAPPED and not live():
        p = FROZEN_DIR / f"{name}.csv"
        if name not in _checked:                       # frozen files must end exactly at DATA_CAP
            last = p.read_text().rstrip("\n").rsplit("\n", 1)[-1].split(",", 1)[0]
            assert last == DATA_CAP, f"{p} ends {last}, expected DATA_CAP {DATA_CAP}"
            _checked.add(name)
        return p
    return RAW_DIR / f"{name}.csv"
