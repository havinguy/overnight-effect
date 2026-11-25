# Source probe: notes and recommendation (2026-11-25; companion to results/source_probe.md, run 20261125T202737Z/)

Installed: vnstock 4.0.4 (pip). It still works today, but it prints a notice (Vietnamese) that generation 4/5 stops and generation 6 will need
"the free API of the securities company where you have an account, or self-prepared data files".

| Source | Works now? | Last-10-session match vs data/raw | 2026-11-24 | Terms-of-use / stability risk (one line) |
|---|---|---|---|---|
| P0 newer vnstock (v6 / free key) | not tested | n/a | n/a | PyPI returns 404 for vnstock (JSON and simple index) today; key registration is at vnstocks.com/login and v6 needs a broker API account: credential => branch stopped (HARD STOP). |
| P1 vnstock 4.0.4 -> VCI (current logger path) | yes, all 4 symbols | 100% on O/H/L/C/V for VN30F1M (10 sessions), 41I1GC000 vs the earlier VCI file (10), VN30 and VNINDEX (5 overlapping sessions; data/raw indices end 2026-11-17). This is SELF-CONSISTENCY (data/raw was written by the same path), i.e. stability, not accuracy. Graded 'NOT replacement-grade' by the pre-registered rule only because it returns no bar after data/raw's last date (data/raw is already current from this source); 41I1GC000 was left out of the grading by the code | absent | Announced sunset of v4/v5 (from 2026-11-10, Decree 363/2026); can stop without notice; VCI endpoint is a broker's undocumented web API. |
| P2 direct VCI gap-chart POST, honest headers | no: HTTP 400 for all 4 symbols | n/a | n/a | vnstock reaches it with browser-impersonating headers (random Device-Id); payload, Referer and Origin were identical to vnstock's, so the User-Agent or Device-Id is the likely cause, not isolated; I did not impersonate. Undocumented endpoint, no published terms for programmatic use. |
| P3 vnstock 4.0.4 -> KBS | yes, but | 'VN30F1M' is a different (fixed) contract: 30% match; on 41I1GC000: H/L/C/V 100%, open 20% (opens rounded); VN30/VNINDEX: close 100%, volume 0% (different volume units), high 40-60% | absent; KBS also lacks 2026-11-23 on 41I1GC000 | Same vnstock v4 path, so it dies with P1; refuses most recent contract codes (earlier audit). |

Intraday: vnstock VCI 1-minute VN30F1M history is served back to at least 2024-05-31 in this probe (request for 2022-03 failed: RetryError); the earlier cached probe (results/intraday_probe.md) already holds VCI 1-minute bars from 2023-09-11 (795 days). Recorded in PARKED.md, not pursued.

Recommendation (probe statement, not an adoption): keep the logger on vnstock 4.0.4 -> VCI while it works (P1 is self-consistent on every field), and keep the
snapshot + old-row check (now in src/track_forward.py) as the guard. None of the credential-free alternatives probed can replace it: P2 refuses
honest requests, P3 is the same library and not field-exact. Continuity after the sunset needs one of: (a) a broker API account and key (your
choice of broker; credentials; may cost money), (b) an official exchange data product or manually downloaded files from HOSE/HNX, or
(c) accepting the end of the forward track when v4 stops. All three are your decision (HARD STOP).
