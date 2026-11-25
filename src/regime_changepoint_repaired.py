"""Side-by-side rerun of src/regime_changepoint_audit.py with the repaired futures input. READ-ONLY on existing files.

The original script text is executed with ONLY these textual substitutions (listed again in the md):
 1. futures input  RL.RG.rd("VN30F1M")  ->  RL.RG.rd("VN30F1M_repaired")   (frozen snapshot copy via data_cap: 13 post-expiry
    rows 2022-11-18..2023-12-22 inserted from VCI contract tickers; all other rows identical).
 2. output prefix  regime_changepoint  ->  regime_changepoint_repaired  (original outputs untouched).
 3. reproduction gate: the asserts against regime_legs_breaks.csv necessarily fail on a different input; they are replaced by
    recording the split t's, and the md sentence says the gate was not applied.
 4. the 'Rerun 1' note of the original run is replaced by a note naming this variant.
Rules S1-S5, seeds, B, W, trimming are unchanged. Because n changes, the same seeds give different bootstrap resamples, so p-values
and date intervals also move by Monte Carlo noise; the Monte Carlo SE of each bootstrap p is reported.
PRE-REGISTERED REPORTING RULE (fixed before the first run): for each series report original vs repaired best-fit (LS) date, 95% date
interval, Holm p, detected flag, cutover inside; a CHANGE is any different LS date, interval endpoint, or detected flag, or a Holm p
crossing 0.05. Placebo ranking, ramp verdict, Monday rows likewise. Report only: no reinterpretation in this run (standing rule).
Usage: python3 src/regime_changepoint_repaired.py
"""
from __future__ import annotations
import sys, types
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import numpy as np, pandas as pd

SRC = Path(__file__).parent / "regime_changepoint_audit.py"
OUT = Path(__file__).resolve().parent.parent / "results"
SUBS = [
    ('fut = RL.RG.futures_nights_from(RL.RG.rd("VN30F1M"))', 'fut = RL.RG.futures_nights_from(RL.RG.rd("VN30F1M_repaired"))'),
    ('NAME = "regime_changepoint"', 'NAME = "regime_changepoint_repaired"'),
    ('        assert abs(v - ref) < 1e-6, f"reproduction gate failed: {k_} {v} vs {ref}"', '        GATE_DIFF[k_] = (v, ref)'),
    ('from __future__ import annotations\n', 'from __future__ import annotations\nGATE_DIFF = {}\n'),
    ('f"Reproduction gate passed: the plain split at 2022-08-25 gives t = ', 'f"VARIANT RUN, futures input VN30F1M_repaired (frozen). Reproduction gate NOT APPLIED (different input); plain split at 2022-08-25 gives t = '),
    ('identical to regime_legs_breaks.csv. "', 'vs regime_legs_breaks.csv (original input): see regime_changepoint_repaired_compare.md. "'),
    ('"Rerun 1: text only (summary wording, date-mapping note, scan-CSV pointer); statistics and seeds unchanged, CSV md5 identical to run 0 (checked outside the script).", "",',
     '"Variant of regime_changepoint_audit.py: only the futures input changed (see src/regime_changepoint_repaired.py for the exact substitutions).", "",'),
]


def run_variant():
    s = SRC.read_text()
    for a, b in SUBS:
        assert s.count(a) == 1, f"substitution target not found exactly once: {a[:60]}"
        s = s.replace(a, b)
    m = types.ModuleType("regime_changepoint_repaired_variant"); m.__file__ = str(SRC)
    exec(compile(s, str(SRC) + " [variant]", "exec"), m.__dict__)
    m.main()
    return m


