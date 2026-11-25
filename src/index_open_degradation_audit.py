"""Diagnostic: is the VN30 index open degraded 2019 .. mid-2021 (H1), and is there a futures/index date misalignment in 2019 (H2)?
READ-ONLY on data/raw/ and results/. Writes only results/index_open_degradation_audit.md and index_open_degradation_*.csv.
Regime and Monday-share results are NOT recomputed (none is printed, not even as a by-product).

Pre-registered (fixed before the first run):
 H2 lag test. Index series shifted by positions in its OWN full trading calendar, then masked (index open flagged -> NaN).
    corr(fut(t), idx(t+k)), k in -2..+2, futures nights aligned with the index at k = 0. An off-zero peak SUPPORTS H2 only if
    (i) the peak corr is significant (Fisher z > 1.96), (ii) z(peak) - z(lag 0) > 2*sqrt(2/(n-3)) on the same nights, and
    (iii) close-to-close shows the same peak lag. If CC peaks at 0 and ON does not, a whole-file date shift is ruled out
    (only an open-field-only shift would remain).
 H1 basket test. Primary: index ON with flagged index opens dropped (continuity with the stability audit), PIT cap-weighted basket
    with ALL stock-days kept (version c), one-day nights, common dates of index, basket and futures. SUPPORT for H1 if, pooled over
    2020Q1-2021Q2, SD(index ON) / SD(basket ON) < 0.50 while the pooled verified-window (2022-11-03..) ratio lies in [0.80, 1.25].
    Reading map: basket normal & index collapsed -> index computation degraded (H1 supported);
                 both collapsed similarly -> anchoring at constituent level (rule fails, index open NOT cleared, basket not a clean reference);
                 neither collapsed -> H1 refuted.
    Version a (flagged stock-days dropped) removes zeros and inflates basket SD: biased toward H1, reported but never counted as support.
Usage: python3 src/index_open_degradation_audit.py
"""
from __future__ import annotations
import hashlib, math, sys, warnings
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from level_a import RAW_DIR, OUT_DIR, decompose

OUT = OUT_DIR
NEW = {"index_open_degradation_audit.md", "index_open_degradation_lags.csv", "index_open_degradation_quarterly.csv", "index_open_degradation_covid.csv"}


def tree_hash():
    H = {}
    for d in (RAW_DIR, OUT):
        for p in sorted(d.glob("*")):
            if p.is_file() and p.name not in NEW: H[str(p)] = hashlib.md5(p.read_bytes()).hexdigest()
    return H


H0 = tree_hash()
import futures_roll_gap_repair as RG
import futures_open_stability_audit as SA
import pit_dayofweek_2x2 as X
import open_filter_audit as OA

VER_LO = "2022-11-03"
LIM = 0.07


def fz(r): return math.atanh(max(min(r, 0.999999), -0.999999))
def qlabel(ix): return ix.to_period("Q").astype(str)


# ------------------------------------------------------------------ Step 1: lags
def lag_test():
    f = RG.futures_nights_from(RG.rd("VN30F1M")); i = RG.index_nights_fixed()
    j = RG.panel_from(f, i); j = j[j.aligned].copy()
    j["fut_CC"] = np.log(j.close / j.entry)
    iv = i.copy(); iv["idx_CC"] = np.log(iv.close / iv.prev_close)
    flag = iv.idx_flag.astype(bool)
    pos = pd.Series(np.arange(len(iv)), index=iv.index)
    groups = [(q, j[qlabel(j.index) == q]) for q in sorted(set(qlabel(j.index))) if "2018Q4" <= q <= "2022Q2"] + [(f"VERIFIED {VER_LO}..", j.loc[VER_LO:])]
    rows = []
    for g, s in groups:
        p = pos.reindex(s.index).values
        for leg in ("ON", "CC"):
            r = {}
            nights = None
            for k in range(-2, 3):
                q = p + k; ok = (q >= 0) & (q < len(iv))
                xi = np.full(len(s), np.nan); xi[ok] = iv[f"idx_{leg}"].values[q[ok]]
                if leg == "ON":
                    fl = np.full(len(s), True); fl[ok] = flag.values[q[ok]]; xi[fl] = np.nan
                r[k] = xi
            M = pd.DataFrame(r, index=s.index); M["y"] = s[f"fut_{leg}"].values
            Mc = M.dropna()                                   # same nights for every lag
            n = len(Mc); cors = {k: Mc.y.corr(Mc[k]) for k in range(-2, 3)}
            pk = max(cors, key=lambda k: cors[k])
            se = 1 / math.sqrt(n - 3) if n > 3 else np.nan
            rows.append(dict(period=g, leg=leg, n=n, **{f"corr_k{k:+d}": cors[k] for k in range(-2, 3)}, peak_lag=pk, peak_corr=cors[pk],
                             peak_sig=fz(cors[pk]) / se > 1.96, peak_beats_lag0=(fz(cors[pk]) - fz(cors[0])) > 2 * math.sqrt(2) * se))
    L = pd.DataFrame(rows)
    on = L[L.leg == "ON"].set_index("period"); cc = L[L.leg == "CC"].set_index("period")
    L["H2_support"] = [(r.leg == "ON") and r.peak_lag != 0 and r.peak_sig and r.peak_beats_lag0 and cc.loc[r.period, "peak_lag"] == r.peak_lag for _, r in L.iterrows()]
    return L


