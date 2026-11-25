"""Level B + 2x2 rebuild with SYMMETRIC treatment of the 7% rule (queue step 6). Measurement only; reads data/raw, writes only its own outputs.

WHAT WAS ASYMMETRIC BEFORE (verified in src/): level_b.py keeps |ON|>7% nights (sensitivity flag only) and reads ON/ID, while
pit_dayofweek_2x2.py and level_b_dayofweek.py drop open_suspicious AND |ON|>7% nights and look at the ON leg only, so Level B and the 2x2
filtered different nights, and the filter conditions on the outcome (a limit gap) for ON but never for ID.
Also: the flat-open flag (open_suspicious) was dropped in the 2x2 though the regime audits keep flat opens (stock flat opens are exact).

TREATMENTS (identical for every table; the SAME nights enter ON, ID and C2C of one table; one-day nights only, gap==1 calendar day):
  P  primary : no outcome-based exclusion. Flat opens kept.
  L  limit   : drop the whole night (both legs) when |ON|>7% or |ID|>7% (proxy for limit-touching; no reference price in the data).
  O  legacy  : the old 2x2 rule: drop open_suspicious or |ON|>7%, applied to all legs here (shows what the old filter did).
Primary = P. L and O are checks. Nothing is chosen by result. Design doc asks for "with and without limit days": P vs L.

TABLES
 1. Level B per stock (current VN30 list, 30 names): ON, ID mean (bp), NW(5) t, own-frequency Sharpe, per treatment.
 2. 2x2 day-of-week: {PIT basket, current-30 basket} x {CW, EW}, variant B shares (as before); weekday = weekday of OPEN date
    (Tue..Fri labelled Mon->Tue.. as in pit_dayofweek_2x2), legs ON and ID, plus Mon+Tue minus Wed+Thu. Re-uses build_weights/cell_series
    from pit_dayofweek_2x2 with its RET/PC panels replaced (same weights and >=10-name rule).
 3. Regime split of the basket (CW PIT) at 2022-08-25: ON/ID/C2C mean, NW t, plain split t (hypot of NW SEs), per treatment.
 4. H3 persistence (Level B): each month-end, rank PIT-basket members with >=40 valid nights in the trailing 60 nights on trailing mean ON; terciles
    (top 1/3 vs bottom 1/3, equal-weight, pooled stock-nights); next calendar month mean ON and ID of each group; spread = top - bottom. Report mean spread, NW(3) t over
    months, full sample and split at the cutover. H3 as stated: ON spread > 0 AND ID spread < 0.  Prediction is not tuned: formation 60, terciles fixed now.
 RERUN 1 (after run 0, run-0 md kept as level_b_rebuild_run0.md): (a) gap fix, 2018-11-21 night was dropped by computing gap after decompose; (b) H3 diagnostics
    D1 = score minus the stock's expanding-mean ON (>=250 prior nights) to remove stock fixed effects; D2 = formation window ended 12 months (252 nights) earlier. Both
    added because run 0 gave t=10 for H3 and a fixed-effect/open-bias artifact is the obvious alternative. Verdict rule R2 still read on the BASE spec; D1/D2 are reported beside
    it and R4: if D1 AND D2 both have ON t<2, H3 is labelled "FIXED-EFFECT ONLY" (persistence of stock level, not time-varying), whichever the base says.
 RERUN 2 (after reviewer pass; run-1 md kept as level_b_rebuild_run1.md), all labelled post-run-0/1 changes:
    (a) D1 now demeans with the stock's mean over nights BEFORE the 60-night formation window (>=250 valid), not an expanding mean that includes it (method change; D1 numbers change);
    (b) R4 is coded and printed; (c) H3 table gains a C2C spread (ON+ID spread cancels => C2C ~0 would fit a stock-level open bias); (d) R1 refinement: if |t|<2 under all
    treatments the break is labelled "NO BREAK UNDER ALL TREATMENTS" rather than sign-dependent; (e) H3 verdict wording: reports base R2 and D1/D2 side by side, does not call H3
    simply SUPPORTED if either ID check fails; (f) H3 group means are pooled stock-nights within the month (not stock-equal-weighted; header corrected); (g) disclosure: gap==1
    keeps only one-day nights, so Fri->Mon and holiday nights are excluded from every table (ON, ID and C2C are NOT full-sample); Mon+Tue minus Wed+Thu uses a plain Welch t, no NW.
 5. Check: 2018-11-21 night present in every basket series (the index_nights() first-row bug does not apply to stock panels; confirmed by count).
INTERPRETATION RULES (fixed before first run):
 R1 A claim is TREATMENT-ROBUST if its sign and |t|>2 status are the same under P, L, O; otherwise TREATMENT-DEPENDENT and reported as such.
 R2 H3 SUPPORTED only if ON spread t>2 and ID spread t<-2 under P; ON-only -> PARTIAL; neither -> NOT SUPPORTED. No Sharpe optimisation.
 R3 Changes versus old results files are reported; not reinterpreted in this run.
Usage: python3 src/level_b_rebuild.py
"""
from __future__ import annotations
import sys, hashlib, math, io, contextlib
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent)); sys.path.insert(0, ".")
import numpy as np, pandas as pd
from level_a import RAW_DIR, decompose
from futures_basis_decomp import nw_t

