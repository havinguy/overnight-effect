# Data

## What is committed

- `vn30_pit_membership.csv` — point-in-time VN30 membership (our compiled panel).
- `vn30_sector_groups.csv` — sector/related-group map used by the capping logic.
- `universe_vn30.txt` — the ticker universe.

These are our own compiled reference data and are safe to share.

## What is NOT committed (fetch it yourself)

Raw daily OHLC for the indices (VN-Index, VN30), the VN30 constituents, and the
VN30F1M / VN30F2M futures is sourced via the [`vnstock`](https://github.com/thinh-vu/vnstock)
library (VCI and KBS providers). It is not redistributed here for size and
vendor-terms reasons.

To rebuild `data/raw/`:

```bash
pip install -r requirements.txt
python src/fetch_indices.py       # VN-Index, VN30, VN30F1M/F2M daily OHLC
python src/fetch_constituents.py  # VN30 member daily OHLC
```

Notes:
- The VCI community source caps history at ~8 years (stocks/VN30 from 2018-11-21); VN-Index reaches back to 2011-04.
- `vnstock` announced (2026) that its v4/v5 free API is being retired in favour of broker-account Open APIs. If the fetch fails, you will need a supported data source. The analysis in this repo was run against data frozen at 2026-11-17 (hash-verified snapshots, not committed).
- Some opens in the vendor feed equal the prior close ("flat opens"); see `src/open_filter_audit.py` and `results/open_audit_summary.md` for how these are flagged and handled.