# ------------------------------------------------------------------ Step 2: basket construct
def stock_flags():
    """per stock-day: open == prior close (open_suspicious), |ON| >= 7% (limit open), on all days; plus one-day mask."""
    F, Lm, V = {}, {}, {}
    for t in X.tickers:
        d = decompose(pd.read_csv(RAW_DIR / f"{t}.csv", parse_dates=["date"])).set_index("date")
        F[t] = d.open_suspicious.astype(bool); Lm[t] = d.r_overnight.abs() >= LIM - 0.0015; V[t] = d.r_overnight.notna()
    return pd.DataFrame(F).sort_index(), pd.DataFrame(Lm).sort_index(), pd.DataFrame(V).sort_index()


def member_weights():
    """date -> (EW names, cap weights at prior close) using the PIT membership / weights of pit_dayofweek_2x2."""
    W = X.build_weights("pit", "B"); return W, sorted(W)


def basket_series(version, scheme, one_day=True):
    ds, db = OA.VERS[version]
    R = OA.ret_panel(ds, db, one_day=one_day)
    return OA.with_ret(R, lambda: X.cell_series("pit", scheme, "B"))


def constituent_shares(W, ed, F, Lm, PCx):
    rows = {}
    idx = F.loc[X.START:].index
    for t in idx:
        e = [x for x in ed if x <= t]
        if not e: continue
        w = W[e[-1]]; names = [n for n in w.index if n in F.columns]
        f = F.loc[t, names]; l = Lm.loc[t, names]; p = PCx.reindex(index=[t], columns=names).iloc[0] if t in PCx.index else pd.Series(np.nan, index=names)
        valid = f.notna()
        cw = (w[names] * p).where(valid)
        rows[t] = dict(n_const=int(valid.sum()), share_flat_ew=f[valid].mean(), share_flat_cw=(cw * f.astype(float)).sum() / cw.sum() if cw.sum() > 0 else np.nan,
                       share_limit_ew=l[valid].mean(), share_limit_cw=(cw * l.astype(float)).sum() / cw.sum() if cw.sum() > 0 else np.nan)
    return pd.DataFrame(rows).T


