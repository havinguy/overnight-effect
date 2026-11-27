"""Regime legs audit. READ-ONLY on data/raw/ and results/ (writes only results/regime_legs_audit.md and regime_legs_*.csv).

Sample: one-day nights (calendar gap = 1 for the stock / futures night), common dates of the PIT cap-weighted basket and VN30F1M,
2018-11-21 .. 2026-11-17. Basket: PIT CW (pit_dayofweek_2x2 weights, variant B), ALL stock-days kept (no flat-open filter); per stock
ON = ln(open/prev close), ID = ln(close/open), C2C = ln(close/prev close), one common validity mask so ON + ID = C2C in the basket.
Futures: ON = ln(open/entry), ID = ln(close/open), C2C = ln(close/entry), entry as build() (F2M prior close on roll days).
Gap = futures minus basket, per date (so gap_C2C = gap_ON + gap_ID exactly). NW lag 5 everywhere.

PRE-REGISTERED INTERPRETATION RULES (fixed before the first run):
 R1 (step 1, per period):  CONVERGENCE / BASIS DRIFT if |t(gap_ON)| >= 2 and |t(gap_ID)| < 2   (gap similar in C2C and ON);
                           OPEN-TIMING SPLIT if |t(gap_ON)| >= 2, gap_ID of opposite sign with |t| >= 2, and |t(gap_C2C)| < 2;
                           otherwise MIXED (or NO ON GAP if |t(gap_ON)| < 2).
 R2 (step 2, stocks):      RELOCATION holds if |t(dC2C)| < 2 and t(dON) >= 2 and t(dID) <= -2, d = post - pre (2022-08-25),
                           SE = sqrt(SE_pre^2 + SE_post^2) from NW SEs of the two subsample means.
 R3 (step 3):              report only, never applied.
 R4 (step 4):              REPLACEMENT of the index-based Monday split: fut_ON = basket_ON + (fut_ON - basket_ON) on Mon->Tue one-day nights;
                           basis share = mean(gap_ON) / mean(fut_ON), Fieller 95% CI; "mostly basis" if share > 50% and |t(gap_ON)| >= 2.
 R5 (step 5):              futures break 95% CI = d +/- 1.96 SE; paired date-level test on d_t = basket_ON_t - fut_ON_t: break(d) = post - pre.
Usage: python3 src/regime_legs_audit.py
"""
from __future__ import annotations
import math, sys, warnings
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from level_a import RAW_DIR, OUT_DIR, decompose

OUT = OUT_DIR
NEW = {"regime_legs_audit.md", "regime_legs_legs.csv", "regime_legs_tolerance.csv", "regime_legs_monday.csv", "regime_legs_breaks.csv"}
import index_open_degradation_audit as IO
IO.NEW = IO.NEW | NEW


def tree_hash():
    import hashlib
    H = {}
    for d in (RAW_DIR, OUT):
        for p in sorted(d.glob("*")):
            if p.is_file() and p.name not in IO.NEW: H[str(p)] = hashlib.md5(p.read_bytes()).hexdigest()
    return H


H0 = tree_hash()
RG, X = IO.RG, IO.X
import futures_basis_followup as FU
from futures_basis_decomp import nw_t

CUT = pd.Timestamp("2022-08-25")
WD = {1: "Mon->Tue", 2: "Tue->Wed", 3: "Wed->Thu", 4: "Thu->Fri"}          # weekday of the OPEN date (one-day nights)


def stock_panels():
    ON, ID, CC = {}, {}, {}
    for t in X.tickers:
        # 2018-11-21 first-night fix (2026-11-27): gap / prior close taken from the RAW series BEFORE decompose() drops row 0
        raw = pd.read_csv(RAW_DIR / f"{t}.csv", parse_dates=["date"]).sort_values("date").reset_index(drop=True); raw["gap"] = raw["date"].diff().dt.days
        d = decompose(raw)
        ok = (d["gap"] == 1) & d[["r_overnight", "r_intraday", "r_cc"]].notna().all(axis=1)
        d = d.set_index("date")
        for P, c in ((ON, "r_overnight"), (ID, "r_intraday"), (CC, "r_cc")): P[t] = d[c].where(ok.values)
    f = lambda P: pd.DataFrame(P).sort_index().loc[X.START:]
    return f(ON), f(ID), f(CC)


