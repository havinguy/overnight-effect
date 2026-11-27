"""ATC-drift test: does the VN30F1M closing auction (14:30-14:45) price in overnight drift? MEASUREMENT ONLY.

The pre-registration (predictions P1-P3, verdict rule, competing hypothesis B, gate, power statement) is in
results/atc_drift_summary.md above the '<!-- RESULTS BELOW' marker. It was written before this script was run, and the
script keeps it verbatim. It only regenerates the part below the marker.

Reads only cached intraday bars in data/raw_intraday/ (no fetching), the frozen daily futures via data_cap, and data/raw/VN30.csv.
Every sample is capped at data_cap.DATA_CAP (2026-11-17).
Writes only results/atc_drift_nights.csv, results/atc_drift_tests.csv and results/atc_drift_summary.md (below the marker).
Reuses futures_basis_followup: load_bars, price_at, hac, ols_ak, weekday_test, CATS; futures_basis_decomp: futures_nights, panel, nw_t.
Usage: python3 src/atc_drift_test.py
"""
from __future__ import annotations
import hashlib, math, sys, warnings
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import futures_basis_decomp as FB
from futures_basis_decomp import nw_t
from futures_basis_followup import load_bars, price_at, hac, ols_ak, weekday_test, CATS, IDIR
from data_cap import DATA_CAP, FROZEN_DIR, RAW_DIR

ROOT = Path(__file__).resolve().parent.parent; OUT = ROOT / "results"
MD = OUT / "atc_drift_summary.md"; MARK = "<!-- RESULTS BELOW (generated) -->"
CAP = pd.Timestamp(DATA_CAP)
GATE = dict(n=782, mean_bp=5.597, t=3.535, tol=0.0005)                  # 2.2a row "2023-09-11 onward, all nights, 09:00"
BONF = 2.576; MDE_K = 1.96 + 0.8416; POWER_BP = 10.0


# ------------------------------------------------------------------ helpers
def nw_se(x):
    x = pd.Series(x).dropna(); t = nw_t(x)
    return abs(x.mean() / t) if (t and np.isfinite(t) and t != 0) else np.nan


def cell(x, **lab):
    x = pd.Series(x).dropna(); se = nw_se(x)
    return dict(**lab, n=len(x), mean_bp=x.mean() * 1e4 if len(x) else np.nan, t=nw_t(x),
                se_bp=se * 1e4, mde80_bp=MDE_K * se * 1e4, power_limited=bool(MDE_K * se * 1e4 > POWER_BP) if np.isfinite(se) else True)


def close_at(x: pd.DataFrame, h: str, before: str) -> tuple[pd.Series, pd.Series]:
    """close of the bar labelled h; if absent, last close of a bar with label < before. Returns (price, filled mask)."""
    c = x.pivot_table(index="date", columns="hm", values="close", aggfunc="last")
    v = c[h] if h in c.columns else pd.Series(np.nan, index=c.index)
    prior = c.loc[:, [k for k in c.columns if k < before]].ffill(axis=1).iloc[:, -1]
    return v.fillna(prior), (v.isna() & prior.notna())


def tree_hash():
    paths = [*sorted(RAW_DIR.glob("*")), *sorted(FROZEN_DIR.glob("*")), *sorted(IDIR.glob("*")),
             ROOT / "src" / "track_forward.py", OUT / "track_forward_boundary.txt"]
    return {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths if p.is_file()}


def fmt(df): return df.to_string(index=False, float_format=lambda v: f"{v:.3f}")


