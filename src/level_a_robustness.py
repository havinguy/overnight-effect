"""Level A robustness from docs/design-doc.md that was not yet run: ON-minus-ID test, pre/post-COVID and pre/post-KRX splits, EW vs CW vs published index.
Measurement only. Reads data/raw (indices, stocks, frozen boundary not involved). Writes only level_a_robustness* in results/.

PRE-REGISTERED (written before the first run)
Data / legs: log legs as in level_a.decompose. Primary = UNFILTERED, ALL nights (Level A definition; the open_suspicious filter selects on outcome,
  see open_audit_summary.md). Check = one-day nights only (gap == 1 calendar day). Prior close / gap from the raw series (2018-11-21 fix).
Series: VNINDEX (open reliable) 2011-04-29..2026-11-17 and its common window 2018-11-21+; VN30 index 2018-11-21+ (open DEGRADED 2019-01-01..2021-06-30
  per index_open_degradation_audit.md: VN30 rows are reported in full AND excluding that window; never used for a verdict inside it);
  PIT VN30 basket CW and EW (pit_dayofweek_2x2 weights, variant B; >= 10 names; a stock's night counts if its previous row is the previous
  VNINDEX trading day, so weekend/holiday nights are included like the index).
Inference: NW (Bartlett, lag 5) t; 95% CI = mean +/- 1.96 NW SE; break t = diff / hypot(SEs).
Test 1 (design doc): d_t = ON_t - ID_t, mean, NW t, CI, per series, full and common samples.
Test 2 (sub-periods). Dates chosen BEFORE running and why:
  COVID: split at 2020-01-23, the day Vietnam's Ministry of Health announced the first confirmed cases (CDC, ASCP/The Hill; WHO country page says
    01-24; the market was closed 23-29 Jan 2020 for Tet, so the first post night is the one ending 2020-01-30). Two-way split as in the design doc;
    plus a three-way cut that isolates the stock-regime date: pre-COVID (< 2020-01-23) / 2020-01-23..2022-08-24 / >= 2022-08-25, because the
    2022-08-25 relocation (C4) otherwise contaminates "post-COVID".
  KRX: split at 2025-05-05, HOSE KRX go-live (Vietnam News 2025-05-05 'KRX system officially goes live'; Tuoi Tre/NLD; The Investor). The night ending
    2025-05-05 is post. Because post-KRX lies wholly inside regime 2, the pre-KRX comparison is ALSO run within regime 2 only (2022-08-25..2025-05-04).
  Rule: a period with < 250 nights is labelled LOW N (reported, no verdict).
Test 3 (weighting): CW vs EW basket vs published VN30 index and VNINDEX on common dates; per regime (pre/post 2022-08-25): ON, ID, ON-ID means,
  paired EW-CW and basket-minus-index differences (NW t), correlation of ON.
READ RULES
 R1 H1 holds in a sample if ON-ID NW t > 2; reversed if t < -2; otherwise "no detectable difference".
 R2 a sub-period split CHANGES the H1 conclusion if the R1 label differs between the two sides (both sides >= 250 nights).
 R3 weighting-robust if EW and CW have the same R1 label in each regime; index-consistent if the published index (outside the degraded window) has it too.
 R4 any number from the VN30 index inside 2019-01-01..2021-06-30 is descriptive only.
TEST 1b (ADDED AFTER RERUN 1, post hoc; run-1 md kept as level_a_robustness_run1.md): rerun 1 showed ON-ID significant on all nights but not on
  one-day nights, so ON, ID and ON-ID are split by night length: 1 day / 3 days (weekend) / other multi-day (holidays). Descriptive; no verdict rule.
RERUN 2 (after reviewer; previous md kept as level_a_robustness_run2pre.md), labelled: (a) R3 index-consistency compared on the SAME dates (CW restricted
  to the VN30 ex-degraded dates); (b) R1 blanked for VN30 index rows that include the degraded window (R4); (c) the pre-registered break t of ON-ID is computed
  for every two-sided split and printed next to R2; (d) VN30 period labels show the dates actually used; (e) disclosure: CIs use 1.96, R1 uses |t| > 2;
  (f) Test 1b cells with n < 250 tagged LOW N (descriptive anyway).
TEST 1c (ADDED IN RERUN 3, post hoc, after final review; previous md kept as level_a_robustness_run3pre.md): flat-open share (open == prior close) and
  |ON| < 5 bp share of the index opens by night length, to test the stale-Monday-open explanation of Test 1b. Descriptive.
RUN LOG: run 0 had an index-alignment bug in legs() (all index rows NaN; md kept as level_a_robustness_run0_bug.md); rerun 1 fixes it, rules unchanged.
Usage: python3 src/level_a_robustness.py
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

ROOT = Path(__file__).resolve().parent.parent; OUT = ROOT / "results"; NAME = "level_a_robustness"
CUT = pd.Timestamp("2022-08-25"); COVID = pd.Timestamp("2020-01-23"); KRX = pd.Timestamp("2025-05-05"); COMMON = pd.Timestamp("2018-11-21")
DEG = (pd.Timestamp("2019-01-01"), pd.Timestamp("2021-06-30"))


def hash_tree():
    h = {}
    for d in (ROOT / "data" / "raw", OUT):
        for p in sorted(d.glob("*")):
            if p.is_file(): h[str(p)] = hashlib.sha256(p.read_bytes()).hexdigest()
    return h


def legs(sym):
    raw = pd.read_csv(RAW_DIR / f"{sym}.csv", parse_dates=["date"]).sort_values("date").reset_index(drop=True)
    pc = raw.close.shift(1)
    d = pd.DataFrame({"ON": (np.log(raw.open) - np.log(pc)).values, "ID": (np.log(raw.close) - np.log(raw.open)).values, "gap": raw.date.diff().dt.days.values}, index=raw.date)   # RERUN 1 FIX: .values (run 0 misaligned -> all NaN)
    return d.iloc[1:]


def basket_legs(cal):
    """PIT basket ON/ID per date, all nights where the stock's previous row is the previous calendar trading day."""
    prev = pd.Series(cal[:-1], index=cal[1:])
    ON, ID, PC = {}, {}, {}
    for t in X.tickers:
        raw = pd.read_csv(RAW_DIR / f"{t}.csv", parse_dates=["date"]).sort_values("date").reset_index(drop=True)
        pc = raw.close.shift(1); pdte = raw.date.shift(1)
        ok = (pdte.values == prev.reindex(raw.date).values) & pc.notna().values
        ON[t] = pd.Series(np.where(ok, np.log(raw.open) - np.log(pc), np.nan), index=raw.date)
        ID[t] = pd.Series(np.where(ok, np.log(raw.close) - np.log(raw.open), np.nan), index=raw.date)
        PC[t] = pd.Series(pc.values, index=raw.date)
    f = lambda D: pd.DataFrame(D).sort_index().loc[COMMON:]
    ON, ID, PC = f(ON), f(ID), f(PC).reindex(f(ON).index)
    W = X.build_weights("pit", "B"); ed = sorted(W); out = {}
    for t in ON.index:
        e = [x for x in ed if x <= t]
        if not e: continue
        w = W[e[-1]]; nm = [n for n in w.index if n in ON.columns]
        on, idl = ON.loc[t, nm].astype(float), ID.loc[t, nm].astype(float)
        v = on.notna().values & idl.notna().values
        cw = (w[nm] * PC.loc[t, nm]).values.astype(float); v &= np.isfinite(cw)
        if v.sum() < 10: continue
        out[t] = dict(CW_ON=np.sum(cw[v] * on.values[v]) / cw[v].sum(), CW_ID=np.sum(cw[v] * idl.values[v]) / cw[v].sum(),
                      EW_ON=on.values[v].mean(), EW_ID=idl.values[v].mean(), k=int(v.sum()))
    B = pd.DataFrame(out).T
    gap = pd.Series((cal[1:] - cal[:-1]).days, index=cal[1:]).reindex(B.index)
    res = {}
    for s in ("CW", "EW"):
        res[s] = pd.DataFrame({"ON": B[f"{s}_ON"].astype(float), "ID": B[f"{s}_ID"].astype(float), "gap": gap})
    return res


