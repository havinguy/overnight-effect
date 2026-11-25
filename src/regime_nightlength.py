"""Regime break (pre/post 2022-08-25) of the PIT-basket legs by NIGHT LENGTH. Measurement only; reads data/raw, writes only regime_nightlength* in results/.
Does not touch data/raw, the boundary, or the logger source.

WHY: level_a_robustness Test 1b (post hoc) found the post-weekend intraday session at about -28 bp (CW basket). The C4/C5 relocation (ON up, ID down at
2022-08-25) was estimated on one-day nights in regime_legs / level_b_rebuild, but the all-nights version mixes in weekend nights. This audit asks whether
the relocation holds on one-day nights and whether the ID side lives only in post-weekend sessions.

DEFINITIONS (fixed before the first run)
- Basket: PIT VN30 basket, CW (primary) and EW (check), from level_a_robustness.basket_legs(): pit_dayofweek_2x2 weights (variant B), >= 10 names,
  a stock's night counts if its previous row is the previous VNINDEX trading day. Unfiltered (flat opens kept). 2018-11-21 onward.
- Legs per date: ON, ID (log), C2C = ON + ID.
- Night length = calendar days since the previous VNINDEX trading day: (a) one-day = 1; (b) post-weekend = 3 (Fri close -> Mon open, Mon session).
  Also reported, descriptive only: all nights, and other multi-day (holidays).
- Regimes: pre = date < 2022-08-25, post = date >= 2022-08-25.
- Inference: NW (Bartlett) lag 5 SE per regime; break = post - pre; break t = break / hypot(SE_pre, SE_post); 95% CI = break +/- 1.96 hypot(SE).
  Weekend series are weekly, so lag 5 spans ~5 weeks there. Report-only: difference of breaks (weekend minus one-day), t = diff / hypot(SE_breaks).
- Low power flag: any regime side with n < 150 nights is tagged LOW N (reported; the verdict still reads the pre-registered rule).

PRE-REGISTERED READ (CW primary; EW reported as agreement check, does not change the verdict)
 V1 RELOCATION STANDS if on one-day nights the ON break > 0 with t > 2 AND the ID break < 0 with t < -2.
 V2 ID SIDE WEEKEND-ONLY -> downgrade C4/C5 wording: one-day ID break NOT (< 0 with t < -2) AND post-weekend ID break < 0 with t < -2.
 V3 ID SIDE NOT LOCATED -> downgrade C4/C5 wording: one-day ID not significant and post-weekend ID not significant either (the pooled ID break
    exists, but cannot be pinned to a night type).
 V4 ON SIDE FAILS on one-day nights (not > 0 with t > 2) -> downgrade C4 ON wording, whatever ID does.
 The C2C break is reported for each night type; no verdict.
 Results are registered as they come out; no reinterpretation of the rule in this run.
RERUN 1 (after reviewer; run-0 md kept as regime_nightlength_run0.md; no change to the estimates or V1-V2/V4 logic), labelled:
 (a) MDE80 = 2.80 x break SE added per cell, plus a power line; (b) the project's earlier n < 250 tag (level_a_robustness) shown beside the < 150 flag;
 (c) V3 code aligned to its header wording: fires when neither ID break has |t| >= 2 (run 0 also fired on a significantly positive ID break; did not
 matter); if no V-rule fires, that is printed; (d) integrity hash taken after the md is written; (e) calendar read from data/raw/VNINDEX.csv directly.
Usage: python3 src/regime_nightlength.py
"""
from __future__ import annotations
import sys, io, math, hashlib, contextlib
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent)); sys.path.insert(0, ".")
import numpy as np, pandas as pd
with contextlib.redirect_stdout(io.StringIO()):
    import level_a_robustness as LA

ROOT = Path(__file__).resolve().parent.parent; OUT = ROOT / "results"; NAME = "regime_nightlength"
CUT = pd.Timestamp("2022-08-25"); LAG = 5
OUTS = {f"{NAME}.md", f"{NAME}_breaks.csv", f"{NAME}_break_diffs.csv"}