def quarterly_sd(B, idx_on, idx_on_all, fut_on, CS):
    rows = []
    def one(g, dates, bname, b):
        J = pd.concat({"idx": idx_on, "bas": b, "fut": fut_on}, axis=1, join="inner").dropna()
        J = J[J.index.isin(dates)]
        Ja = pd.concat({"idx": idx_on_all, "bas": b, "fut": fut_on}, axis=1, join="inner").dropna(); Ja = Ja[Ja.index.isin(dates)]
        if len(J) < 10: return None
        r = SA.ols(J.idx * 1e4, J.bas * 1e4)
        rfb = SA.ols(J.fut * 1e4, J.bas * 1e4); rfi = SA.ols(J.fut * 1e4, J.idx * 1e4)      # ADDED AFTER FIRST RUN (localises the weak leg)
        cs = CS[CS.index.isin(J.index)]
        return dict(period=g, basket=bname, n=len(J), sd_idx_bp=J.idx.std() * 1e4, sd_bas_bp=J.bas.std() * 1e4, sd_fut_bp=J.fut.std() * 1e4,
                    mean_idx_bp=J.idx.mean() * 1e4, mean_bas_bp=J.bas.mean() * 1e4, mean_fut_bp=J.fut.mean() * 1e4,
                    ratio_idx_over_bas=J.idx.std() / J.bas.std(), slope_idx_on_bas=r["k"], slope_nw_se=r["se_k"], r2=r["r2"],
                    sd_fut_over_bas=J.fut.std() / J.bas.std(), r2_fut_on_bas=rfb["r2"], r2_fut_on_idx=rfi["r2"], k_fut_on_bas=rfb["k"],
                    n_incl_flagged_idx=len(Ja), ratio_incl_flagged_idx=Ja.idx.std() / Ja.bas.std(),
                    share_flat_ew=cs.share_flat_ew.mean(), share_flat_cw=cs.share_flat_cw.mean(), share_limit_ew=cs.share_limit_ew.mean(), share_limit_cw=cs.share_limit_cw.mean())
    allq = sorted(set(qlabel(idx_on.index)))
    for bname, b in B.items():
        for q in allq:
            dates = idx_on_all.index[qlabel(idx_on_all.index) == q]; x = one(q, dates, bname, b)
            if x: rows.append(x)
        for g, lo, hi in (("POOLED 2020Q1-2021Q2", "2020-01-01", "2021-06-30"), ("POOLED 2019", "2019-01-01", "2019-12-31"),
                          (f"POOLED verified {VER_LO}..", VER_LO, "2026-12-31"), ("POOLED pre 2018-11..2022-06", "2018-11-01", "2022-06-30")):
            dates = idx_on_all.loc[lo:hi].index; x = one(g, dates, bname, b)
            if x: rows.append(x)
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ Step 3: COVID
def covid(CS_all, Ball):
    f1 = RG.rd("VN30F1M"); f2 = RG.rd("VN30F2M"); d = RG.build_from(f1, 0, 0.0)
    d["fut_ON_bp"] = np.log(d.open / d.entry) * 1e4
    m = d.loc["2020-03-01":"2020-03-31"]; top = m.fut_ON_bp.abs().sort_values(ascending=False).index[:10]
    i = RG.index_nights_fixed()
    rows = []
    for t in sorted(top):
        r = d.loc[t]; ii = i.loc[t] if t in i.index else None
        f2p = f2.close.shift(1).get(t, np.nan); f2o = f2.open.get(t, np.nan)
        rows.append(dict(date=str(t.date()), weekday=t.day_name()[:3], fut_entry=r.entry, fut_open=r.open, fut_ON_bp=r.fut_ON_bp,
                         f2m_prev_close=f2p, f2m_open=f2o, f2m_ON_bp=np.log(f2o / f2p) * 1e4 if pd.notna(f2o) and pd.notna(f2p) else np.nan,
                         idx_prev_close=ii.prev_close if ii is not None else np.nan, idx_open=ii.open if ii is not None else np.nan,
                         idx_ON_bp=ii.idx_ON * 1e4 if ii is not None else np.nan, idx_flag=bool(ii.idx_flag) if ii is not None else None,
                         basket_cw_all_nights_bp=Ball["cap"].r.get(t, np.nan) * 1e4, basket_ew_all_nights_bp=Ball["ew"].r.get(t, np.nan) * 1e4,
                         const_flat_ew=CS_all.share_flat_ew.get(t, np.nan), const_flat_cw=CS_all.share_flat_cw.get(t, np.nan),
                         const_limit_ew=CS_all.share_limit_ew.get(t, np.nan), const_limit_cw=CS_all.share_limit_cw.get(t, np.nan)))
    return pd.DataFrame(rows)


EXPOSED = [
    ("Mechanically biased if idx_ON is pinned near 0 (dbasis ~ fut_ON)", [
        "futures_basis_summary.md R1: Monday dbasis share of futures ON 2018-11..2021 = 82% (t 2.21; 80%, t 2.29 ex-flagged) -> pushed toward 100%",
        "futures_basis_summary.md: pre-2022-08-25 Mon->Tue dbasis_ON +12.82 bp (t 2.58) and idx_ON 0.06 bp -> basis absorbs the futures move",
        "open_audit_summary.md regime split: published VN30 overnight pre-2022-08-25 0.89 bp (t 0.70) vs post 9.99 bp -> pre value affected; direction of correction not established (pinned days are set to 0, so the mean moves toward the unaffected days' mean, not necessarily toward 0); "
        "Level A VN30 pre-period overnight likewise",
        "futures_basis_followup: pre-cutover dbasis weekday tests (Mon->Tue minus others t 2.09 / 2.24)"]),
    ("Exposed, direction depends on the mechanism (uniform scaling inflates k; pinning a fraction of days to 0 attenuates it)", [
        "futures_basis_summary.md R3 slopes 2019 0.36, 2020 0.98, 2021 0.46 (and 2018 0.84, 2022 0.71)",
        "futures_basis_followup offset: pre-cutover reference (a +4.9 bp, k 0.64)",
        "futures_open_stability_audit.md: 2020Q1-2021Q2 attribution of the weak ON relation to the index leg; 2019 'unexplained'"]),
    ("Exposed split, total unaffected", [
        "pit_residual_split.csv: replica->index and index->futures legs pre-2022 (replica->futures total does not use the index)",
        "futures_basis_summary.md R2 decomposition basket-minus-futures 5.01 = basket-minus-index 0.91 + index-minus-futures 4.10 bp (Wed->Thu; index-sample years)",
        "open_audit_summary.md basket-vs-published-index gap 3.82 bp (filtered) / 0.08 bp (unfiltered) and its weekday shape (Mon->Tue +4.0, Thu->Fri -4.1 bp), pre-2022 part",
        "open_quality.md / level_a_summary*.csv VN30 rows (VNINDEX rows share the same issue type: same vendor feed)"]),
    ("Not exposed", [
        "Level C futures (VN30F1M only), level_c_phase2, phase2_trackforward_spec.md, forward track log",
        "Stock baskets (Level B, PIT 2x2) - they use stock opens, which carry their own flat-open issue (open_audit flags 20-34%/yr), not the index open",
        "CUTOVER = 2022-08-25 itself: set from the T+2 settlement rule (VSD 109/110, option_c_t2_equity.py), not from index-open behaviour"]),
]


