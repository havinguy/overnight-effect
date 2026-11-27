"""Market-state control for the 2022-08-25 break. READ-ONLY on data/raw/ and results/ (writes only results/regime_market_state_audit.md
and regime_market_state_*.csv). Futures via data_cap (frozen snapshot, original VN30F1M input as in regime_changepoint_audit).

Question: does the ON / ID break at 2022-08-25 survive once the 2022 bear-market-to-recovery path is controlled; do the 2018 and 2020
drawdowns show the same leg pattern (placebo episodes)?

PRE-REGISTERED RULES (fixed before the first run; outcome-neutral):
 Sample: the regime_changepoint_audit sample (one-day nights, common CW basket / EW basket / VN30F1M dates, 2018-11-22..2026-11-17, n 1559).
 Series: CW ON, CW ID (primary), EW ON, EW ID, FUT ON, PAIRED = CW ON - FUT ON (reported).
 Controls, all from the VCI VNINDEX daily file and known at the close of the PRIOR trading day t-1 (no look-ahead):
   R60  = ln(close_{t-1} / close_{t-61}),  R120 = ln(close_{t-1} / close_{t-121})   (VNINDEX trading days; closes, not opens)
   RV20 = SD of the 20 daily close-to-close log returns ending t-1
   TO   = ln( mean volume over the 20 days ending t-1 / mean volume over the 250 days ending t-1 )   (relative turnover: VNINDEX volume
          rises ~4x 2019-21, so raw turnover would mostly be a time trend collinear with the break; zero volume -> missing)
   Controls are z-scored over the sample. Nights with any control missing are dropped from BOTH the baseline and controlled fits.
 Model: y_t = a + b*POST_t + c'X_t + e_t, POST = 1{t >= 2022-08-25}, OLS, Newey-West (Bartlett, lag 5) SE for b. y in bp.
   Baseline = same model without X on the same nights. Specs: (A) all four controls [PRIMARY]; (B) R60 + R120; (C) RV20 + TO.
 Rule C (per series, per spec), comparing b_ctrl to b_base:
   SURVIVES            |t(b_ctrl)| >= 2 and sign(b_ctrl) = sign(b_base)
   ATTENUATED, N.S.    same sign, |t(b_ctrl)| < 2
   SIGN FLIP           opposite sign (with its |t| reported)
   Retained share = b_ctrl / b_base reported. Collinearity: R^2 of POST on X reported; if R^2 > 0.5 the spec is flagged LOW POWER
   (the controls can absorb a true break) and its verdict is reported but marked.
   Answer to the question uses spec A on CW ON and CW ID: "break survives market-state control" iff both SURVIVE.
 Placebo episodes: VNINDEX trough = date of the minimum VCI VNINDEX close in calendar year E, E in {2018, 2020, 2022}.
   Window = 125 one-day nights before the trough (pre) vs the trough night and 124 after (post), t as in regime_changepoint S2
   (difference of means, hypot of NW SEs). Series: VNINDEX ON / ID / C2C one-day nights (VCI; only source with 2018 data), plus the
   CW basket legs where the window is fully inside the basket sample (not 2018). Pattern rule = regime_legs R2 verbatim:
   t(dON) >= 2, t(dID) <= -2, |t(dC2C)| < 2 -> "SHOWS RELOCATION SIGNATURE". The 2022 trough window contains 2022-08-25 (it is
   the same episode, not a placebo) and is reported as the comparator; 2018 and 2020 are the placebos.
   Caveats stated: VCI VNINDEX open quality (2021 fill; flagged opens kept as in regime_changepoint S4).
Usage: python3 src/regime_market_state_audit.py
"""
from __future__ import annotations
import hashlib, math, sys, warnings
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from level_a import RAW_DIR, OUT_DIR, decompose

OUT = OUT_DIR
NAME = "regime_market_state"
NEW = {f"{NAME}_audit.md", f"{NAME}_controls.csv", f"{NAME}_episodes.csv", f"{NAME}_collinearity.csv"}


def tree_hash():
    H = {}
    for d in (RAW_DIR, OUT):
        for p in sorted(d.glob("*")):
            if p.is_file() and p.name not in NEW: H[str(p)] = hashlib.md5(p.read_bytes()).hexdigest()
    return H


