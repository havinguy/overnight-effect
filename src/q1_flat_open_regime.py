"""Q1 at date level: is the 2022-08-25 stock relocation (C4/C5) an artifact of flat-open FREQUENCY? Measurement only; writes only q1_flat_open_regime* in results/.

DEFINITIONS (fixed before the first run)
- Universe: PIT VN30 basket members on each date (pit_dayofweek_2x2.build_weights("pit","B"), latest effective date <= t), 2018-11-21 onward.
- Night: one-day night only (gap == 1 calendar day), gap and prior close taken from the RAW series before decompose() (the 2018-11-21 fix).
- Flag (flat open): |open_t - close_{t-1}| < 1e-9, i.e. the data's open_suspicious definition (src/fetch_indices.py), recomputed here from raw prices.
- Regimes: pre = dates < 2022-08-25, post = dates >= 2022-08-25.
- Basket: date-level, CW primary (shares x free float x capping x prior close, as pit_dayofweek_2x2), EW check; >= 10 valid names per date.
- Inference: NW (Bartlett, lag 5) t for each regime mean; break t = (post - pre) / hypot(NW SE_pre, NW SE_post) (same as regime_legs_audit).

PRE-REGISTERED TESTS
 (i)  Flat-open share by regime: per date, share of eligible PIT members flagged (EW share; CW-weighted share as a check); mean over dates per regime,
      difference in percentage points with break t. Also pooled stock-day share per calendar year for PIT members and for the current-30 list (answers Q3).
 (ii) Unflagged-only: date-level basket ON and ID on unflagged stock-days only; pre, post, break t (CW and EW).
 (iii) All days (= treatment P in level_b_rebuild): the same table for comparison.
 (iv) Diagnostic for C9 (H3): rerun level_b_rebuild.h3_months("base") on unflagged-only ON/ID panels; report spreads, months, and the holding-month flag share of the
      top vs bottom tercile under the all-days sort.
 (iv-b) ADDED AFTER RUN 1 (run-1 md kept as q1_flat_open_regime_run1.md): in run 1 the unflagged-only H3 kept only 18 of 94 months, because
      the >=40-valid-of-60 eligibility rule fails once ~27% of nights are flagged. Coverage-matched variant: formation score = mean of the stock's last 60
      UNFLAGGED nights within the last 120 sessions (>= 40 required), holding month on unflagged nights. R3 is still read literally on (iv); (iv-b) is reported
      beside it and labelled post hoc.
 RERUN 2 (after reviewer; previous md kept as q1_flat_open_regime_run2pre.md), labelled changes: R3 bracket "[coverage, low power]" removed (it was
      asserted, not tested); all-days H3 on the SAME eligible months printed beside (iv); identity check implemented; share-break CI also with NW lag 20 and 60
      (persistent series); NW SE computed directly; integrity excludes only this run's output names; (iv-b) carries the R2 selection caveat and is kept out
      of the R3 line; H3 inference uses NW lag 3 (monthly), as in level_b_rebuild.
 Identity check (report only): on all days ON_P = (1 - s_w) * ON_unflagged-basket only approximately (weights differ), so the gap is reported, not used.

PRE-REGISTERED READ (from the user's brief, verbatim logic)
 R1: if the unflagged-only CW ON break is positive with t > 2 AND the EW flat-open share changes by less than 5 percentage points across regimes,
     then "a flat-open-frequency artifact does not explain the relocation (C4/C5)". If either fails, C4/C5 wording is downgraded and the md says so.
 R2: dropping flagged days selects on the outcome (flagged names close lower on the same date: open_audit_summary.md, t -5.77). So:
     version (iii) (all days) is the LEVEL estimate and supports C4/C5 levels; version (ii) supports only the conditional statement in R1
     (the break is not produced by a change in how often opens are flat). (ii) is not a level estimate.
 R3: C9 reading: if the unflagged-only H3 ON spread keeps t > 2, H3 ON persistence is not produced by flat-open zeros; if the ID spread loses |t| > 2, say so.
 An earlier ad hoc pooled check (current-30, stock-days, not date-level) is a HYPOTHESIS only and is not used for any verdict.
Usage: python3 src/q1_flat_open_regime.py
"""
from __future__ import annotations
import sys, io, math, hashlib, contextlib
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent)); sys.path.insert(0, ".")
import numpy as np, pandas as pd
from level_a import RAW_DIR
from futures_basis_decomp import nw_t
with contextlib.redirect_stdout(io.StringIO()):
    import pit_dayofweek_2x2 as X
    import level_b_rebuild as LB

