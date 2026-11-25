"""Diagnostic: can continuous VN30F1M opens before 2022-06-20 be told apart from the verified opens (2022-11-03 onward)
using only data already held?  READ-ONLY on data/raw/, data/raw_rollgap/ and results/.
Writes only results/futures_open_stability_audit.md, _yearly.csv, _quarterly.csv, _breaks.csv.
No main result is re-run or filtered.

Pre-registered rules (fixed before the first run, not changed afterwards):
  Step 1  a year is flagged on a measure if its rate is >= 3x the verified-window rate ("several times baseline").
          Spike ratio = share at distance 0 ticks / mean share at 1-2 ticks; reported for every measure, compared to baseline.
  Step 2/3 sample: invested, aligned nights (futures and index start from the same prior trading day), index open not flagged.
          A quarter departs from the verified window (pooled 2022-11-03 .. 2026-11-17) on
            k      if |k_q - k_ver| > 2 * NW SE(k_q)
            R^2    if |atanh(r_q) - atanh(r_ver)| > 2 * sqrt(1/(n_q-3) + 1/(n_ver-3))   (r = sqrt(R^2), Fisher z)
            res SD if sd_q/sd_ver outside 1 +/- 2/sqrt(2 n_q)
  Candidate breaks 2022-07-11, 2022-08-25, 2022-11-03: Chow-type comparison of 60 nights before vs 60 nights from the date
          (HAC Wald chi2(2) on intercept+slope shift; log residual-variance ratio z). Plus a sup-Wald scan over all dates (15% trim).
Primary futures file: data/raw/VN30F1M.csv (what published results use). Sensitivity: VN30F1M_repaired.csv (night 2021-05-04 excluded).
Usage: python3 src/futures_open_stability_audit.py
"""
from __future__ import annotations
import hashlib, math, sys, warnings
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import futures_roll_gap_repair as RG
from futures_basis_decomp import nw_t
from level_a import OUT_DIR, RAW_DIR

OUT = OUT_DIR
TOL = 0.051
VER_LO, END = "2022-11-03", "2026-11-17"
EPI_LO, EPI_HI = "2022-07-11", "2022-11-02"
CANDIDATES = ["2022-07-11", "2022-08-25", "2022-11-03"]
CHOW_W = 60
L = 5
ANDREWS_5PCT = 11.79   # Andrews (1993) sup-Wald, 2 restrictions, 15% trimming, 5% level (approx.)


# ------------------------------------------------------------------ helpers
def norm_sf(z): return 0.5 * math.erfc(z / math.sqrt(2))


def ols(y, x, L=L):
    """y = a + k x. Returns dict a, k, NW SEs, R2, resid SD, n, residuals."""
    j = pd.concat([y, x], axis=1).dropna(); Y, X = j.iloc[:, 0].values, j.iloc[:, 1].values; n = len(Y)
    if n < 10: return dict(n=n, a=np.nan, k=np.nan, se_a=np.nan, se_k=np.nan, r2=np.nan, sd=np.nan, u=None)
    Xm = np.column_stack([np.ones(n), X]); XtXi = np.linalg.inv(Xm.T @ Xm); b = XtXi @ Xm.T @ Y; u = Y - Xm @ b
    V = XtXi @ hac_S(Xm * u[:, None], L) @ XtXi
    r2 = 1 - (u @ u) / ((Y - Y.mean()) @ (Y - Y.mean()))
    return dict(n=n, a=b[0], k=b[1], se_a=math.sqrt(V[0, 0]), se_k=math.sqrt(V[1, 1]), r2=r2, sd=u.std(ddof=2), u=pd.Series(u, index=j.index))


def hac_S(g, L):
    S = g.T @ g
    for l in range(1, L + 1): G = g[l:].T @ g[:-l]; S += (1 - l / (L + 1)) * (G + G.T)
    return S


def wald_shift(y, x, d):
    """y = a + k x + da*d + dk*d*x; HAC Wald on (da, dk). Returns chi2(2) stat."""
    Xm = np.column_stack([np.ones(len(y)), x, d, d * x]); XtXi = np.linalg.inv(Xm.T @ Xm); b = XtXi @ Xm.T @ y; u = y - Xm @ b
    V = XtXi @ hac_S(Xm * u[:, None], L) @ XtXi
    R = b[2:]; W = R @ np.linalg.inv(V[2:, 2:]) @ R
    return float(W), b[2], b[3]


def md5(p): return hashlib.md5(Path(p).read_bytes()).hexdigest()