H0 = tree_hash()
import regime_legs_audit as RL

CUT = pd.Timestamp("2022-08-25"); L = 5; W = 125


def ols_hac(y, X):
    n, k = X.shape; XtXi = np.linalg.inv(X.T @ X); b = XtXi @ X.T @ y; u = y - X @ b; g = X * u[:, None]; S = g.T @ g
    for l in range(1, L + 1): G = g[l:].T @ g[:-l]; S += (1 - l / (L + 1)) * (G + G.T)
    V = XtXi @ S @ XtXi; return b, np.sqrt(np.diag(V)), u


def r2(y, X):
    b = np.linalg.lstsq(X, y, rcond=None)[0]; u = y - X @ b; return 1 - (u @ u) / ((y - y.mean()) @ (y - y.mean()))


def verdict(bc, tc, bb):
    if np.sign(bc) != np.sign(bb): return "SIGN FLIP"
    return "SURVIVES" if abs(tc) >= 2 else "ATTENUATED, N.S."


def main():
    PON, PID, PCC = RL.stock_panels()
    Bc = pd.DataFrame({"ON": RL.basket(PON, "cap"), "ID": RL.basket(PID, "cap"), "C2C": RL.basket(PCC, "cap")})
    Be = pd.DataFrame({"ON": RL.basket(PON, "ew"), "ID": RL.basket(PID, "ew")})
    fut = RL.RG.futures_nights_from(RL.RG.rd("VN30F1M")); fut = fut[(fut.hold_type == "") & fut.invested].copy()
    F = pd.DataFrame({"ON": np.log(fut.open / fut.entry), "ID": np.log(fut.close / fut.open), "C2C": np.log(fut.close / fut.entry)})
    J = Bc.add_prefix("b_").join(F.add_prefix("f_"), how="inner").dropna().loc["2018-11-21":].join(Be.add_prefix("e_"), how="left")
    S = {"CW ON": J.b_ON, "CW ID": J.b_ID, "EW ON": J.e_ON, "EW ID": J.e_ID, "FUT ON": J.f_ON, "PAIRED CW-FUT ON": J.b_ON - J.f_ON}

    v = pd.read_csv(RAW_DIR / "VNINDEX.csv", parse_dates=["date"]).set_index("date").sort_index()
    lc = np.log(v.close); r = lc.diff(); vol = v.volume.where(v.volume > 0)
    X0 = pd.DataFrame({"R60": lc - lc.shift(60), "R120": lc - lc.shift(120), "RV20": r.rolling(20).std(),
                       "TO": np.log(vol.rolling(20, min_periods=20).mean() / vol.rolling(250, min_periods=200).mean())}).shift(1)   # known at t-1 close
    X = X0.reindex(J.index); keep = X.notna().all(axis=1); Jk, Xk = J[keep], X[keep]
    Z = (Xk - Xk.mean()) / Xk.std()
    post = (Jk.index >= CUT).astype(float)
    SPECS = {"A all four": ["R60", "R120", "RV20", "TO"], "B R60+R120": ["R60", "R120"], "C RV20+TO": ["RV20", "TO"]}
    COL = pd.DataFrame([dict(spec=k, r2_post_on_controls=r2(post, np.column_stack([np.ones(len(post)), Z[c].values])), low_power=r2(post, np.column_stack([np.ones(len(post)), Z[c].values])) > 0.5) for k, c in SPECS.items()])
    lp = COL.set_index("spec").low_power
    rows = []
    for nm, s in S.items():
        y = s[keep].values * 1e4; one = np.ones(len(y))
        bb, sb, _ = ols_hac(y, np.column_stack([one, post])); tb = bb[1] / sb[1]
        for sp, cols in SPECS.items():
            b, se, _ = ols_hac(y, np.column_stack([one, post, Z[cols].values])); t = b[1] / se[1]
            rows.append(dict(series=nm, spec=sp, n=len(y), b_base_bp=bb[1], t_base=tb, b_ctrl_bp=b[1], t_ctrl=t, retained_share=b[1] / bb[1],
                             verdict=verdict(b[1], t, bb[1]), low_power_spec=bool(lp[sp]),
                             **{f"c_{c}_bp_per_sd": b[2 + i] for i, c in enumerate(cols)}, **{f"t_{c}": b[2 + i] / se[2 + i] for i, c in enumerate(cols)}))
    CT = pd.DataFrame(rows)
    A = CT[CT.spec == "A all four"].set_index("series")
    surv = A.loc["CW ON", "verdict"] == "SURVIVES" and A.loc["CW ID", "verdict"] == "SURVIVES"

    # ---- episodes
    # 2018-11-21 first-night fix (2026-11-27): gap / prior close taken from the RAW series BEFORE decompose() drops row 0 (VNINDEX: 2011-04-29)
    vraw = pd.read_csv(RAW_DIR / "VNINDEX.csv", parse_dates=["date"]).sort_values("date").reset_index(drop=True); vraw["gap"] = vraw["date"].diff().dt.days
    vd = decompose(vraw)
    vd = vd[vd.gap == 1].set_index("date")[["r_overnight", "r_intraday", "r_cc"]].rename(columns={"r_overnight": "ON", "r_intraday": "ID", "r_cc": "C2C"})
    ep = []
    for E in (2018, 2020, 2022):
        tr = v.close[str(E)].idxmin()
        for src, D in (("VNINDEX (VCI)", vd), ("CW basket", J[["b_ON", "b_ID", "b_C2C"]].rename(columns=lambda c: c[2:]))):
            p = int(np.searchsorted(D.index.values, tr.to_datetime64()))
            if p - W < 0 or p + W > len(D):
                ep.append(dict(episode=E, trough=tr.date(), series=src, status="window outside sample")); continue
            pre, pst = D.iloc[p - W:p], D.iloc[p:p + W]
            r_ = {l: RL.diff(pst[l], pre[l]) for l in ("ON", "ID", "C2C")}
            sig = r_["ON"]["t"] >= 2 and r_["ID"]["t"] <= -2 and abs(r_["C2C"]["t"]) < 2
            ep.append(dict(episode=E, trough=tr.date(), series=src, status="ok", window=f"{D.index[p - W].date()}..{D.index[p + W - 1].date()}",
                           contains_cutover=bool(D.index[p - W] <= CUT <= D.index[p + W - 1]), drawdown_pct=100 * (v.close[str(E)].min() / v.close[:tr].iloc[-260:].max() - 1),
                           dON_bp=r_["ON"]["d_bp"], tON=r_["ON"]["t"], dID_bp=r_["ID"]["d_bp"], tID=r_["ID"]["t"], dC2C_bp=r_["C2C"]["d_bp"], tC2C=r_["C2C"]["t"],
                           signature=sig, role="comparator (same episode as the cutover)" if E == 2022 else "placebo"))
    EP = pd.DataFrame(ep)

    f = lambda D: D.to_string(index=False, float_format=lambda x: f"{x:.2f}")
    M = ["# Market-state control audit", "",
         "Read-only. Script `src/regime_market_state_audit.py`; rules pre-registered in its header before the first run. Futures input: frozen VN30F1M (original), as regime_changepoint_audit.", "",
         f"Sample: {len(J)} one-day nights; {int((~keep).sum())} dropped for missing controls -> n {int(keep.sum())} ({Jk.index.min().date()}..{Jk.index.max().date()}). "
         "Controls (VNINDEX, known at t-1 close): R60, R120 trailing log returns; RV20 trailing 20-day realized vol; TO = ln(20d / 250d mean volume). z-scored. OLS, NW lag 5.", "",
         "## Collinearity of POST with the controls", "", "```", f(COL), "```", "",
         "## 1. Break b at 2022-08-25, baseline vs controlled (bp; NW t)", "", "```",
         f(CT[["series", "spec", "n", "b_base_bp", "t_base", "b_ctrl_bp", "t_ctrl", "retained_share", "verdict", "low_power_spec"]]), "```", "",
         "Control coefficients (bp per 1 SD, NW t), spec A:", "", "```", f(CT[CT.spec == "A all four"][["series"] + [c for c in CT.columns if c.startswith(("c_", "t_R", "t_T"))]].dropna(axis=1, how="all")), "```", "",
         f"- Spec A: CW ON {A.loc['CW ON','b_base_bp']:+.2f} -> {A.loc['CW ON','b_ctrl_bp']:+.2f} bp (t {A.loc['CW ON','t_base']:.2f} -> {A.loc['CW ON','t_ctrl']:.2f}) {A.loc['CW ON','verdict']}; "
         f"CW ID {A.loc['CW ID','b_base_bp']:+.2f} -> {A.loc['CW ID','b_ctrl_bp']:+.2f} bp (t {A.loc['CW ID','t_base']:.2f} -> {A.loc['CW ID','t_ctrl']:.2f}) {A.loc['CW ID','verdict']}. "
         f"Answer under the rule: break {'SURVIVES' if surv else 'does NOT survive (both legs required)'} market-state control.", "",
         "## 2. Drawdown episodes (VNINDEX trough; ±125 one-day nights)", "", "```", f(EP), "```", "",
         "Caveat: VNINDEX legs use VCI opens (flagged opens kept); the 2018 episode has no basket data (sample starts 2018-11-21) and no KBS cross-check.", ""]
    CT.to_csv(OUT / f"{NAME}_controls.csv", index=False); EP.to_csv(OUT / f"{NAME}_episodes.csv", index=False); COL.to_csv(OUT / f"{NAME}_collinearity.csv", index=False)
    H1 = tree_hash()
    M += [f"Integrity: md5 of every pre-existing file in data/raw/ and results/ identical before and after: {H0 == H1} ({len(H0)} files).", ""]
    e = EP[EP.status == "ok"].set_index(["episode", "series"])
    def es(E, s):
        if (E, s) not in e.index: return f"{E} {s}: n/a"
        q = e.loc[(E, s)]; return f"{E} {s} dON {q.dON_bp:+.1f} (t {q.tON:.2f}), dID {q.dID_bp:+.1f} (t {q.tID:.2f}), dC2C {q.dC2C_bp:+.1f} (t {q.tC2C:.2f}) -> {'signature' if q.signature else 'no signature'}"
    M += ["## Summary (5 lines)", "",
          f"1. Collinearity: R^2 of POST on controls A {COL.iloc[0].r2_post_on_controls:.2f}, B {COL.iloc[1].r2_post_on_controls:.2f}, C {COL.iloc[2].r2_post_on_controls:.2f}" + (" (LOW POWER flagged: " + ", ".join(COL[COL.low_power].spec) + ")" if COL.low_power.any() else " (none flagged LOW POWER)") + f"; n {int(keep.sum())}.",
          f"2. Spec A (all four controls): CW ON b {A.loc['CW ON','b_base_bp']:+.1f} -> {A.loc['CW ON','b_ctrl_bp']:+.1f} bp, t {A.loc['CW ON','t_base']:.2f} -> {A.loc['CW ON','t_ctrl']:.2f} ({A.loc['CW ON','verdict']}); CW ID {A.loc['CW ID','b_base_bp']:+.1f} -> {A.loc['CW ID','b_ctrl_bp']:+.1f}, t {A.loc['CW ID','t_base']:.2f} -> {A.loc['CW ID','t_ctrl']:.2f} ({A.loc['CW ID','verdict']}) -> break {'survives' if surv else 'does not survive'} under the rule.",
          "3. Other series, spec A: " + "; ".join(f"{k} t {r.t_base:.2f} -> {r.t_ctrl:.2f} ({r.verdict})" for k, r in A.drop(["CW ON", "CW ID"]).iterrows()) + ". Specs B/C in the table.",
          "4. Placebo drawdowns (VNINDEX legs): " + es(2018, "VNINDEX (VCI)") + "; " + es(2020, "VNINDEX (VCI)") + "; basket " + es(2020, "CW basket") + ".",
          "5. Comparator 2022 trough window (contains the cutover): " + es(2022, "VNINDEX (VCI)") + "; basket " + es(2022, "CW basket") + ". Report only, no reinterpretation."]
    (OUT / f"{NAME}_audit.md").write_text("\n".join(M) + "\n"); print("\n".join(M))


if __name__ == "__main__":
    main()