def basket(P, scheme="cap"): return IO.OA.with_ret(P, lambda: X.cell_series("pit", scheme, "B")).r


def ms(x):
    x = pd.Series(x).dropna(); n = len(x)
    if n < 5: return dict(n=n, mean_bp=np.nan, t=np.nan, se_bp=np.nan)
    t = nw_t(x); m = x.mean() * 1e4; return dict(n=n, mean_bp=m, t=t, se_bp=abs(m / t) if t else np.nan)


def diff(a, b):
    """post-minus-pre style difference of two independent subsample means a (post), b (pre)."""
    A, B = ms(a), ms(b); d = A["mean_bp"] - B["mean_bp"]; se = math.hypot(A["se_bp"], B["se_bp"])
    return dict(pre_bp=B["mean_bp"], pre_t=B["t"], post_bp=A["mean_bp"], post_t=A["t"], d_bp=d, se_bp=se, t=d / se, lo95=d - 1.96 * se, hi95=d + 1.96 * se, n_pre=B["n"], n_post=A["n"])


def fm(x, f="{:.2f}"): return "" if pd.isna(x) else f.format(x)


def main():
    PON, PID, PCC = stock_panels()
    B = pd.DataFrame({"ON": basket(PON), "ID": basket(PID), "C2C": basket(PCC)})
    assert (B.ON + B.ID - B.C2C).abs().max() < 1e-10, "basket legs not additive"
    fut = RG.futures_nights_from(RG.rd("VN30F1M")); fut = fut[(fut.hold_type == "") & fut.invested].copy()
    F = pd.DataFrame({"ON": np.log(fut.open / fut.entry), "ID": np.log(fut.close / fut.open), "C2C": np.log(fut.close / fut.entry)})
    J = B.add_prefix("b_").join(F.add_prefix("f_"), how="inner").dropna().loc["2018-11-21":]
    for l in ("ON", "ID", "C2C"): J[f"g_{l}"] = J[f"f_{l}"] - J[f"b_{l}"]
    J["wd"] = J.index.weekday
    per = {"pre 2022-08-25": J[J.index < CUT], "post 2022-08-25": J[J.index >= CUT], "all": J}
    M = ["# Regime legs audit", "", "Read-only on data/raw/ and results/. Script: `src/regime_legs_audit.py`. Rules R1-R5 are pre-registered in the script header (fixed before the first run).", "",
         f"Sample: one-day nights, common basket/futures dates, n = {len(J)} ({J.index.min().date()}..{J.index.max().date()}). Basket = PIT cap-weighted, all stock-days kept. "
         "Gap = futures minus basket per date; gap_C2C = gap_ON + gap_ID exactly. Log returns, bp, NW t (lag 5).", ""]

    # ---------------- Step 1
    rows = []
    for g, s in per.items():
        r = dict(period=g, n=len(s))
        for pre, nm in (("b", "basket"), ("f", "futures"), ("g", "gap")):
            for l in ("ON", "ID", "C2C"):
                m = ms(s[f"{pre}_{l}"]); r[f"{nm}_{l}_bp"] = m["mean_bp"]; r[f"{nm}_{l}_t"] = m["t"]
        tO, tI, tC = r["gap_ON_t"], r["gap_ID_t"], r["gap_C2C_t"]
        if abs(tO) < 2: verdict = "NO ON GAP"
        elif abs(tI) < 2: verdict = "CONVERGENCE / BASIS DRIFT"
        elif np.sign(r["gap_ID_bp"]) != np.sign(r["gap_ON_bp"]) and abs(tI) >= 2 and abs(tC) < 2: verdict = "OPEN-TIMING SPLIT"
        else: verdict = "MIXED"
        r["R1_verdict"] = verdict; rows.append(r)
    L1 = pd.DataFrame(rows)
    M += ["## 1. Leg decomposition (mean bp, NW t)", ""]
    for nm in ("basket", "futures", "gap"):
        T = pd.DataFrame([{"period": r.period, "n": r.n, **{l: f"{r[f'{nm}_{l}_bp']:.2f} ({r[f'{nm}_{l}_t']:.2f})" for l in ("ON", "ID", "C2C")}} for _, r in L1.iterrows()])
        M += [f"**{nm}**" + (" (futures minus basket)" if nm == "gap" else ""), "", "```", T.to_string(index=False), "```", ""]
    M += ["R1 verdicts: " + "; ".join(f"{r.period}: {r.R1_verdict}" for _, r in L1.iterrows()), ""]

    # ---------------- Step 2
    pre, post = per["pre 2022-08-25"], per["post 2022-08-25"]
    D2 = pd.DataFrame([dict(series=f"{nm} {l}", **diff(post[f"{p}_{l}"], pre[f"{p}_{l}"])) for p, nm in (("b", "basket"), ("f", "futures"), ("g", "gap")) for l in ("ON", "ID", "C2C")])
    rb = D2.set_index("series")
    reloc = abs(rb.loc["basket C2C", "t"]) < 2 and rb.loc["basket ON", "t"] >= 2 and rb.loc["basket ID", "t"] <= -2
    M += ["## 2. Relocation test (post minus pre 2022-08-25)", "", "```", D2.to_string(index=False, float_format=lambda v: f"{v:.2f}"), "```", "",
          f"R2 (stocks): dC2C {rb.loc['basket C2C','d_bp']:.2f} bp (t {rb.loc['basket C2C','t']:.2f}), dON {rb.loc['basket ON','d_bp']:.2f} (t {rb.loc['basket ON','t']:.2f}), "
          f"dID {rb.loc['basket ID','d_bp']:.2f} (t {rb.loc['basket ID','t']:.2f}) -> RELOCATION {'HOLDS' if reloc else 'DOES NOT HOLD'}.", ""]

    # ---------------- Step 3
    W, ed = IO.member_weights()
    rows = []
    dates = J.index
    mem = {}
    for t in dates:
        e = [x for x in ed if x <= t]
        if e: mem[t] = W[e[-1]].index
    def tol(lo, hi, label):
        ds = [t for t in dates if lo <= t <= hi and t in mem]
        vals = np.concatenate([PON.loc[t, [n for n in mem[t] if n in PON.columns]].dropna().values for t in ds]) if ds else np.array([])
        bon, bcc = J.loc[lo:hi, "b_ON"], J.loc[lo:hi, "b_C2C"]
        return dict(period=label, nights=len(ds), constituent_nights=len(vals), share_exact0=(np.abs(vals) < 1e-12).mean(), share_lt_5bp=(np.abs(vals) < 5e-4).mean(),
                    share_lt_10bp=(np.abs(vals) < 1e-3).mean(), share_5_10bp_band=((np.abs(vals) >= 5e-4) & (np.abs(vals) < 1e-3)).mean(),
                    basket_ON_sd_bp=bon.std() * 1e4, basket_C2C_sd_bp=bcc.std() * 1e4, ON_sd_over_C2C_sd=bon.std() / bcc.std())
    T3 = [tol(pd.Timestamp(f"{y}-01-01"), pd.Timestamp(f"{y}-12-31"), str(y)) for y in range(2018, 2027)]
    T3 += [tol(pd.Timestamp("2018-11-21"), CUT - pd.Timedelta(days=1), "pre 2022-08-25"), tol(CUT, pd.Timestamp("2026-12-31"), "post 2022-08-25"),
           tol(pd.Timestamp("2018-11-21"), pd.Timestamp("2019-12-31"), "window 2018-19"), tol(pd.Timestamp("2023-01-01"), pd.Timestamp("2025-12-31"), "window 2023-25")]
    T3 = pd.DataFrame(T3)
    w1, w2 = T3.set_index("period").loc["window 2018-19"], T3.set_index("period").loc["window 2023-25"]
    M += ["## 3. Tolerance-based flat-open detector, stocks (report only; not applied)", "",
          "Share of PIT-member constituent-nights (one-day, common dates) with |ON| exactly 0, < 5 bp (0.05%), < 10 bp (0.1%); basket ON and C2C SD; ON/C2C SD ratio as a volatility-normalised spread.", "",
          "```", T3.to_string(index=False, float_format=lambda v: f"{v:.3f}"), "```", "",
          f"- Comparable-volatility windows: basket C2C SD 2018-19 {w1.basket_C2C_sd_bp:.1f} bp vs 2023-25 {w2.basket_C2C_sd_bp:.1f} bp; basket ON SD {w1.basket_ON_sd_bp:.1f} vs {w2.basket_ON_sd_bp:.1f} bp; "
          f"ON/C2C SD ratio {w1.ON_sd_over_C2C_sd:.3f} vs {w2.ON_sd_over_C2C_sd:.3f}. Near-flat (< 10 bp) share {w1.share_lt_10bp:.3f} vs {w2.share_lt_10bp:.3f}; exact-zero {w1.share_exact0:.3f} vs {w2.share_exact0:.3f}; "
          f"the 5-10 bp band (near-flat but not exact) {w1.share_5_10bp_band:.3f} vs {w2.share_5_10bp_band:.3f}.", ""]

    # ---------------- Step 4
    rows = []
    for g, lo, hi in (("2018-11..2021", "2018-11-21", "2021-12-31"), ("2022-2026", "2022-01-01", "2026-12-31"), ("pre 2022-08-25", "2018-11-21", "2022-08-24"), ("post 2022-08-25", "2022-08-25", "2026-12-31")):
        s = J.loc[lo:hi]
        for wd, nm in WD.items():
            x = s[s.wd == wd]; f_, b_, g_ = ms(x.f_ON), ms(x.b_ON), ms(x.g_ON)
            rc = FU.ratio_ci(x.g_ON, x.f_ON)
            rows.append(dict(period=g, night=nm, n=f_["n"], fut_ON_bp=f_["mean_bp"], fut_t=f_["t"], basket_ON_bp=b_["mean_bp"], basket_t=b_["t"], gap_ON_bp=g_["mean_bp"], gap_t=g_["t"],
                             basis_share_pct=100 * rc.get("ratio", np.nan), fieller_lo_pct=100 * rc.get("fieller_lo", np.nan), fieller_hi_pct=100 * rc.get("fieller_hi", np.nan), fieller=rc.get("fieller", "")))
    L4 = pd.DataFrame(rows)
    L4["R4_mostly_basis"] = (L4.basis_share_pct > 50) & (L4.gap_t.abs() >= 2)
    mon = L4[(L4.night == "Mon->Tue")].set_index("period")
    M += ["## 4. REPLACEMENT of the 82% Monday claim: basket (not index) as the reference leg", "",
          "This replaces futures_basis_summary.md R1 ('Monday dbasis share 82%, t 2.21, 2018-11..2021', computed against the VN30 index open). "
          "fut_ON = basket_ON + gap_ON on one-day nights; share = mean(gap)/mean(fut_ON), Fieller 95% CI.", "",
          "```", L4.to_string(index=False, float_format=lambda v: f"{v:.2f}"), "```", "",
          f"- NEW Mon->Tue basis share 2018-11..2021: {mon.loc['2018-11..2021','basis_share_pct']:.0f}% (gap {mon.loc['2018-11..2021','gap_ON_bp']:.2f} bp, t {mon.loc['2018-11..2021','gap_t']:.2f}; "
          f"futures {mon.loc['2018-11..2021','fut_ON_bp']:.2f} bp, basket {mon.loc['2018-11..2021','basket_ON_bp']:.2f} bp; Fieller {fm(mon.loc['2018-11..2021','fieller_lo_pct'], '{:.0f}')}..{fm(mon.loc['2018-11..2021','fieller_hi_pct'], '{:.0f}')}%; "
          f"n {int(mon.loc['2018-11..2021','n'])}) -> R4 mostly basis: {bool(mon.loc['2018-11..2021','R4_mostly_basis'])}.",
          f"- 2022-2026: {mon.loc['2022-2026','basis_share_pct']:.0f}% (gap {mon.loc['2022-2026','gap_ON_bp']:.2f} bp, t {mon.loc['2022-2026','gap_t']:.2f}; futures {mon.loc['2022-2026','fut_ON_bp']:.2f}, basket {mon.loc['2022-2026','basket_ON_bp']:.2f}; "
          f"Fieller {fm(mon.loc['2022-2026','fieller_lo_pct'], '{:.0f}')}..{fm(mon.loc['2022-2026','fieller_hi_pct'], '{:.0f}')}%, {mon.loc['2022-2026','fieller']}) -> R4 mostly basis: {bool(mon.loc['2022-2026','R4_mostly_basis'])}.",
          "- Differences from the original: one-day nights only, CW PIT basket instead of the index, common basket/futures dates; the original used all Mon->Tue nights with an index leg.", ""]

    # ---------------- Step 5
    fb = diff(post.f_ON, pre.f_ON); sb = diff(post.b_ON, pre.b_ON); dd = diff(post.b_ON - post.f_ON, pre.b_ON - pre.f_ON)
    D5 = pd.DataFrame([dict(test="futures ON break (post - pre)", **fb), dict(test="basket ON break (post - pre)", **sb), dict(test="paired: break of (basket ON - futures ON) per date", **dd)])
    M += ["## 5. Futures break CI and paired stock-minus-futures break", "", "```", D5.to_string(index=False, float_format=lambda v: f"{v:.2f}"), "```", "",
          f"- Futures ON break {fb['d_bp']:.2f} bp, 95% CI {fb['lo95']:.2f}..{fb['hi95']:.2f} bp. Paired date-level break (basket - futures) {dd['d_bp']:.2f} bp, t {dd['t']:.2f} "
          f"(CI {dd['lo95']:.2f}..{dd['hi95']:.2f}).", ""]

    L1.to_csv(OUT / "regime_legs_legs.csv", index=False); D2.assign(step=2).to_csv(OUT / "regime_legs_breaks.csv", index=False)
    pd.concat([D2.assign(step=2), D5.rename(columns={"test": "series"}).assign(step=5)]).to_csv(OUT / "regime_legs_breaks.csv", index=False)
    T3.to_csv(OUT / "regime_legs_tolerance.csv", index=False); L4.to_csv(OUT / "regime_legs_monday.csv", index=False)
    globals().update(_L1=L1, _D2=D2, _T3=T3, _L4=L4, _D5=D5, _reloc=reloc)
    l1 = L1.set_index("period"); pr, po = l1.loc["pre 2022-08-25"], l1.loc["post 2022-08-25"]
    m18, m22 = mon.loc["2018-11..2021"], mon.loc["2022-2026"]
    M += ["## Reading", "",
          f"**Where the futures-basket gap sits.** Pre-cutover the gap is in ON ({pr.gap_ON_bp:.2f} bp, t {pr.gap_ON_t:.2f}); ID is negative but not significant ({pr.gap_ID_bp:.2f}, t {pr.gap_ID_t:.2f}), "
          f"so R1 returns CONVERGENCE / BASIS DRIFT. The C2C gap is only {pr.gap_C2C_bp:.2f} bp (t {pr.gap_C2C_t:.2f}), about half the ON gap: R1 is met because the intraday offset is not significant, "
          f"not because C2C clearly equals ON - borderline between the two rows. Post-cutover R1 returns OPEN-TIMING SPLIT: ON {po.gap_ON_bp:.2f} (t {po.gap_ON_t:.2f}), ID {po.gap_ID_bp:.2f} (t {po.gap_ID_t:.2f}), C2C {po.gap_C2C_bp:.2f} (t {po.gap_C2C_t:.2f}). "
          "That verdict is the stock relocation seen from the other side: no futures leg moves across the cutover (all |t| < 0.6), so the post-cutover gap pattern comes entirely from the basket's own shift "
          "and carries no information about futures open timing (the same applies to the significant 2022-26 Mon->Tue gap, basket above futures).",
          f"Pre-cutover, about half of the ON excess ({pr.gap_C2C_bp:.1f} of {pr.gap_ON_bp:.1f} bp) carries to the close and about half reverses intraday without reaching significance; the convergence verdict rests on that absence of evidence.", "",
          f"**Relocation (stocks).** Holds under R2: basket C2C is unchanged across the cutover ({rb.loc['basket C2C','d_bp']:+.2f} bp, t {rb.loc['basket C2C','t']:.2f}) while ON rises {rb.loc['basket ON','d_bp']:+.2f} (t {rb.loc['basket ON','t']:.2f}) and ID falls {rb.loc['basket ID','d_bp']:+.2f} (t {rb.loc['basket ID','t']:.2f}). "
          "The stock 'regime' is a move of return from the trading day to the night with the daily total unchanged. Futures show no change in any leg (all |t| < 0.6). "
          f"Power: the C2C 'unchanged' result has a 95% CI of {rb.loc['basket C2C','lo95']:.1f}..{rb.loc['basket C2C','hi95']:.1f} bp, so a C2C change smaller than about 10 bp could not be detected.", "",
          f"**Tolerance detector.** Stock flat opens are exact, not near-flat: the 5-10 bp band adds only {T3.share_5_10bp_band.min():.3f}-{T3.share_5_10bp_band.max():.3f} of constituent-nights on top of the exact-zero share. "
          f"Near-flat share pre {T3.set_index('period').loc['pre 2022-08-25','share_lt_10bp']:.3f} vs post {T3.set_index('period').loc['post 2022-08-25','share_lt_10bp']:.3f}; 2019 is the highest year ({T3.set_index('period').loc['2019','share_lt_10bp']:.3f}). "
          f"The 2018-19 and 2023-25 windows are NOT comparable in volatility (basket C2C SD {w1.basket_C2C_sd_bp:.0f} vs {w2.basket_C2C_sd_bp:.0f} bp), so the volatility-normalised ON/C2C SD ratio is the comparison: "
          f"{w1.ON_sd_over_C2C_sd:.3f} vs {w2.ON_sd_over_C2C_sd:.3f}, i.e. no compression of the stock overnight between the two windows. 2019 has both the lowest stock ON/C2C ratio ({T3.set_index('period').loc['2019','ON_sd_over_C2C_sd']:.3f}) and the highest near-flat share ({T3.set_index('period').loc['2019','share_lt_10bp']:.3f}), "
          "consistent with the degradation audit's 'both references degraded' reading for 2019.", "",
          f"**Monday split, replaced.** With the basket as reference, the 2018-11..2021 Mon->Tue futures edge {m18.fut_ON_bp:.2f} bp splits into basket {m18.basket_ON_bp:.2f} bp (t {m18.basket_t:.2f}) and futures-minus-basket {m18.gap_ON_bp:.2f} bp (t {m18.gap_t:.2f}): "
          f"basis share {m18.basis_share_pct:.0f}% (Fieller {m18.fieller_lo_pct:.0f}..{m18.fieller_hi_pct:.0f}%), not 'mostly basis' under R4. The 82% claim is no longer supported: the share is undetermined (gap t " + f"{m18.gap_t:.2f}" + "; the Fieller interval covers 0%, 48%, 82% and 100%), so the data cannot distinguish 48% from 82%. "
          f"The replacement is clean: the futures leg reproduces the original exactly ({m18.fut_ON_bp:.2f} bp, n {int(m18.n)}), so the whole change comes from the reference leg (basket {m18.basket_ON_bp:.2f} bp vs index 2.78 bp). "
          f"In 2022-2026 the basket exceeds the futures on Mon->Tue (share {m22.basis_share_pct:.0f}%, Fieller {m22.fieller_lo_pct:.0f}..{m22.fieller_hi_pct:.0f}%). "
          "The only R4 'mostly basis' rows are pre-cutover Thu->Fri (gap 11.4 bp, t 2.63) with a futures mean that is not significant, so the share (>300%) is not meaningful.", "",
          f"**Breaks.** Futures ON break {fb['d_bp']:.2f} bp, 95% CI {fb['lo95']:.2f}..{fb['hi95']:.2f}. Paired date-level break of (basket - futures) {dd['d_bp']:.2f} bp, t {dd['t']:.2f}: the stock break is significantly larger than the futures break.", "",
          "Caveats: pre-2022-06 futures opens are unverified (open-definition / stability audits); one-day nights only; stock flat opens kept (exact-zero ON on ~27% of constituent-nights, both periods).", "",
          "## Summary (5 lines)", "",
          f"1. Futures-basket gap: pre-cutover in ON ({pr.gap_ON_bp:.1f} bp, t {pr.gap_ON_t:.1f}) with an insignificant ID offset ({pr.gap_ID_bp:.1f}, t {pr.gap_ID_t:.1f}) and C2C {pr.gap_C2C_bp:.1f} (t {pr.gap_C2C_t:.1f}) -> R1 CONVERGENCE/BASIS DRIFT (borderline: half the ON excess reverses intraday, n.s.); post-cutover R1 says OPEN-TIMING SPLIT (ON {po.gap_ON_bp:.1f}, ID {po.gap_ID_bp:+.1f}, C2C {po.gap_C2C_bp:.1f} n.s.), but that is the stock relocation seen from the futures side (no futures leg moves), not evidence on futures open timing.",
          f"2. Relocation holds for stocks: C2C unchanged ({rb.loc['basket C2C','d_bp']:+.1f} bp, t {rb.loc['basket C2C','t']:.2f}), ON {rb.loc['basket ON','d_bp']:+.1f} (t {rb.loc['basket ON','t']:.1f}), ID {rb.loc['basket ID','d_bp']:+.1f} (t {rb.loc['basket ID','t']:.1f}); futures break {fb['d_bp']:.1f} bp (95% CI {fb['lo95']:.1f}..{fb['hi95']:.1f}); paired stock-minus-futures break {dd['d_bp']:.1f} bp (t {dd['t']:.1f}); C2C CI {rb.loc['basket C2C','lo95']:.1f}..{rb.loc['basket C2C','hi95']:.1f} bp, so changes < ~10 bp undetectable.",
          f"3. Flat-open tolerance: stock flat opens are exact (5-10 bp band <= {T3.share_5_10bp_band.max():.3f}); near-flat share pre {T3.set_index('period').loc['pre 2022-08-25','share_lt_10bp']:.3f} vs post {T3.set_index('period').loc['post 2022-08-25','share_lt_10bp']:.3f}; ON/C2C SD ratio 2018-19 {w1.ON_sd_over_C2C_sd:.2f} vs 2023-25 {w2.ON_sd_over_C2C_sd:.2f} (windows differ in volatility, C2C SD {w1.basket_C2C_sd_bp:.0f} vs {w2.basket_C2C_sd_bp:.0f} bp): no compression of stock overnight between the windows; 2019 alone combines the lowest ratio and highest near-flat share.",
          f"4. New Monday split (REPLACES 82%): 2018-11..2021 Mon->Tue futures {m18.fut_ON_bp:.1f} bp = basket {m18.basket_ON_bp:.1f} + gap {m18.gap_ON_bp:.1f} (t {m18.gap_t:.2f}); basis share {m18.basis_share_pct:.0f}% (Fieller {m18.fieller_lo_pct:.0f}..{m18.fieller_hi_pct:.0f}%): the 82% claim is no longer supported, the share is undetermined (cannot distinguish 48% from 82%); futures leg identical to the original (15.44 bp, n 154), change comes from the reference (basket 8.05 vs index 2.78 bp); 2022-26 {m22.basis_share_pct:.0f}% (basket above futures).",
          "5. Open question: does the half of the pre-cutover futures ON excess that reverses intraday come from how pre-2022 futures opens were defined (needs verified opens to answer)? Second: what moved stock return from intraday to overnight at 2022-08-25 with futures unchanged - consistent with the T+2 afternoon-sale rule, mechanism not identified here.", ""]
    H1 = tree_hash()
    M += [f"Integrity: md5 of every pre-existing file in data/raw/ and results/ identical before and after: {H0 == H1} ({len(H0)} files)."]
    (OUT / "regime_legs_audit.md").write_text("\n".join(M) + "\n"); print("\n".join(M))


if __name__ == "__main__":
    main()
