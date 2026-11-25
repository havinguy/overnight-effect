"""Regime change-point audit. READ-ONLY on data/raw/ and results/ (writes only results/regime_changepoint_audit.md and regime_changepoint_*.csv).

Sample (steps 1-3, 5): the regime_legs_audit sample, rebuilt with its own functions: one-day nights, common dates of the PIT CW basket
(all stock-days kept), the PIT EW basket and VN30F1M (roll-fixed entry), 2018-11-21 .. 2026-11-17. Series (log returns):
  CW ON, CW ID, EW ON, EW ID, FUT ON, PAIRED = CW ON - FUT ON (per date).
Reproduction gate: the plain pre/post split at 2022-08-25 must reproduce regime_legs_breaks.csv (CW ON, CW ID, FUT ON, paired) to 1e-6
in t; otherwise the script stops.

PRE-REGISTERED RULES (fixed before the first run; not changed afterwards):
 Break statistic t_k (all steps): mean(post) - mean(pre), SE = sqrt(SE_pre^2 + SE_post^2), each SE the NW (Bartlett, lag 5) SE of the
   subsample mean - the regime_legs diff() statistic. k = position of the first post night.
 S1 Change-point scan, single mean shift, per series.
   Candidates: k from ceil(0.15 n) to n - ceil(0.15 n) (15% trimming each end).
   BEST-FIT DATE (primary) = least-squares break (argmin SSR of the two-mean model). argmax |t_k| reported as secondary.
   sup|t| multiple-testing correction (primary): circular block bootstrap of the demeaned series, block 10 nights, B = 999,
   same t_k statistic and candidate set; p = (1 + #{sup* >= sup_obs}) / (B + 1); the 95% bootstrap critical value is reported.
   Across the six series: Holm adjustment of those p-values (family = 6). Report-only: an iid-Gaussian (Andrews-type) simulated 5%
   critical value for sup|t| (20000 reps, same n and trimming) - NOT used for decisions (ignores volatility clustering).
   BREAK-DATE 95% INTERVAL: residual block bootstrap around the fitted LS break (fitted two-mean step + circular-block-resampled
   residuals, block 10, B = 999), LS break re-estimated each time, 2.5/97.5 percentiles of the dates.
   2022-08-25 "inside" if its position lies within the interval (inclusive).
   If the Holm-adjusted sup|t| p >= 0.05 the series has NO DETECTED BREAK and its date interval is declared UNINFORMATIVE.
 S2 Placebo comparison. PRIMARY statistic: local window, W = 125 one-day nights each side (pre = the 125 nights before date d,
   post = d and the 124 after), t as above. Named dates 2022-07-11, 2022-08-25, 2022-11-03, 2022-11-18 (first sample night >= date).
   Random dates: 10 drawn once, before any statistic is computed, with numpy default_rng(20261124), without replacement, from sample
   nights in 2019-01-01..2021-12-31 whose full window fits in the sample and whose post window ends before 2022-08-25 (so no random
   window contains the cutover). Ranking: number of random dates with |t_W| > |t_W(2022-08-25)|, per series.
   Report-only: the plain full-sample split t at each date (contaminated: any pre-cutover split puts the post regime in "post").
 S3 Sharpness. Step: D = 1{date >= 2022-08-25}. Ramp: linear in calendar days from 2022-07-11 (0) to 2022-10-09 (1) = 2022-08-25 -/+ 45
   days (90 days ~ 3 months), 0 before, 1 after. OLS y = a + b*regressor, both 2 parameters; Gaussian AIC = n ln(SSR/n) + 2*2.
   dAIC = AIC_ramp - AIC_step. dAIC > 2 -> SHARP (step better); dAIC < -2 -> GRADUAL (ramp better); |dAIC| <= 2 -> NOT DISTINGUISHABLE.
   Primary series: CW ON. EW ON and PAIRED reported. Caveat stated: iid Gaussian likelihood, ignores autocorrelation/heteroskedasticity.
 S4 VNINDEX legs by calendar year 2012-2026, one-day nights, ON / ID / C2C mean bp and NW t.
   VCI (data/raw/VNINDEX.csv) primary, flagged opens (open == prior close) KEPT; check: flagged days dropped (all three legs).
   KBS (data/raw_kbs_index/KBS_VNINDEX_1D.csv, from 2018-11-19) reported alongside. Per-year caveat from computed flat-open shares
   (>10% in a source -> caveat), plus "no KBS cross-check" before 2019 (2018 partial).
   READING of "2018" and "2023" regime changes (not defined elsewhere in the project): adjacent calendar years, Y-1 vs Y
   (2017 vs 2018; 2022 vs 2023). RELOCATION signature = the regime_legs R2 rule verbatim: |t(dC2C)| < 2 and t(dON) >= 2 and t(dID) <= -2,
   d = Y - (Y-1), SE = hypot of NW SEs. 2018 judged on VCI (only source); 2023 on VCI and KBS. Every adjacent pair is tabulated so the
   background rate of the signature is visible. Report-only: VNINDEX 2021-08-25..2022-08-24 vs 2022-08-25..2023-08-24 (the cutover itself).
 S5 Monday read-out: basket (CW) Mon->Tue ON rows read from results/regime_legs_monday.csv for "2018-11..2021" and "pre 2022-08-25"
   (= 2018-11-21..2022-08-24), recomputed here and asserted equal. "Distinguishable" = |t| >= 2 for Mon->Tue minus the other one-day
   nights (Tue->Wed, Wed->Thu, Thu->Fri) in the same window, SE = hypot of NW SEs. The one-sample comparison against the window's
   all-night mean is report-only (that mean contains the Mondays).
 Seeds: S1 null 1001+i, S1 interval 2001+i (i = series index), S2 draw 20261124, iid simulation 3001. Run once; any rerun is recorded.
Usage: python3 src/regime_changepoint_audit.py
"""
from __future__ import annotations
import hashlib, math, sys, warnings
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from level_a import RAW_DIR, OUT_DIR, decompose