def hash_tree():
    h = {}
    for d in (ROOT / "data" / "raw", OUT):
        for p in sorted(d.glob("*")):
            if p.is_file(): h[str(p)] = hashlib.sha256(p.read_bytes()).hexdigest()
    return h


def nw_se(x, L=LAG):
    x = pd.Series(x).dropna().values.astype(float); n = len(x); u = x - x.mean(); lrv = u @ u / n
    for l in range(1, min(L, n - 1) + 1): lrv += 2 * (1 - l / (L + 1)) * (u[l:] @ u[:-l]) / n
    return math.sqrt(max(lrv, 0) / n)


def brk(s):
    a, b = s[s.index < CUT].dropna(), s[s.index >= CUT].dropna()
    sa, sb = nw_se(a), nw_se(b); d = b.mean() - a.mean(); se = math.hypot(sa, sb)
    return dict(n_pre=len(a), n_post=len(b), pre_bp=a.mean() * 1e4, pre_t=a.mean() / sa, post_bp=b.mean() * 1e4, post_t=b.mean() / sb,
                break_bp=d * 1e4, break_se_bp=se * 1e4, break_t=d / se, lo95=(d - 1.96 * se) * 1e4, hi95=(d + 1.96 * se) * 1e4,
                low_n=bool(min(len(a), len(b)) < 150), lt250=bool(min(len(a), len(b)) < 250), mde80_bp=2.80 * se * 1e4)