ROOT = Path(__file__).resolve().parent.parent; OUT = ROOT / "results"; NAME = "q1_flat_open_regime"
CUT = pd.Timestamp("2022-08-25"); START = pd.Timestamp("2018-11-21"); TOL = 1e-9


def hash_tree():
    h = {}
    for d in (ROOT / "data" / "raw", OUT):
        for p in sorted(d.glob("*")):
            if p.is_file(): h[str(p)] = hashlib.sha256(p.read_bytes()).hexdigest()
    return h


def load():
    ON, ID, FL, PC = {}, {}, {}, {}
    for t in X.tickers:
        raw = pd.read_csv(RAW_DIR / f"{t}.csv", parse_dates=["date"]).sort_values("date").reset_index(drop=True)
        pc = raw.close.shift(1); gap = raw.date.diff().dt.days
        ok = (gap == 1) & pc.notna()
        on = np.log(raw.open) - np.log(pc); idl = np.log(raw.close) - np.log(raw.open)
        fl = (raw.open - pc).abs() < TOL
        i = raw.date
        ON[t] = pd.Series(on.where(ok).values, index=i); ID[t] = pd.Series(idl.where(ok).values, index=i)
        FL[t] = pd.Series(fl.where(ok).values, index=i, dtype="object"); PC[t] = pd.Series(pc.values, index=i)
    f = lambda D: pd.DataFrame(D).sort_index().loc[START:]
    ON, ID, FL, PC = f(ON), f(ID), f(FL), f(PC)
    return ON, ID, FL, PC.reindex(ON.index)


def basket(P_, PC, W, scheme, mask=None):
    ed = sorted(W); out = {}
    for t in P_.index:
        e = [x for x in ed if x <= t]
        if not e: continue
        w = W[e[-1]]; names = [n for n in w.index if n in P_.columns]
        r = P_.loc[t, names].astype(float)
        if mask is not None: r = r.where(mask.loc[t, names].astype(bool))
        ww = np.ones(len(names)) if scheme == "ew" else (w[names] * PC.loc[t, names]).values.astype(float)
        v = r.notna().values & np.isfinite(ww)
        if v.sum() < 10: continue
        out[t] = (np.sum(ww[v] * r.values[v]) / ww[v].sum(), int(v.sum()))
    return pd.DataFrame(out, index=["r", "k"]).T


def share_series(FL, PC, W, scheme):
    ed = sorted(W); out = {}
    for t in FL.index:
        e = [x for x in ed if x <= t]
        if not e: continue
        w = W[e[-1]]; names = [n for n in w.index if n in FL.columns]
        f = FL.loc[t, names]; v = f.notna().values
        ww = np.ones(len(names)) if scheme == "ew" else (w[names] * PC.loc[t, names]).values.astype(float)
        v &= np.isfinite(ww)
        if v.sum() < 10: continue
        out[t] = np.sum(ww[v] * f.values[v].astype(float)) / ww[v].sum()
    return pd.Series(out)


def h3_unflagged_cov(ONu, IDu, W):
    me = ONu.groupby(ONu.index.to_period("M")).tail(1).index; out = []
    for i, d in enumerate(me[:-1]):
        if not any(e <= d for e in W): continue
        names = [n for n in W[max(e for e in W if e <= d)].index if n in ONu.columns]
        hist = ONu.loc[:d].tail(120)[names]
        sc = pd.Series({n: hist[n].dropna().tail(60).mean() for n in names if hist[n].notna().sum() >= 40}).dropna()
        if len(sc) < 9: continue
        k = len(sc) // 3; nxt = (ONu.index > d) & (ONu.index <= me[i + 1]); top, bot = sc.nlargest(k).index, sc.nsmallest(k).index
        r = {"month_end": d}
        for leg, P_ in (("ON", ONu), ("ID", IDu)):
            r[f"{leg}_spread"] = P_.loc[nxt, top].stack().mean() - P_.loc[nxt, bot].stack().mean()
        out.append(r)
    H = pd.DataFrame(out).set_index("month_end"); H["CC_spread"] = H.ON_spread + H.ID_spread
    return H


def nw_se(x, L=5):
    x = pd.Series(x).dropna().values.astype(float); n = len(x); u = x - x.mean(); lrv = u @ u / n
    for l in range(1, min(L, n - 1) + 1): lrv += 2 * (1 - l / (L + 1)) * (u[l:] @ u[:-l]) / n
    return math.sqrt(max(lrv, 0) / n)