OUT = OUT_DIR
NAME = "regime_changepoint"
NEW = {f"{NAME}_audit.md"} | {f"{NAME}_{s}.csv" for s in ("scan", "summary", "placebo", "ramp", "vnindex_year", "vnindex_pairs", "monday")}


def tree_hash():
    H = {}
    for d in (RAW_DIR, OUT, RAW_DIR.parent / "raw_kbs_index"):
        for p in sorted(d.glob("*")):
            if p.is_file() and p.name not in NEW: H[str(p)] = hashlib.md5(p.read_bytes()).hexdigest()
    return H


H0 = tree_hash()                                     # before any project import
import regime_legs_audit as RL
from futures_basis_decomp import nw_t

CUT = pd.Timestamp("2022-08-25")
L = 5; TRIM = 0.15; BLK = 10; B = 999; W = 125
NAMED = ["2022-07-11", "2022-08-25", "2022-11-03", "2022-11-18"]


# ------------------------------------------------------------------ vectorised break statistic
class Seg:
    """Prefix sums so that the NW variance of any segment mean is O(L)."""
    def __init__(self, x):
        self.x = x; n = len(x); self.n = n
        self.P = np.concatenate([[0.0], np.cumsum(x)]); self.Q = np.concatenate([[0.0], np.cumsum(x * x)])
        self.C = {}
        for l in range(1, L + 1):
            y = np.zeros(n); y[l:] = x[l:] * x[:-l]; self.C[l] = np.concatenate([[0.0], np.cumsum(y)])

    def mean_var(self, a, b):
        a = np.asarray(a); b = np.asarray(b); m_ = b - a; S = self.P[b] - self.P[a]; m = S / m_
        g = (self.Q[b] - self.Q[a]) - m_ * m * m
        for l in range(1, L + 1):
            sxx = self.C[l][b] - self.C[l][a + l]; s1 = self.P[b] - self.P[a + l]; s2 = self.P[b - l] - self.P[a]
            g = g + 2 * (1 - l / (L + 1)) * (sxx - m * (s1 + s2) + (m_ - l) * m * m)
        return m, g / m_ / m_                          # mean, NW variance of the mean (lrv/n with lrv = g/n)

    def tstat(self, ks, a=None, b=None):
        n = self.n; ks = np.asarray(ks)
        a = np.zeros_like(ks) if a is None else np.asarray(a); b = np.full_like(ks, n) if b is None else np.asarray(b)
        m1, v1 = self.mean_var(a, ks); m2, v2 = self.mean_var(ks, b)
        return (m2 - m1) / np.sqrt(v1 + v2), m2 - m1

    def ssr(self, ks):
        n = self.n; S1 = self.P[ks]; S2 = self.P[n] - S1
        return self.Q[n] - S1 ** 2 / ks - S2 ** 2 / (n - ks)


