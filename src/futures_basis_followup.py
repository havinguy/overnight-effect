"""Follow-up to futures_basis_decomp.py. MEASUREMENT ONLY.

Part 1 (daily data): 1a reconcile the 2023 index-ON gap; 1b weekday-equality Wald tests on dbasis_ON;
1c offset vs proportional lag (fut_ON = a + k idx_ON); 1d weekday tests on the intraday basis change.
Part 2 (intraday, vnstock VCI 1m futures + VCI 5m index cached in data/raw_intraday/): futures path from the
prior ATC to 09:00/09:15/09:30/10:00, catch-up by index-ON tercile, basis at matched times, recovery of the
overnight basis shortfall, and a descriptive Monday exit-time sensitivity.

Conventions (as futures_basis_decomp.py): log returns, nights on the open date, weekday label = entry-close weekday,
roll nights enter at the VN30F2M close (level_c_futures.build), NW lag 5.
Intraday bars are labelled by bar START (tested in the probe); price at h = open of the bar labelled h
(first print at or after h); if minute h has no print, the last close before h is used (counted).
Usage: python3 src/futures_basis_followup.py [--probe]
"""
from __future__ import annotations
import argparse, math, sys, time, warnings
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import futures_basis_decomp as FB
from futures_basis_decomp import CUTOVER, LAGS, nw_t, ORDER
from level_a import RAW_DIR, OUT_DIR
from level_c_futures import build, MULT

OUT = OUT_DIR
IDIR = Path(__file__).resolve().parent.parent / "data" / "raw_intraday"
CATS = ["Mon->Tue", "Tue->Wed", "Wed->Thu", "Thu->Fri", "Fri->Mon (weekend)"]
BASE = dict(roll_cost=0.0005, fee_vnd=12_500, slippage=0.0001)       # level_c_phase2.BASE
FUT_H = ["09:00", "09:15", "09:30", "10:00"]
IDX_H = ["09:15", "09:30", "10:00"]


# ------------------------------------------------------------------ stats helpers
def hac(g: np.ndarray, L=LAGS) -> np.ndarray:
    """Bartlett long-run covariance (sum, not mean) of score rows g (n x k), in time order."""
    S = g.T @ g
    for l in range(1, L + 1):
        G = g[l:].T @ g[:-l]; S += (1 - l / (L + 1)) * (G + G.T)
    return S