def split(s, label, scale=1e4, L=5):
    a, b = s[s.index < CUT].dropna(), s[s.index >= CUT].dropna()
    se = lambda x: nw_se(x, L)
    return dict(series=label, n_pre=len(a), n_post=len(b), pre=a.mean() * scale, pre_t=nw_t(a), post=b.mean() * scale, post_t=nw_t(b),
                diff=(b.mean() - a.mean()) * scale, break_t=(b.mean() - a.mean()) / math.hypot(se(a), se(b)),
                diff_lo95=((b.mean() - a.mean()) - 1.96 * math.hypot(se(a), se(b))) * scale, diff_hi95=((b.mean() - a.mean()) + 1.96 * math.hypot(se(a), se(b))) * scale)


def main():
    H0 = hash_tree()
    ON, ID, FL, PC = load()
    W = X.build_weights("pit", "B")
    unfl = FL.astype(float) == 0.0
    # (i) share
    SH = []
    for sch in ("ew", "cap"):
        ss = share_series(FL, PC, W, sch)
        for L_ in (5, 20, 60):
            SH.append(dict(**split(ss, f"flat-open share ({sch}) [pct points]", scale=100, L=L_), nw_lag=L_))
    SH = pd.DataFrame(SH)
    # per-year pooled stock-day share: PIT members and current-30
    pit_mask = pd.DataFrame(False, index=FL.index, columns=FL.columns); ed = sorted(W)
    for t in FL.index:
        e = [x for x in ed if x <= t]
        if e: pit_mask.loc[t, [n for n in W[e[-1]].index if n in FL.columns]] = True
    yr = []
    for lab, m in (("PIT members", pit_mask), ("current-30", pd.DataFrame(FL.columns.isin(X.cur30)[None, :].repeat(len(FL), 0), index=FL.index, columns=FL.columns))):
        F = FL.where(m)
        for y, g in F.groupby(F.index.year):
            v = g.stack().astype(float); yr.append(dict(universe=lab, year=y, stock_days=len(v), flat_share_pct=v.mean() * 100))
    YR = pd.DataFrame(yr)
    # (ii)/(iii) legs
    LEG = []
    for sch in ("cap", "ew"):
        for leg, P_ in (("ON", ON), ("ID", ID)):
            LEG.append(dict(version="(iii) all days", scheme=sch, leg=leg, **split(basket(P_, PC, W, sch).r, f"{leg} {sch} all")))
            LEG.append(dict(version="(ii) unflagged only", scheme=sch, leg=leg, **split(basket(P_, PC, W, sch, mask=unfl).r, f"{leg} {sch} unflagged")))
        LEG.append(dict(version="flagged only (ID; ON = 0 by construction)", scheme=sch, leg="ID", **split(basket(ID, PC, W, sch, mask=(FL.astype(float) == 1.0)).r, f"ID {sch} flagged")))
    LEG = pd.DataFrame(LEG).drop(columns="series")
    sc_ = share_series(FL, PC, W, "cap"); onP = basket(ON, PC, W, "cap").r; onU = basket(ON, PC, W, "cap", mask=unfl).r
    jj = pd.concat([onP, onU, sc_], axis=1, join="inner").dropna(); jj.columns = ["P", "U", "s"]
    IDN = []
    for lab, m in (("pre", jj.index < CUT), ("post", jj.index >= CUT)):
        x = jj[m]; IDN.append(dict(regime=lab, ON_P_bp=x.P.mean() * 1e4, one_minus_s_times_ON_U_bp=((1 - x.s) * x.U).mean() * 1e4, gap_bp=(x.P - (1 - x.s) * x.U).mean() * 1e4, cw_share_pct=x.s.mean() * 100))
    IDN = pd.DataFrame(IDN)
    ds = IDN.cw_share_pct.iloc[1] - IDN.cw_share_pct.iloc[0]; onu_post = jj[jj.index >= CUT].U.mean() * 1e4
    share_effect = -ds / 100 * onu_post   # bp of the all-days ON break attributable to the share change alone (flagged ON = 0)
    # (iv) H3 on unflagged panels
    ONu, IDu = ON.where(unfl), ID.where(unfl)
    Hall = LB.h3_months(ON, ID, W, "base"); Hu = LB.h3_months(ONu, IDu, W, "base")
    H3 = []
    Hc = h3_unflagged_cov(ONu, IDu, W); Hsame = Hall.loc[Hall.index.intersection(Hu.index)]
    for lab, H in (("all days (= level_b_rebuild P base)", Hall), ("all days, same months as unflagged-only", Hsame), ("unflagged only", Hu), ("(iv-b, post hoc) unflagged, coverage-matched [selects on outcome]", Hc)):
        for leg in ("ON", "ID", "CC"):
            x = H[f"{leg}_spread"].dropna()
            H3.append(dict(version=lab, leg=leg, months=len(x), spread_bp=x.mean() * 1e4, nw3_t=nw_t(x, 3) if len(x) > 3 else np.nan))
    H3 = pd.DataFrame(H3)
    # holding-month flag share of top vs bottom tercile (all-days sort)
    me = ON.groupby(ON.index.to_period("M")).tail(1).index; fs = []
    for i, d in enumerate(me[:-1]):
        names = [n for n in W[max(e for e in W if e <= d)].index if n in ON.columns] if any(e <= d for e in W) else []
        win = ON.loc[:d].tail(60)[names]; sc = win.mean()[win.notna().sum() >= 40].dropna()
        if len(sc) < 9: continue
        k = len(sc) // 3; nxt = (ON.index > d) & (ON.index <= me[i + 1])
        top, bot = sc.nlargest(k).index, sc.nsmallest(k).index
        fs.append(dict(month_end=d, top_flag=FL.loc[nxt, top].stack().astype(float).mean(), bot_flag=FL.loc[nxt, bot].stack().astype(float).mean()))
    FS = pd.DataFrame(fs).set_index("month_end"); FS["diff"] = FS.top_flag - FS.bot_flag
    fs_row = dict(months=len(FS), top_flag_pct=FS.top_flag.mean() * 100, bot_flag_pct=FS.bot_flag.mean() * 100, diff_pp=FS["diff"].mean() * 100, nw3_t=nw_t(FS["diff"], 3))
    # verdicts
    sh_ew = SH[(SH.nw_lag == 5)].iloc[0]; on_u = LEG[(LEG.version == "(ii) unflagged only") & (LEG.scheme == "cap") & (LEG.leg == "ON")].iloc[0]
    c1 = bool(on_u["diff"] > 0 and on_u.break_t > 2); c2 = bool(abs(sh_ew["diff"]) < 5)
    r1 = ("PASS: a flat-open-frequency artifact does not explain the relocation (C4/C5)" if (c1 and c2) else
          "FAIL: downgrade C4/C5 wording (" + ("unflagged ON break not positive with t>2" if not c1 else "") + ("; " if (not c1 and not c2) else "") + ("flat-open share moved >= 5 pp" if not c2 else "") + ")")
    h3u = H3[H3.version == "unflagged only"].set_index("leg")
    r3 = ("H3 ON persistence survives on unflagged nights (t %.2f)" % h3u.loc["ON", "nw3_t"]) if h3u.loc["ON", "nw3_t"] > 2 else ("H3 ON persistence does NOT survive on unflagged nights (t %.2f)" % h3u.loc["ON", "nw3_t"])
    hc = H3[H3.version.str.startswith("(iv-b")].set_index("leg")
    r3b = f"(iv-b, post hoc, selects on outcome: flagged nights dropped in formation and holding, so not a level or tradable estimate, {int(hc.loc['ON','months'])} months) ON spread {hc.loc['ON','spread_bp']:.2f} bp (t {hc.loc['ON','nw3_t']:.2f}), ID {hc.loc['ID','spread_bp']:.2f} bp (t {hc.loc['ID','nw3_t']:.2f}), C2C {hc.loc['CC','spread_bp']:.2f} bp (t {hc.loc['CC','nw3_t']:.2f})"
    hs = H3[H3.version == "all days, same months as unflagged-only"].set_index("leg")
    r3 += f" on {int(h3u.loc['ON','months'])} of {len(Hall)} eligible months (all days on those same months: ON t {hs.loc['ON','nw3_t']:.2f}, ID t {hs.loc['ID','nw3_t']:.2f})"
    r3 += ("; ID reversal keeps |t|>2 (t %.2f)" % h3u.loc["ID", "nw3_t"]) if h3u.loc["ID", "nw3_t"] < -2 else ("; ID reversal loses |t|>2 (t %.2f)" % h3u.loc["ID", "nw3_t"])
    for n_, D in (("share", SH), ("share_by_year", YR), ("legs", LEG), ("h3", H3)):
        D.to_csv(OUT / f"{NAME}_{n_}.csv", index=False)
    FS.to_csv(OUT / f"{NAME}_h3_flagshare_months.csv")
    IDN.to_csv(OUT / f"{NAME}_identity.csv", index=False)
    OUTS = {f"{NAME}.md", f"{NAME}_h3_flagshare_months.csv", f"{NAME}_identity.csv"} | {f"{NAME}_{n_}.csv" for n_ in ("share", "share_by_year", "legs", "h3")}
    H1 = hash_tree(); changed = [k for k in H1 if k in H0 and H0[k] != H1[k] and Path(k).name not in OUTS]
    integrity = not changed and all(Path(k).name in OUTS for k in H1 if k not in H0)
    f = lambda D: D.to_string(index=False, float_format=lambda v: f"{v:.2f}")
    yp = YR.pivot(index="year", columns="universe", values="flat_share_pct")
    L = [f"# Q1 at date level: flat-open frequency vs the 2022-08-25 relocation (src/{NAME}.py)", "",
         "Rules and the read are pre-registered in the script header, except (iv-b) (added after run 1) and the rerun-2 changes listed there. Units: legs in bp per one-day night; shares in percentage points.", "",
         "## (i) Flat-open share (open == prior close), PIT members, date-level", "", "```", f(SH), "```", "",
         "Pooled stock-day share by calendar year (Q3):", "", "```", yp.to_string(float_format=lambda v: f"{v:.1f}"), "```", "",
         "## (ii)/(iii) ON and ID by regime: all days (level estimate) vs unflagged only (conditional check, selects on outcome)", "", "```", f(LEG), "```", "",
         "## (iv) H3 (C9) on unflagged nights; tercile flag share in the holding month", "", "```", f(H3), "```", "",
         "Holding-month flag share, top vs bottom tercile (all-days sort): " + ", ".join(f"{k} {v:.2f}" for k, v in fs_row.items()), "",
         f"R1: {r1}.", f"Identity check (CW): ON_P vs (1 - s) x ON_unflagged by regime: " + "; ".join(f"{r.regime} {r.ON_P_bp:.2f} vs {r.one_minus_s_times_ON_U_bp:.2f} bp (gap {r.gap_bp:.2f})" for _, r in IDN.iterrows()) + f". Because flagged nights have ON = 0 exactly, the {ds:+.2f} pp CW share change can move the all-days ON by only about {share_effect:+.2f} bp of the {LEG[(LEG.version == '(iii) all days') & (LEG.scheme == 'cap') & (LEG.leg == 'ON')]['diff'].iloc[0]:.2f} bp break: this supports R1 without relying on the selected sample (ii).", "Share-break CI is shown with NW lag 5, 20 and 60 (the daily share is persistent; the lag-5 CI is too narrow).", "R2: (iii) is the level estimate for C4/C5; (ii) supports only the R1 conditional statement.", f"R3: {r3}.", f"R3 companion: {r3b}.", "",
         f"Integrity (no existing file changed): {integrity}", "", "## Summary (5 lines)", "",
         f"1. Flat-open share (EW, PIT): pre {sh_ew.pre:.1f}% vs post {sh_ew.post:.1f}% (diff {sh_ew['diff']:+.1f} pp, t {sh_ew.break_t:.2f}); yearly pooled share PIT {YR[YR.universe=='PIT members'].flat_share_pct.min():.1f}-{YR[YR.universe=='PIT members'].flat_share_pct.max():.1f}%, current-30 {YR[YR.universe=='current-30'].flat_share_pct.min():.1f}-{YR[YR.universe=='current-30'].flat_share_pct.max():.1f}%.",
         "2. CW ON break: " + "; ".join(f"{r.version} {r['diff']:+.2f} bp (t {r.break_t:.2f}, CI {r.diff_lo95:.1f}..{r.diff_hi95:.1f})" for _, r in LEG[(LEG.scheme == 'cap') & (LEG.leg == 'ON')].iterrows()) + ".",
         "3. CW ID break: " + "; ".join(f"{r.version} {r['diff']:+.2f} bp (t {r.break_t:.2f})" for _, r in LEG[(LEG.scheme == 'cap') & (LEG.leg == 'ID')].iterrows()) + ".",
         f"4. R1 -> {r1}.",
         f"5. R3 -> {r3}. Companion (post hoc, selected sample): {r3b}; integrity {integrity}."]
    (OUT / f"{NAME}.md").write_text("\n".join(L) + "\n"); print("\n".join(L)); assert integrity


if __name__ == "__main__":
    main()