def main():
    m = run_variant()
    O = pd.read_csv(OUT / "regime_changepoint_summary.csv").set_index("series"); R = pd.read_csv(OUT / "regime_changepoint_repaired_summary.csv").set_index("series")
    B = 999
    rows = []
    for k in O.index:
        o, r = O.loc[k], R.loc[k]
        chg = []
        if o.ls_date != r.ls_date: chg.append("LS date")
        if o.ci_lo != r.ci_lo or o.ci_hi != r.ci_hi: chg.append("interval")
        if bool(o.detected) != bool(r.detected): chg.append("detected flag")
        if (o.p_holm < 0.05) != (r.p_holm < 0.05): chg.append("Holm p crosses 0.05")
        if bool(o.cut_inside) != bool(r.cut_inside): chg.append("cutover inside")
        rows.append(dict(series=k, n_orig=int(o.n), n_rep=int(r.n), ls_date_orig=o.ls_date, ls_date_rep=r.ls_date, ci_orig=f"{o.ci_lo}..{o.ci_hi}", ci_rep=f"{r.ci_lo}..{r.ci_hi}",
                         sup_t_orig=o.sup_abs_t, sup_t_rep=r.sup_abs_t, p_holm_orig=o.p_holm, p_holm_rep=r.p_holm, mc_se_p_rep=np.sqrt(r.p_boot * (1 - r.p_boot) / B),
                         t_cut_orig=o.t_at_cut_pointwise, t_cut_rep=r.t_at_cut_pointwise, detected_orig=bool(o.detected), detected_rep=bool(r.detected),
                         cut_inside_orig=bool(o.cut_inside), cut_inside_rep=bool(r.cut_inside), changes=", ".join(chg) or "none"))
    C = pd.DataFrame(rows)
    PO = pd.read_csv(OUT / "regime_changepoint_placebo.csv"); PR = pd.read_csv(OUT / "regime_changepoint_repaired_placebo.csv")
    def rank(P):
        out = {}
        for s, g in P.groupby("series", sort=False):
            c = g[(g.kind == "named") & (g.date == "2022-08-25")].t_window.iloc[0]; out[s] = (int((g[g.kind == "random"].t_window.abs() > abs(c)).sum()), c)
        return out
    ro, rr = rank(PO), rank(PR)
    PC = pd.DataFrame([dict(series=s, random_above_orig=ro[s][0], random_above_rep=rr[s][0], t_cut_window_orig=ro[s][1], t_cut_window_rep=rr[s][1],
                            same_random_dates=list(PO[(PO.series == s) & (PO.kind == "random")].date) == list(PR[(PR.series == s) & (PR.kind == "random")].date)) for s in ro])
    RO = pd.read_csv(OUT / "regime_changepoint_ramp.csv").set_index("series"); RR = pd.read_csv(OUT / "regime_changepoint_repaired_ramp.csv").set_index("series")
    RC = pd.DataFrame([dict(series=s, dAIC_orig=RO.loc[s, "dAIC_ramp_minus_step"], dAIC_rep=RR.loc[s, "dAIC_ramp_minus_step"], verdict_orig=RO.loc[s, "verdict"], verdict_rep=RR.loc[s, "verdict"]) for s in RO.index])
    MO = pd.read_csv(OUT / "regime_changepoint_monday.csv"); MR = pd.read_csv(OUT / "regime_changepoint_repaired_monday.csv")
    mon_same = np.allclose(MO.select_dtypes("number").values, MR.select_dtypes("number").values, equal_nan=True)
    G = pd.DataFrame([dict(test=k, t_repaired=v[0], t_original=v[1]) for k, v in m.GATE_DIFF.items()])
    C.to_csv(OUT / "regime_changepoint_repaired_compare.csv", index=False)
    f = lambda D: D.to_string(index=False, float_format=lambda v: f"{v:.3f}")
    chg = C[C.changes != "none"]
    L = ["# Change-point audit: original vs repaired futures input (side-by-side)", "",
         "Script `src/regime_changepoint_repaired.py` executes `src/regime_changepoint_audit.py` with only the substitutions listed in its header "
         "(futures input -> frozen VN30F1M_repaired.csv; output prefix; reproduction gate replaced by recording). Full variant outputs: `results/regime_changepoint_repaired_audit.md` + CSVs. "
         "Same seeds; n differs, so bootstrap resamples differ (Monte Carlo SE of p shown).", "",
         "## Plain split at 2022-08-25 (original gate values vs repaired input)", "", "```", f(G), "```", "",
         "## 1. Change-point scan", "", "```", f(C), "```", "",
         "## 2. Placebo ranking (random dates with |t_window| above 08-25)", "", "```", f(PC), "```", "",
         "## 3. Ramp vs step", "", "```", f(RC), "```", "",
         f"## 5. Monday rows: numerically identical: {mon_same} (the repaired rows are all after 2022-08-25, outside both Monday windows).", "",
         "## Summary (5 lines)", "",
         f"1. Sample: n {C.n_orig.iloc[0]} -> {C.n_rep.iloc[0]} one-day nights (repaired post-expiry days enter as futures/basket common dates); plain-split t at 08-25 CW ON {G.set_index('test').iloc[0].t_original:.2f} -> {G.set_index('test').iloc[0].t_repaired:.2f}, paired {G.set_index('test').iloc[-1].t_original:.2f} -> {G.set_index('test').iloc[-1].t_repaired:.2f}.",
         "2. Changes (LS date / interval / detected / Holm crossing 0.05 / cutover inside): " + ("; ".join(f"{r.series}: {r.changes} (LS {r.ls_date_orig} -> {r.ls_date_rep}; CI {r.ci_orig} -> {r.ci_rep}; Holm {r.p_holm_orig:.3f} -> {r.p_holm_rep:.3f})" for _, r in chg.iterrows()) or "none") + ".",
         "3. Unchanged series: " + (", ".join(C[C.changes == "none"].series) or "none") + f"; detected set original {', '.join(C[C.detected_orig].series)} vs repaired {', '.join(C[C.detected_rep].series)}.",
         "4. Placebo: " + ", ".join(f"{r.series} {r.random_above_orig}->{r.random_above_rep}/10" for _, r in PC.iterrows()) + f"; ramp CW ON dAIC {RC.iloc[0].dAIC_orig:+.2f} -> {RC.iloc[0].dAIC_rep:+.2f} ({RC.iloc[0].verdict_orig} -> {RC.iloc[0].verdict_rep}).",
         f"5. Monday rows identical: {mon_same}. Report only; differences are not reinterpreted in this run."]
    (OUT / "regime_changepoint_repaired_compare.md").write_text("\n".join(L) + "\n"); print("\n".join(L))


if __name__ == "__main__":
    main()