def cbb_index(rng, n):
    nb = -(-n // BLK); st = rng.integers(0, n, nb)
    return ((st[:, None] + np.arange(BLK)[None, :]) % n).ravel()[:n]


def holm(p):
    p = np.asarray(p); o = np.argsort(p); m = len(p); adj = np.empty(m); run = 0
    for r, i in enumerate(o): run = max(run, (m - r) * p[i]); adj[i] = min(1, run)
    return adj


def ols2(y, r):
    X = np.column_stack([np.ones(len(y)), r]); b, *_ = np.linalg.lstsq(X, y, rcond=None); u = y - X @ b; return b, float(u @ u)


def ms(x): return RL.ms(x)
def dif(a, b): return RL.diff(a, b)
def fm(x, f="{:.2f}"): return "" if pd.isna(x) else f.format(x)


# ------------------------------------------------------------------ VNINDEX helpers
def vci_vnindex():
    d = decompose(pd.read_csv(RAW_DIR / "VNINDEX.csv", parse_dates=["date"]))
    d = d[d.date.diff().dt.days == 1].set_index("date")
    return pd.DataFrame({"ON": d.r_overnight, "ID": d.r_intraday, "C2C": d.r_cc, "flat": d.open_suspicious.astype(bool)})


def kbs_vnindex():
    k = pd.read_csv(RAW_DIR.parent / "raw_kbs_index" / "KBS_VNINDEX_1D.csv", parse_dates=["time"]); k["date"] = k.time.dt.normalize()
    k = k.drop_duplicates("date", keep="last").set_index("date").sort_index(); pc = k.close.shift(1)
    ok = k.index.to_series().diff().dt.days == 1
    return pd.DataFrame({"ON": np.log(k.open / pc), "ID": np.log(k.close / k.open), "C2C": np.log(k.close / pc), "flat": (k.open - pc).abs() < 0.005})[ok].dropna(subset=["ON"])


def reloc(a, b):
    """a = later period, b = earlier period; R2 verbatim."""
    r = {l: dif(a[l], b[l]) for l in ("ON", "ID", "C2C")}
    sig = abs(r["C2C"]["t"]) < 2 and r["ON"]["t"] >= 2 and r["ID"]["t"] <= -2
    return dict(dON_bp=r["ON"]["d_bp"], tON=r["ON"]["t"], dID_bp=r["ID"]["d_bp"], tID=r["ID"]["t"], dC2C_bp=r["C2C"]["d_bp"], tC2C=r["C2C"]["t"], relocation=sig)


def main():
    # ---------------- sample
    PON, PID, PCC = RL.stock_panels()
    Bc = pd.DataFrame({"ON": RL.basket(PON, "cap"), "ID": RL.basket(PID, "cap"), "C2C": RL.basket(PCC, "cap")})
    Be = pd.DataFrame({"ON": RL.basket(PON, "ew"), "ID": RL.basket(PID, "ew")})
    fut = RL.RG.futures_nights_from(RL.RG.rd("VN30F1M")); fut = fut[(fut.hold_type == "") & fut.invested].copy()
    F = pd.DataFrame({"ON": np.log(fut.open / fut.entry), "ID": np.log(fut.close / fut.open), "C2C": np.log(fut.close / fut.entry)})
    J0 = Bc.add_prefix("b_").join(F.add_prefix("f_"), how="inner").dropna().loc["2018-11-21":]       # regime_legs sample
    J = J0.join(Be.add_prefix("e_"), how="left")
    assert J[["e_ON", "e_ID"]].notna().all().all(), "EW basket missing on regime_legs dates"
    J["wd"] = J.index.weekday
    S = {"CW ON": J.b_ON, "CW ID": J.b_ID, "EW ON": J.e_ON, "EW ID": J.e_ID, "FUT ON": J.f_ON, "PAIRED CW-FUT ON": J.b_ON - J.f_ON}
    dates = J.index; n = len(J); kc = int(np.searchsorted(dates.values, CUT.to_datetime64()))

    # ---------------- S2 random draw FIRST (before any statistic)
    pos = np.arange(n); yr = dates.year
    elig = pos[(yr >= 2019) & (yr <= 2021) & (pos - W >= 0) & (pos + W <= kc)]
    RND = np.sort(np.random.default_rng(20261124).choice(elig, 10, replace=False))

    # ---------------- reproduction gate
    RB = pd.read_csv(OUT / "regime_legs_breaks.csv").set_index("series")
    pre, post = J[J.index < CUT], J[J.index >= CUT]
    gate = {"basket ON": dif(post.b_ON, pre.b_ON)["t"], "basket ID": dif(post.b_ID, pre.b_ID)["t"], "futures ON": dif(post.f_ON, pre.f_ON)["t"],
            "paired: break of (basket ON - futures ON) per date": dif(post.b_ON - post.f_ON, pre.b_ON - pre.f_ON)["t"]}
    for k_, v in gate.items():
        ref = RB.loc[k_, "t"]; ref = ref.iloc[0] if hasattr(ref, "iloc") else ref
        assert abs(v - ref) < 1e-6, f"reproduction gate failed: {k_} {v} vs {ref}"
    seg_chk = Seg(J.b_ON.values).tstat([kc])[0][0]
    assert abs(seg_chk - gate["basket ON"]) < 1e-8, "vectorised t differs from regime_legs diff()"

    M = ["# Regime change-point audit", "",
         "Read-only on data/raw/ and results/. Script: `src/regime_changepoint_audit.py`; rules S1-S5 pre-registered in the script header before the first run.", "",
         f"Sample: regime_legs_audit sample (one-day nights, common CW basket / futures dates), n = {n}, {dates.min().date()}..{dates.max().date()}; EW basket present on all of them. "
         f"Reproduction gate passed: the plain split at 2022-08-25 gives t = {gate['basket ON']:.2f} (CW ON), {gate['basket ID']:.2f} (CW ID), {gate['futures ON']:.2f} (FUT ON), "
         f"{gate['paired: break of (basket ON - futures ON) per date']:.2f} (paired), identical to regime_legs_breaks.csv. "
         f"Break t = (post - pre mean) / hypot(NW SEs), lag 5. 2022-08-25 = night #{kc} of {n}.", ""]

    # ---------------- S1
    lo_k = math.ceil(TRIM * n); ks = np.arange(lo_k, n - lo_k + 1)
    scan_rows, summ = [], []
    sim = np.random.default_rng(3001); sup_iid = []
    for _ in range(10):
        z = sim.standard_normal((2000, n)); cs = np.cumsum(z, axis=1); tot = cs[:, -1:]
        k1 = ks[None, :]; m1 = cs[:, ks - 1] / k1; m2 = (tot - cs[:, ks - 1]) / (n - k1)
        sup_iid.append(np.abs((m2 - m1) / np.sqrt(1 / k1 + 1 / (n - k1))).max(axis=1))
    crit_iid = float(np.quantile(np.concatenate(sup_iid), 0.95))
    for i, (nm, s) in enumerate(S.items()):
        x = s.values.astype(float); sg = Seg(x)
        t, d = sg.tstat(ks); ssr = sg.ssr(ks)
        k_ls = int(ks[np.argmin(ssr)]); k_t = int(ks[np.argmax(np.abs(t))]); sup = float(np.abs(t).max())
        t_cut = float(t[ks == kc][0])
        scan_rows.append(pd.DataFrame({"series": nm, "k": ks, "date": dates[ks].date, "t": t, "break_bp": d * 1e4, "ssr_minus_min": ssr - ssr.min()}))
        rng = np.random.default_rng(1001 + i); xd = x - x.mean(); sups = np.empty(B)
        for b in range(B): sups[b] = np.abs(Seg(xd[cbb_index(rng, n)]).tstat(ks)[0]).max()
        p = (1 + (sups >= sup).sum()) / (B + 1)
        m1, m2 = x[:k_ls].mean(), x[k_ls:].mean(); fit = np.where(pos < k_ls, m1, m2); e = x - fit
        rng = np.random.default_rng(2001 + i); kb = np.empty(B, int)
        for b in range(B):
            y = fit + e[cbb_index(rng, n)]; kb[b] = ks[np.argmin(Seg(y).ssr(ks))]
        qlo, qhi = np.quantile(kb, [0.025, 0.975]).round().astype(int)
        summ.append(dict(series=nm, n=n, ls_date=dates[k_ls].date(), ls_break_bp=(m2 - m1) * 1e4, t_at_ls=float(t[ks == k_ls][0]),
                         supt_date=dates[k_t].date(), sup_abs_t=sup, boot_crit95=float(np.quantile(sups, 0.95)), iid_crit95_reportonly=crit_iid, p_boot=p,
                         ci_lo=dates[qlo].date(), ci_hi=dates[qhi].date(), ci_width_nights=int(qhi - qlo), share_boot_within_10_of_cut=float((np.abs(kb - kc) <= 10).mean()),
                         cut_inside=bool(qlo <= kc <= qhi), t_at_cut_pointwise=t_cut, rank_of_cut_abs_t=int((np.abs(t) > abs(t_cut)).sum()) + 1, n_candidates=len(ks)))
    SU = pd.DataFrame(summ); SU["p_holm"] = holm(SU.p_boot.values); SU["detected"] = SU.p_holm < 0.05
    SU["interval"] = np.where(SU.detected, "informative", "UNINFORMATIVE (no detected break)")
    SC = pd.concat(scan_rows, ignore_index=True)
    T1 = SU[["series", "ls_date", "ls_break_bp", "t_at_ls", "supt_date", "sup_abs_t", "boot_crit95", "p_boot", "p_holm", "ci_lo", "ci_hi", "ci_width_nights", "cut_inside", "t_at_cut_pointwise", "rank_of_cut_abs_t", "interval"]]
    M += ["## 1. Change-point scan (single mean shift, 15% trimming)", "",
          f"{len(ks)} candidate dates {dates[ks[0]].date()}..{dates[ks[-1]].date()}. Best-fit = LS break; sup|t| = max NW break t over candidates; p_boot from a circular block bootstrap of the demeaned series "
          f"(block {BLK}, B {B}), Holm across the 6 series. Date interval: residual block bootstrap around the LS break (B {B}), 2.5-97.5%. "
          f"rank_of_cut_abs_t = rank of |t| at 2022-08-25 among all {len(ks)} candidates. Report-only iid-Gaussian 5% critical value for sup|t|: {crit_iid:.2f}. "
          f"t and break size at every candidate date: `results/{NAME}_scan.csv`.", "",
          "```", T1.to_string(index=False, float_format=lambda v: f"{v:.3f}"), "```", ""]
    for _, r in SU.iterrows():
        M.append(f"- {r.series}: LS break {r.ls_date} ({r.ls_break_bp:+.2f} bp), sup|t| {r.sup_abs_t:.2f} at {r.supt_date} vs bootstrap 5% critical {r.boot_crit95:.2f} "
                 f"(p {r.p_boot:.3f}, Holm {r.p_holm:.3f}); 95% date interval {r.ci_lo}..{r.ci_hi} ({r.ci_width_nights} nights) -> 2022-08-25 {'INSIDE' if r.cut_inside else 'OUTSIDE'}"
                 f"{'' if r.detected else '; NO DETECTED BREAK, interval uninformative'}. Pointwise t at 2022-08-25 {r.t_at_cut_pointwise:.2f} (rank {r.rank_of_cut_abs_t}/{r.n_candidates}).")
    M.append("")

    # ---------------- S2
    named = [int(np.searchsorted(dates.values, pd.Timestamp(d).to_datetime64())) for d in NAMED]
    prow = []
    for nm, s in S.items():
        sg = Seg(s.values.astype(float))
        for kind, kk in [("named", k) for k in named] + [("random", k) for k in RND]:
            tw, dw = sg.tstat([kk], [kk - W], [kk + W]); tf, df_ = sg.tstat([kk])
            prow.append(dict(series=nm, kind=kind, date=dates[kk].date(), k=kk, window_contains_cut=bool(kk - W <= kc < kk + W), t_window=tw[0], break_window_bp=dw[0] * 1e4,
                             t_fullsplit_reportonly=tf[0], break_fullsplit_bp=df_[0] * 1e4))
    PL = pd.DataFrame(prow)
    rk = []
    for nm, g in PL.groupby("series", sort=False):
        c = g[(g.kind == "named") & (g.date == dates[kc].date())].iloc[0]; r_ = g[g.kind == "random"]
        rk.append(dict(series=nm, t_window_cut=c.t_window, n_random_above=int((r_.t_window.abs() > abs(c.t_window)).sum()), max_abs_random=r_.t_window.abs().max(),
                       n_random_above_fullsplit_reportonly=int((r_.t_fullsplit_reportonly.abs() > abs(c.t_fullsplit_reportonly)).sum()),
                       other_named=", ".join(f"{x.date} {x.t_window:.2f}" for _, x in g[(g.kind == "named") & (g.date != dates[kc].date())].iterrows())))
    RK = pd.DataFrame(rk)
    M += ["## 2. Placebo comparison", "",
          f"Primary: local window, {W} one-day nights each side. Random dates (drawn first, seed 20261124, from {len(elig)} eligible 2019-2021 nights whose windows end before 2022-08-25): "
          + ", ".join(str(dates[k].date()) for k in RND) + ". The 2022 named dates other than 08-25 have windows that contain the cutover. "
          "t_fullsplit is report-only: a pre-cutover split puts the whole post-cutover regime on the 'post' side.", "",
          "Named-date mapping (first sample night >= date): 2022-07-11 -> 2022-07-12 (07-11 is a Monday open, i.e. a weekend night, not a one-day night); "
          "2022-11-18 -> 2022-11-22: 2022-11-18 is absent from data/raw/VN30F1M.csv (the file regime_legs_audit and this script read), so 11-21 is a 'holiday' hold and 11-18 drops from the "
          "common sample. data/raw/VN30F1M_repaired.csv does contain 2022-11-18 (one of 13 inserted post-expiry rows, 2022-11-18..2023-12-22, futures_roll_gap_inserted_rows.csv). "
          "Reported, not repaired here: the regime_legs sample (and this one) omits those 13 nights.", "",
          "```", PL.to_string(index=False, float_format=lambda v: f"{v:.2f}"), "```", "", "Ranking (|t_window| of random dates above the 2022-08-25 value):", "",
          "```", RK.to_string(index=False, float_format=lambda v: f"{v:.2f}"), "```", ""]

    # ---------------- S3
    cal = (dates - (CUT - pd.Timedelta(days=45))).days.values / 90.0
    ramp = np.clip(cal, 0, 1); step = (dates >= CUT).astype(float)
    rr = []
    for nm in ("CW ON", "EW ON", "PAIRED CW-FUT ON"):
        y = S[nm].values * 1e4; bs, ss = ols2(y, step); br, sr = ols2(y, ramp)
        aic_s = n * math.log(ss / n) + 4; aic_r = n * math.log(sr / n) + 4; da = aic_r - aic_s
        rr.append(dict(series=nm, n=n, step_shift_bp=bs[1], ramp_shift_bp=br[1], ssr_step=ss, ssr_ramp=sr, aic_step=aic_s, aic_ramp=aic_r, dAIC_ramp_minus_step=da,
                       verdict="SHARP" if da > 2 else ("GRADUAL" if da < -2 else "NOT DISTINGUISHABLE"), nights_inside_ramp=int(((ramp > 0) & (ramp < 1)).sum())))
    RA = pd.DataFrame(rr); ra = RA.set_index("series").loc["CW ON"]
    M += ["## 3. Sharpness: step vs 3-month linear ramp centred on 2022-08-25", "",
          "Ramp linear in calendar days 2022-07-11 -> 2022-10-09. Both models 2 parameters; dAIC = AIC_ramp - AIC_step (positive favours the step). Gaussian iid likelihood (caveat: ignores autocorrelation and volatility clustering).", "",
          "```", RA.to_string(index=False, float_format=lambda v: f"{v:.2f}"), "```", "",
          f"- CW ON: dAIC {ra.dAIC_ramp_minus_step:+.2f} -> {ra.verdict}. The two models differ only on the {int(ra.nights_inside_ramp)} nights inside the ramp, out of {n}.", ""]

    # ---------------- S4
    V, K = vci_vnindex(), kbs_vnindex()
    yrows = []
    for y in range(2012, 2027):
        v = V[V.index.year == y]; vd = v[~v.flat]; k = K[K.index.year == y]
        r = dict(year=y, vci_n=len(v), vci_flat=v.flat.mean())
        for l in ("ON", "ID", "C2C"): m = ms(v[l]); r[f"vci_{l}_bp"] = m["mean_bp"]; r[f"vci_{l}_t"] = m["t"]
        for l in ("ON", "ID", "C2C"): m = ms(vd[l]); r[f"vcidrop_{l}_bp"] = m["mean_bp"]; r[f"vcidrop_{l}_t"] = m["t"]
        r["kbs_n"] = len(k); r["kbs_flat"] = k.flat.mean() if len(k) else np.nan
        for l in ("ON", "ID", "C2C"): m = ms(k[l]) if len(k) >= 5 else dict(mean_bp=np.nan, t=np.nan); r[f"kbs_{l}_bp"] = m["mean_bp"]; r[f"kbs_{l}_t"] = m["t"]
        cav = []
        if y < 2018: cav.append("VCI only, no KBS cross-check")
        elif y == 2018: cav.append(f"KBS only from 2018-11-19 ({len(k)} nights)")
        if r["vci_flat"] > 0.10: cav.append(f"VCI flat opens {r['vci_flat']:.0%} (VCI fills open = prior close)")
        if pd.notna(r["kbs_flat"]) and r["kbs_flat"] > 0.10: cav.append(f"KBS flat opens {r['kbs_flat']:.0%}")
        elif pd.notna(r["kbs_flat"]) and r["kbs_flat"] > 0.02: cav.append(f"KBS flat opens {r['kbs_flat']:.1%}")
        r["caveat"] = "; ".join(cav) or "-"; yrows.append(r)
    VY = pd.DataFrame(yrows)
    pairs = []
    for src, D_ in (("VCI", V), ("VCI flagged dropped", V[~V.flat]), ("KBS", K)):
        for y in range(2013, 2027):
            a, b = D_[D_.index.year == y], D_[D_.index.year == y - 1]
            if len(a) < 100 or len(b) < 100: continue
            pairs.append(dict(source=src, pair=f"{y-1}->{y}", **reloc(a, b)))
        a, b = D_.loc["2022-08-25":"2023-08-24"], D_.loc["2021-08-25":"2022-08-24"]
        if len(a) > 100 and len(b) > 100: pairs.append(dict(source=src, pair="cutover year (report-only) 21/22->22/23", **reloc(a, b)))
    VP = pd.DataFrame(pairs)
    vt = VY[["year", "vci_n", "vci_flat", "vci_ON_bp", "vci_ON_t", "vci_ID_bp", "vci_ID_t", "vci_C2C_bp", "vci_C2C_t", "kbs_n", "kbs_flat", "kbs_ON_bp", "kbs_ON_t", "kbs_ID_bp", "kbs_ID_t", "kbs_C2C_bp", "kbs_C2C_t"]]
    vdrop = VY[["year", "vcidrop_ON_bp", "vcidrop_ON_t", "vcidrop_ID_bp", "vcidrop_ID_t", "vcidrop_C2C_bp", "vcidrop_C2C_t"]]
    def sig(src, pr):
        q = VP[(VP.source == src) & (VP.pair == pr)]
        if q.empty: return f"{src} {pr}: n/a"
        q = q.iloc[0]; return (f"{src} {pr}: dON {q.dON_bp:+.1f} (t {q.tON:.2f}), dID {q.dID_bp:+.1f} (t {q.tID:.2f}), dC2C {q.dC2C_bp:+.1f} (t {q.tC2C:.2f}) -> "
                               f"{'RELOCATION' if q.relocation else 'no relocation signature'}")
    bg = VP[~VP.pair.str.startswith("cutover")].groupby("source").relocation.agg(["sum", "size"])
    M += ["## 4. VNINDEX legs by year (one-day nights, mean bp, NW t)", "",
          "VCI primary (flagged opens kept); KBS alongside from 2018-11-19. Caveats per year:", ""] + [f"- {r.year}: {r.caveat}" for _, r in VY.iterrows()] + ["",
          "```", vt.to_string(index=False, float_format=lambda v: f"{v:.2f}"), "```", "", "Check: VCI with flagged (open == prior close) days dropped:", "",
          "```", vdrop.to_string(index=False, float_format=lambda v: f"{v:.2f}"), "```", "",
          "Adjacent-year relocation test (R2 verbatim: |t(dC2C)| < 2, t(dON) >= 2, t(dID) <= -2; d = later - earlier):", "",
          "```", VP.to_string(index=False, float_format=lambda v: f"{v:.2f}"), "```", "",
          "Reading of '2018' and '2023': adjacent calendar years Y-1 vs Y (stated in the header; the project defines no other dates for them). "
          "2023 is AFTER the 2022-08-25 cutover, and 2022 contains about four months of the post-cutover regime, so 2022->2023 straddles the cutover and is not an independent event.", "",
          "- " + sig("VCI", "2017->2018"), "- " + sig("VCI flagged dropped", "2017->2018"), "- " + sig("VCI", "2022->2023"), "- " + sig("KBS", "2022->2023"),
          "- Cutover year, report-only: " + sig("VCI", "cutover year (report-only) 21/22->22/23") + "; " + sig("KBS", "cutover year (report-only) 21/22->22/23"),
          "- Background: relocation signature in " + ", ".join(f"{s} {int(r['sum'])}/{int(r['size'])}" for s, r in bg.iterrows()) + " adjacent-year pairs; pairs flagged: "
          + (", ".join(f"{r.source} {r.pair}" for _, r in VP[VP.relocation & ~VP.pair.str.startswith('cutover')].iterrows()) or "none") + ".", ""]

    # ---------------- S5
    MC = pd.read_csv(OUT / "regime_legs_monday.csv")
    mrows = []
    for per, lo, hi in (("2018-11..2021", "2018-11-21", "2021-12-31"), ("pre 2022-08-25", "2018-11-21", "2022-08-24")):
        s = J.loc[lo:hi]; mon, oth = s[s.wd == 1].b_ON, s[s.wd.isin([2, 3, 4])].b_ON
        c = MC[(MC.period == per) & (MC.night == "Mon->Tue")].iloc[0]; m = ms(mon)
        assert abs(m["mean_bp"] - c.basket_ON_bp) < 1e-9 and m["n"] == c.n, f"Monday recompute differs ({per})"
        dd = dif(mon, oth); allm = ms(s.b_ON)
        mrows.append(dict(window=per, csv_basket_mon_bp=c.basket_ON_bp, csv_basket_mon_t=c.basket_t, n_mon=int(c.n), other_nights_bp=dd["pre_bp"], other_nights_t=dd["pre_t"], n_other=dd["n_pre"],
                          mon_minus_other_bp=dd["d_bp"], mon_minus_other_t=dd["t"], lo95=dd["lo95"], hi95=dd["hi95"], distinguishable=abs(dd["t"]) >= 2,
                          all_nights_bp=allm["mean_bp"], all_nights_t=allm["t"], onesample_vs_allmean_t_reportonly=(c.basket_ON_bp - allm["mean_bp"]) / (c.basket_ON_bp / c.basket_t)))
    MO = pd.DataFrame(mrows); mo = MO.set_index("window")
    M += ["## 5. Basket Mon->Tue overnight (read-out from regime_legs_monday.csv)", "",
          "Note: in regime_legs_monday.csv the 8.05 bp basket figure is the **2018-11..2021** row, not 2018-11..2022-08-24. Both rows are shown; recomputed values equal the CSV exactly.", "",
          "```", MO.to_string(index=False, float_format=lambda v: f"{v:.2f}"), "```", "",
          f"- 2018-11-21..2022-08-24: basket Mon->Tue {mo.loc['pre 2022-08-25','csv_basket_mon_bp']:.2f} bp (t {mo.loc['pre 2022-08-25','csv_basket_mon_t']:.2f}, n {int(mo.loc['pre 2022-08-25','n_mon'])}); "
          f"minus other one-day nights {mo.loc['pre 2022-08-25','mon_minus_other_bp']:+.2f} bp (t {mo.loc['pre 2022-08-25','mon_minus_other_t']:.2f}) -> "
          f"{'distinguishable' if mo.loc['pre 2022-08-25','distinguishable'] else 'NOT distinguishable'}. All-night mean {mo.loc['pre 2022-08-25','all_nights_bp']:.2f} bp.",
          f"- 2018-11..2021: basket Mon->Tue {mo.loc['2018-11..2021','csv_basket_mon_bp']:.2f} bp (t {mo.loc['2018-11..2021','csv_basket_mon_t']:.2f}, n {int(mo.loc['2018-11..2021','n_mon'])}); "
          f"minus other nights {mo.loc['2018-11..2021','mon_minus_other_bp']:+.2f} bp (t {mo.loc['2018-11..2021','mon_minus_other_t']:.2f}) -> "
          f"{'distinguishable' if mo.loc['2018-11..2021','distinguishable'] else 'NOT distinguishable'}.", ""]

    # ---------------- outputs
    SC.to_csv(OUT / f"{NAME}_scan.csv", index=False); SU.to_csv(OUT / f"{NAME}_summary.csv", index=False); PL.to_csv(OUT / f"{NAME}_placebo.csv", index=False)
    RA.to_csv(OUT / f"{NAME}_ramp.csv", index=False); VY.to_csv(OUT / f"{NAME}_vnindex_year.csv", index=False); VP.to_csv(OUT / f"{NAME}_vnindex_pairs.csv", index=False)
    MO.to_csv(OUT / f"{NAME}_monday.csv", index=False)
    H1 = tree_hash()
    M += ["Caveats: pre-2022-06 futures opens unverified; one-day nights only; stock flat opens kept; VNINDEX opens per the caveat list.", "",
          "Rerun 1: text only (summary wording, date-mapping note, scan-CSV pointer); statistics and seeds unchanged, CSV md5 identical to run 0 (checked outside the script).", "",
          f"Integrity: md5 of every pre-existing file in data/raw/, data/raw_kbs_index/ and results/ identical before and after: {H0 == H1} ({len(H0)} files).", ""]

    su = SU.set_index("series"); cw = su.loc["CW ON"]; rcw = RK.set_index("series")
    det = ", ".join(f"{k} {r.ls_date} [{r.ci_lo}..{r.ci_hi}]{' cut in' if r.cut_inside else ' cut OUT'}" for k, r in su[su.detected].iterrows()) or "none"
    nod = ", ".join(su[~su.detected].index) or "none"
    q18 = VP[(VP.source == "VCI") & (VP.pair == "2017->2018")]; q23v = VP[(VP.source == "VCI") & (VP.pair == "2022->2023")]; q23k = VP[(VP.source == "KBS") & (VP.pair == "2022->2023")]
    yn = lambda q: "n/a" if q.empty else ("YES" if q.iloc[0].relocation else "no")
    pm = mo.loc["pre 2022-08-25"]; p18 = mo.loc["2018-11..2021"]
    M += ["## Summary (5 lines)", "",
          f"1. Break date: CW ON LS break {cw.ls_date}, 95% interval {cw.ci_lo}..{cw.ci_hi} ({cw.ci_width_nights} nights; 2022-08-25 {'inside' if cw.cut_inside else 'OUTSIDE'}, but the interval does not single it out: cutover |t| ranks {cw.rank_of_cut_abs_t}/{cw.n_candidates}); sup|t| {cw.sup_abs_t:.2f} vs block-bootstrap 5% critical {cw.boot_crit95:.2f} (Holm p {cw.p_holm:.3f}). "
          f"ON legs: LS dates {su.loc['CW ON','ls_date']} (CW), {su.loc['EW ON','ls_date']} (EW), paired {su.loc['PAIRED CW-FUT ON','ls_date']}; ID legs: LS date {su.loc['CW ID','ls_date']} (CW, rank of cutover {su.loc['CW ID','rank_of_cut_abs_t']}) and {su.loc['EW ID','ls_date']} (EW, rank {su.loc['EW ID','rank_of_cut_abs_t']}). "
          f"Holm p < 0.05: {', '.join(su[su.detected].index)}; not detected (interval uninformative): {nod}.",
          f"2. Placebo (±{W} nights, local window): random 2019-21 dates with |t| above the 08-25 value: " + ", ".join(f"{k} {int(r.n_random_above)}/10" for k, r in rcw.iterrows()) + f"; CW ON t at 08-25 only {rcw.loc['CW ON','t_window_cut']:.2f} (max random {rcw.loc['CW ON','max_abs_random']:.2f}) vs {PL[(PL.series=='CW ON')&(PL.k==named[3])].t_window.iloc[0]:.2f} at the 2022-11-18 named date (mapped to {dates[named[3]].date()}).",
          f"3. Sharpness (CW ON): dAIC ramp - step {ra.dAIC_ramp_minus_step:+.2f} -> {ra.verdict}; EW ON {RA.set_index('series').loc['EW ON','dAIC_ramp_minus_step']:+.2f}, paired {RA.set_index('series').loc['PAIRED CW-FUT ON','dAIC_ramp_minus_step']:+.2f} ({int(ra.nights_inside_ramp)} nights inside the ramp).",
          f"4. Earlier relocations (VNINDEX, R2 rule, Y-1 vs Y): 2017->2018 no - ON FELL ({q18.iloc[0].dON_bp:+.1f} bp, t {q18.iloc[0].tON:.2f}), the opposite direction; 2022->2023 NOT ROBUST: R2 met only in VCI with flagged opens kept (dID t {q23v.iloc[0].tID:.2f}), not with flagged dropped (t {VP[(VP.source=='VCI flagged dropped')&(VP.pair=='2022->2023')].iloc[0].tID:.2f}) or KBS (t {q23k.iloc[0].tID:.2f}); ON up (t > 3) and C2C flat in all three. 2022->2023 straddles the cutover, so it is not an independent event; background "
          + ", ".join(f"{s} {int(r['sum'])}/{int(r['size'])}" for s, r in bg.iterrows()) + " adjacent pairs.",
          f"5. Monday basket: 2018-11-21..2022-08-24 Mon->Tue {pm.csv_basket_mon_bp:.2f} bp (t {pm.csv_basket_mon_t:.2f}), minus other nights {pm.mon_minus_other_bp:+.2f} (t {pm.mon_minus_other_t:.2f}) -> {'distinguishable' if pm.distinguishable else 'not distinguishable'}; the 8.05 bp figure is the 2018-11..2021 row (t {p18.csv_basket_mon_t:.2f}; vs other nights t {p18.mon_minus_other_t:.2f})."]
    (OUT / f"{NAME}_audit.md").write_text("\n".join(M) + "\n"); print("\n".join(M))


if __name__ == "__main__":
    main()