# ------------------------------------------------------------------ main
def main() -> int:
    H0 = tree_hash()
    pre = MD.read_text(); assert MARK in pre, "pre-registration marker missing in results/atc_drift_summary.md"
    pre = pre.split(MARK)[0] + MARK + "\n"

    f1 = load_bars("VCI", "VN30F1M", "1m"); i5 = load_bars("VCI", "VN30", "5m")
    f1 = f1[f1.date <= CAP]; i5 = i5[i5.date <= CAP]
    FP, ff_f = price_at(f1, ["09:00", "09:15", "09:30", "10:00"])
    C1429, fill1429 = close_at(f1, "14:29", "14:30")
    C1445 = f1[f1.hm == "14:45"].groupby("date").close.last().reindex(C1429.index)           # ATC bar only, no fallback
    IP, ff_i = price_at(i5, ["09:15", "09:30", "10:00"])
    I1425, ffi1425 = close_at(i5, "14:25", "14:30")
    I1445 = i5[i5.hm == "14:45"].groupby("date").close.last().reindex(I1425.index)

    fut = FB.futures_nights(); j = FB.panel(); j = j[j.aligned]
    assert fut.index.max() <= CAP and j.index.max() <= CAP

    # ---------------- STEP 2 gate: 2.2a night set and entry
    fv = fut[fut.invested & fut.index.isin(FP.index) & fut.index.isin(j.index)].copy()
    fv["on_atc"] = np.log(FP["09:00"].reindex(fv.index) / fv.entry)
    g = fv.on_atc.dropna(); gm, gt = g.mean() * 1e4, nw_t(g)
    gate_ok = len(g) == GATE["n"] and abs(gm - GATE["mean_bp"]) <= GATE["tol"] and abs(gt - GATE["t"]) <= GATE["tol"]
    fp = pd.read_csv(OUT / "futures_basis_followup_intraday.csv")
    fp = fp[(fp.period == "2023-09-11 onward (all intraday)") & (fp.subset == "all nights") & (fp.h == "09:00")].iloc[0]
    gate_ok = gate_ok and abs(gm - fp.mean_bp) < 1e-6 and abs(gt - fp.t) < 1e-4
    gate_line = (f"n {len(g)} (target {GATE['n']}), mean {gm:.6f} bp (target {GATE['mean_bp']}; full-precision 2.2a value {fp.mean_bp:.6f} from "
                 f"futures_basis_followup_intraday.csv, diff {gm - fp.mean_bp:.1e}), NW t {gt:.5f} (2.2a {fp.t:.5f}): {'PASS' if gate_ok else 'FAIL'}")
    # reconciliation of alternative cuts (diagnostic; explains a ~5.0 bp quick cut)
    E = fv.prev_date
    alt = []
    def add(lab, s): s = pd.Series(s).dropna(); alt.append(dict(cut=lab, n=len(s), mean_bp=s.mean() * 1e4, t=nw_t(s)))
    add("GATE: 2.2a set, entry = build() (F2M close on roll nights), exit 09:00 bar open", fv.on_atc)
    allinv = fut[fut.invested & fut.index.isin(FP.index)]
    add("+ misaligned nights kept (all invested futures nights with a 1m day)", np.log(FP["09:00"].reindex(allinv.index) / allinv.entry))
    add("entry = intraday 14:45 close of prior 1m day (no roll fix: crosses contracts on roll nights)",
        np.log(FP["09:00"].reindex(fv.index).values / C1445.reindex(E).values))
    days = FP.index[FP.index <= CAP]; prevday = pd.Series(days, index=days).shift(1)
    naive = np.log(FP["09:00"].reindex(days).values / C1445.reindex(prevday).values)
    add("naive: every consecutive 1m day pair, 14:45 close -> 09:00 open, no roll fix, no alignment", pd.Series(naive, index=days))
    add("GATE set but simple (not log) returns", FP["09:00"].reindex(fv.index) / fv.entry - 1)
    add("GATE set, exit = daily open instead of 09:00 bar", np.log(fv.open / fv.entry))
    add("GATE set ex roll nights", fv.on_atc[~fv.is_roll])
    ALT = pd.DataFrame(alt)
    if not gate_ok:
        MD.write_text(pre + "\n## STEP 2 GATE FAILED -- nothing else computed\n" + gate_line + "\n\n" + fmt(ALT) + "\n")
        print("GATE FAILED:", gate_line); print(fmt(ALT)); return 1

    # ---------------- legs per night
    fv["E"] = E
    fv["c1429"] = C1429.reindex(E).values; fv["c1445"] = C1445.reindex(E).values
    fv["daily_close_E"] = fut.close.reindex(E).values                    # F1M daily close on E (expiring contract on roll nights)
    fv["a"] = np.log(fv.c1445 / fv.c1429)
    fv["on_1429"] = np.log(FP["09:00"].reindex(fv.index) / fv.c1429)
    fv["expiry_day_auction"] = fv.is_roll                                 # E = expiry day <=> T = roll day
    fv["c1429_filled"] = fill1429.reindex(fv.E).fillna(False).values
    atc_eq_daily = np.isclose(fv.c1445, fv.daily_close_E, atol=0.051)
    nr = fv[~fv.is_roll]
    ident = (nr.on_1429 - nr.a - nr.on_atc).abs().max()
    T = []
    # ---------------- A: auction leg
    T.append(cell(fv.a, test="A", sample="all nights (full intraday sample, P1)"))
    T.append(cell(fv.a[~fv.is_roll], test="A", sample="ex expiry-day auctions"))
    T.append(cell(fv.a[fv.is_roll], test="A", sample="expiry-day auctions only (E = expiry, T = roll)"))
    for y in sorted(set(fv.index.year)): T.append(cell(fv.a[fv.index.year == y], test="A", sample=f"year {y}"))
    WA, JA = weekday_test(fv.a, fv.night)
    WA_ex, JA_ex = weekday_test(fv.a[~fv.is_roll], fv.night[~fv.is_roll])
    # ---------------- B: offset regression + decomposition
    REG = []
    for lab, s in [("non-roll nights (P2 primary)", nr), ("all nights", fv)]:
        o = ols_ak(s.on_atc, s.a)
        REG.append(dict(sample=lab, n=o["n"], intercept_bp=o["a_bp"], intercept_t=o["a_t"], slope=o["k"], slope_se=o["k_se"],
                        slope_t=o["k"] / o["k_se"], pearson_r=s[["on_atc", "a"]].dropna().corr().iloc[0, 1], r2=o["r2"]))
    REG = pd.DataFrame(REG)
    DEC = []
    for nm, s in [("all (non-roll)", nr)] + [(c, nr[nr.night == c]) for c in CATS]:
        m1429, ma, mo = s.on_1429.mean() * 1e4, s.a.mean() * 1e4, s.on_atc.mean() * 1e4
        DEC.append(dict(night=nm, n=len(s.dropna(subset=["a", "on_atc"])), on_1429_bp=m1429, t_on_1429=nw_t(s.on_1429), a_bp=ma, t_a=nw_t(s.a),
                        on_atc_bp=mo, t_on_atc=nw_t(s.on_atc), share_a=ma / m1429 if m1429 else np.nan))
    DEC = pd.DataFrame(DEC)
    # ---------------- C: matched auction, 1-yr window
    w = fv[fv.E.isin(I1425.index) & fv.E.isin(I1445.dropna().index)].copy()
    w["idx_leg"] = np.log(I1445.reindex(w.E).values / I1425.reindex(w.E).values)
    w["dleg"] = w.a - w.idx_leg
    idx_close_chk = np.isclose(I1445.reindex(w.E).values, j.prev_close.reindex(w.index).values, atol=0.051).mean()
    CC = []
    for nm, s in [("all", w)] + [(c, w[w.night == c]) for c in CATS]:
        for v in ["a", "idx_leg", "dleg"]:
            CC.append(cell(s[v], test="C", night=nm, leg={"a": "futures auction leg a", "idx_leg": "index auction leg (14:25 close -> 14:45 close)", "dleg": "futures - index"}[v]))
    CC = pd.DataFrame(CC)
    WC, JC = weekday_test(w.dleg, w.night)
    # ---------------- D: competing hypothesis B, index open overshoot (1-yr window)
    d = fv[fv.index.isin(IP.index)].copy()
    d["idx_ON"] = j.idx_ON.reindex(d.index); sg = np.sign(d.idx_ON)
    d["fut_ON_atc"] = d.on_atc
    DD = []
    for h in ["09:30", "10:00"]:
        d[f"idrift_{h}"] = np.log(IP[h].reindex(d.index) / IP["09:15"].reindex(d.index))
        d[f"fdrift_{h}"] = np.log(FP[h].reindex(d.index) / FP["09:15"].reindex(d.index))
        d[f"irev_{h}"] = -sg * d[f"idrift_{h}"]; d[f"frev_{h}"] = -sg * d[f"fdrift_{h}"]
    for nm, s in [("all", d), ("Wed->Thu", d[d.night == "Wed->Thu"])]:
        DD.append(cell(s.idx_ON, test="D", night=nm, stat="index ON (prior close -> 09:15 open)"))
        DD.append(cell(s.fut_ON_atc, test="D", night=nm, stat="futures ON (prior ATC -> 09:00)"))
        for h in ["09:30", "10:00"]:
            DD.append(cell(s[f"idrift_{h}"], test="D", night=nm, stat=f"index drift 09:15->{h}"))
            DD.append(cell(s[f"fdrift_{h}"], test="D", night=nm, stat=f"futures drift 09:15->{h}"))
            DD.append(cell(s[f"irev_{h}"], test="D", night=nm, stat=f"index symmetric revert -sign(idxON)*drift 09:15->{h}"))
            DD.append(cell(s[f"frev_{h}"], test="D", night=nm, stat=f"futures counterpart -sign(idxON)*drift 09:15->{h}"))
    DD = pd.DataFrame(DD)
    SL = []
    for h in ["09:30", "10:00"]:
        for who in ["idrift", "fdrift"]:
            o = ols_ak(d[f"{who}_{h}"], d.idx_ON)
            SL.append(dict(y=f"{'index' if who == 'idrift' else 'futures'} drift 09:15->{h}", x="idx_ON", n=o["n"], slope=o["k"], slope_t=o["k"] / o["k_se"],
                           intercept_bp=o["a_bp"], intercept_t=o["a_t"]))
    SL = pd.DataFrame(SL)

    # ---------------- verdicts (pre-registered rule)
    pA = T[0]; p1 = pA["mean_bp"] > 0 and pA["t"] > 2
    r0 = REG.iloc[0]; p2 = r0.slope < 0 and r0.slope_t < -2
    wrow = next(r for r in WA if r["night"] == "Wed->Thu"); p3 = wrow["minus_others_bp"] >= 5 and wrow["minus_others_t"] > BONF
    reject = abs(pA["t"]) < 2 and abs(r0.slope_t) < 2
    if p1 and (p2 or p3): verdict = "H SUPPORTED"
    elif reject: verdict = "H REJECTED; B reported as the better-supported account (by the pre-registered rule)"
    else: verdict = "H NOT SUPPORTED (mixed: neither the support nor the rejection condition is met)"
    irv = DD[(DD.night == "all") & (DD.stat.str.startswith("index symmetric revert")) & (DD.stat.str.endswith("10:00"))].iloc[0]
    frv = DD[(DD.night == "all") & (DD.stat.str.startswith("futures counterpart")) & (DD.stat.str.endswith("10:00"))].iloc[0]
    b_corr = irv.mean_bp > 0 and irv.t > 2 and abs(frv.t) < 2

    # ---------------- write
    pd.DataFrame(fv[["E", "night", "is_roll", "entry", "c1429", "c1445", "daily_close_E", "a", "on_atc", "on_1429"]]).assign(
        idx_leg=w.idx_leg.reindex(fv.index), dleg=w.dleg.reindex(fv.index)).rename_axis("date").to_csv(OUT / "atc_drift_nights.csv")
    allt = pd.concat([pd.DataFrame(T), pd.DataFrame(WA).assign(test="A weekday (all)"), pd.DataFrame(WA_ex).assign(test="A weekday (ex expiry-day)"),
                      REG.assign(test="B regression"), DEC.assign(test="B decomposition"), CC, pd.DataFrame(WC).assign(test="C weekday minus-others on dleg"),
                      DD, SL.assign(test="D slope"), ALT.assign(test="STEP2 reconciliation")], ignore_index=True)
    allt.to_csv(OUT / "atc_drift_tests.csv", index=False)
    WAd = pd.DataFrame(WA)[["night", "n", "mean_bp", "mean_t", "minus_others_bp", "minus_others_t"]]
    WAx = pd.DataFrame(WA_ex)[["night", "n", "mean_bp", "mean_t", "minus_others_bp", "minus_others_t"]]
    WCd = pd.DataFrame(WC)[["night", "n", "mean_bp", "mean_t", "minus_others_bp", "minus_others_t"]] if WC else pd.DataFrame()
    pl = lambda df: ", ".join(" / ".join(str(r[k]) for k in ("sample", "night", "leg", "stat") if k in r and isinstance(r[k], str)) for _, r in df[df.power_limited].iterrows())
    L = [pre, "## STEP 2 reproduction gate", gate_line, "",
         "Reconciliation of alternative cuts (diagnostic only; the gate row is the one used):", fmt(ALT), "",
         f"Data checks: C(14:29) filled from an earlier bar on {int(fv.c1429_filled.sum())} auction days; ATC 14:45 bar close == F1M daily close on "
         f"{atc_eq_daily.mean() * 100:.1f}% of auction days (non-roll {atc_eq_daily[~fv.is_roll.values].mean() * 100:.1f}%); identity on_1429 = a + on_atc on non-roll nights, max residual {ident:.2e}. "
         f"Index 14:45 close == daily index close on {idx_close_chk * 100:.1f}% of window nights; index 14:25 filled on {int(ffi1425.sum())} days. Futures 09:00 forward-fills {ff_f}. "
         f"Cap {DATA_CAP}: last night {fv.index.max():%Y-%m-%d}, last auction day {fv.E.max():%Y-%m-%d}.", "",
         "## A. Auction leg a = ln C(14:45) - ln C(14:29)", fmt(pd.DataFrame(T)[["sample", "n", "mean_bp", "t", "se_bp", "mde80_bp"]]), "",
         f"By weekday (auction day; Bonferroni |t| > {BONF}), all nights:", fmt(WAd), f"Joint Wald chi2(4) all equal: {JA.get('wald', np.nan):.2f}, p {JA.get('wald_p', np.nan):.3f}", "",
         "By weekday, ex expiry-day auctions:", fmt(WAx), "",
         "## B. Offset: on_atc = c + b*a (NW SEs)", fmt(REG), "",
         "Decomposition on non-roll nights: on_1429 = a + on_atc (bp; share_a = a / on_1429)", fmt(DEC), "",
         f"## C. Matched auction legs, index-intraday window ({w.index.min():%Y-%m-%d} .. {w.index.max():%Y-%m-%d}, n {len(w)})",
         f"POWER LIMIT (stated before the numbers): n ~ {len(w)}, Wed n {int((w.night == 'Wed->Thu').sum())}. MDE80 = 2.80 x NW SE; cells with MDE80 > {POWER_BP:.0f} bp are POWER-LIMITED.",
         fmt(CC[["night", "leg", "n", "mean_bp", "t", "se_bp", "mde80_bp", "power_limited"]]), "",
         "Weekday minus-others on (futures - index) auction leg:", fmt(WCd) if len(WCd) else "(too few nights)", "",
         f"## D. Competing hypothesis B: index open overshoot (window, n {len(d)})",
         fmt(DD[["night", "stat", "n", "mean_bp", "t", "mde80_bp", "power_limited"]]), "",
         "Slope of post-open drift on index ON (NW):", fmt(SL), "",
         "## VERDICTS (pre-registered rule)",
         f"- P1 {'HOLDS' if p1 else 'DOES NOT HOLD'}: mean(a) = {pA['mean_bp']:.2f} bp, NW t {pA['t']:.2f}, n {pA['n']}; 95% CI {pA['mean_bp'] - 1.96 * pA['se_bp']:.2f} .. "
         f"{pA['mean_bp'] + 1.96 * pA['se_bp']:.2f} bp (MDE80 {pA['mde80_bp']:.1f} bp). The null is tight: the futures auction adds at most ~1 bp per night on average, "
         "against a ~10 bp futures-vs-index ON gap, so rejecting P1 is not a power problem.",
         f"- P2 {'HOLDS' if p2 else 'DOES NOT HOLD'}: slope of on_atc on a = {r0.slope:.3f} (NW t {r0.slope_t:.2f}), Pearson r {r0.pearson_r:.3f}, n {int(r0.n)} non-roll nights.",
         f"- P3 {'HOLDS' if p3 else 'DOES NOT HOLD'} AS PRE-REGISTERED: Wed auction minus other four = {wrow['minus_others_bp']:.2f} bp (t {wrow['minus_others_t']:.2f}; threshold >= 5 bp and t > {BONF}). "
         "CAVEAT: the request said 'order ~10 bp'; the pre-registration operationalised that as >= 5 bp. Under a >= 10 bp reading P3 FAILS. Either way the verdict is unchanged because P1 fails.",
         f"- **{verdict}.**",
         f"- B independent corroboration (index rev 09:15->10:00 > 0 with t > 2 AND futures counterpart |t| < 2): {'YES' if b_corr else 'NO'} "
         f"(index {irv.mean_bp:.2f} bp t {irv.t:.2f}; futures {frv.mean_bp:.2f} bp t {frv.t:.2f}; window n {int(irv.n)}, MDE80 {irv.mde80_bp:.1f} bp).",
         "- READING. The rule labels B 'better supported' because H's two conditions both fail (mean a ~ 0, slope ~ 0). The pre-registered corroboration check "
         "(SYMMETRIC, gap-proportional reversion) is " + ("NO: there is no symmetric reversion of the index open. " if not b_corr else "YES. ")
         + f"At the MEAN level D points in B's direction, but only borderline and power-limited: by 10:00 the index gives back {DD[(DD.night == 'all') & (DD.stat == 'index drift 09:15->10:00')].mean_bp.iloc[0]:.2f} bp "
           f"(t {DD[(DD.night == 'all') & (DD.stat == 'index drift 09:15->10:00')].t.iloc[0]:.2f}, MDE80 {DD[(DD.night == 'all') & (DD.stat == 'index drift 09:15->10:00')].mde80_bp.iloc[0]:.1f} bp) while futures move "
           f"{DD[(DD.night == 'all') & (DD.stat == 'futures drift 09:15->10:00')].mean_bp.iloc[0]:.2f} bp (t {DD[(DD.night == 'all') & (DD.stat == 'futures drift 09:15->10:00')].t.iloc[0]:.2f}). "
           "Combined with the POST HOC index closing-auction dip below, everything that moves is on the INDEX side (its close dips, its open is high, and it drifts down after the open), while futures are flat "
           "at all three points (post hoc reading; one-year window). "
         + f"P3 held on its own (Wed auction minus others {wrow['minus_others_bp']:.2f} bp, t {wrow['minus_others_t']:.2f}), but the pooled auction leg is ~0 because "
           "Thu/Fri auctions are negative; under the rule P3 cannot rescue H without P1.",
         f"- STEP 2 '5.0 bp quick cut': not reproduced exactly by any cut above. The nearest are keeping the 4 misaligned Thu-close -> Mon-open nights "
         f"({ALT.mean_bp.iloc[1]:.2f} bp) and the naive consecutive-day pairing with no roll fix ({ALT.mean_bp.iloc[3]:.2f} bp); the gate set reproduces 2.2a exactly.",
         f"- POWER-LIMITED cells (MDE80 > {POWER_BP:.0f} bp): A: {pl(pd.DataFrame(T)) or 'none'}; C: {pl(CC) or 'none'}; D: {pl(DD) or 'none'}.", ""]
    # ---------------- POST HOC (not pre-registered; added after seeing C): index closing-auction dip and matched-clock ON gap
    ph = w.copy(); ph["idx_ON"] = j.idx_ON.reindex(ph.index); ph["dbasis_ON"] = j.dbasis_ON.reindex(ph.index)
    ph["idx_ON_1425"] = ph.idx_ON + ph.idx_leg                     # ln I_open(T) - ln I_close(14:25, E), since prior close = 14:45 close
    ph["fut_ON_1429"] = ph.on_1429.where(~ph.is_roll)
    ph["gap_close"] = ph.idx_ON - ph.on_atc; ph["gap_pre_auction"] = ph.idx_ON_1425 - ph.fut_ON_1429
    PH = pd.DataFrame([cell(ph.idx_ON, stat="index ON from 14:45 close (= daily)"), cell(ph.idx_ON_1425, stat="index ON from 14:25 close (pre-auction)"),
                       cell(ph.on_atc, stat="futures ON from 14:45 ATC"), cell(ph.fut_ON_1429, stat="futures ON from 14:29 close (non-roll)"),
                       cell(ph.gap_close, stat="index - futures ON, closing prints (all window nights)"),
                       cell(ph.gap_close.where(~ph.is_roll), stat="index - futures ON, closing prints (non-roll, same nights as next row)"),
                       cell(ph.gap_pre_auction, stat="index - futures ON, pre-auction clocks (non-roll)"),
                       cell((ph.gap_close - ph.gap_pre_auction).where(~ph.is_roll), stat="difference = (futures - index) auction leg, non-roll")])
    o1 = ols_ak(ph.idx_ON, ph.idx_leg); o2 = ols_ak(-ph.dbasis_ON, ph.dleg)
    L += ["## POST HOC (not pre-registered; added after seeing section C; does not change the verdicts above)",
          "The index (not the futures) moves in its closing auction: index leg 14:25 -> 14:45 is negative while the futures leg is ~0. "
          "Measured from pre-auction clocks (index 14:25 close, futures 14:29 close), the index-minus-futures ON gap shrinks from the closing-print value to the row below "
          "(compare on the same non-roll nights; by construction the difference is test C's futures-minus-index auction leg). That is a MEAN-LEVEL statement: on average, the index's own closing auction "
          "lowers the index close relative to the futures close, and that accounts for much of the measured ON gap in this window.",
          "It is NOT a night-by-night recovery of the index: the slope of index ON on the index auction leg is POSITIVE (a bigger auction dip goes with a LOWER next "
          "index ON, i.e. continuation). The BASIS does revert night by night (the overnight shortfall rises with the futures-minus-index auction leg).",
          fmt(PH[["stat", "n", "mean_bp", "t", "mde80_bp", "power_limited"]]),
          f"OLS index ON on index auction leg: slope {o1['k']:.3f} (NW t {o1['k'] / o1['k_se']:.2f}), n {o1['n']}. "
          f"OLS overnight basis shortfall (-dbasis_ON) on (futures - index) auction leg: slope {o2['k']:.3f} (NW t {o2['k'] / o2['k_se']:.2f}), n {o2['n']}.",
          "One year only (window); exploratory; would need its own pre-registered test on a longer index-intraday history.", ""]
    PH.assign(test="POST HOC").to_csv(OUT / "atc_drift_posthoc.csv", index=False)
    H1 = tree_hash(); assert H0 == H1, "protected files changed during run"
    L += [f"Provenance: src/atc_drift_test.py on data/raw_intraday/VCI_VN30F1M_1m.csv + VCI_VN30_5m.csv (backup data/snapshots/raw_intraday_20261127T014311Z.tar.gz), "
          f"frozen daily futures (data/snapshots/frozen_20261117) + data/raw/VN30.csv; cap {DATA_CAP}; n {len(fv)} nights ({fv.index.min():%Y-%m-%d}..{fv.index.max():%Y-%m-%d}), "
          f"window n {len(w)}. Protected files (data/raw, frozen, raw_intraday, track_forward.py, boundary; {len(H0)} files) hash-identical before/after."]
    MD.write_text("\n".join(L) + "\n"); print("\n".join(L[1:])); return 0


if __name__ == "__main__":
    sys.exit(main())