def fm(x, f="{:.3f}"): return "" if pd.isna(x) else f.format(x)


def main():
    L = lag_test()
    # index ON (one-day nights handled by basket intersection), flagged dropped / kept
    i = RG.index_nights_fixed()
    idx_on = i.idx_ON[~i.idx_flag.astype(bool)]; idx_on_all = i.idx_ON
    fut = RG.futures_nights_from(RG.rd("VN30F1M")); fut_on = fut.fut_ON.dropna()
    B = {"cw_c_allkept": basket_series("c", "cap").r, "ew_c_allkept": basket_series("c", "ew").r,
         "cw_a_flagdropped": basket_series("a", "cap").r, "ew_a_flagdropped": basket_series("a", "ew").r}
    F, Lm, V = stock_flags(); W, ed = member_weights()
    CS = constituent_shares(W, ed, F, Lm, X.PC)
    Q = quarterly_sd(B, idx_on, idx_on_all, fut_on, CS)
    Ball = {"cap": basket_series("c", "cap", one_day=False), "ew": basket_series("c", "ew", one_day=False)}
    C = covid(CS, Ball)

    L.to_csv(OUT / "index_open_degradation_lags.csv", index=False)
    Q.to_csv(OUT / "index_open_degradation_quarterly.csv", index=False)
    C.to_csv(OUT / "index_open_degradation_covid.csv", index=False)

    P = Q[Q.basket == "cw_c_allkept"].set_index("period")
    r_h1 = P.loc["POOLED 2020Q1-2021Q2", "ratio_idx_over_bas"]; r_ver = P.loc[f"POOLED verified {VER_LO}..", "ratio_idx_over_bas"]
    h1 = (r_h1 < 0.5) and (0.8 <= r_ver <= 1.25)
    qh = [q for q in P.index if "2020Q1" <= q <= "2021Q2"]
    nq_h1 = sum(P.loc[q, "ratio_idx_over_bas"] < 0.5 for q in qh)

    M = ["# Index open degradation audit (VN30 index open 2018-2022)", "",
         "Diagnostic only. Read-only on data/raw/ and results/; regime and Monday-share results are not recomputed. Script: `src/index_open_degradation_audit.py`.", "",
         "Hypotheses (fixed by the brief): H1 the VN30 index open is degraded 2019 .. mid-2021 (e.g. reference prices for constituents with no ATO match anchor it near the prior close). "
         "H2 a date misalignment between the futures and index files in some 2019 quarters.", "",
         "## Pre-registered rules (script header, fixed before the first run)", "",
         "- H2: index shifted by positions in its own full calendar, then flagged opens masked; all five lags on the same nights. Off-zero peak supports H2 only if the peak is significant "
         "(Fisher z > 1.96), beats lag 0 by > 2 sqrt(2/(n-3)) in z, and close-to-close peaks at the same lag. CC at 0 with ON off zero rules out a whole-file shift.",
         "- H1: primary = index ON with flagged index opens dropped vs PIT cap-weighted basket with all stock-days kept, one-day nights, common index/basket/futures dates. "
         "Support if pooled 2020Q1-2021Q2 SD(index)/SD(basket) < 0.50 while the pooled verified ratio is in [0.80, 1.25]. "
         "Reading map: basket normal & index collapsed -> index computation degraded (H1); both collapsed -> constituent-level anchoring (index not cleared, basket not a clean reference); neither -> H1 refuted.",
         "- Version a (flagged stock-days dropped) removes zero returns and inflates basket SD: biased toward H1; reported, never counted as support (the open-filter audit's selection-on-outcome caveat: "
         "flagged names close 11.7 bp below unflagged names on the same date, t -5.77, so dropping them selects on the outcome).", ""]

    M += ["## 1. Lag test (futures overnight t vs index overnight t+k; aligned nights)", ""]
    T = L.copy()
    for c in [c for c in T.columns if c.startswith("corr_")] + ["peak_corr"]: T[c] = T[c].map(fm)
    M += ["```", T.to_string(index=False), "```", ""]
    on = L[L.leg == "ON"]; cc = L[L.leg == "CC"]
    off_on = list(on[on.peak_lag != 0].period); off_cc = list(cc[cc.peak_lag != 0].period); sup = list(L[L.H2_support].period)
    M += [f"- ON peak off lag 0 in: {', '.join(f'{r.period} (k {r.peak_lag:+d}, r {r.peak_corr:.2f}, sig {r.peak_sig}, beats 0 {r.peak_beats_lag0})' for _, r in on[on.peak_lag != 0].iterrows()) or 'none'}.",
          f"- CC peak off lag 0 in: {', '.join(off_cc) or 'none'}; CC lag-0 corr range over pre-period quarters {cc[cc.period < 'V']["corr_k+0"].min():.2f}-{cc[cc.period < 'V']["corr_k+0"].max():.2f} "
          f"(verified {cc[cc.period >= 'V']["corr_k+0"].iloc[0]:.2f}).",
          f"- H2 supported (all three conditions) in: {', '.join(sup) or 'none'}.", ""]
    for q in ("2019Q1", "2019Q3", "2019Q4"):
        r = on.set_index("period").loc[q]; c_ = cc.set_index("period").loc[q]
        M += [f"- {q}: ON corr k-2..+2 = {', '.join(fm(r[f'corr_k{k:+d}'], '{:.2f}') for k in range(-2, 3))} (n {r.n}); CC = {', '.join(fm(c_[f'corr_k{k:+d}'], '{:.2f}') for k in range(-2, 3))}."]
    M += [""]

    M += ["## 2. Index-open construct: PIT constituent basket vs published index (one-day nights, common dates)", "",
          "SDs and means in bp; ratio = SD(index ON)/SD(basket ON); slope/R^2 = index ON on basket ON; flat = constituent open == prior close (open_suspicious); "
          "limit = |constituent ON| >= ~6.85% (limit open). Shares are averaged over the quarter's common dates (ew = equal weight over PIT members, cw = cap weight). "
          "Mondays and holidays drop out (baskets use one-day nights only). r2_fut_on_bas / r2_fut_on_idx: ADDED AFTER THE FIRST RUN (futures ON on basket / on index, same dates). "
          "First run had a bug in ratio_incl_flagged_idx (date set taken from unflagged days, so flagged days never entered); fixed before reporting.", ""]
    show = ["period", "n", "sd_idx_bp", "sd_bas_bp", "sd_fut_bp", "mean_idx_bp", "mean_bas_bp", "mean_fut_bp", "ratio_idx_over_bas", "ratio_incl_flagged_idx", "slope_idx_on_bas", "r2",
            "r2_fut_on_bas", "r2_fut_on_idx", "k_fut_on_bas", "sd_fut_over_bas", "share_flat_ew", "share_flat_cw", "share_limit_cw"]
    for b in B:
        T = Q[Q.basket == b][show].copy()
        for c in show[2:]: T[c] = T[c].map(lambda v: fm(v, "{:.1f}") if c.endswith("_bp") else fm(v))
        M += [f"### basket {b}" + (" (PRIMARY)" if b == "cw_c_allkept" else (" (biased toward H1; not counted)" if "_a_" in b else "")), "", "```", T.to_string(index=False), "```", ""]
    Pa = Q[Q.basket == "cw_a_flagdropped"].set_index("period")
    Pe = Q[Q.basket == "ew_c_allkept"].set_index("period")
    M += [f"- PRIMARY rule: pooled 2020Q1-2021Q2 ratio {r_h1:.3f} (< 0.50 needed); pooled verified ratio {r_ver:.3f} (in [0.80, 1.25] needed) -> H1 {'SUPPORTED' if h1 else 'NOT SUPPORTED by the rule'}. "
          f"Quarters 2020Q1-2021Q2 with ratio < 0.50: {nq_h1}/{len(qh)}.",
          f"- Pooled 2020Q1-2021Q2: SD index {P.loc['POOLED 2020Q1-2021Q2','sd_idx_bp']:.1f}, basket {P.loc['POOLED 2020Q1-2021Q2','sd_bas_bp']:.1f}, futures {P.loc['POOLED 2020Q1-2021Q2','sd_fut_bp']:.1f} bp; "
          f"verified: index {P.loc[f'POOLED verified {VER_LO}..','sd_idx_bp']:.1f}, basket {P.loc[f'POOLED verified {VER_LO}..','sd_bas_bp']:.1f}, futures {P.loc[f'POOLED verified {VER_LO}..','sd_fut_bp']:.1f} bp.",
          f"- Other baskets, pooled 2020Q1-2021Q2 ratio: EW all-kept {Pe.loc['POOLED 2020Q1-2021Q2','ratio_idx_over_bas']:.3f} (verified {Pe.loc[f'POOLED verified {VER_LO}..','ratio_idx_over_bas']:.3f}); "
          f"CW flag-dropped {Pa.loc['POOLED 2020Q1-2021Q2','ratio_idx_over_bas']:.3f} (verified {Pa.loc[f'POOLED verified {VER_LO}..','ratio_idx_over_bas']:.3f}; biased toward H1).",
          f"- With flagged index opens kept (zeros in): pooled 2020Q1-2021Q2 ratio {P.loc['POOLED 2020Q1-2021Q2','ratio_incl_flagged_idx']:.3f}, verified {P.loc[f'POOLED verified {VER_LO}..','ratio_incl_flagged_idx']:.3f}.",
          f"- Pooled 2019: ratio {P.loc['POOLED 2019','ratio_idx_over_bas']:.3f}, slope {P.loc['POOLED 2019','slope_idx_on_bas']:.3f}, R^2 {P.loc['POOLED 2019','r2']:.3f}; "
          f"constituent flat share cw {P.loc['POOLED 2019','share_flat_cw']:.3f} vs verified {P.loc[f'POOLED verified {VER_LO}..','share_flat_cw']:.3f}.", ""]

    M += ["## 3. COVID check: 10 largest |futures ON| nights in 2020-03", "",
          "Futures = continuous VN30F1M (no per-contract ticker exists for 2020); F2M = continuous VN30F2M as a second contract with its own prints. "
          "Baskets here use ALL nights (one_day=False, version c), so Monday nights are included; const_* = constituent shares on that date.", "",
          "```", C.to_string(index=False, float_format=lambda v: f"{v:.2f}"), "```", ""]

    reg = C[(C.idx_ON_bp.abs() >= 0.5 * C.basket_cw_all_nights_bp.abs()) & (C.idx_flag == False)]
    same_sign_f2 = int((np.sign(C.fut_ON_bp) == np.sign(C.f2m_ON_bp)).sum())
    quiet = C[(C.idx_ON_bp.abs() < 10) & (C.basket_cw_all_nights_bp.abs() > 50)]
    M += [f"- Index registered at least half the basket move on {len(reg)}/10 nights ({', '.join(reg.date) or 'none'}); index |ON| < 10 bp while basket |ON| > 50 bp on {len(quiet)}/10 "
          f"({', '.join(quiet.date)}), with constituent flat-open share (cw) {quiet.const_flat_cw.min():.2f}-{quiet.const_flat_cw.max():.2f} on those nights; 1 night index-flagged (2020-03-16).",
          f"- F1M and F2M overnight moves have the same sign on {same_sign_f2}/10 nights and similar size: the continuous futures opens are corroborated by a second contract (same vendor feed, so not independent of the vendor's open definition).",
          "- Futures and basket have opposite signs on 2020-03-17 and 2020-03-24 (futures +105 / +149 bp, basket -325 / -125 bp); not explained here (futures open earlier than the stock ATO is one candidate, untested).", ""]
    pv = P.loc[f"POOLED verified {VER_LO}.."]; ph = P.loc["POOLED 2020Q1-2021Q2"]; p19 = P.loc["POOLED 2019"]
    vmin = P[(P.index >= "2023Q1") & (P.index <= "2026Q4")].ratio_idx_over_bas.min()
    M += ["## Reading", "",
          f"**H2 (date misalignment).** Under the brief's literal sentence, 2019Q3 is a marginal off-zero peak (+1: 0.446 vs 0.440 at lag 0, n 26); it fails the pre-registered margin and CC peaks at 0, so H2 is not supported. Close-to-close peaks at lag 0 in every quarter (corr {cc[cc.period < 'V']['corr_k+0'].min():.2f}-{cc[cc.period < 'V']['corr_k+0'].max():.2f}), so a whole-file date shift is ruled out. "
          "ON peaks off zero in 2019Q3 (+1), 2020Q2 (+1) and 2020Q4 (-1), but none beats lag 0 by the pre-registered margin, and 2019Q1/Q4 peak at 0 with low correlation. "
          f"CC misses the brief's expected corr > 0.9 in 2019Q1-Q3 ({', '.join(f'{v:.2f}' for v in cc.set_index('period').loc[['2019Q1','2019Q2','2019Q3'], 'corr_k+0'])}) and 2020Q2 ({cc.set_index('period').loc['2020Q2','corr_k+0']:.2f}); reported as a miss, not misalignment, since the peak stays at 0. "
          "Caveat: requiring all five lags unflagged cuts ON n to 24-46 in 2019 (index flag rate 9-17%), so the test is weak there.", "",
          f"**H1 (index open degraded): pre-registered rule NOT met, as written.** The 2020Q1-2021Q2 leg holds (ratio {ph.ratio_idx_over_bas:.3f} < 0.50) but the calibration leg fails: "
          f"even in the verified window the index ON SD is only {pv.ratio_idx_over_bas:.3f} of the cap-weighted basket's (< 0.80), so this basket is not a 1:1 index replica and the rule cannot be passed. "
          "This is reported as is and not reinterpreted into support.",
          f"Descriptively: relative to verified, the 2020Q1-2021Q2 ratio is {ph.ratio_idx_over_bas / pv.ratio_idx_over_bas:.2f}x; the quarterly ratios 2020Q2 {P.loc['2020Q2','ratio_idx_over_bas']:.2f}, 2020Q4 {P.loc['2020Q4','ratio_idx_over_bas']:.2f}, "
          f"2021Q1 {P.loc['2021Q1','ratio_idx_over_bas']:.2f}, 2021Q2 {P.loc['2021Q2','ratio_idx_over_bas']:.2f} lie far below every verified quarter (min {vmin:.2f}). "
          f"Constituent flat-open shares are not elevated then (cw {ph.share_flat_cw:.2f} vs verified {pv.share_flat_cw:.2f}), so the reading-map row is 'basket normal, index collapsed'.",
          f"Added after the first run (localises the weak leg, not a pre-registered test): futures-on-basket R^2 pooled 2020Q1-2021Q2 {ph.r2_fut_on_bas:.2f} vs verified {pv.r2_fut_on_bas:.2f}, "
          f"while futures-on-index R^2 is {ph.r2_fut_on_idx:.2f} vs {pv.r2_fut_on_idx:.2f}. The futures open tracks the constituents normally; the index open does not.", "",
          f"**2019 is different.** Index/basket SD ratio {p19.ratio_idx_over_bas:.2f} (no collapse), but constituent flat-open share is higher than in the verified window (cw {p19.share_flat_cw:.2f} vs verified {pv.share_flat_cw:.2f}). "
          f"Futures-on-basket R^2 {p19.r2_fut_on_bas:.2f} (verified {pv.r2_fut_on_bas:.2f}); index-on-basket R^2 {p19.r2:.2f} (verified {pv.r2:.2f}). "
          f"In 2019Q4 index and basket agree with each other (R^2 {P.loc['2019Q4','r2']:.2f}) but neither explains the futures (fut-on-basket {P.loc['2019Q4','r2_fut_on_bas']:.3f}, fut-on-index {P.loc['2019Q4','r2_fut_on_idx']:.3f}) "
          f"in a low-volatility quarter (futures SD {P.loc['2019Q4','sd_fut_bp']:.0f} bp; verified low-vol quarters 2023Q2/Q3 give fut-on-basket {P.loc['2023Q2','r2_fut_on_bas']:.2f}/{P.loc['2023Q3','r2_fut_on_bas']:.2f}). "
          "But 2019Q4 also has the highest constituent flat-open share in the table (cw " + f"{P.loc['2019Q4','share_flat_cw']:.2f}" + "), and index and basket are built from the same opens, so their agreement does not validate either: "
          "the reading map's 'both degraded' row applies. Three candidates remain for 2019Q4: a futures-open problem, genuinely weak co-movement, or constituent-level anchoring degrading both stock-based references. Not separable here.", "",
          "**2021Q3-Q4 (added after the first run, descriptive).** Clean references (index-on-basket R^2 " + f"{P.loc['2021Q3','r2']:.2f}/{P.loc['2021Q4','r2']:.2f}" + ", flat shares "
          + f"{P.loc['2021Q3','share_flat_cw']:.2f}/{P.loc['2021Q4','share_flat_cw']:.2f}" + ", index flags ~0) yet fut-on-basket R^2 " + f"{P.loc['2021Q3','r2_fut_on_bas']:.2f}/{P.loc['2021Q4','r2_fut_on_bas']:.2f}"
          + ". Low-volatility comparison (fut-on-basket R^2, k, fut/basket SD ratio, futures SD):", "", "```",
          P.loc[["2019Q4", "2021Q3", "2021Q4", "2023Q2", "2023Q3", "2024Q1", "2025Q3", "2025Q4"], ["n", "sd_fut_bp", "sd_bas_bp", "r2_fut_on_bas", "k_fut_on_bas", "sd_fut_over_bas", "share_flat_cw"]].round(3).to_string(), "```", "",
          f"2021Q3/Q4 are somewhat below but close to the verified low-volatility quarters 2025Q3/Q4 (R^2 {P.loc['2025Q3','r2_fut_on_bas']:.2f}/{P.loc['2025Q4','r2_fut_on_bas']:.2f}, SD ratio {P.loc['2025Q3','sd_fut_over_bas']:.2f}/{P.loc['2025Q4','sd_fut_over_bas']:.2f}), "
          "so on this comparison 2021H2 is not clearly different from an ordinary low-volatility period on verified opens (no test, n ~50 per quarter); 2019Q4's R^2 is below all of them.", "",
          f"**COVID nights.** The index open failed to register the constituents' overnight move on {len(quiet)} of the 10 largest March-2020 nights (one of them index-flagged); on "
          f"{int((quiet.const_flat_cw < 0.05).sum())} of those {len(quiet)} nights fewer than 5% (cw) of constituents opened flat, so constituent anchoring cannot explain them; "
          "both futures series registered it (F2M from the same vendor feed: corroboration, not independent confirmation). Consistent with an index open taken before constituents' opening prices were in (H1's mechanism), but the computation itself is not observable here.", ""]
    M += ["## Summary (5 lines)", "",
          f"1. Peak lags: 2019Q3 ON is a marginal off-zero peak (+1, 0.446 vs 0.440) under the brief's sentence, but fails the pre-registered margin; close-to-close peaks at 0 in every quarter 2018Q4-2022Q2 (corr {cc[cc.period < 'V']['corr_k+0'].min():.2f}-{cc[cc.period < 'V']['corr_k+0'].max():.2f}); ON peaks off zero only in 2019Q3 (+1), 2020Q2 (+1), 2020Q4 (-1), none beating lag 0 by the pre-registered margin; H2 not supported (whole-file shift ruled out).",
          f"2. H1: pre-registered rule not met as written (2020Q1-2021Q2 index/basket SD ratio {ph.ratio_idx_over_bas:.2f} < 0.50 holds, but the verified calibration ratio is {pv.ratio_idx_over_bas:.2f}, outside [0.80, 1.25]); descriptively 2020Q2, 2020Q4, 2021Q1, 2021Q2 (ratios 0.06-0.35) sit far below every verified quarter (min {vmin:.2f}) with normal constituent flat shares, and futures track the basket (R^2 {ph.r2_fut_on_bas:.2f}) but not the index ({ph.r2_fut_on_idx:.2f}).",
          f"3. COVID: on {len(quiet)}/10 of the largest March-2020 futures nights the index open moved < 10 bp while the constituent basket moved > 50 bp ({int((quiet.const_flat_cw < 0.05).sum())} of them with < 5% of constituents (cw) opening flat); F1M and F2M (same vendor) agree in sign on {same_sign_f2}/10; the index registered the move on only {len(reg)} night.",
          "4. Exposed (not recomputed): mechanically biased if H1 holds - R1 Monday basis share 82% (toward 100%), pre-cutover Mon->Tue dbasis +12.82 bp, follow-up pre-cutover weekday tests; affected, direction not established - pre-cutover VN30 overnight 0.89 bp and Level A VN30 pre-period, R3 slopes 2019-21, pre-cutover offset k 0.64, stability-audit attribution; split only - pit_residual_split legs, R2 0.91 + 4.10 split, open-audit basket-vs-index gap/shape.",
          "5. Open question: 2019Q4 is not explained by H1 or H2 - the futures overnight relates to neither index nor basket (R^2 <= 0.08), below every verified low-vol quarter, while constituent flat opens peak (0.40); futures-open problem, weak co-movement, or constituent anchoring degrading both references cannot be separated without intraday or per-contract 2019 data (2021H2, by contrast, is close to verified low-vol quarters).", ""]
    M += ["## 4. Headline numbers that depend on the index open 2018-22 (not recomputed)", ""]
    for h, items in EXPOSED:
        M += [f"**{h}**", ""] + [f"- {x}" for x in items] + [""]
    H1 = tree_hash()
    same = H0 == H1
    M += [f"Integrity: md5 of every file in data/raw/ and results/ (excluding this audit's outputs) identical before and after the run: {same} ({len(H0)} files)."]
    (OUT / "index_open_degradation_audit.md").write_text("\n".join(M) + "\n")
    print("\n".join(M))


if __name__ == "__main__":
    main()