def chi2_sf(w, df):
    """Survival function of chi-square for even df (closed form)."""
    assert df % 2 == 0
    h = w / 2; return math.exp(-h) * sum(h ** i / math.factorial(i) for i in range(df // 2))


def ols_ak(y: pd.Series, x: pd.Series):
    """y = a + k x with NW SEs: a (bp), se(a), t(a), k, se(k), t(k vs 0), t(k vs 1), n."""
    j = pd.concat([y, x], axis=1).dropna(); Y, Xv = j.iloc[:, 0].values, j.iloc[:, 1].values; n = len(Y)
    if n < 10: return dict(n=n)
    X = np.column_stack([np.ones(n), Xv]); XtXi = np.linalg.inv(X.T @ X); b = XtXi @ X.T @ Y; u = Y - X @ b
    V = XtXi @ hac(X * u[:, None]) @ XtXi; sa, sk = math.sqrt(V[0, 0]), math.sqrt(V[1, 1])
    return dict(n=n, a_bp=b[0] * 1e4, a_se_bp=sa * 1e4, a_t=b[0] / sa, k=b[1], k_se=sk, k_t_vs1=(b[1] - 1) / sk,
                r2=1 - (u @ u) / ((Y - Y.mean()) @ (Y - Y.mean())))


def weekday_test(y: pd.Series, night: pd.Series) -> tuple[list[dict], dict]:
    """y on 5 night dummies (no intercept), HAC lag 5 in date order. Returns per-category rows and the joint test."""
    m = night.isin(CATS) & y.notna(); yy, nn = y[m].sort_index(), night[m].sort_index()
    X = np.column_stack([(nn == c).values.astype(float) for c in CATS]); Y = yy.values; n = len(Y)
    cnt = X.sum(0)
    if (cnt < 3).any(): return [], dict(n=n, n_excluded_holiday=int((~night.isin(CATS)).sum()))
    XtXi = np.linalg.inv(X.T @ X); b = XtXi @ X.T @ Y; u = Y - X @ b
    V = XtXi @ hac(X * u[:, None]) @ XtXi
    rows = []
    for i, c in enumerate(CATS):
        w = -np.ones(5) / 4; w[i] = 1.0                          # beta_i - mean(other four betas)
        d = w @ b; se = math.sqrt(w @ V @ w)
        rows.append(dict(night=c, n=int(cnt[i]), mean_bp=b[i] * 1e4, mean_t=b[i] / math.sqrt(V[i, i]),
                         minus_others_bp=d * 1e4, minus_others_t=d / se))
    R = np.column_stack([np.eye(4), -np.ones((4, 1))])           # all equal to the weekend mean
    rb = R @ b; W = float(rb @ np.linalg.inv(R @ V @ R.T) @ rb)
    return rows, dict(n=n, n_excluded_holiday=int((~night.isin(CATS)).sum()), grand_mean_bp=Y.mean() * 1e4,
                      grand_mean_t=nw_t(pd.Series(Y)), wald=W, wald_df=4, wald_p=chi2_sf(W, 4))


def ratio_ci(x: pd.Series, y: pd.Series):
    """R = mean(x)/mean(y), delta method with NW long-run covariance of (x, y)."""
    k = pd.concat([x, y], axis=1).dropna(); n = len(k)
    if n < 10: return dict(n=n)
    X = k.values; mx, my = X.mean(0); U = X - X.mean(0); S = hac(U) / n   # long-run cov of the means x n
    R = mx / my; g = np.array([1 / my, -mx / my ** 2]); se = math.sqrt(g @ S @ g / n)
    # Fieller set {R: (mx - R my)^2 <= z^2 Var(mean x - R mean y)}; contains 0 iff |t_num| < z
    V = S / n; z2 = 1.96 ** 2
    qa, qb, qc = my ** 2 - z2 * V[1, 1], -2 * (mx * my - z2 * V[0, 1]), mx ** 2 - z2 * V[0, 0]
    disc = qb ** 2 - 4 * qa * qc
    if qa > 0 and disc >= 0: f_lo, f_hi, f_kind = (-qb - math.sqrt(disc)) / (2 * qa), (-qb + math.sqrt(disc)) / (2 * qa), "bounded"
    else: f_lo, f_hi, f_kind = -np.inf, np.inf, "unbounded (denominator not significant)"
    return dict(n=n, num_bp=mx * 1e4, den_bp=my * 1e4, ratio=R, fieller_lo=f_lo, fieller_hi=f_hi, fieller=f_kind,
                delta_se=se, delta_lo=R - 1.96 * se, delta_hi=R + 1.96 * se)


def ms(x, pre=""):
    x = pd.Series(x).dropna(); return {f"{pre}n": len(x), f"{pre}mean_bp": x.mean() * 1e4 if len(x) else np.nan, f"{pre}t": nw_t(x)}


# ------------------------------------------------------------------ data
def samples():
    j = FB.panel(); mis = j[~j.aligned]; j = j[j.aligned]
    return j, mis


def periods_1b(j):
    return {"pre 2022-08-25": j[j.index < CUTOVER], "post 2022-08-25": j[j.index >= CUTOVER], "2023-01-01 onward": j[j.index >= "2023-01-01"]}


# ------------------------------------------------------------------ Part 1
def reconcile() -> tuple[pd.DataFrame, pd.DataFrame]:
    v = FB.index_nights(); v = v[v.index >= "2018-11-21"]
    f = FB.futures_nights(); jall = FB.panel(); ja = jall[jall.aligned]
    steps = {"1 full index nights (gate convention)": v,
             "2 & futures bar exists on the date": v[v.index.isin(f.index)],
             "3 & futures night invested (roll F2M close exists)": v[v.index.isin(f.index[f.invested])],
             "4 & same prior trading day (decomposition sample)": v[v.index.isin(ja.index)]}
    rows = []
    for y in [2023, "all"]:
        for s, g in steps.items():
            gg = g if y == "all" else g[g.index.year == y]
            rows.append(dict(year=y, step=s, **ms(gg.idx_ON)))
    mis = jall[~jall.aligned].copy()
    lst = pd.DataFrame({"date": mis.index, "year": mis.index.year, "idx_ON_bp": mis.idx_ON.values * 1e4, "fut_ON_bp": mis.fut_ON.values * 1e4,
                        "fut_prior_day": mis.prev_date.values, "idx_prior_day": mis.prev_date_idx.values,
                        "night_label": mis.night.values, "idx_flag": mis.idx_flag.values})
    lst["idx_gap_calendar_days"] = (lst.date - lst.idx_prior_day).dt.days
    lst["fut_gap_calendar_days"] = (lst.date - lst.fut_prior_day).dt.days
    # dates missing from one file explain the mismatch
    fidx, iidx = set(f.index) | {f.prev_date.min()}, set(v.index)
    lst["note"] = ["futures prior day missing from VN30.csv" if p not in iidx else ("index prior day missing from VN30F1M.csv" if q not in fidx else "") for p, q in zip(lst.fut_prior_day, lst.idx_prior_day)]
    for y in [2023, "all"]:
        a = ja if y == "all" else ja[ja.index.year == y]; b = jall if y == "all" else jall[jall.index.year == y]
        rows.append(dict(year=y, step="5 decomposition sample, misaligned nights INCLUDED (step 3 ∩ index)", **ms(b.idx_ON)))
        rows.append(dict(year=y, step="6 decomposition sample (misaligned EXCLUDED), = step 4", **ms(a.idx_ON)))
    return pd.DataFrame(rows), lst


def part1(j):
    flag = j.idx_flag.astype(bool); robust = ~j.is_roll & ~j.near_expiry
    WT, OF = [], []
    for var, col in [("dbasis_ON", "dbasis_ON"), ("dbasis_ID", "dbasis_ID")]:
        for per, g in periods_1b(j).items():
            if var == "dbasis_ID" and per == "pre 2022-08-25": pass
            for samp, mask in [("all days", pd.Series(True, index=g.index)), ("ex index-flagged", ~flag.reindex(g.index)),
                               ("all days, ex roll & expiry-1..+1", robust.reindex(g.index)),
                               ("ex flagged, ex roll & expiry-1..+1", (~flag & robust).reindex(g.index))]:
                gg = g[mask]
                rows, jt = weekday_test(gg[col], gg.night)
                base = dict(variable=var, period=per, sample=samp)
                for r in rows: WT.append({**base, **r})
                WT.append({**base, "night": "JOINT (all 5 equal)", "n": jt["n"], "mean_bp": jt.get("grand_mean_bp"), "mean_t": jt.get("grand_mean_t"),
                           "wald": jt.get("wald"), "wald_p": jt.get("wald_p"), "n_excluded_holiday": jt["n_excluded_holiday"]})
    for samp, jj in [("all days", j), ("ex index-flagged", j[~flag])]:
        for lab, g in [(str(y), jj[jj.index.year == y]) for y in range(2022, 2027)] + \
                      [("post 2022-08-25 pooled", jj[jj.index >= CUTOVER]), ("pre 2022-08-25 pooled (reference)", jj[jj.index < CUTOVER]),
                       ("post 2022-08-25, ex roll & expiry-1..+1", jj[(jj.index >= CUTOVER) & ~jj.is_roll & ~jj.near_expiry])]:
            OF.append(dict(sample=samp, period=lab, **ols_ak(g.fut_ON, g.idx_ON), mean_dbasis_bp=g.dbasis_ON.mean() * 1e4))
    return pd.DataFrame(WT), pd.DataFrame(OF)


# ------------------------------------------------------------------ Part 2: probe and cache
PROBE = [("VCI", "VN30F1M", "1m"), ("VCI", "VN30F1M", "5m"), ("VCI", "VN30F1M", "15m"), ("VCI", "VN30", "1m"), ("VCI", "VN30", "5m"), ("VCI", "VN30", "15m"),
         ("KBS", "VN30F1M", "1m"), ("KBS", "VN30F1M", "5m"), ("KBS", "VN30F1M", "15m"), ("KBS", "VN30", "1m"), ("KBS", "VN30", "5m"), ("KBS", "VN30", "15m")]


def fetch_probe():
    from vnstock import Quote
    from fetch_indices import THROTTLE_SECS
    IDIR.mkdir(parents=True, exist_ok=True); rows = []
    for src, sym, iv in PROBE:
        rec = dict(source=src, symbol=sym, interval=iv)
        for attempt in range(3):
            try:
                df = Quote(symbol=sym, source=src).history(start="2017-01-01", end=pd.Timestamp.today().strftime("%Y-%m-%d"), interval=iv)
                if df is None or df.empty: rec["status"] = "empty"; break
                df.to_csv(IDIR / f"{src}_{sym}_{iv}.csv", index=False)
                rec.update(status="ok", rows_raw=len(df)); break
            except BaseException as e:                              # vnstock's rate limiter raises SystemExit
                rec["status"] = f"error {type(e).__name__}: {str(e)[:120]}"; time.sleep(65 if attempt < 2 else 0)
        rows.append(rec); print(rec, flush=True); time.sleep(THROTTLE_SECS + 1)
    pd.DataFrame(rows).to_csv(IDIR / "_probe_fetch_log.csv", index=False)


def load_bars(src, sym, iv) -> pd.DataFrame | None:
    p = IDIR / f"{src}_{sym}_{iv}.csv"
    if not p.exists(): return None
    x = pd.read_csv(p, parse_dates=["time"]).dropna(subset=["open", "close"])   # VCI 5m/15m pad a 24h grid with NaN rows
    x["date"] = x.time.dt.normalize(); x["hm"] = x.time.dt.strftime("%H:%M")
    return x


def describe_bars(x: pd.DataFrame, daily: pd.DataFrame, sym: str) -> dict:
    f, l = x.groupby("date").first(), x.groupby("date").last()
    k = f[["open", "hm"]].join(daily[["open", "close"]].add_suffix("_d"), how="inner"); k["last_close"] = l.close; k["last_hm"] = l.hm
    per = x.groupby("date").size()
    exp_first = "09:00" if sym.startswith("VN30F") else "09:15"
    return dict(first=x.time.min(), last=x.time.max(), days=len(per), rows=len(x), median_bars_per_day=per.median(),
                first_bar_hm_mode=f.hm.mode().iat[0], share_first_bar_at_expected=(f.hm == exp_first).mean(),
                n_bars_before_0900=int((x.hm < "09:00").sum()),
                first_open_eq_daily_open=np.isclose(k.open, k.open_d, atol=0.051).mean(), last_close_eq_daily_close=np.isclose(k.last_close, k.close_d, atol=0.051).mean(),
                last_bar_hm_mode=l.hm.mode().iat[0], days_matched_to_daily=len(k))


def probe_md():
    from data_cap import futures_csv
    Fd = pd.read_csv(futures_csv("VN30F1M"), parse_dates=["date"]).set_index("date")
    Id = pd.read_csv(RAW_DIR / "VN30.csv", parse_dates=["date"]).set_index("date")
    log = pd.read_csv(IDIR / "_probe_fetch_log.csv") if (IDIR / "_probe_fetch_log.csv").exists() else None
    rows = []
    for src, sym, iv in PROBE:
        x = load_bars(src, sym, iv)
        if x is None or x.empty: rows.append(dict(source=src, symbol=sym, interval=iv, status="no data")); continue
        rows.append(dict(source=src, symbol=sym, interval=iv, status="ok", **describe_bars(x, Fd if sym.startswith("VN30F") else Id, sym)))
    P = pd.DataFrame(rows)
    # bar-label test: 5m vs 1m (index, VCI) and futures 5m vs 1m
    tests = []
    for sym in ["VN30", "VN30F1M"]:
        a, b = load_bars("VCI", sym, "1m"), load_bars("VCI", sym, "5m")
        if a is None or b is None: continue
        a, b = a.set_index("time"), b.set_index("time")
        c = b.index.intersection(a.index); c = c[(c.strftime("%H:%M") > "09:15") & (c.strftime("%H:%M") < "11:25")]
        tests.append(dict(symbol=sym, n=len(c), open5_eq_open1_same_label=np.isclose(b.open.reindex(c), a.open.reindex(c), atol=0.011).mean(),
                          close5_eq_close1_label_plus4m=np.isclose(b.close.reindex(c), a.close.reindex(c + pd.Timedelta("4min")), atol=0.011).mean(),
                          close5_eq_close1_same_label=np.isclose(b.close.reindex(c), a.close.reindex(c), atol=0.011).mean()))
    T = pd.DataFrame(tests)
    # index 5m VCI vs KBS at the sampling times
    xc = []
    v5, k5, v1 = load_bars("VCI", "VN30", "5m"), load_bars("KBS", "VN30", "5m"), load_bars("VCI", "VN30", "1m")
    if v5 is not None:
        for h in IDX_H:
            pv = v5[v5.hm == h].set_index("date").open
            for nm, o in [("KBS 5m", k5), ("VCI 1m", v1)]:
                if o is None: continue
                po = o[o.hm == h].set_index("date").open; c = pv.index.intersection(po.index)
                xc.append(dict(h=h, vs=nm, n=len(c), share_equal=np.isclose(pv[c], po[c], atol=0.011).mean(), max_abs_diff=(pv[c] - po[c]).abs().max()))
    X = pd.DataFrame(xc)
    f1 = load_bars("VCI", "VN30F1M", "1m")
    pre = f1[f1.hm < "09:00"][["time", "open", "close", "volume"]] if f1 is not None else pd.DataFrame()
    vc = f1.hm.value_counts() if f1 is not None else pd.Series(dtype=int)
    vmed = f1.pivot_table(index="date", columns="hm", values="volume").median() if f1 is not None else pd.Series(dtype=float)
    L = ["# Intraday feasibility probe (vnstock sources only: VCI, then KBS)", "",
         f"Probe run {pd.Timestamp.today():%Y-%m-%d}; raw responses cached in data/raw_intraday/ (separate from data/raw/). "
         "Query: Quote(symbol, source).history(start='2017-01-01', end=today, interval). Community-tier warnings printed by vnstock: "
         "'1m limited to 6 months', '5m/15m limited to 1 year'.", "",
         "## Coverage per source / symbol / interval", (log.to_string(index=False) if log is not None else ""), "",
         P.to_string(index=False), "",
         "## Findings",
         "- **VN30F1M 1m (VCI) goes back to 2023-09-11 (~3.2 years, ~241 bars/day), despite vnstock's stated 6-month community cap** for 1m. "
         "That cap may be enforced later, so the data is cached now. Earlier than 2023-09-11 nothing is returned (no row cap observed: the response is not a round number). "
         "VCI VN30F1M 5m/15m and VCI VN30 5m/15m return 1 year on a padded 24h grid (NaN rows outside the session; dropped). "
         "KBS VN30F1M intraday is sparse (1m starts 2026-05-25 with ~6,200 rows; many minutes missing) and is not used.",
         "- **VN30 index intraday exists**: VCI/KBS 1m from 2026-05-25 (~6 months), VCI/KBS 5m from 2025-11-20 (1 year). The first index bar of each day is 09:15 "
         "(the stock ATO result); there is no index print between 09:00 and 09:15. The 1m/5m windows roll (on this run VCI 5m starts 2025-11-24, VCI 1m 2026-05-27).",
         "- **KBS index 09:15 bar disagrees with the daily open**: KBS's first index bar open equals the (VCI) daily open on only ~40% of days, by up to ~39 points, "
         "while VCI 5m/1m match it on 99.6%/98%; at 09:30 and 10:00 KBS and VCI agree exactly. VCI 5m is used, KBS is a cross-check only.",
         "- The response includes the current, incomplete session (2026-11-23 VN time) and 2026-11-18..20, after the daily files end; analysis only uses dates present in the daily files.",
         "- **Timezone**: timestamps are naive and run 09:00..14:45 (futures) / 09:15..14:45 (index), i.e. Vietnam local time (UTC+7); no conversion applied.",
         "- **Daily-bar check**: first intraday bar open vs daily open and last bar close vs daily close are in the table (columns first_open_eq_daily_open, last_close_eq_daily_close).",
         "- **How the futures ATO appears**: there is no separate 08:45 bar. The ATO match (struck at 09:00) is folded into the bar labelled 09:00: its open equals the daily open "
         f"on ~99.7% of days and its median volume ({vmed.get('09:00', np.nan):.0f} contracts) is >2x the 09:01 bar ({vmed.get('09:01', np.nan):.0f}). "
         f"Only {len(pre)} stray bars before 09:00 exist in 3 years (dates {', '.join(sorted(set(str(t.date()) for t in pre.time)))}); they are ignored. "
         "The ATC appears as a single bar labelled 14:45 whose close equals the daily close on every day.",
         f"- Bars labelled 11:30 exist on {int(vc.get('11:30', 0))} of {f1.date.nunique() if f1 is not None else 0} futures days and 14:30 on {int(vc.get('14:30', 0))}; "
         "there are no 12:59 or 14:31..14:44 bars. Consistent with bar-START labels (prints stamped exactly at 11:30:00 / 14:30:00 fall in a minute of their own).",
         "", "## Bar-timestamp convention test (5m bars vs 1m bars, VCI)",
         "If labels are bar-start, a 5m bar labelled t has the open of the 1m bar t and the close of the 1m bar t+4min.", T.to_string(index=False), "",
         "Result: **labels are bar-start times**. Price at time h is therefore taken as the open of the bar labelled h (first print at or after h).", "",
         "## Index 5m (VCI, used) vs KBS 5m and VCI 1m at the sampling times (open of bar labelled h)", X.to_string(index=False), "",
         "## Decision", "VN30F1M intraday history is >1 month (3.2 years), so Part 2 runs. Basis at matched times is limited to the index-intraday window "
         "(5m, 2025-11-20 onward). No trackforward addendum is required by the stop rule; track_forward.py and the frozen boundary are untouched."]
    (OUT / "intraday_probe.md").write_text("\n".join(L) + "\n")
    return P, T, X


# ------------------------------------------------------------------ Part 2: analysis
def price_at(x: pd.DataFrame, hs: list[str]) -> tuple[pd.DataFrame, dict]:
    """open of the bar labelled h; else last close before h on that date (counted)."""
    o = x.pivot_table(index="date", columns="hm", values="open", aggfunc="first")
    c = x.pivot_table(index="date", columns="hm", values="close", aggfunc="last")
    out, ff = {}, {}
    for h in hs:
        v = o[h] if h in o.columns else pd.Series(np.nan, index=o.index)
        prior = c.loc[:, [k for k in c.columns if k < h]].ffill(axis=1).iloc[:, -1] if any(k < h for k in c.columns) else pd.Series(np.nan, index=c.index)
        ff[h] = int((v.isna() & prior.notna()).sum()); out[h] = v.fillna(prior)
    return pd.DataFrame(out), ff


def part2(j, fut):
    f1, i5 = load_bars("VCI", "VN30F1M", "1m"), load_bars("VCI", "VN30", "5m")
    if f1 is None: return None
    FP, ff_f = price_at(f1, FUT_H)
    IP, ff_i = price_at(i5, IDX_H) if i5 is not None else (pd.DataFrame(), {})
    info = dict(fut_ffill=ff_f, idx_ffill=ff_i, fut_days=len(FP), idx_days=len(IP), fut_first=FP.index.min(), idx_first=IP.index.min() if len(IP) else None)
    R = []
    # ---- gate: 09:00 exit reproduces build() gross and net on the same nights
    d = build(0, BASE["roll_cost"], fee_vnd=BASE["fee_vnd"], slippage=BASE["slippage"])
    d = d[d.invested & d.index.isin(FP.index)]
    f09 = FP["09:00"].reindex(d.index)
    g_gross = (f09 / d.entry - 1); g_net = g_gross - (BASE["fee_vnd"] / (MULT * d.entry) + BASE["fee_vnd"] / (MULT * f09) + 2 * BASE["slippage"] + np.where(d.is_roll, BASE["roll_cost"], 0))
    info["gate"] = dict(n=len(d), max_abs_gross_diff_bp=float((g_gross - d.r_gross).abs().max() * 1e4), mean_gross_diff_bp=float((g_gross - d.r_gross).mean() * 1e4),
                        mean_net_diff_bp=float((g_net - d.r_net).mean() * 1e4), n_open_mismatch=int((~np.isclose(f09, d.open)).sum()))
    # ---- futures cumulative return from prior ATC to h (all invested nights with intraday coverage)
    # entry as in the daily decomposition: aligned nights only (drops Thu-close -> Mon-open nights around missing roll days)
    fv = fut[fut.invested & fut.index.isin(FP.index) & fut.index.isin(j.index)].copy()
    info["fv_dropped_misaligned"] = int((fut.invested & fut.index.isin(FP.index) & ~fut.index.isin(j.index)).sum())
    for h in FUT_H: fv[f"cum_{h}"] = np.log(FP[h].reindex(fv.index) / fv.entry)
    fv["c0900_0915"] = fv["cum_09:15"] - fv["cum_09:00"]; fv["c0900_0930"] = fv["cum_09:30"] - fv["cum_09:00"]; fv["c0900_1000"] = fv["cum_10:00"] - fv["cum_09:00"]
    grp = [(str(y), fv[fv.index.year == y]) for y in sorted(set(fv.index.year))] + [("2023-09-11 onward (all intraday)", fv)]
    for lab, g in grp:
        for nightsel, gg in [("all nights", g), ("Mon->Tue", g[g.night == "Mon->Tue"])]:
            for h in FUT_H: R.append(dict(table="2.2a futures cum ln return prior ATC -> h", period=lab, subset=nightsel, h=h, **ms(gg[f"cum_{h}"])))
    # ---- catch-up 09:00 -> 09:15 / 09:30 by index-ON tercile (aligned decomposition nights with intraday futures)
    jj = j[j.index.isin(FP.index)].copy()
    for col, h in [("c0900_0915", "09:15"), ("c0900_0930", "09:30"), ("c0900_1000", "10:00")]: jj[col] = fv[col].reindex(jj.index)
    jj["terc"] = pd.qcut(jj.idx_ON, 3, labels=["T1 small/negative", "T2 middle", "T3 large gap-up"])
    cut = jj.groupby("terc").idx_ON.agg(["min", "max"]) * 1e4
    for t, g in list(jj.groupby("terc")) + [("all", jj)]:
        rng = f"idx_ON {cut.loc[t,'min']:.0f}..{cut.loc[t,'max']:.0f} bp" if t != "all" else ""
        for col in ["c0900_0915", "c0900_0930", "c0900_1000"]:
            R.append(dict(table="2.2b futures catch-up from 09:00 by index-ON tercile (2023-09-11 onward)", period=str(t), subset=rng, h=col.replace("c0900_", "09:00->").replace("0915", "09:15").replace("0930", "09:30").replace("1000", "10:00"),
                          **ms(g[col]), idx_ON_mean_bp=g.idx_ON.mean() * 1e4, dbasis_ON_mean_bp=g.dbasis_ON.mean() * 1e4))
    # ---- basis at matched times (index-intraday window)
    REC = []
    if len(IP):
        bb = j[j.index.isin(FP.index) & j.index.isin(IP.index)].copy()
        chk = np.isclose(IP["09:15"].reindex(bb.index), bb.open_idx, atol=0.051)
        info["idx_0915_eq_daily_open"] = float(chk.mean()); info["basis_window"] = (bb.index.min(), bb.index.max(), len(bb))
        for h in IDX_H:
            bb[f"b_{h}"] = np.log(FP[h].reindex(bb.index) / IP[h].reindex(bb.index))
            bb[f"dB_prev_{h}"] = bb[f"b_{h}"] - bb.b_prevclose            # basis change prior close -> h (matched clocks)
            bb[f"rec_{h}"] = bb[f"b_{h}"] - bb.b_open                     # basis change from the daily opens (F 09:00, I 09:15) -> h
        bb["shortfall"] = -bb.dbasis_ON
        wl = f"index-intraday window ({bb.index.min():%Y-%m-%d} onward)"
        il30 = np.log(IP["09:30"].reindex(bb.index) / IP["09:15"].reindex(bb.index))
        info["corr_idxON_idx0915_0930"] = float(bb.idx_ON.corr(il30)); info["slope_idx0915_0930_on_idxON"] = float(np.polyfit(bb.idx_ON, il30, 1)[0])
        # legs of the recovery: (ln F_h - ln F_0900) - (ln I_h - ln I_0915); who moves, futures or index?
        for h in IDX_H:
            fl = np.log(FP[h].reindex(bb.index) / FP["09:00"].reindex(bb.index)); il = np.log(IP[h].reindex(bb.index) / IP["09:15"].reindex(bb.index))
            for lab, sel in [(wl, slice(None)), ("Wed->Thu (window)", bb.night == "Wed->Thu"), ("Fri->Mon (weekend) (window)", bb.night == "Fri->Mon (weekend)")]:
                R.append(dict(table="2.2e recovery legs: futures 09:00->h and index 09:15->h", period=lab, subset="futures leg", h=h, **ms(fl[sel])))
                R.append(dict(table="2.2e recovery legs: futures 09:00->h and index 09:15->h", period=lab, subset="index leg", h=h, **ms(il[sel])))
        for lab, g in [(wl, bb), ("2026 only", bb[bb.index.year == 2026])] + [(f"{nm} (window)", bb[bb.night == nm]) for nm in CATS]:
            R.append(dict(table="2.2c basis change from prior close", period=lab, subset="", h="daily open (F 09:00 / I 09:15) = dbasis_ON", **ms(g.dbasis_ON)))
            for h in IDX_H:
                R.append(dict(table="2.2c basis change from prior close", period=lab, subset="", h=f"{h} matched", **ms(g[f"dB_prev_{h}"])))
            for h in IDX_H:
                rc = ratio_ci(g[f"rec_{h}"], g.shortfall)
                REC.append(dict(period=lab, h=f"daily open -> {h}", **rc, shortfall_t=nw_t(g.shortfall), num_t=nw_t(g[f"rec_{h}"])))
        info["bb"] = bb
    # ---- Monday exit-time sensitivity (descriptive), simple returns, base costs as level_c_phase2 (incl. 5 bp roll placeholder)
    m = d[(d.hold_type == "") & (pd.Series(d.index, index=d.index).shift(1).dt.weekday.values == 0)] if False else None
    dd = build(0, BASE["roll_cost"], fee_vnd=BASE["fee_vnd"], slippage=BASE["slippage"])
    ew = pd.Series(dd.index, index=dd.index).shift(1).dt.weekday
    mon = dd[(dd.hold_type == "") & dd.invested & (ew == 0) & dd.index.isin(FP.index)]
    for h in ["09:00", "09:15", "09:30"]:
        px = FP[h].reindex(mon.index)
        gross = px / mon.entry - 1
        net = gross - (BASE["fee_vnd"] / (MULT * mon.entry) + BASE["fee_vnd"] / (MULT * px) + 2 * BASE["slippage"] + np.where(mon.is_roll, BASE["roll_cost"], 0))
        for lab, sel in [("2023-09-11 onward (post-cutover, intraday window)", slice(None)), ("2026", mon.index.year == 2026)]:
            R.append(dict(table="2.3 Monday exit-time sensitivity (simple, descriptive)", period=lab, subset="gross", h=h, **ms(gross[sel])))
            R.append(dict(table="2.3 Monday exit-time sensitivity (simple, descriptive)", period=lab, subset="net of base costs", h=h, **ms(net[sel])))
    return pd.DataFrame(R), pd.DataFrame(REC), info


# ------------------------------------------------------------------ main
def fmt(df, cols=None): return (df if cols is None else df[[c for c in cols if c in df.columns]]).to_string(index=False)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--probe", action="store_true"); a = ap.parse_args()
    pd.set_option("display.width", 250, "display.max_columns", 40, "display.float_format", "{:.3f}".format, "display.max_colwidth", 70)
    if a.probe:
        fetch_probe(); P, T, X = probe_md(); print(P.to_string(index=False)); print(T.to_string(index=False)); print(X.to_string(index=False)); return
    j, _ = samples(); fut = FB.futures_nights()
    RC, LST = reconcile()
    pd.concat([RC.assign(section="waterfall"), LST.assign(section="misaligned nights")], ignore_index=True).to_csv(OUT / "futures_basis_followup_reconcile.csv", index=False)
    WT, OF = part1(j)
    WT.to_csv(OUT / "futures_basis_followup_weekday_tests.csv", index=False); OF.to_csv(OUT / "futures_basis_followup_offset.csv", index=False)
    p2 = part2(j, fut) if (IDIR / "VCI_VN30F1M_1m.csv").exists() else None
    if p2 is not None:
        R2, REC, info = p2
        pd.concat([R2, REC.assign(table="2.2d recovery of overnight shortfall (ratio, delta-method NW CI)")], ignore_index=True).to_csv(OUT / "futures_basis_followup_intraday.csv", index=False)

    L = ["# Futures basis follow-up (measurement only)", "",
         "## 1a. Reconcile 2023 index ON (11.1 bp decomposition sample vs 9.9 bp full index)", fmt(RC), "",
         "Misaligned nights (prior trading day differs between VN30F1M and VN30):", fmt(LST.drop(columns=["year"])), ""]
    def wt(var, per, samp, cols=("night", "n", "mean_bp", "mean_t", "minus_others_bp", "minus_others_t", "wald", "wald_p", "n_excluded_holiday")):
        return fmt(WT[(WT.variable == var) & (WT.period == per) & (WT["sample"] == samp)], list(cols))
    L += ["## 1b. Weekday equality on dbasis_ON (5 night dummies, no intercept, HAC lag 5 over consecutive nights; 'minus others' = beta_k - mean of the other four betas; "
          "joint Wald chi2(4) that all five are equal; holiday nights excluded). JOINT row: mean_bp = period grand mean (all five categories)."]
    for per in ["pre 2022-08-25", "post 2022-08-25", "2023-01-01 onward"]:
        for samp in ["all days", "ex index-flagged", "all days, ex roll & expiry-1..+1", "ex flagged, ex roll & expiry-1..+1"]:
            L += [f"### {per} | {samp}", wt("dbasis_ON", per, samp), ""]
    L += ["## 1c. Offset vs proportional lag: fut_ON = a + k idx_ON (NW SEs)", fmt(OF), "",
          "## 1d. Weekday equality on the intraday basis change dbasis_ID = fut_ID - idx_ID"]
    for per in ["post 2022-08-25", "2023-01-01 onward"]:
        for samp in ["all days", "all days, ex roll & expiry-1..+1"]:
            L += [f"### {per} | {samp}", wt("dbasis_ID", per, samp), ""]
    probe_txt = (OUT / "intraday_probe.md").read_text() if (OUT / "intraday_probe.md").exists() else "(probe not run)"
    L += ["## 2.0 Probe outcome (full text: results/intraday_probe.md)", probe_txt.split("## Findings")[1].split("## Bar-timestamp")[0].strip() if "## Findings" in probe_txt else probe_txt, ""]
    if p2 is not None:
        g = info["gate"]
        L += ["## 2.x Reproduction gate: exit at the 09:00 bar open vs build() (same nights, base costs incl. 5 bp roll placeholder)",
              f"n {g['n']}; max |gross diff| {g['max_abs_gross_diff_bp']:.3f} bp, mean gross diff {g['mean_gross_diff_bp']:.4f} bp, mean net diff {g['mean_net_diff_bp']:.4f} bp; "
              f"nights where the 09:00 bar open != daily open: {g['n_open_mismatch']}.",
              f"Forward-fills (no print in minute h): futures {info['fut_ffill']} of {info['fut_days']} days; index {info['idx_ffill']} of {info['idx_days']} days. "
              f"Index 09:15 bar open == daily index open on {info.get('idx_0915_eq_daily_open', np.nan)*100:.1f}% of basis-window nights; basis window {info.get('basis_window')}.", ""]
        L += [f"2.2a uses aligned decomposition nights only ({info['fv_dropped_misaligned']} misaligned Thu-close -> Mon-open nights in the intraday window dropped).", ""]
        for t in R2.table.unique():
            L += [f"## {t}", fmt(R2[R2.table == t].drop(columns=["table"]).dropna(axis=1, how="all")), ""]
            if t.startswith("2.3"):
                L += ["DESCRIPTIVE ONLY, NO EXIT SELECTION. Exits after 09:00 are fills in the continuous session and carry intraday price risk over the extra 15-30 minutes; "
                      "the base costs (12,500 VND/side + 1 bp slippage/side + 5 bp roll placeholder) are applied unchanged although continuous-session fills are not auction fills. "
                      "These rows cannot be mixed into the pre-registered rule (exit = Tuesday ATO, results/phase2_trackforward_spec.md), which is unchanged.", ""]
        L += ["## 2.2d Recovery: mean(b_h - b_open) / mean(-dbasis_ON) on the same nights (b_open = ln F_0900 - ln I_0915, the daily decomposition's open basis). "
              "From daily open -> 09:15 the index term is zero (I_0915 is the index open), so that ratio is pure futures movement.", fmt(REC), ""]
    # ---------------- verdicts
    L += ["## Pre-registered reads (as written)",
          "- W1: Wednesday is special if Wed->Thu dbasis minus the other weekdays is negative with |t| > 2 post-2022-08-25 and still |t| > 2 excluding roll and near-expiry nights. Otherwise the Wednesday 'puzzle' is a uniform post-2022 basis shortfall.",
          "- W2: Monday is special if Mon->Tue minus others is positive with |t| > 2 under the same two conditions.",
          "- T1 (mechanical timing): holds if, post-2022-08-25, the 09:00->09:30 basis change recovers >= 50% of the mean overnight basis shortfall, with a CI excluding zero. "
          "T2 (systematic offset): holds if recovery is < 25% or the CI includes zero while the shortfall is significant. Between 25% and 50% is ambiguous.",
          "- O1: offset in the daily fit, a is significantly negative (|t| > 2) post-2022-08-25.", "- Between thresholds = ambiguous. Bonferroni: 5 weekday cells x 3 periods x 2 variables = 30 'minus others' cells -> |t| ~3.1.", ""]
    V = []
    def cell(night, samp, per="post 2022-08-25"):
        return WT[(WT.variable == "dbasis_ON") & (WT.period == per) & (WT["sample"] == samp) & (WT.night == night)].iloc[0]
    for samp_pair in [("all days", "all days, ex roll & expiry-1..+1"), ("ex index-flagged", "ex flagged, ex roll & expiry-1..+1")]:
        w0, w1 = cell("Wed->Thu", samp_pair[0]), cell("Wed->Thu", samp_pair[1])
        m0, m1 = cell("Mon->Tue", samp_pair[0]), cell("Mon->Tue", samp_pair[1])
        def vv(c0, c1, sign):
            ok = lambda c: (np.sign(c.minus_others_bp) == sign) and abs(c.minus_others_t) > 2
            if ok(c0) and ok(c1): return "HOLDS"
            if (np.sign(c0.minus_others_bp) == sign and abs(c0.minus_others_t) > 2) or (np.sign(c1.minus_others_bp) == sign and abs(c1.minus_others_t) > 2): return "AMBIGUOUS (one condition only)"
            return "DOES NOT HOLD"
        V.append(f"[{samp_pair[0]}] W1 {vv(w0, w1, -1)}: Wed->Thu minus others {w0.minus_others_bp:.2f} bp (t {w0.minus_others_t:.2f}); ex roll/near-expiry {w1.minus_others_bp:.2f} bp (t {w1.minus_others_t:.2f}, n {int(w1.n)}).")
        V.append(f"[{samp_pair[0]}] W2 {vv(m0, m1, +1)}: Mon->Tue minus others {m0.minus_others_bp:.2f} bp (t {m0.minus_others_t:.2f}); ex roll/near-expiry {m1.minus_others_bp:.2f} bp (t {m1.minus_others_t:.2f}, n {int(m1.n)}).")
    for samp in ["all days", "ex index-flagged"]:
        o = OF[(OF["sample"] == samp) & (OF.period == "post 2022-08-25 pooled")].iloc[0]
        o1 = "HOLDS" if (o.a_bp < 0 and abs(o.a_t) > 2) else "DOES NOT HOLD"
        V.append(f"[{samp}] O1 {o1}: post-2022-08-25 a = {o.a_bp:.2f} bp (NW t {o.a_t:.2f}), k = {o.k:.3f} (SE {o.k_se:.3f}; t vs 1 {o.k_t_vs1:.2f}), n {int(o.n)}.")
    if p2 is not None and len(REC):
        lg = R2[(R2.table.str.startswith("2.2e")) & R2.period.str.startswith("index-intraday window") & (R2.h == "09:30")].set_index("subset")
        r = REC[(REC.period.str.startswith("index-intraday window")) & (REC.h == "daily open -> 09:30")].iloc[0]
        rr, lo, hi = r.ratio, r.fieller_lo, r.fieller_hi; sf_sig = abs(r.shortfall_t) > 2
        if rr >= 0.5 and lo > 0: t1 = "T1 HOLDS (mechanical timing)"
        elif (rr < 0.25 or (lo <= 0 <= hi)) and sf_sig: t1 = "T2 HOLDS as written (CI includes zero while the shortfall is significant)"
        elif not sf_sig: t1 = "NEITHER (shortfall not significant in the window)"
        else: t1 = "AMBIGUOUS"
        V.append(f"T1/T2 [window {info['basis_window'][0]:%Y-%m-%d}..{info['basis_window'][1]:%Y-%m-%d}, n {int(r.n)}, NOT the full post-2022-08-25 period]: {t1}. "
                 f"Shortfall -dbasis_ON {r.den_bp:.2f} bp (NW t {r.shortfall_t:.2f}); basis change daily open -> 09:30 {r.num_bp:.2f} bp (t {r.num_t:.2f}); "
                 f"recovery point estimate {rr*100:.0f}%, Fieller 95% CI {lo*100:.0f}% .. {hi*100:.0f}% (contains 0 because |t_num| < 1.96; the delta-method CI "
                 f"{r.delta_lo*100:.0f}%..{r.delta_hi*100:.0f}% understates the uncertainty near zero and is not used). The point estimate is above 50%, so the evidence leans toward "
                 "a transient shortfall but is not conclusive on one year of data. MECHANISM (point estimates): the movement is mostly on the INDEX side after its 09:15 open "
                 f"(index leg 09:15->09:30 {lg.loc['index leg','mean_bp']:.2f} bp, t {lg.loc['index leg','t']:.2f}) rather than futures catching up "
                 f"(futures leg 09:00->09:30 {lg.loc['futures leg','mean_bp']:.2f} bp, t {lg.loc['futures leg','t']:.2f}); on matched clocks at 09:15 the shortfall is unchanged. "
                 f"The post-open index move does not scale with the overnight gap (corr(idx_ON, index 09:15->09:30) = {info['corr_idxON_idx0915_0930']:.3f}, slope "
                 f"{info['slope_idx0915_0930_on_idxON']:.3f}), so it looks more like a roughly constant post-open index drift than a gap-proportional overshoot or a futures lag.")
    L += ["## Verdicts"] + V
    L += ["", "## Notes",
          "- 1a: the 2023 gap (9.86 -> 11.08 bp) is entirely the 24 index nights around the 12 2023 roll days that are MISSING from data/raw/VN30F1M.csv (the first trading day after each "
          "3rd-Thursday expiry is absent for 14 consecutive months, 2022-11 .. 2023-12; the VCI 1m feed omits the same days). Each missing day removes the index Thu->Fri night (no futures bar) and makes the next Monday misaligned "
          "(futures night spans Thu close -> Mon open, including Friday's session and a contract change). Those futures-only nights remain in level_c_futures.build() as 'holiday' "
          "nights (e.g. 2023-08-21 fut ON -506 bp); they do not enter Monday statistics. Including 2021-05-04 (VN30F1M.csv also lacks 2021-04-29), the 15 nights whose prior futures day is missing sum to "
          "-1,061 bp of simple futures ON, i.e. -0.46 bp on the 2,284-night all-nights futures mean (4.99 bp with them, 5.49 bp without). Reported only; existing files were not changed.",
          "- 2.x gate: the 12 nights where the 09:00 bar open differs from the daily open are 5 days with stray pre-09:00 prints (the daily open is the first stray print), "
          "5 days with no 09:00 bar (dropped, no fill possible) and 2 days with a 0.1-0.8 point difference; mean difference 0.03 bp.",
          "- The weekday HAC t-stats differ from futures_basis_decomp Table B because lags here run over consecutive nights, not consecutive same-weekday nights."]
    (OUT / "futures_basis_followup_summary.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