# ------------------------------------------------------------------ Step 1
def step1(f1):
    d = RG.build_from(f1, 0, 0.0)                         # entry = same-contract prior close (F2M on roll days)
    d = d.join(f1[["high", "low", "volume"]])
    d = d[d.entry.notna()]
    tick = lambda a, b: np.rint((a - b).abs() * 10)
    dist = {"prior_close": tick(d.open, d.entry), "close": tick(d.open, d.close), "high": tick(d.open, d.high), "low": tick(d.open, d.low)}
    lock = np.isclose(d.open, d.high, atol=TOL) & np.isclose(d.open, d.low, atol=TOL) & np.isclose(d.open, d.close, atol=TOL)
    outside = (d.open > d.high + TOL) | (d.open < d.low - TOL)
    groups = {str(y): d.index.year == y for y in range(2017, 2027)}
    groups[f"episode {EPI_LO}..{EPI_HI}"] = (d.index >= EPI_LO) & (d.index <= EPI_HI)
    groups[f"pre-ticker 2017-08..2022-06-19"] = d.index < "2022-06-20"
    groups[f"BASELINE verified {VER_LO}..{END}"] = d.index >= VER_LO
    rows = []
    for g, m in groups.items():
        r = dict(period=g, n_days=int(m.sum()))
        for nm, ds in dist.items():
            x = ds[m]
            for t in range(4): r[f"{nm}_d{t}"] = (x == t).mean()
            r[f"{nm}_eq_pct"] = r[f"{nm}_d0"] * 100
            r[f"{nm}_spike"] = r[f"{nm}_d0"] / ((r[f"{nm}_d1"] + r[f"{nm}_d2"]) / 2) if (r[f"{nm}_d1"] + r[f"{nm}_d2"]) > 0 else np.nan
        r["lock_OHLC_n"] = int(lock[m].sum())
        r["open_eq_prior_close_excl_lock_pct"] = ((dist["prior_close"][m] == 0) & ~lock[m]).mean() * 100
        r["open_outside_range_n"] = int(outside[m].sum())
        r["open_whole_point_pct"] = (np.rint(d.open[m] * 10) % 10 == 0).mean() * 100
        r["close_whole_point_pct"] = (np.rint(d.close[m] * 10) % 10 == 0).mean() * 100
        r["median_price"] = d.open[m].median()
        r["file_open_suspicious_pct"] = d.open_suspicious[m].astype(bool).mean() * 100
        rows.append(r)
    Y = pd.DataFrame(rows)
    base = Y.iloc[-1]
    for nm in dist:
        Y[f"{nm}_eq_x_baseline"] = Y[f"{nm}_eq_pct"] / base[f"{nm}_eq_pct"] if base[f"{nm}_eq_pct"] > 0 else np.nan
        Y[f"{nm}_flag_3x"] = Y[f"{nm}_eq_x_baseline"] >= 3
    out_dates = list(d.index[outside])
    return Y, out_dates, d, lock


# ------------------------------------------------------------------ Steps 2/3
def sample(f1, exclude=()):
    f = RG.futures_nights_from(f1, exclude=exclude); i = RG.index_nights_fixed()
    j = RG.panel_from(f, i)
    j = j[j.aligned & ~j.idx_flag.astype(bool)].copy()
    j["fut_CC"] = np.log(j.close / j.entry)                       # same contract as entry (F2M->F1M on roll days, as build())
    j["idx_CC"] = np.log(j.close_idx / j.prev_close)
    return j


def idx_flag_rate():
    i = RG.index_nights_fixed(); return i.idx_flag.astype(bool).groupby(i.index.to_period("Q")).mean()


def quarterly(j, feed):
    ver = j.loc[VER_LO:]
    V = {leg: ols(ver[f"fut_{leg}"] * 1e4, ver[f"idx_{leg}"] * 1e4) for leg in ("ON", "CC")}
    VR = {leg: ols(ver[f"idx_{leg}"] * 1e4, ver[f"fut_{leg}"] * 1e4) for leg in ("ON", "CC")}
    fr = idx_flag_rate(); rows = []
    groups = [(str(q), j[j.index.to_period("Q") == q]) for q in sorted(j.index.to_period("Q").unique())]
    groups += [(f"VERIFIED {VER_LO}..{END}", ver), (f"episode {EPI_LO}..{EPI_HI}", j.loc[EPI_LO:EPI_HI]),
               ("pre 2018-11..2022-06-19", j.loc[:"2022-06-19"])]
    for g, s in groups:
        for leg in ("ON", "CC"):
            r = ols(s[f"fut_{leg}"] * 1e4, s[f"idx_{leg}"] * 1e4); rv = ols(s[f"idx_{leg}"] * 1e4, s[f"fut_{leg}"] * 1e4)
            v = V[leg]; n = r["n"]
            dk = abs(r["k"] - v["k"]) > 2 * r["se_k"] if n >= 10 else np.nan
            dr = (abs(math.atanh(math.sqrt(max(r["r2"], 0))) - math.atanh(math.sqrt(v["r2"]))) > 2 * math.sqrt(1 / (n - 3) + 1 / (v["n"] - 3))) if n >= 10 else np.nan
            ratio = r["sd"] / v["sd"] if n >= 10 else np.nan
            ds = (abs(ratio - 1) > 2 / math.sqrt(2 * n)) if n >= 10 else np.nan
            rows.append(dict(feed=feed, period=g, leg=leg, n=n, k=r["k"], k_nw_se=r["se_k"], intercept_bp=r["a"], intercept_nw_se=r["se_a"],
                             r2=r["r2"], resid_sd_bp=r["sd"], sd_y_bp=s[f"fut_{leg}"].std() * 1e4, sd_x_bp=s[f"idx_{leg}"].std() * 1e4, k_reverse=rv["k"], k_reverse_nw_se=rv["se_k"],
                             resid_sd_ratio_to_verified=ratio, depart_k=dk, depart_r2=dr, depart_sd=ds,
                             idx_flag_rate_all_nights=fr.get(pd.Period(g, "Q"), np.nan) if g[:2] == "20" and "Q" in g else np.nan))
    return pd.DataFrame(rows), V