ROOT = Path(__file__).resolve().parent.parent; OUT = ROOT / "results"; NAME = "level_b_rebuild"
CUT = pd.Timestamp("2022-08-25")
with contextlib.redirect_stdout(io.StringIO()):
    import pit_dayofweek_2x2 as X
TREATS = {"P": "no outcome filter", "L": "drop night if |ON|>7% or |ID|>7%", "O": "legacy: open_suspicious or |ON|>7%"}


def hash_tree():
    h = {}
    for d in (ROOT / "data" / "raw", OUT):
        for p in sorted(d.glob("*")):
            if p.is_file(): h[str(p)] = hashlib.sha256(p.read_bytes()).hexdigest()
    return h


def panels(treat):
    ON, ID, CC, PC = {}, {}, {}, {}
    for t in X.tickers:
        raw = pd.read_csv(RAW_DIR / f"{t}.csv", parse_dates=["date"]).sort_values("date").reset_index(drop=True)
        d = decompose(raw)
        gap = raw["date"].diff().dt.days.iloc[1:].reset_index(drop=True); ok = (gap == 1)   # RERUN 1 FIX: gap taken BEFORE decompose drops row 0 (kept the 2018-11-21 night)
        if treat == "L": ok &= ~((d.r_overnight.abs() > 0.07) | (d.r_intraday.abs() > 0.07))
        if treat == "O": ok &= ~(d["open_suspicious"].astype(bool) | (d.r_overnight.abs() > 0.07))
        d = d.set_index("date"); m = ok.values
        ON[t], ID[t], CC[t] = d.r_overnight.where(m), d.r_intraday.where(m), d.r_cc.where(m)
        PC[t] = raw.set_index("date").close.shift(1)      # RERUN 1 FIX: prev close from the raw series (the old shift-after-decompose gave NaN on 2018-11-21 => CW basket lost the night)
    f = lambda D: pd.DataFrame(D).sort_index().loc[X.START:]
    ON, ID, CC, PC = f(ON), f(ID), f(CC), f(PC)
    return ON, ID, CC, PC.reindex(ON.index)


def h3_months(ON, ID, W_PIT, mode):
    pit_names = lambda d: list(W_PIT[max(e for e in W_PIT if e <= d)].index) if any(e <= d for e in W_PIT) else []
    me = ON.groupby(ON.index.to_period("M")).tail(1).index; out = []
    for i, d in enumerate(me[:-1]):
        names = [n for n in pit_names(d) if n in ON.columns]; hist = ON.loc[:d]
        if mode == "D2_lag12m":
            if len(hist) < 60 + 252: continue
            win = hist.iloc[-(60 + 252):-252][names]
        else:
            win = hist.tail(60)[names]
        ok_ = win.notna().sum() >= 40; sc = win.mean()[ok_]
        if mode == "D1_demeaned":
            ex = hist.iloc[:-60][names]; okx = ex.notna().sum() >= 250     # RERUN 2: mean before the formation window
            sc = (sc - ex.mean()[sc.index])[okx.reindex(sc.index).fillna(False)]
        sc = sc.dropna()
        if len(sc) < 9: continue
        nxt = (ON.index > d) & (ON.index <= me[i + 1]); k = len(sc) // 3
        top, bot = sc.nlargest(k).index, sc.nsmallest(k).index; r = {"month_end": d}
        for leg, P_ in (("ON", ON), ("ID", ID)):
            r[f"{leg}_top"] = P_.loc[nxt, top].stack().mean(); r[f"{leg}_bot"] = P_.loc[nxt, bot].stack().mean()
        out.append(r)
    H = pd.DataFrame(out).set_index("month_end")
    for leg in ("ON", "ID"): H[f"{leg}_spread"] = H[f"{leg}_top"] - H[f"{leg}_bot"]
    H["CC_spread"] = H.ON_spread + H.ID_spread; H["CC_top"] = H.ON_top + H.ID_top; H["CC_bot"] = H.ON_bot + H.ID_bot     # RERUN 2
    return H