def main():
    H0 = hash_tree()
    cal = pd.DatetimeIndex(pd.read_csv(ROOT / "data" / "raw" / "VNINDEX.csv", parse_dates=["date"]).date.sort_values().values)
    B = LA.basket_legs(pd.DatetimeIndex(cal))
    rows = []
    for sch in ("CW", "EW"):
        d = B[sch].copy(); d["C2C"] = d.ON + d.ID
        for night, m in (("one-day", d.gap == 1), ("post-weekend", d.gap == 3), ("all nights", d.gap.notna()), ("other multi-day", (d.gap != 1) & (d.gap != 3))):
            for leg in ("ON", "ID", "C2C"):
                rows.append(dict(scheme=sch, night=night, leg=leg, **brk(d.loc[m, leg])))
    T = pd.DataFrame(rows)
    # report-only: weekend break minus one-day break
    D = []
    for sch in ("CW", "EW"):
        for leg in ("ON", "ID", "C2C"):
            w = T[(T.scheme == sch) & (T.night == "post-weekend") & (T.leg == leg)].iloc[0]; o = T[(T.scheme == sch) & (T.night == "one-day") & (T.leg == leg)].iloc[0]
            dd = w.break_bp - o.break_bp; se = math.hypot(w.break_se_bp, o.break_se_bp)
            D.append(dict(scheme=sch, leg=leg, weekend_break_bp=w.break_bp, oneday_break_bp=o.break_bp, diff_bp=dd, diff_t=dd / se))
    D = pd.DataFrame(D)
    g = lambda sch, night, leg: T[(T.scheme == sch) & (T.night == night) & (T.leg == leg)].iloc[0]
    def verdict(sch):
        on1, id1, idw = g(sch, "one-day", "ON"), g(sch, "one-day", "ID"), g(sch, "post-weekend", "ID")
        on_ok = on1.break_bp > 0 and on1.break_t > 2; id1_ok = id1.break_bp < 0 and id1.break_t < -2; idw_ok = idw.break_bp < 0 and idw.break_t < -2
        v = []
        if on_ok and id1_ok: v.append("V1 RELOCATION STANDS on one-day nights")
        if not id1_ok and idw_ok: v.append("V2 ID SIDE WEEKEND-ONLY: downgrade C4/C5 wording")
        if abs(id1.break_t) < 2 and abs(idw.break_t) < 2: v.append("V3 ID SIDE NOT LOCATED by night type: downgrade C4/C5 wording")
        if not on_ok: v.append("V4 ON SIDE FAILS on one-day nights: downgrade C4 ON wording")
        return ("; ".join(v) or "no V-rule fired"), dict(on1_t=on1.break_t, id1_t=id1.break_t, idw_t=idw.break_t)
    vc, kc = verdict("CW"); ve, ke = verdict("EW")
    T.to_csv(OUT / f"{NAME}_breaks.csv", index=False); D.to_csv(OUT / f"{NAME}_break_diffs.csv", index=False)
    f = lambda X: X.to_string(index=False, float_format=lambda v: f"{v:.2f}")
    r = lambda sch, night, leg: (lambda x: f"{x.break_bp:+.2f} bp (t {x.break_t:.2f}, CI {x.lo95:.1f}..{x.hi95:.1f}; n {x.n_pre}/{x.n_post})")(g(sch, night, leg))
    pw = g("CW", "post-weekend", "ID"); od = g("CW", "one-day", "ID")
    from math import erf
    Phi = lambda z: 0.5 * (1 + erf(z / math.sqrt(2)))
    power = Phi(abs(od.break_bp) / pw.break_se_bp - 1.96)
    power_line = (f"Power (rerun 1): post-weekend CW ID break SE {pw.break_se_bp:.1f} bp, MDE80 {pw.mde80_bp:.1f} bp; power to detect a break of the one-day size "
                  f"({od.break_bp:.1f} bp) about {power*100:.0f}%. The post-weekend cells therefore cannot distinguish 'no weekend break' from 'the same break on weekends'; "
                  f"V2 could only fire for a weekend ID break below about {-1.96*pw.break_se_bp:.1f} bp. Post-weekend cells have n 179/201 (< 250 under the earlier project rule).")
    L = [f"# Regime break by night length, PIT basket (src/{NAME}.py)", "", "Definitions and the verdict rule were pre-registered in the script header before the first run. bp per night; NW lag 5.", "",
         "## Break table (post 2022-08-25 minus pre)", "", "```", f(T), "```", "",
         "## Report-only: post-weekend break minus one-day break", "", "```", f(D), "```", "",
         f"Verdict (CW, primary): {vc}.", f"Agreement check (EW): {ve}.", "", power_line, "",
         "Reading: the post-weekend intraday drop is present in both regimes (a level in each); whether the post-weekend session also relocates at 2022-08-25 is undetermined.", "",
         "## Summary (5 lines)", "",
         f"1. One-day nights, CW: ON {r('CW','one-day','ON')}; ID {r('CW','one-day','ID')}; C2C {r('CW','one-day','C2C')}.",
         f"2. Post-weekend nights, CW: ON {r('CW','post-weekend','ON')}; ID {r('CW','post-weekend','ID')}; C2C {r('CW','post-weekend','C2C')}.",
         f"3. EW check: one-day ON {r('EW','one-day','ON')}, ID {r('EW','one-day','ID')}; post-weekend ID {r('EW','post-weekend','ID')}.",
         f"4. Verdict CW: {vc}. EW: {ve}.",
         f"5. Weekend-minus-one-day break difference (report only), CW: " + "; ".join(f"{x.leg} {x.diff_bp:+.2f} bp (t {x.diff_t:.2f})" for _, x in D[D.scheme == 'CW'].iterrows()) + "."]
    (OUT / f"{NAME}.md").write_text("\n".join(L) + "\n")
    H1 = hash_tree(); changed = [k for k in H1 if k in H0 and H0[k] != H1[k] and Path(k).name not in OUTS]
    integrity = not changed and all(Path(k).name in OUTS for k in H1 if k not in H0)
    with open(OUT / f"{NAME}.md", "a") as fh: fh.write(f"\nIntegrity (checked after all writes; no existing file changed, only {NAME}* written): {integrity}\n")
    print("\n".join(L)); print("Integrity:", integrity); assert integrity


if __name__ == "__main__":
    main()