def breaks(j, feed):
    rows = []
    for leg in ("ON", "CC"):
        y_all, x_all = (j[f"fut_{leg}"] * 1e4).values, (j[f"idx_{leg}"] * 1e4).values; idx = j.index
        for c in CANDIDATES:
            p = idx.searchsorted(pd.Timestamp(c)); lo, hi = max(0, p - CHOW_W), min(len(idx), p + CHOW_W)
            y, x = y_all[lo:hi], x_all[lo:hi]; dd = (np.arange(lo, hi) >= p).astype(float)
            W, da, dk = wald_shift(y, x, dd)
            b = ols(pd.Series(y[dd == 0]), pd.Series(x[dd == 0])); a = ols(pd.Series(y[dd == 1]), pd.Series(x[dd == 1]))
            z = math.log(a["sd"] ** 2 / b["sd"] ** 2) / math.sqrt(2 / (b["n"] - 2) + 2 / (a["n"] - 2))
            rows.append(dict(feed=feed, leg=leg, test=f"Chow {c} (+/-{CHOW_W} nights)", date=c, n_before=b["n"], n_after=a["n"],
                             k_before=b["k"], k_after=a["k"], a_before=b["a"], a_after=a["a"], r2_before=b["r2"], r2_after=a["r2"],
                             sd_before=b["sd"], sd_after=a["sd"], wald_chi2_2=W, p_wald=math.exp(-W / 2),
                             logvar_z=z, p_var=2 * norm_sf(abs(z))))
        # sup-Wald scan, 15% trim, full sample
        n = len(y_all); best = (-1, None, None)
        for p in range(int(0.15 * n), int(0.85 * n)):
            dd = (np.arange(n) >= p).astype(float); W, _, _ = wald_shift(y_all, x_all, dd)
            if W > best[0]: best = (W, idx[p], p)
        # variance scan (descriptive): residuals from full-sample fit, max |z| of log variance ratio
        u = ols(pd.Series(y_all), pd.Series(x_all))["u"].values; bv = (0, None)
        for p in range(int(0.15 * n), int(0.85 * n)):
            v1, v2 = u[:p].var(), u[p:].var(); z = math.log(v2 / v1) / math.sqrt(2 / p + 2 / (n - p))
            if abs(z) > abs(bv[0]): bv = (z, idx[p])
        rows.append(dict(feed=feed, leg=leg, test="sup-Wald scan (a,k), 15% trim", date=str(best[1].date()), wald_chi2_2=best[0],
                         p_wald=np.nan, note=f"Andrews 5% cv ~{ANDREWS_5PCT}"))
        rows.append(dict(feed=feed, leg=leg, test="max |z| residual-variance split (descriptive)", date=str(bv[1].date()), logvar_z=bv[0]))
    return pd.DataFrame(rows)


def positive_control(f1):
    """Episode quarters with ticker opens substituted for continuous opens (closes identical)."""
    S, _ = RG.contract_front_series(); f1t = f1.copy()
    w = S.loc["2022-06-20":EPI_HI]; common = w.index.intersection(f1t.index); f1t.loc[common, "open"] = w.loc[common, "open"]
    jt = sample(f1t); jc = sample(f1); rows = []
    ver = jc.loc[VER_LO:]; v = ols(ver.fut_ON * 1e4, ver.idx_ON * 1e4)
    for g, (lo, hi) in {"2022Q3": ("2022-07-01", "2022-09-30"), "2022Q4": ("2022-10-01", "2022-12-31"), "episode": (EPI_LO, EPI_HI)}.items():
        for nm, jj in (("continuous", jc), ("ticker", jt)):
            s = jj.loc[lo:hi]; r = ols(s.fut_ON * 1e4, s.idx_ON * 1e4)
            rows.append(dict(period=g, open_source=nm, n=r["n"], k=r["k"], k_nw_se=r["se_k"], r2=r["r2"], resid_sd_bp=r["sd"],
                             depart_k=abs(r["k"] - v["k"]) > 2 * r["se_k"],
                             depart_r2=abs(math.atanh(math.sqrt(r["r2"])) - math.atanh(math.sqrt(v["r2"]))) > 2 * math.sqrt(1 / (r["n"] - 3) + 1 / (v["n"] - 3)),
                             depart_sd=abs(r["sd"] / v["sd"] - 1) > 2 / math.sqrt(2 * r["n"])))
    for nm, jj in (("continuous", jc), ("ticker", jt)):
        s = jj.loc[EPI_LO:EPI_HI].drop(pd.Timestamp("2022-10-10"), errors="ignore"); r = ols(s.fut_ON * 1e4, s.idx_ON * 1e4)
        rows.append(dict(period="episode excl. 2022-10-10 (sensitivity only)", open_source=nm, n=r["n"], k=r["k"], k_nw_se=r["se_k"], r2=r["r2"], resid_sd_bp=r["sd"],
                         depart_k=abs(r["k"] - v["k"]) > 2 * r["se_k"],
                         depart_r2=abs(math.atanh(math.sqrt(r["r2"])) - math.atanh(math.sqrt(v["r2"]))) > 2 * math.sqrt(1 / (r["n"] - 3) + 1 / (v["n"] - 3)),
                         depart_sd=abs(r["sd"] / v["sd"] - 1) > 2 / math.sqrt(2 * r["n"])))
    diff = (jt.fut_ON - jc.fut_ON).loc[EPI_LO:EPI_HI] * 1e4
    return pd.DataFrame(rows), diff