def tstat_plain(x):
    x = x.dropna(); return x.mean() / (x.std() / math.sqrt(len(x)))


def main():
    H0 = hash_tree()
    W_PIT = X.build_weights("pit", "B"); W_CUR = X.build_weights("cur30", "B")
    rows_ps, rows_dow, rows_reg, rows_h3, rows_chk = [], [], [], [], []
    series = {}
    for tr in TREATS:
        ON, ID, CC, PC = panels(tr)
        # --- 1. per stock
        for t in X.cur30:
            for leg, P_ in (("ON", ON), ("ID", ID)):
                x = P_[t].dropna(); yrs = (x.index[-1] - x.index[0]).days / 365.25
                rows_ps.append(dict(treat=tr, ticker=t, leg=leg, n=len(x), mean_bp=x.mean() * 1e4, nw_t=nw_t(x), sharpe_own=x.mean() / x.std() * math.sqrt(len(x) / yrs)))
        # --- 2. 2x2 (patch panels in X)
        for leg, P_ in (("ON", ON), ("ID", ID), ("CC", CC)):
            X.RET, X.PC = P_, PC
            for basket, W in (("pit", W_PIT), ("cur30", W_CUR)):
                X.build_weights = lambda b, v, _W=W: _W            # cell_series calls build_weights(basket, variant)
                for sch in ("cap", "ew"):
                    s = X.cell_series(basket, sch, "B"); series[(tr, leg, basket, sch)] = s
                    for wd, nm in X.NAMES.items():
                        x = s[s.wd == wd].r
                        rows_dow.append(dict(treat=tr, leg=leg, cell=f"{basket}_{sch}", night=nm, n=len(x), mean_bp=x.mean() * 1e4, plain_t=tstat_plain(x), nw_t=nw_t(x)))
                    mt, wt = s[s.wd.isin([1, 2])].r, s[s.wd.isin([3, 4])].r
                    rows_dow.append(dict(treat=tr, leg=leg, cell=f"{basket}_{sch}", night="Mon+Tue minus Wed+Thu", n=len(mt) + len(wt), mean_bp=(mt.mean() - wt.mean()) * 1e4,
                                         plain_t=(mt.mean() - wt.mean()) / math.sqrt(mt.var() / len(mt) + wt.var() / len(wt)), nw_t=np.nan))
        # --- 3. regime split (PIT CW)
        for leg in ("ON", "ID", "CC"):
            s = series[(tr, leg, "pit", "cap")].r; a, b = s[s.index < CUT], s[s.index >= CUT]
            def se(x): return abs(x.mean() / nw_t(x))
            ta = nw_t(a); tb = nw_t(b); diff = b.mean() - a.mean(); t = diff / math.hypot(se(a), se(b))
            rows_reg.append(dict(treat=tr, leg=leg, n_pre=len(a), n_post=len(b), pre_bp=a.mean() * 1e4, post_bp=b.mean() * 1e4, pre_nw_t=ta, post_nw_t=tb, diff_bp=diff * 1e4, break_t=t))
        # --- 4. H3 (base, and diagnostics D1, D2 ADDED AFTER RUN 0; see header)
        for mode in ("base", "D1_demeaned", "D2_lag12m"):
            H = h3_months(ON, ID, W_PIT, mode); H.to_csv(OUT / f"{NAME}_h3_months_{tr}_{mode}.csv")
            for lab, h in (("full", H), ("pre", H[H.index < CUT]), ("post", H[H.index >= CUT])):
                for leg in ("ON", "ID", "CC"):
                    x = h[f"{leg}_spread"].dropna()
                    rows_h3.append(dict(treat=tr, mode=mode, sample=lab, leg=leg, months=len(x), spread_bp_per_night=x.mean() * 1e4, nw3_t=nw_t(x, 3) if len(x) > 3 else np.nan, top_bp=h[f"{leg}_top"].mean() * 1e4, bot_bp=h[f"{leg}_bot"].mean() * 1e4))
        # --- 5. 2018-11-21 check
        for key in ("pit", "cur30"):
            s = series[(tr, "ON", key, "cap")]
            rows_chk.append(dict(treat=tr, basket=key, first_date=str(s.index[0].date()), has_2018_11_21=pd.Timestamp("2018-11-21") in s.index, n=len(s)))
    PS, DOW, REG, H3, CHK = map(pd.DataFrame, (rows_ps, rows_dow, rows_reg, rows_h3, rows_chk))
    for n_, D in (("perstock", PS), ("dayofweek", DOW), ("regime", REG), ("h3", H3), ("check_2018_11_21", CHK)):
        D.to_csv(OUT / f"{NAME}_{n_}.csv", index=False)
    # old vs new comparison for the old 2x2 (legacy file) : PIT CW ON by night
    old = pd.read_csv(OUT / "pit_dayofweek_2x2.csv"); old = old[(old.variant == "B") & (old.cell == "pit_cap")][["night", "n", "mean_bp", "t"]]
    new = DOW[(DOW.treat == "O") & (DOW.leg == "ON") & (DOW.cell == "pit_cap")][["night", "n", "mean_bp", "plain_t"]]
    CMP = old.merge(new, on="night", suffixes=("_old", "_rebuild_O")); CMP.to_csv(OUT / f"{NAME}_old_vs_O.csv", index=False)
    # --- ps summary
    ps_sum = PS.groupby(["treat", "leg"]).apply(lambda g: pd.Series(dict(stocks=len(g), pos_mean=int((g.mean_bp > 0).sum()), t_gt2=int((g.nw_t > 2).sum()), t_lt_m2=int((g.nw_t < -2).sum()), median_sharpe=g.sharpe_own.median())), include_groups=False).reset_index()
    H1 = hash_tree(); changed = [k for k in H1 if k in H0 and H0[k] != H1[k] and not Path(k).name.startswith(NAME)]   # own outputs may be overwritten
    new_files = [k for k in H1 if k not in H0]; integrity = not changed and all(Path(k).name.startswith(NAME) for k in new_files)
    f = lambda D: D.to_string(index=False, float_format=lambda v: f"{v:.2f}")
    piv = DOW[DOW.night == "Mon+Tue minus Wed+Thu"].pivot_table(index=["leg", "cell"], columns="treat", values="plain_t")
    pivm = DOW[DOW.night == "Mon+Tue minus Wed+Thu"].pivot_table(index=["leg", "cell"], columns="treat", values="mean_bp")
    # robustness verdict (R1) on the regime break
    rb = REG.pivot(index="leg", columns="treat", values="break_t")
    def r1(v): return "NO BREAK UNDER ALL TREATMENTS" if (v.abs() < 2).all() else "TREATMENT-ROBUST" if (np.sign(v) == np.sign(v.iloc[0])).all() and ((v.abs() > 2) == (v.abs() > 2).iloc[0]).all() else "TREATMENT-DEPENDENT"
    verd = {leg: r1(rb.loc[leg]) for leg in rb.index}
    h3p = H3[(H3.treat == "P") & (H3["sample"] == "full") & (H3["mode"] == "base")].set_index("leg")
    d1 = H3[(H3.treat == "P") & (H3["sample"] == "full") & (H3["mode"] == "D1_demeaned")].set_index("leg"); d2 = H3[(H3.treat == "P") & (H3["sample"] == "full") & (H3["mode"] == "D2_lag12m")].set_index("leg")
    tON, tID = h3p.loc["ON", "nw3_t"], h3p.loc["ID", "nw3_t"]
    h3v = "SUPPORTED under base R2" if (tON > 2 and tID < -2) else ("PARTIAL (ON only)" if tON > 2 else "NOT SUPPORTED")
    cc = H3[(H3.treat == "P") & (H3["sample"] == "full") & (H3["mode"] == "base") & (H3.leg == "CC")].iloc[0]
    r4 = bool(d1.loc["ON", "nw3_t"] < 2 and d2.loc["ON", "nw3_t"] < 2)
    id_ok = bool(d1.loc["ID", "nw3_t"] < -2 and d2.loc["ID", "nw3_t"] < -2)
    h3v2 = ("FIXED-EFFECT ONLY (R4)" if r4 else "ON persistence survives D1 and D2 (R4 not triggered)") + ("; ID reversal survives D1 and D2" if id_ok else "; ID reversal NOT significant under both D1 and D2")
    L = [f"# Level B + 2x2 rebuild, symmetric 7% rule (src/{NAME}.py)", "", "Rules are in the script header (pre-registered). Primary treatment P; L and O are checks.", "",
         "Treatments: " + "; ".join(f"{k} = {v}" for k, v in TREATS.items()), "",
         "## 1. Level B per stock (summary across 30 current-VN30 names)", "", "```", f(ps_sum), "```", "",
         "## 2. 2x2 day-of-week: Mon+Tue minus Wed+Thu, plain Welch t by treatment (mean bp below)", "", "```", piv.to_string(float_format=lambda v: f"{v:.2f}"), "", pivm.to_string(float_format=lambda v: f"{v:.2f}"), "```", "",
         "Full weekday table: results/level_b_rebuild_dayofweek.csv. Old (legacy 2x2) vs rebuilt O, PIT CW ON:", "", "```", f(CMP), "```", "",
         "## 3. Regime split of PIT CW basket at 2022-08-25", "", "```", f(REG), "```", "",
         "R1 verdict on break t: " + "; ".join(f"{k} {v}" for k, v in verd.items()), "",
         "## 4. H3 persistence (tercile spread, next-month nights)", "", "```", f(H3), "```", "",
         f"R2 verdict (P, full sample, base): ON spread t {tON:.2f}, ID spread t {tID:.2f} -> H3 {h3v}.",
         f"R4 check: {h3v2}. Base C2C spread {cc.spread_bp_per_night:.2f} bp (t {cc.nw3_t:.2f}): ON and ID spreads offset, which fits (but does not prove) a stock-level open-price effect that moves return between legs without changing the daily return.",
         f"Diagnostics (ADDED AFTER RUN 0; D1 redefined in rerun 2): D1 demeaned score ON {d1.loc['ON','spread_bp_per_night']:.2f} bp (t {d1.loc['ON','nw3_t']:.2f}), ID {d1.loc['ID','spread_bp_per_night']:.2f} bp (t {d1.loc['ID','nw3_t']:.2f}); D2 12-month lag ON {d2.loc['ON','spread_bp_per_night']:.2f} bp (t {d2.loc['ON','nw3_t']:.2f}), ID {d2.loc['ID','spread_bp_per_night']:.2f} bp (t {d2.loc['ID','nw3_t']:.2f}).",
         "Treatment O (drops flat opens) leaves few eligible months for H3 (month counts in the table); by R1 read literally its H3 is TREATMENT-DEPENDENT; the cause is not measured here, so no coverage explanation is claimed.",
         "Scope: only one-day nights (gap == 1) enter every table, so Fri->Mon and holiday nights are excluded; ON/ID/C2C means are not full-sample. Mon+Tue minus Wed+Thu uses a plain Welch t (no NW); ON values 1.5-2.0 are at the threshold, not a significant day-of-week effect. Legacy-vs-O differences (e.g. Tue->Wed n 394 vs 395) come from the 2018-11-21 fix.", "",
         "## 5. 2018-11-21 check", "", "```", f(CHK), "```", "",
         f"Integrity (no existing file changed, only {NAME}* created): {integrity}", "",
         "## Summary (5 lines)", "",
         f"1. Treatments P/L/O are applied identically to Level B, 2x2 and regime split; H3 also, but under O only {int(H3[(H3.treat=='O')&(H3['mode']=='base')&(H3['sample']=='full')&(H3.leg=='ON')].months.iloc[0])} months are eligible (not comparable). The legacy 2x2 dropped flat opens and |ON|>7% nights on the ON leg only.",
         "2. Level B per stock (P): " + "; ".join(f"{r.leg} {int(r.pos_mean)}/30 positive, {int(r.t_gt2)} with NW t>2, {int(r.t_lt_m2)} with t<-2" for _, r in ps_sum[ps_sum.treat == "P"].iterrows()) + ".",
         "3. Regime break t (PIT CW, post minus pre): " + "; ".join(f"{l} " + "/".join(f"{rb.loc[l, t]:.2f}" for t in TREATS) + f" ({verd[l]})" for l in rb.index) + " for P/L/O.",
         f"4. H3 (P, full, base): ON spread {h3p.loc['ON','spread_bp_per_night']:.2f} bp (t {tON:.2f}), ID {h3p.loc['ID','spread_bp_per_night']:.2f} bp (t {tID:.2f}) -> {h3v}; D1 t {d1.loc['ON','nw3_t']:.2f}/{d1.loc['ID','nw3_t']:.2f}; D2 t {d2.loc['ON','nw3_t']:.2f}/{d2.loc['ID','nw3_t']:.2f} (ON/ID); C2C spread {cc.spread_bp_per_night:.1f} bp; {h3v2}.",
         f"5. 2018-11-21 night present in all basket series: {bool(CHK.has_2018_11_21.all())}; integrity {integrity}. Differences vs old files reported, not reinterpreted."]
    (OUT / f"{NAME}.md").write_text("\n".join(L) + "\n"); print("\n".join(L)); assert integrity


if __name__ == "__main__":
    main()