def stat(x):
    x = x.dropna(); n = len(x)
    if n < 10: return dict(n=n, mean_bp=np.nan, nw_t=np.nan, lo95=np.nan, hi95=np.nan)
    t = nw_t(x); se = abs(x.mean() / t) if t and np.isfinite(t) and t != 0 else np.nan
    return dict(n=n, mean_bp=x.mean() * 1e4, nw_t=t, lo95=(x.mean() - 1.96 * se) * 1e4, hi95=(x.mean() + 1.96 * se) * 1e4)


def r1(t):
    return "H1 holds (ON>ID)" if t > 2 else ("reversed (ON<ID)" if t < -2 else "no detectable difference")


def main():
    H0 = hash_tree()
    S = {"VNINDEX": legs("VNINDEX"), "VN30 index": legs("VN30")}
    cal = S["VNINDEX"].index.insert(0, pd.Timestamp("2011-04-28"))
    B = basket_legs(pd.DatetimeIndex(cal))
    S["PIT basket CW"], S["PIT basket EW"] = B["CW"], B["EW"]
    def samples(name, d):
        out = []
        base = {"VNINDEX": [("full 2011-04-29+", d), ("common 2018-11-21+", d.loc[COMMON:])]}.get(name, [("common 2018-11-21+", d.loc[COMMON:])])
        out += base
        if name == "VN30 index":
            dd = d.loc[COMMON:]; out.append(("common ex degraded 2019-01..2021-06", dd[(dd.index < DEG[0]) | (dd.index > DEG[1])]))
        return out
    T1 = []
    for name, d in S.items():
        for nights, dn in (("all nights", d), ("one-day nights", d[d.gap == 1])):
            for lab, x in samples(name, dn):
                for leg, v in (("ON", x.ON), ("ID", x.ID), ("ON-ID", x.ON - x.ID)):
                    T1.append(dict(series=name, nights=nights, sample=lab, leg=leg, **stat(v)))
    T1b = []
    for name, d in S.items():
        x = d.loc[COMMON:] if name != "VNINDEX" else d
        if name == "VN30 index": x = x[(x.index < DEG[0]) | (x.index > DEG[1])]
        for lab, m in (("1-day", x.gap == 1), ("3-day weekend", x.gap == 3), ("other multi-day", (x.gap != 1) & (x.gap != 3))):
            row = dict(series=name + (" (ex degraded)" if name == "VN30 index" else ""), night_length=lab, low_n=bool(m.sum() < 250))
            for leg, v in (("ON", x.ON[m]), ("ID", x.ID[m]), ("ON-ID", (x.ON - x.ID)[m])):
                s_ = stat(v); row.update({"n": s_["n"], f"{leg}_bp": s_["mean_bp"], f"{leg}_t": s_["nw_t"]})
            T1b.append(row)
    T1b = pd.DataFrame(T1b)
    T1c = []
    for sym in ("VNINDEX", "VN30"):
        r_ = pd.read_csv(RAW_DIR / f"{sym}.csv", parse_dates=["date"]).sort_values("date").reset_index(drop=True)
        pc_ = r_.close.shift(1); g_ = r_.date.diff().dt.days; fl_ = (r_.open - pc_).abs() < 1e-9; on_ = np.log(r_.open / pc_)
        for lab, m in (("1-day", g_ == 1), ("3-day weekend", g_ == 3), ("other multi-day", (g_ > 1) & (g_ != 3))):
            T1c.append(dict(series=sym, night_length=lab, n=int(m.sum()), flat_open_pct=fl_[m].mean() * 100, abs_ON_lt_5bp_pct=(on_[m].abs() < 5e-4).mean() * 100))
    T1c = pd.DataFrame(T1c)
    T1 = pd.DataFrame(T1); T1["R1"] = np.where(T1.leg == "ON-ID", T1.nw_t.map(r1), "")
    T1.loc[(T1.series == "VN30 index") & ~T1["sample"].str.contains("ex degraded"), "R1"] = "(descriptive only, R4)"
    # Test 2
    def periods(name, d):
        P = [("COVID 2-way", "pre-COVID (< 2020-01-23)", d[d.index < COVID]), ("COVID 2-way", "post-COVID (>= 2020-01-23)", d[d.index >= COVID]),
             ("COVID 3-way", "pre-COVID", d[d.index < COVID]), ("COVID 3-way", "2020-01-23..2022-08-24", d[(d.index >= COVID) & (d.index < CUT)]),
             ("COVID 3-way", ">= 2022-08-25", d[d.index >= CUT]),
             ("KRX", "pre-KRX (< 2025-05-05)", d[d.index < KRX]), ("KRX", "post-KRX (>= 2025-05-05)", d[d.index >= KRX]),
             ("KRX within regime 2", "2022-08-25..2025-05-04", d[(d.index >= CUT) & (d.index < KRX)]), ("KRX within regime 2", "post-KRX (>= 2025-05-05)", d[d.index >= KRX])]
        return P
    T2 = []
    for name, d in S.items():
        if name == "VN30 index": d = d[(d.index < DEG[0]) | (d.index > DEG[1])]
        for split, per, x in periods(name, d):
            if len(x) == 0: continue
            row = dict(series=name + (" (ex degraded)" if name == "VN30 index" else ""), split=split, period=per, dates_used=f"{x.index.min().date()}..{x.index.max().date()}")
            for leg, v in (("ON", x.ON), ("ID", x.ID), ("ON-ID", x.ON - x.ID)):
                s_ = stat(v); row.update({f"{leg}_bp": s_["mean_bp"], f"{leg}_t": s_["nw_t"]}); row["n"] = s_["n"]
            row["ONmID_lo95"], row["ONmID_hi95"] = stat(x.ON - x.ID)["lo95"], stat(x.ON - x.ID)["hi95"]
            row["R1"] = r1(row["ON-ID_t"]) if row["n"] >= 250 else "LOW N"
            T2.append(row)
    T2 = pd.DataFrame(T2)
    chg = []
    for (sr, sp), g in T2.groupby(["series", "split"], sort=False):
        if sp == "COVID 3-way": continue
        labs = list(g.R1)
        dsub = S["VN30 index"][(S["VN30 index"].index < DEG[0]) | (S["VN30 index"].index > DEG[1])] if sr.startswith("VN30") else S[sr]
        sides = [x for _, _, x in periods(sr, dsub) if True]
        P_ = {per: x for spl, per, x in periods(sr, dsub) if spl == sp}; xs = list(P_.values())
        a_, b_ = (xs[0].ON - xs[0].ID).dropna(), (xs[1].ON - xs[1].ID).dropna()
        def _se(v):
            v = v.values.astype(float); n = len(v); u = v - v.mean(); lrv = u @ u / n
            for l in range(1, 6): lrv += 2 * (1 - l / 6) * (u[l:] @ u[:-l]) / n
            return math.sqrt(lrv / n)
        bt = (b_.mean() - a_.mean()) / math.hypot(_se(a_), _se(b_)) if len(a_) > 10 and len(b_) > 10 else np.nan
        chg.append(dict(series=sr, split=sp, break_t_ONmID=bt, sides=" | ".join(f"{p}: {l}" for p, l in zip(g.period, labs)),
                                          R2=("LOW N" if "LOW N" in labs else ("CHANGES H1 conclusion" if len(set(labs)) > 1 else "same H1 conclusion"))))
    CHG = pd.DataFrame(chg)
    # Test 3
    j = pd.concat({k: S[k][["ON", "ID"]] for k in S}, axis=1).loc[COMMON:].dropna()
    T3 = []
    for reg, m in (("pre 2022-08-25", j.index < CUT), ("post 2022-08-25", j.index >= CUT), ("all common", j.index >= COMMON)):
        x = j[m]
        for k in S:
            if k == "VN30 index":
                xx = x[(x.index < DEG[0]) | (x.index > DEG[1])]; lab = "VN30 index (ex degraded)"
            else: xx, lab = x, k
            on, idl = xx[(k, "ON")], xx[(k, "ID")]
            T3.append(dict(regime=reg, series=lab, n=len(xx), ON_bp=on.mean() * 1e4, ON_t=nw_t(on), ID_bp=idl.mean() * 1e4, ID_t=nw_t(idl),
                           ONmID_bp=(on - idl).mean() * 1e4, ONmID_t=nw_t(on - idl), R1=r1(nw_t(on - idl))))
        for a, b in (("PIT basket EW", "PIT basket CW"), ("PIT basket CW", "VN30 index"), ("PIT basket EW", "VN30 index"), ("PIT basket CW", "VNINDEX")):
            xx = x[(x.index < DEG[0]) | (x.index > DEG[1])] if "VN30 index" in (a, b) else x
            for leg in ("ON", "ID"):
                dd = xx[(a, leg)] - xx[(b, leg)]; s_ = stat(dd)
                T3.append(dict(regime=reg, series=f"{a} minus {b}" + (" (ex degraded)" if "VN30 index" in (a, b) else ""), n=s_["n"], **{f"{leg}_bp": s_["mean_bp"], f"{leg}_t": s_["nw_t"]},
                               corr_ON=xx[(a, "ON")].corr(xx[(b, "ON")]) if leg == "ON" else np.nan))
    T3 = pd.DataFrame(T3)
    lab3 = T3[T3.R1.notna() & (T3.regime != "all common")].pivot(index="series", columns="regime", values="R1")
    wr = {reg: lab3.loc["PIT basket EW", reg] == lab3.loc["PIT basket CW", reg] for reg in lab3.columns}
    ic, icd = {}, {}
    for reg, m in (("pre 2022-08-25", j.index < CUT), ("post 2022-08-25", j.index >= CUT)):
        x = j[m]; x = x[(x.index < DEG[0]) | (x.index > DEG[1])]
        li, lc = r1(nw_t(x[("VN30 index", "ON")] - x[("VN30 index", "ID")])), r1(nw_t(x[("PIT basket CW", "ON")] - x[("PIT basket CW", "ID")]))
        ic[reg] = li == lc; icd[reg] = f"same {len(x)} dates: VN30 '{li}' vs CW '{lc}' (CW ON-ID {(x[('PIT basket CW','ON')]-x[('PIT basket CW','ID')]).mean()*1e4:.2f} bp, t {nw_t(x[('PIT basket CW','ON')]-x[('PIT basket CW','ID')]):.2f})"
    for n_, D in (("test1_onmid", T1), ("test2_subperiods", T2), ("test2_verdicts", CHG), ("test3_weighting", T3), ("test1b_nightlength", T1b), ("test1c_flatopen_nightlength", T1c)):
        D.to_csv(OUT / f"{NAME}_{n_}.csv", index=False)
    H1 = hash_tree(); changed = [k for k in H1 if k in H0 and H0[k] != H1[k] and not Path(k).name.startswith(NAME)]
    integrity = not changed and all(Path(k).name.startswith(NAME) for k in H1 if k not in H0)
    f = lambda D: D.to_string(index=False, float_format=lambda v: f"{v:.2f}")
    t1p = T1[(T1.leg == "ON-ID") & (T1.nights == "all nights")]
    L = [f"# Level A robustness (src/{NAME}.py)", "", "Pre-registered rules and split dates (with sources) are in the script header. bp per night; NW lag 5.", "",
         "## Test 1: ON minus ID (design doc t-test on the mean difference)", "", "```", f(T1[T1.leg == "ON-ID"]), "```", "",
         "## Test 1b (post hoc): legs by night length (VNINDEX full sample; others common 2018-11-21+)", "", "```", f(T1b), "```", "",
         "## Test 1c (post hoc): index flat-open share by night length", "", "```", f(T1c), "```", "",
         "## Test 2: sub-period splits (VN30 index excludes its degraded window 2019-01..2021-06)", "", "```", f(T2), "```", "", "```", CHG.to_string(index=False), "```", "",
         "## Test 3: EW vs CW basket vs published index (common dates, all nights)", "", "```", f(T3), "```", "",
         "R3 weighting-robust (EW label == CW label): " + ", ".join(f"{k}: {v}" for k, v in wr.items()) + "; index-consistent on the same dates (VN30 index ex degraded vs CW): " + "; ".join(f"{k}: {v} [{icd[k]}]" for k, v in ic.items()), "",
         "Note: CIs use 1.96 x NW SE; R1 uses |t| > 2, so a CI excluding 0 with t in (1.96, 2) is labelled 'no detectable difference' (VNINDEX pre-COVID: t 1.96). Break t of ON-ID across each split is in the verdict table; Test 1b cells with n < 250 are tagged LOW N.", "",
         f"Integrity (no existing file changed): {integrity}", "", "## Summary (5 lines)", "",
         "1. ON-ID (all nights): " + "; ".join(f"{r.series} {r['sample']} {r.mean_bp:+.2f} bp (NW t {r.nw_t:.2f}, CI {r.lo95:.1f}..{r.hi95:.1f})" + (" [descriptive, R4]" if r.R1.startswith("(descr") else "") for _, r in t1p.iterrows()) + "; on one-day nights ON-ID is not significant for VNINDEX or either basket (|t| <= 1.08); the VN30 index ex degraded is the exception (t 2.76, n 1086). Test 1b: much of the all-nights difference comes from the post-weekend intraday session (VNINDEX Monday ID -22.3 bp, t -4.74).",
         "2. COVID split: " + "; ".join(f"{r.series}: {r.R2} (break t {r.break_t_ONmID:.2f})" for _, r in CHG[CHG.split == "COVID 2-way"].iterrows()) + ". KRX split: " + "; ".join(f"{r.series}: {r.R2} (break t {r.break_t_ONmID:.2f})" for _, r in CHG[CHG.split == "KRX"].iterrows()) + ".",
         "3. KRX within regime 2: " + "; ".join(f"{r.series}: {r.R2}" for _, r in CHG[CHG.split == "KRX within regime 2"].iterrows()) + f". Post-KRX n = {int(T2[(T2.period.str.startswith('post-KRX')) & (T2.series == 'VNINDEX')].n.iloc[0])} nights (VNINDEX).",
         "4. Weighting (R3): " + ", ".join(f"{k} {'robust' if v else 'NOT robust'}" for k, v in wr.items()) + "; index-consistent on same dates: " + ", ".join(f"{k} {v}" for k, v in ic.items()) + ".",
         f"5. VN30 index numbers inside 2019-01..2021-06 are descriptive only (R4); integrity {integrity}."]
    (OUT / f"{NAME}.md").write_text("\n".join(L) + "\n"); print("\n".join(L)); assert integrity


if __name__ == "__main__":
    main()