def simulate_power(j, V, sigmas=(10, 25, 50, 100), seeds=20, thresh=12):
    """ADDED AFTER THE FIRST RUN (power check). Add iid N(0, sigma) bp to fut_ON on verified nights only (an open error moves ON only),
    re-apply the pre-registered k and R^2 rules to each verified quarter against the CLEAN pooled verified window.
    'Detectable' fixed before running: mean flagged quarters >= thresh of 16 on the R^2 rule."""
    ver = j.loc[VER_LO:]; v = V["ON"]; rng = np.random.default_rng(20261124)
    qs = [q for q in sorted(ver.index.to_period("Q").unique()) if str(q) >= "2023Q1"]
    rows = []
    for sg in (0,) + tuple(sigmas):
        fr2, fk, fboth_pass = [], [], []
        for sd in range(seeds if sg else 1):
            y = ver.fut_ON * 1e4 + (rng.normal(0, sg, len(ver)) if sg else 0)
            nr2 = nk = npass = 0
            for q in qs:
                m = ver.index.to_period("Q") == q; r = ols(y[m], ver.idx_ON[m] * 1e4); n = r["n"]
                d2 = abs(math.atanh(math.sqrt(max(r["r2"], 1e-12))) - math.atanh(math.sqrt(v["r2"]))) > 2 * math.sqrt(1 / (n - 3) + 1 / (v["n"] - 3))
                dk = abs(r["k"] - v["k"]) > 2 * r["se_k"]
                nr2 += d2; nk += dk; npass += (not d2) and (not dk)
            fr2.append(nr2); fk.append(nk); fboth_pass.append(npass)
        rows.append(dict(sigma_bp=sg, seeds=seeds if sg else 1, quarters=len(qs), mean_flag_r2=np.mean(fr2), mean_flag_k=np.mean(fk),
                         mean_pass_both=np.mean(fboth_pass), detectable=np.mean(fr2) >= thresh))
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ main
def fm(x, f="{:.3f}"): return "" if pd.isna(x) else f.format(x)


def main():
    from data_cap import futures_csv
    raws = [futures_csv("VN30F1M"), futures_csv("VN30F1M_repaired"), RAW_DIR / "VN30.csv", futures_csv("VN30F2M")]
    h0 = {p.name: md5(p) for p in raws}
    f1 = RG.rd("VN30F1M"); f1r = RG.rd("VN30F1M_repaired").drop(columns="source")

    Y, out_dates, d1, lock = step1(f1)
    j = sample(f1); jr = sample(f1r, exclude=["2021-05-04"])
    Q, V = quarterly(j, "original"); Qr, _ = quarterly(jr, "repaired")
    B = pd.concat([breaks(j, "original"), breaks(jr, "repaired")], ignore_index=True)
    PC, pcdiff = positive_control(f1)

    Y.to_csv(OUT / "futures_open_stability_audit_yearly.csv", index=False)
    pd.concat([Q, Qr], ignore_index=True).to_csv(OUT / "futures_open_stability_audit_quarterly.csv", index=False)
    B.to_csv(OUT / "futures_open_stability_audit_breaks.csv", index=False)

    SIM = simulate_power(j, V)
    SIM.to_csv(OUT / "futures_open_stability_audit_power.csv", index=False)
    # minimum detectable iid open error (resid SD rule) at typical quarterly n
    qn = Q[(Q.leg == "ON") & Q.period.str.match(r"^\d{4}Q\d$")].n
    nq = int(qn.median()); c = 2 / math.sqrt(2 * nq); s_ver = V["ON"]["sd"]; mde = s_ver * math.sqrt((1 + c) ** 2 - 1)

    # ---------------- markdown
    Lm = ["# Futures open stability audit (continuous VN30F1M, 2017-2026)", "",
          "Diagnostic only. Read-only on data/raw/ and results/; no main result re-run, nothing filtered. Script: `src/futures_open_stability_audit.py`.",
          "", "Question: can the continuous VN30F1M opens before 2022-06-20 be told apart from the verified opens (2022-11-03 onward, "
          "100% match with per-contract tickers) using only data already held?", "",
          "## Pre-registered rules (written into the script header before the first run; not changed)", "",
          "- Step 1: a period is flagged on a measure if its equality rate is >= 3x the verified-window rate. Distance is |open - reference| in 0.1-point ticks; "
          "`spike` = share at 0 ticks / mean share at 1-2 ticks (a filled or stale open shows as a spike at 0 relative to its neighbours; "
          "chance coincidence, which rises at lower price levels, does not). Prior close = same-contract prior close, i.e. `build()` entry (VN30F2M close on roll days).",
          "- Steps 2-3: invested, aligned nights, index open not flagged; fixed-first-row index nights. Quarter departs from the pooled verified window on "
          "k if |k_q - k_ver| > 2 NW SE(k_q); on R^2 if Fisher-z distance > 2 sqrt(1/(n_q-3)+1/(n_ver-3)); on residual SD if sd_q/sd_ver is outside 1 +/- 2/sqrt(2 n_q).",
          "- Breaks: Chow-type +/-60 nights at 2022-07-11, 2022-08-25, 2022-11-03 (HAC Wald chi2(2) on intercept and slope shift; log residual-variance ratio z), "
          f"plus a sup-Wald scan over all dates (15% trim; Andrews 5% critical value ~{ANDREWS_5PCT}).",
          "- Primary futures file: `data/raw/VN30F1M.csv` (what published results use). Sensitivity: `VN30F1M_repaired.csv`, night 2021-05-04 excluded.", ""]

    Lm += ["## 1. Filled-open detector, by year", ""]
    cols = ["period", "n_days", "prior_close_eq_pct", "prior_close_spike", "close_eq_pct", "close_spike", "high_eq_pct", "high_spike",
            "low_eq_pct", "low_spike", "lock_OHLC_n", "open_outside_range_n", "open_whole_point_pct", "median_price"]
    T = Y[cols].copy()
    for cc in cols[2:]:
        T[cc] = T[cc].map(lambda v: fm(v, "{:.0f}") if cc in ("lock_OHLC_n", "open_outside_range_n", "median_price") else fm(v, "{:.2f}"))
    Lm += ["```", T.to_string(index=False), "```", ""]
    X = Y[["period"] + [f"{m}_eq_x_baseline" for m in ("prior_close", "close", "high", "low")]].copy()
    for cc in X.columns[1:]: X[cc] = X[cc].map(lambda v: fm(v, "{:.2f}"))
    Lm += ["Equality rate as a multiple of baseline:", "", "```", X.to_string(index=False), "```", ""]
    flagged = [(r.period, m) for _, r in Y.iterrows() for m in ("prior_close", "close", "high", "low") if r[f"{m}_flag_3x"] and not r.period.startswith("BASELINE")]
    base = Y.iloc[-1]
    Lm += [f"- Flagged (>= 3x baseline): {', '.join(f'{p} [{m}]' for p, m in flagged) if flagged else 'none'}.",
           f"- Baseline (verified window): open = prior close {base.prior_close_eq_pct:.2f}% (spike {base.prior_close_spike:.2f}), = close {base.close_eq_pct:.2f}%, "
           f"= high {base.high_eq_pct:.2f}%, = low {base.low_eq_pct:.2f}%.",
           f"- Open outside [low, high]: {len(out_dates)} day(s){': ' + ', '.join(str(t.date()) for t in out_dates) if out_dates else ''}.",
           f"- O=H=L=C lock days: {int(lock.sum())} in total ({', '.join(str(t.date()) for t in d1.index[lock]) if lock.sum() <= 12 else 'see CSV'}).",
           "- Open = close days in 2017 (the only flag): " + ", ".join(f"{t.date()} (O {r.open}, H {r.high}, L {r.low}, C {r.close}, prior close {r.entry})"
                                                          for t, r in d1[(d1.index.year == 2017) & np.isclose(d1.open, d1.close, atol=TOL)].iterrows())
           + "; 3 of 95 days, each with a real intraday range, so the 3x flag rests on 3 days.",
           "- Spike ratio blank = no days at 1-2 ticks in that period (undefined).",
           "- The file's own `open_suspicious` column compares with the naive prior close (expiring contract on roll days); it is not used here (kept in the CSV as `file_open_suspicious_pct`).",
           "- Whole-point prices (decimal .0) are over-represented in every year (round-number clustering, not a grid change: every price is on the 0.1 grid in every year).", ""]

    Lm += ["## 2-3. Quarterly relation, futures vs VN30 index (original file)", "",
           f"Verified window pooled ({VER_LO}..{END}): ON n {V['ON']['n']}, k {V['ON']['k']:.3f} (NW SE {V['ON']['se_k']:.3f}), a {V['ON']['a']:.2f} bp, "
           f"R^2 {V['ON']['r2']:.3f}, resid SD {V['ON']['sd']:.1f} bp | CC n {V['CC']['n']}, k {V['CC']['k']:.3f} (SE {V['CC']['se_k']:.3f}), "
           f"a {V['CC']['a']:.2f} bp, R^2 {V['CC']['r2']:.3f}, resid SD {V['CC']['sd']:.1f} bp.", ""]
    show = ["period", "n", "k", "k_nw_se", "intercept_bp", "r2", "resid_sd_bp", "sd_y_bp", "sd_x_bp", "k_reverse", "depart_k", "depart_r2", "depart_sd", "idx_flag_rate_all_nights"]
    for leg, title in (("ON", "Overnight: fut_ON on idx_ON (log, bp)"), ("CC", "Control, close-to-close: fut_CC on idx_CC (same entry as build())")):
        T = Q[Q.leg == leg][show].copy()
        for cc in ["k", "k_nw_se", "r2", "k_reverse", "idx_flag_rate_all_nights"]: T[cc] = T[cc].map(lambda v: fm(v))
        for cc in ["intercept_bp", "resid_sd_bp", "sd_y_bp", "sd_x_bp"]: T[cc] = T[cc].map(lambda v: fm(v, "{:.2f}"))
        for cc in ["depart_k", "depart_r2", "depart_sd"]: T[cc] = T[cc].map(lambda v: "" if pd.isna(v) else ("X" if v else "."))
        Lm += [f"### {title}", "", "(sd_y = SD of the futures leg, sd_x = SD of the index leg; k_reverse = slope of index on futures.)", "", "```", T.to_string(index=False), "```", ""]

    qq = lambda df, leg: df[(df.leg == leg) & df.period.str.match(r"^\d{4}Q\d$")]
    def dep(df, leg, col): return [r.period for _, r in qq(df, leg).iterrows() if r[col] is True or r[col] == True]
    summ = {}
    for leg in ("ON", "CC"):
        summ[leg] = {c: dep(Q, leg, c) for c in ("depart_k", "depart_r2", "depart_sd")}
        nq_ = len(qq(Q, leg))
        Lm += [f"- {leg}: quarters departing on k {len(summ[leg]['depart_k'])}/{nq_} ({', '.join(summ[leg]['depart_k']) or 'none'}); "
               f"on R^2 {len(summ[leg]['depart_r2'])}/{nq_} ({', '.join(summ[leg]['depart_r2']) or 'none'}); "
               f"on resid SD {len(summ[leg]['depart_sd'])}/{nq_} ({', '.join(summ[leg]['depart_sd']) or 'none'})."]
    isver = lambda p: p >= "2023Q1"; ispre = lambda p: p <= "2022Q2"
    Lm += ["", "Noise floor: share of quarters departing, verified quarters (2023Q1-2026Q4) vs pre-ticker quarters (2018Q4-2022Q2). "
           "Verified quarters are compared with their own pooled window, so their departure rate is what the rule produces on opens known to be right.", ""]
    NF = []
    for leg in ("ON", "CC"):
        qd = qq(Q, leg)
        for c in ("depart_k", "depart_r2", "depart_sd"):
            v_ = qd[qd.period.map(isver)]; p_ = qd[qd.period.map(ispre)]
            NF.append(dict(leg=leg, rule=c, verified=f"{int((v_[c] == True).sum())}/{len(v_)}", pre=f"{int((p_[c] == True).sum())}/{len(p_)}"))
    Lm += ["```", pd.DataFrame(NF).to_string(index=False), "```", ""]
    on_only = {c: sorted(set(summ["ON"][c]) - set(summ["CC"][c])) for c in summ["ON"]}
    Lm += [f"- Departures in ON but not in CC (the open-specific signal): k {', '.join(on_only['depart_k']) or 'none'}; "
           f"R^2 {', '.join(on_only['depart_r2']) or 'none'}; resid SD {', '.join(on_only['depart_sd']) or 'none'}.", ""]

    Lm += ["### Repaired-file sensitivity (quarters that differ from the original file only)", ""]
    a_ = Q.set_index(["period", "leg"]); b_ = Qr.set_index(["period", "leg"]); keys = [k for k in a_.index if k in b_.index]
    dif = [k for k in keys if a_.loc[k, "n"] != b_.loc[k, "n"] or not np.isclose(a_.loc[k, "k"], b_.loc[k, "k"], equal_nan=True)]
    if dif:
        T = pd.DataFrame([dict(period=p, leg=l, n_orig=a_.loc[(p, l), "n"], n_rep=b_.loc[(p, l), "n"], k_orig=fm(a_.loc[(p, l), "k"]), k_rep=fm(b_.loc[(p, l), "k"]),
                               r2_orig=fm(a_.loc[(p, l), "r2"]), r2_rep=fm(b_.loc[(p, l), "r2"]), sd_orig=fm(a_.loc[(p, l), "resid_sd_bp"], "{:.2f}"),
                               sd_rep=fm(b_.loc[(p, l), "resid_sd_bp"], "{:.2f}"),
                               dep_rep="".join("X" if b_.loc[(p, l), c] is True or b_.loc[(p, l), c] == True else "." for c in ("depart_k", "depart_r2", "depart_sd")))
                          for p, l in dif])
        Lm += ["```", T.to_string(index=False), "```", "(dep_rep = departure flags k/R^2/SD on the repaired file, vs the repaired verified window.)", ""]
    else:
        Lm += ["No quarter differs.", ""]

    Lm += ["### Candidate break dates and scan", ""]
    bc = ["feed", "leg", "test", "date", "n_before", "n_after", "k_before", "k_after", "r2_before", "r2_after", "sd_before", "sd_after", "wald_chi2_2", "p_wald", "logvar_z", "p_var"]
    T = B.reindex(columns=bc).copy()
    for cc in bc[4:]: T[cc] = T[cc].map(lambda v: fm(v, "{:.0f}") if cc.startswith("n_") else fm(v))
    Lm += ["```", T.to_string(index=False), "```", ""]

    Lm += ["### Power: positive control on the known episode (continuous vs ticker opens; closes identical)", "", "```", PC.to_string(index=False, float_format=lambda v: f"{v:.3f}"), "```", "",
           f"- Episode open-error in return units (ticker minus continuous fut_ON, sample nights): n {pcdiff.count()}, SD {pcdiff.std():.2f} bp, "
           f"SD excluding 2022-10-10 {pcdiff.drop(pd.Timestamp('2022-10-10'), errors='ignore').std():.2f} bp, non-zero on {(pcdiff.abs() > 1e-9).sum()} nights.",
           "- The residual-SD rule has no specificity (it flags 13/16 verified quarters on opens known to be right), so power comes only from the k and R^2 rules.", "",
           "### Power simulation (ADDED AFTER THE FIRST RUN; threshold fixed before running it)", "",
           "i.i.d. N(0, sigma) bp added to fut_ON on verified nights only (index and close-to-close untouched); each verified quarter re-tested with the pre-registered "
           "rules against the clean pooled verified window; 20 seeds. 'Detectable' = mean R^2-rule flags >= 12 of 16 quarters (floor with sigma = 0 is the first row).", "",
           "```", SIM.to_string(index=False, float_format=lambda v: f"{v:.2f}"), "```", ""]

    # descriptive (not a pre-registered rule): is each pre-ticker quarter's ON k and R^2 inside the range spanned by verified quarters?
    qo = qq(Q, "ON"); vq = qo[qo.period >= "2023Q1"]; pq = qo[qo.period <= "2022Q2"]
    kr, rr = (vq.k.min(), vq.k.max()), (vq.r2.min(), vq.r2.max())
    inside = [r.period for _, r in pq.iterrows() if kr[0] <= r.k <= kr[1] and rr[0] <= r.r2 <= rr[1]]
    passv = [r.period for _, r in vq.iterrows() if r.depart_k == False and r.depart_r2 == False]
    passp = [r.period for _, r in pq.iterrows() if r.depart_k == False and r.depart_r2 == False]
    det = SIM[SIM.detectable].sigma_bp.min() if SIM.detectable.any() else np.nan
    s50 = SIM.set_index("sigma_bp")
    sdq = qo.set_index("period")
    Lm += ["## Reading", "",
           "**Step 1.** No period reaches 3x baseline on open = prior close (max " + f"{Y.prior_close_eq_x_baseline.iloc[:-1].max():.2f}x" + "); the pre-ticker spike ratio "
           f"({Y.iloc[-2].prior_close_spike:.2f}) is not above baseline ({base.prior_close_spike:.2f}); no open outside [low, high] and no O=H=L=C day in any year. "
           "The only flag is 2017 open = close, on 3 of 95 days with real ranges. No sign of filled or stale futures opens in the form the 2021 index feed showed.", "",
           "**Steps 2-3.** The quarterly rules flag many verified quarters too (noise floor above), so a single departing quarter means little. "
           "Pre-ticker quarters depart more often than verified ones on R^2, in BOTH legs (ON 10/15 vs 6/16; CC 7/15 vs 2/16): the futures-index relation itself was looser before 2022, not only at the open.",
           f"The ON-specific weakness sits in 2019Q1-2021Q2. In 2020Q1-2021Q2 it coincides with the index leg collapsing (fut/idx ON SD ratio 1.9-11.2 vs 0.6-1.5 in verified quarters): idx_ON SD 2020Q2 {sdq.loc['2020Q2','sd_x_bp']:.1f} bp, "
           f"2021Q1 {sdq.loc['2021Q1','sd_x_bp']:.1f}, 2021Q2 {sdq.loc['2021Q2','sd_x_bp']:.1f} (verified ~{V['ON']['n'] and qo[qo.period>='2023Q1'].sd_x_bp.median():.0f}) while fut_ON SD stays "
           f"{sdq.loc['2020Q2','sd_y_bp']:.0f}, {sdq.loc['2021Q1','sd_y_bp']:.0f}, {sdq.loc['2021Q2','sd_y_bp']:.0f} bp and index close-to-close SD is normal. "
           "Forward k blows up (2021Q1 6.5) and reverse k collapses: the pattern a shrunken/stale index open produces, even on days the index flag passes. "
           "Read with caution: it points at the index open, but the data cannot prove the futures open is clean in those quarters, because the reference itself is degraded. "
           f"2019Q1, 2019Q3 and 2019Q4 are different: ON R^2 {sdq.loc['2019Q1','r2']:.2f}, {sdq.loc['2019Q3','r2']:.2f}, {sdq.loc['2019Q4','r2']:.3f} with a normal SD ratio "
           f"({sdq.loc['2019Q1','sd_y_bp']/sdq.loc['2019Q1','sd_x_bp']:.1f}, {sdq.loc['2019Q3','sd_y_bp']/sdq.loc['2019Q3','sd_x_bp']:.1f}, {sdq.loc['2019Q4','sd_y_bp']/sdq.loc['2019Q4','sd_x_bp']:.1f}) "
           "and index-flag rates of 9-17%: the two overnight legs are nearly unrelated there and nothing here says which leg is at fault. Unexplained.",
           f"Pre-registered rules, quarters passing BOTH k and R^2: verified {len(passv)}/{len(vq)}, pre-ticker {len(passp)}/{len(pq)} ({', '.join(passp) or 'none'}). "
           "On these rules the pre-ticker overnight relation IS distinguishable from the verified window; part of that is explained by the index leg (2020Q1-2021Q2) and by the looser close-to-close relation, part (2019) is not explained.",
           f"POST-HOC and lenient (added after seeing results, not a test): pre-ticker quarters whose ON k and R^2 both lie inside the range spanned by the 16 verified quarters "
           f"(k {kr[0]:.2f}-{kr[1]:.2f}, R^2 {rr[0]:.2f}-{rr[1]:.2f}): {', '.join(inside) or 'none'}.", "",
           "**Breaks.** 2022-07-11 (episode start): ON intercept/slope shift, Wald p 0.026 (k 0.59 -> 0.91, R^2 0.49 -> 0.73); CC none (p 0.65); both legs show a variance drop (market volatility). 2022-08-25: CC breaks (p < 0.001), ON does not (p 0.24): "
           "an instrument/market change, not an open one. 2022-11-03: ON-only break (Wald 12.5, p 0.002; repaired file 9.3, p 0.009; CC p 0.92), k 0.97 -> 0.59, R^2 0.73 -> 0.44: "
           "so both edges of the mismatch episode carry an ON-only coefficient shift, and the futures-index overnight fit was TIGHTER inside the episode than on either side (the episode window departs from the verified window on k and R^2, toward a better fit). This is not attributable to the open definition: ticker opens reproduce it (episode excl. 2022-10-10: k 0.90 / R^2 0.68 vs continuous 0.90 / 0.71, positive-control table). CC does not shift at either edge, so the cause is unidentified (a change in how the futures and index overnight moves relate over that period, whichever open is used). The sup-Wald maxima (ON 2023-12-29, CC 2021-06-28) exceed ~11.8 but are at neither candidate date.", "",
           "**Power.** The residual-SD rule cannot discriminate (13/16 verified quarters flagged). In the simulation (added after the first run), an i.i.d. futures-open error is detectable "
           f"by the R^2 rule only at sigma = {det:.0f} bp (mean flags {s50.loc[det,'mean_flag_r2']:.1f}/16); at 50 bp it is {s50.loc[50,'mean_flag_r2']:.1f}/16, at 25 bp {s50.loc[25,'mean_flag_r2']:.1f}/16, at 10 bp {s50.loc[10,'mean_flag_r2']:.1f}/16 vs a floor of {s50.loc[0,'mean_flag_r2']:.0f}/16. "
           f"The known 2022 episode's open error, excluding 2022-10-10, is about {pcdiff.drop(pd.Timestamp('2022-10-10'), errors='ignore').std():.0f} bp SD, and continuous vs ticker opens give practically the same quarterly k / R^2 once 2022-10-10 is set aside: "
           "this audit could not have detected the one episode we know about. The pre-ticker R^2 flag rate (10/15) is in the range the simulation produces for a 25-50+ bp error, "
           "but the close-to-close control is also degraded pre-2022, so that rate cannot be attributed to the futures open.", "",
           "**What this can and cannot establish.** It can show that the pre-2022-06 futures opens have no filled- or stale-open signature (Step 1), and that the 2022 edge shifts are not caused by the open definition (ticker opens reproduce them). "
           "It cannot show the opens are right, and on the pre-registered k/R^2 rules the 2019-2021 overnight relation is NOT indistinguishable from the verified window. The data cannot assign that difference to the futures open: "
           "the index open is degraded in 2020Q1-2021Q2, close-to-close is looser too, and 2019 is unexplained. The test sees only i.i.d. errors of roughly 100 bp SD (50 bp is borderline), and 2017-08..2018-11-19 "
           "is covered by Step 1 only (the VN30 index file starts 2018-11-20). Passing Step 1 is not proof; failing Steps 2-3 is not proof of a bad open.", "",
           "## Summary (5 lines)", "",
           f"1. Filled-open rates: no year >= 3x baseline on open = prior close / high / low (pre-ticker 1.17x, spike {Y.iloc[-2].prior_close_spike:.2f} vs {base.prior_close_spike:.2f}); only flag 2017 open = close (3 of 95 days); no out-of-range or locked opens.",
           "2. Break dates: ON-only coefficient shifts at both edges of the 2022 episode, 2022-07-11 (p 0.026) and 2022-11-03 (p 0.002; repaired 0.009), with a tighter fit inside it (R^2 0.72 vs 0.53 verified), but ticker opens reproduce it (0.68 excl. 2022-10-10), so the shifts are not attributable to the open definition (cause unidentified; CC does not shift); 2022-08-25 breaks in close-to-close too, so it is not an open break; the all-date sup-Wald scan peaks at 2023-12-29 (ON) and 2021-06-28 (CC), not at any candidate date.",
           "3. Control: close-to-close is also looser before 2022 (R^2 departures 7/15 vs 2/16), and the ON weakness in 2020Q1-2021Q2 tracks a collapse in index-open variance (points at the index open); 2019Q1/Q3/Q4 ON R^2 0.00-0.10 is unexplained and could be either leg.",
           f"4. Indistinguishable: on Step 1 every year except 2017 (3 open = close days); on Steps 2-3 (pre-registered k and R^2) only {', '.join(passp)} pass, vs {len(passv)}/{len(vq)} verified quarters, so the 2019-2021 overnight relation IS distinguishable (2020Q1-2021Q2 explained by the index leg, 2019 unexplained); 2017-08..2018-11 has Step 1 only.",
           f"5. Open question: are the 2019-2021H1 futures opens right? Step 2 used the VCI index open, which is degraded there; the PIT constituent-open basket (`pit_basket()`, from data/raw/ stock files, from 2018-11) is held but was not run because the brief specified the index. It is the natural next run; even then the test detects only i.i.d. errors of ~{det:.0f} bp SD, far above the ~11 bp 2022 episode.", ""]
    h1 = {p.name: md5(p) for p in raws}
    Lm += [f"Raw files unchanged (md5 before = after): {all(h0[k] == h1[k] for k in h0)}.", ""]
    (OUT / "futures_open_stability_audit.md").write_text("\n".join(Lm))
    print("\n".join(Lm))


if __name__ == "__main__":
    main()
