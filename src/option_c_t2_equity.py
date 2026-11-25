"""Phase 2, Option C: T+2-constrained equity version of the overnight effect (MEASUREMENT ONLY).

Single VN30 stocks, point-in-time membership as of the ENTRY date T (latest effective_date <= T in
data/vn30_pit_membership.csv, the same lookup pit_dayofweek_2x2.py uses). T+k = k-th next VNINDEX trading day.

Settlement (see results/option_c_summary.md for sources):
  regime 2, entries T >= CUTOVER: shares credited before 13:00 on T+2 -> earliest exit Close[T+2] (ATC).
  regime 1, entries T <  CUTOVER: earliest sale T+3 -> earliest exit Open[T+3] (ATO); Close[T+3] variant also.
Legs (log): ON_k = ln O[T+k] - ln C[T+k-1], ID_k = ln C[T+k] - ln O[T+k].

Rules are computed for EVERY entry date (column `executable` marks rule == actual regime; the other rows are
counterfactual "same rule in the other regime" comparisons). Inference is on date-level baskets, never pooled
stock-nights. Imports pit_dayofweek_2x2 (loads data at import, writes nothing); level_b_dayofweek.py is NOT
imported because it rewrites its results at import time.
"""
import sys, math
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import numpy as np, pandas as pd
import warnings
warnings.filterwarnings("ignore", message=".*encountered in matmul")   # spurious macOS-Accelerate matmul warnings; results checked finite
pd.set_option("future.no_silent_downcasting", True)
import pit_dayofweek_2x2 as X          # PIT membership M, build_weights (s*f*c), cell_series, START
from level_a import RAW_DIR

CUTOVER = pd.Timestamp("2022-08-25")   # first trade date (T+0) sellable in the T+2 afternoon (VSD 109/110/QD-VSD, eff. 2022-08-29)
START = X.START                        # 2018-11-21, stock price data limit
LIMIT = 0.069                          # HOSE +/-7% band; >= +6.9% close = limit-up (unbuyable), <= -6.9% = limit-down (unsellable)
TAX_BP, BROKER_BP, MIN_K = 10.0, (10, 15, 25), 10
OUT = Path("results")
WD = {0: "Mon", 1: "Tue", 2: "Wed", 3: "Thu", 4: "Fri"}
PERIODS = {"P1 2018-11..2022-08 (regime 1)": (START, CUTOVER - pd.Timedelta(days=1)),
           "P2 2022-08-25..2025 (regime 2)": (CUTOVER, pd.Timestamp("2025-12-31")),
           "P3 2026-only (regime 2)": (pd.Timestamp("2026-01-01"), pd.Timestamp("2026-12-31")),
           "Regime 2 all (P2+P3)": (CUTOVER, pd.Timestamp("2026-12-31")),
           "Full 2018-11..2026-11": (START, pd.Timestamp("2026-12-31"))}
RULES = {"R2_T2close": dict(H=2, exit="close", regime=2), "R1_T3open": dict(H=3, exit="open", regime=1),
         "R1_T3close": dict(H=3, exit="close", regime=1)}

# ---------------- panel on the VNINDEX calendar ----------------
cal = pd.read_csv(RAW_DIR / "VNINDEX.csv", parse_dates=["date"])["date"]
cal = pd.DatetimeIndex(sorted(cal[cal >= START - pd.Timedelta(days=10)]))
tickers = X.tickers
O, C, S = {}, {}, {}
for t in tickers:
    d = pd.read_csv(RAW_DIR / f"{t}.csv", parse_dates=["date"]).drop_duplicates("date").set_index("date").reindex(cal)
    O[t], C[t], S[t] = d["open"].where(d["open"] > 0), d["close"].where(d["close"] > 0), d["open_suspicious"].astype("boolean").fillna(True).astype(bool)
O, C, S = pd.DataFrame(O), pd.DataFrame(C), pd.DataFrame(S)
lo, lc = np.log(O), np.log(C)
gap = pd.Series(cal.to_series().diff().dt.days.values, index=cal)          # calendar days of the night ending on each date

M = X.M
eff = np.array(sorted(M.effective_date.unique()), dtype="datetime64[ns]")
eidx = np.searchsorted(eff, cal.values, side="right") - 1
mem_sets = {e: set(M.ticker[M.effective_date == e]) for e in eff}
MEM = pd.DataFrame(False, index=cal, columns=tickers)
for i, e in enumerate(eidx):
    if e >= 0: MEM.iloc[i] = [t in mem_sets[eff[e]] for t in tickers]
W = X.build_weights("pit", "B")                                           # {effective_date: s*f*c}
WCAP = pd.DataFrame(np.nan, index=cal, columns=tickers)
for i, e in enumerate(eidx):
    if e >= 0 and pd.Timestamp(eff[e]) in W: WCAP.iloc[i] = W[pd.Timestamp(eff[e])].reindex(tickers).values
WCAP = WCAP * C                                                           # x Close[T] (back-adjusted prices, flag 8)
ENTRY = MEM & (cal >= START)[:, None]


def sh(df, k):
    return df.shift(-k)


def rule_panel(H, exit):
    legs = {}
    for k in range(1, H + 1):
        legs[f"ON{k}"] = sh(lo, k) - sh(lc, k - 1)
        if not (exit == "open" and k == H): legs[f"ID{k}"] = sh(lc, k) - sh(lo, k)
    xl = (sh(lc, H) if exit == "close" else sh(lo, H)) - lc
    inwin = pd.Series(np.arange(len(cal)) + H < len(cal), index=cal)
    cand = ENTRY & inwin.values[:, None]
    bars = C.notna() & C.shift(1).notna()
    for k in range(1, H + 1): bars &= sh(O, k).notna() & sh(C, k).notna()
    buy_lu = (C / C.shift(1) - 1) >= LIMIT
    sell_ld = ((sh(C, H) / sh(C, H - 1) - 1) if exit == "close" else (sh(O, H) / sh(C, H - 1) - 1)) <= -LIMIT
    susp = pd.DataFrame(False, index=cal, columns=tickers)
    for k in range(1, H + 1): susp |= sh(S, k).fillna(True).astype(bool)
    E = cand & bars & ~buy_lu & ~sell_ld
    D = E & ~susp
    chk = sum(legs.values()).where(E) - xl.where(E)
    assert np.nanmax(np.abs(chk.values)) < 1e-9, "legs do not sum to the hold"
    clean = pd.Series(np.ones(len(cal), bool), index=cal)
    for k in range(1, H + 1): clean &= (gap.shift(-k) == 1).values
    counts = dict(candidates=int(cand.values.sum()), skip_missing_bar=int((cand & ~bars).values.sum()),
                  excl_buy_limit_up=int((cand & bars & buy_lu).values.sum()),
                  excl_sell_limit_down=int((cand & bars & ~buy_lu & sell_ld).values.sum()),
                  eligible_close_set=int(E.values.sum()), dropped_suspicious_open=int((E & susp).values.sum()),
                  decomp_set=int(D.values.sum()))
    counts["dropped_suspicious_share_%"] = 100 * counts["dropped_suspicious_open"] / max(counts["eligible_close_set"], 1)
    return legs, xl, E, D, clean, counts


def basket(vals, mask, w=None):
    v = vals.where(mask)
    if w is None:
        r, k = v.mean(axis=1), v.notna().sum(axis=1)
    else:
        ww = w.where(v.notna())
        r, k = (v * ww).sum(axis=1) / ww.sum(axis=1), ww.notna().sum(axis=1)
    return r.where(k >= MIN_K), k


def nw_se(x, L):
    x = np.asarray(x, float); n = len(x); u = x - x.mean(); lrv = u @ u / n
    for l in range(1, L + 1): lrv += 2 * (1 - l / (L + 1)) * (u[l:] @ u[:-l]) / n
    return math.sqrt(lrv / n)


def st(x, L=None):
    x = x.dropna(); n = len(x)
    if n < 3: return dict(n_dates=n)
    out = dict(n_dates=n, mean_bp=x.mean() * 1e4, sd_bp=x.std() * 1e4, t=x.mean() / (x.std() / math.sqrt(n)), hit_pct=(x > 0).mean() * 100)
    if L: out["t_nw"] = x.mean() / nw_se(x, L)
    out["small_n_flag"] = n < 20
    return out


def hac_weekday(y, L):
    """y: date-level Series; regress on 5 weekday dummies, Bartlett HAC. Returns Wald(equal means) p and MonTue-WedThu t."""
    y = y.dropna(); wd = y.index.weekday.values; Xd = np.stack([(wd == k).astype(float) for k in range(5)], 1)
    keep = Xd.sum(0) > 0; Xd = Xd[:, keep]; n, p = Xd.shape
    XtX_i = np.linalg.inv(Xd.T @ Xd); b = XtX_i @ Xd.T @ y.values; u = y.values - Xd @ b; g = Xd * u[:, None]
    Sm = g.T @ g
    for l in range(1, L + 1): G = g[l:].T @ g[:-l]; Sm += (1 - l / (L + 1)) * (G + G.T)
    V = XtX_i @ Sm @ XtX_i
    R = np.hstack([np.ones((p - 1, 1)), -np.eye(p - 1)])
    Wd = float((R @ b) @ np.linalg.inv(R @ V @ R.T) @ (R @ b)); df = p - 1
    pval = math.exp(-Wd / 2) * (1 + Wd / 2) if df == 4 else float("nan")   # chi2(4) survival, closed form
    c = np.zeros(p); idx = list(np.where(keep)[0])
    for k, wt in ((0, .5), (1, .5), (2, -.5), (3, -.5)):
        if k in idx: c[idx.index(k)] = wt
    return dict(wald_equal_weekdays=Wd, wald_df=df, wald_p=pval, montue_minus_wedthu_bp=float(c @ b) * 1e4,
                montue_minus_wedthu_t_hac=float(c @ b / math.sqrt(c @ V @ c)))


def cells(series_fn):
    """yield (period, sample, weekday, Series) for each cut; series_fn(sample) -> date-level Series"""
    for per, (a, b) in PERIODS.items():
        for sample in SAMPLES:
            s = series_fn(sample)
            s = s[(s.index >= a) & (s.index <= b)]
            if sample.endswith("ex2021"): s = s[s.index.year != 2021]
            yield per, sample, "All", s
            for k, nm in WD.items(): yield per, sample, nm, s[s.index.weekday == k]


def main():
    global SAMPLES
    holds, legrows, grid, counts_rows, hac_rows, series = [], [], [], [], [], {}
    for rn, spec in RULES.items():
        H, ex, reg = spec["H"], spec["exit"], spec["regime"]
        legs, xl, E, D, clean, cnt = rule_panel(H, ex)
        regime_of = pd.Series(np.where(cal >= CUTOVER, 2, 1), index=cal)
        for per, (a, b) in PERIODS.items():
            m = ((cal >= a) & (cal <= b))[:, None]
            counts_rows.append(dict(rule=rn, period=per, **{k: int((v & m).values.sum()) if isinstance(v, pd.DataFrame) else v for k, v in
                                    dict(candidates=ENTRY & m & pd.Series(np.arange(len(cal)) + H < len(cal), index=cal).values[:, None],
                                         eligible_close_set=E, decomp_set=D).items()}))
        counts_rows.append(dict(rule=rn, period="ALL (detail)", **cnt))
        hold_set = D if ex == "open" else E
        simple = np.exp(xl) - 1
        ser = {}
        for sample in ("all", "clean"):
            cm = clean.values[:, None] if sample == "clean" else True
            ser[("EW", sample)] = basket(simple, hold_set & cm)
            ser[("EWlog", sample)] = basket(xl, hold_set & cm)
            ser[("cap", sample)] = basket(simple, hold_set & cm, WCAP)
        series[rn] = ser
        # ---- holds
        SAMPLES = ("all", "clean")
        for wgt in ("EW", "cap"):
            for per, sample, wd, s in cells(lambda smp: ser[(wgt, smp)][0]):
                exe = (per.startswith("P1") and reg == 1) or (("regime 2" in per or "Regime 2" in per) and reg == 2)
                sl = ser[("EWlog", sample)][0].reindex(s.index) if wgt == "EW" else None
                k = ser[(wgt, sample)][1].reindex(s.dropna().index)
                r = dict(rule=rn, hold_nights=H, exit=ex, executable=exe, period=per, sample=sample, weighting=wgt, weekday=wd,
                         hold_set="decomp (opens clean)" if ex == "open" else "close-only", mean_k=k.mean(),
                         **st(s, H if wd == "All" else None))
                if sl is not None and len(s.dropna()): r["mean_log_bp"] = sl.mean() * 1e4
                for bb in BROKER_BP:
                    if "mean_bp" in r: r[f"net_bp_brk{bb}"] = r["mean_bp"] - (2 * bb + TAX_BP)
                holds.append(r)
                if exe and sample == "all" and "mean_bp" in r:
                    for bb in BROKER_BP:
                        rt = 2 * bb + TAX_BP; se = r["sd_bp"] / math.sqrt(r["n_dates"])
                        if wd == "All": se = nw_se(s.dropna() * 1e4, H)
                        grid.append(dict(rule=rn, period=per, weighting=wgt, weekday=wd, n_dates=r["n_dates"], brokerage_bp_side=bb,
                                         roundtrip_cost_bp=rt, gross_bp=r["mean_bp"], net_bp_per_hold=r["mean_bp"] - rt,
                                         net_t=(r["mean_bp"] - rt) / se, net_bp_per_overnight=(r["mean_bp"] - rt) / H,
                                         breakeven_roundtrip_bp=r["mean_bp"], gross_t=r.get("t_nw", r["t"])))
        # ---- weekday HAC tests on the full date series
        for per, (a, b) in PERIODS.items():
            for wgt in ("EW", "cap"):
                y = ser[(wgt, "all")][0]; y = y[(y.index >= a) & (y.index <= b)]
                if y.notna().sum() > 50: hac_rows.append(dict(rule=rn, period=per, weighting=wgt, nw_lags=H, **hac_weekday(y, H)))
        # ---- legs on the decomposition subset (same dates/stocks for legs and hold)
        SAMPLES = ("all", "clean", "ex2021", "no_open_filter")
        names = list(legs)
        lb = {}
        for sample in ("all", "clean"):
            cm = clean.values[:, None] if sample == "clean" else True
            lb[sample] = {nm: basket(v, D & cm)[0] for nm, v in legs.items()}
            lb[sample]["xlog"] = basket(xl, D & cm)[0]; lb[sample]["xsimple"] = basket(simple, D & cm)[0]
            lb[sample]["k"] = basket(xl, D & cm)[1]
        lb["ex2021"] = lb["all"]
        lb["no_open_filter"] = {nm: basket(v, E)[0] for nm, v in legs.items()}
        lb["no_open_filter"].update(xlog=basket(xl, E)[0], xsimple=basket(simple, E)[0], k=basket(xl, E)[1])
        for per, (a, b) in PERIODS.items():
            for sample in SAMPLES:
                base = lb[sample]; idx = base["xlog"].dropna().index
                idx = idx[(idx >= a) & (idx <= b)]
                if sample == "ex2021": idx = idx[idx.year != 2021]
                for wd in ["All"] + list(WD.values()):
                    ii = idx if wd == "All" else idx[idx.weekday == [k for k, v in WD.items() if v == wd][0]]
                    if len(ii) < 3:
                        legrows.append(dict(rule=rn, period=per, sample=sample, weekday=wd, n_dates=len(ii))); continue
                    on = sum(base[nm].reindex(ii) for nm in names if nm.startswith("ON"))
                    idd = sum(base[nm].reindex(ii) for nm in names if nm.startswith("ID"))
                    L = H if wd == "All" else 0
                    tt = lambda x: x.mean() / (nw_se(x, L) if L else x.std() / math.sqrt(len(x)))
                    r = dict(rule=rn, executable=(per.startswith("P1") and reg == 1) or ("egime 2" in per and reg == 2),
                             period=per, sample=sample, weekday=wd, n_dates=len(ii), mean_k=base["k"].reindex(ii).mean(),
                             **{f"{nm}_bp": base[nm].reindex(ii).mean() * 1e4 for nm in names},
                             overnight_only_bp=on.mean() * 1e4, intraday_drag_bp=idd.mean() * 1e4,
                             hold_log_bp=base["xlog"].reindex(ii).mean() * 1e4, hold_simple_bp=base["xsimple"].reindex(ii).mean() * 1e4,
                             t_overnight_only=tt(on), t_intraday=tt(idd), t_hold=tt(base["xlog"].reindex(ii)),
                             giveback_share_of_overnight=(-idd.mean() / on.mean()) if on.mean() > 0 else np.nan,
                             small_n_flag=len(ii) < 20)
                    legrows.append(r)
    pd.DataFrame(legrows).to_csv(OUT / "option_c_legs.csv", index=False)
    HO = pd.DataFrame(holds); HO.to_csv(OUT / "option_c_holds.csv", index=False)
    G = pd.DataFrame(grid); G.to_csv(OUT / "option_c_cost_grid.csv", index=False)
    HAC = pd.DataFrame(hac_rows); CNT = pd.DataFrame(counts_rows)
    LG = pd.DataFrame(legrows)
    lb_tab = levelb_basket()
    write_summary(HO, LG, G, HAC, CNT, lb_tab)


def levelb_basket():
    """1-night day-of-week on date-level EW baskets, PIT membership (reuses pit_dayofweek_2x2.cell_series; nights keyed by
    open-date weekday there: 1 = Mon->Tue). Same filters as Level B: one-day nights, open_suspicious and |ON|>7% dropped, k>=10."""
    lbcsv = pd.read_csv(OUT / "level_b_dayofweek.csv"); lbcsv = lbcsv[lbcsv["filter"] == "filtered"].set_index("night")
    pit = X.cell_series("pit", "ew"); cur = X.levelb_ew()
    rows = []
    per_cuts = {"Full 2018-11..2026-11": (START, pd.Timestamp("2026-12-31")), **{k: v for k, v in PERIODS.items() if k[:2] in ("P1", "P2", "P3")}}
    for per, (a, b) in per_cuts.items():
        p = pit[(pit.index >= a) & (pit.index <= b)]; c = cur[(cur.index >= a) & (cur.index <= b)]
        for wd, nm in X.NAMES.items():
            x, y = p[p.wd == wd].r, c[c.wd == wd].r
            r = dict(period=per, night=nm, pit_ew_dates=len(x), pit_ew_mean_bp=x.mean() * 1e4, pit_ew_t=x.mean() / (x.std() / math.sqrt(len(x))),
                     pit_ew_hit_pct=(x > 0).mean() * 100, cur30_ew_dates=len(y), cur30_ew_mean_bp=y.mean() * 1e4, cur30_ew_t=y.mean() / (y.std() / math.sqrt(len(y))))
            if per.startswith("Full") and nm in lbcsv.index:
                r.update(pooled_stock_nights=lbcsv.loc[nm, "stock_nights"], pooled_mean_bp=lbcsv.loc[nm, "pooled_mean_bp"],
                         pooled_naive_t=lbcsv.loc[nm, "pooled_naive_t"], levelb_csv_ew_mean_bp=lbcsv.loc[nm, "ew_mean_bp"], levelb_csv_ew_t=lbcsv.loc[nm, "ew_t"])
            rows.append(r)
        mt, wt = p[p.wd.isin([1, 2])].r, p[p.wd.isin([3, 4])].r
        rows.append(dict(period=per, night="Mon+Tue minus Wed+Thu", pit_ew_dates=len(mt) + len(wt), pit_ew_mean_bp=(mt.mean() - wt.mean()) * 1e4,
                         pit_ew_t=(mt.mean() - wt.mean()) / math.sqrt(mt.var() / len(mt) + wt.var() / len(wt))))
    T = pd.DataFrame(rows); T.to_csv(OUT / "levelb_dayofweek_basket.csv", index=False)
    return T


def write_summary(HO, LG, G, HAC, CNT, LBT):
    pd.set_option("display.width", 250, "display.max_columns", 40, "display.float_format", "{:.2f}".format)
    R2 = "Regime 2 all (P2+P3)"; P1 = "P1 2018-11..2022-08 (regime 1)"
    def hrow(rule, per, wgt="EW", sample="all", wd="All"):
        x = HO[(HO.rule == rule) & (HO.period == per) & (HO.weighting == wgt) & (HO["sample"] == sample) & (HO.weekday == wd)]
        return x.iloc[0] if len(x) else None
    def lrow(rule, per, sample="all", wd="All"):
        x = LG[(LG.rule == rule) & (LG.period == per) & (LG["sample"] == sample) & (LG.weekday == wd)]
        return x.iloc[0] if len(x) else None
    def tab(df, cols):
        return df[cols].to_string(index=False)
    L = []
    L.append("# Option C: T+2-constrained equity overnight effect (measurement only)\n")
    L.append("Nothing is selected here, so there is no forward test. Single VN30 stocks, point-in-time membership as of the entry date, "
             "date-level baskets for all inference.\n")
    L.append("## Settlement rule and source")
    L.append(f"- Cutover constant `CUTOVER = {CUTOVER.date()}` (trade date T+0). Trades on/after it: shares credited before 13:00 on T+2, "
             "sellable in the T+2 afternoon session -> earliest exit Close[T+2] (ATC). Before it: earliest sale T+3 -> earliest exit Open[T+3] (ATO).")
    L.append("- Source: Thi truong Tai chinh Tien te (SBV-affiliated journal), 'Tu ngay 29/8, chinh thuc rut ngan thoi gian thanh toan giao dich chung khoan xuong con T+2': "
             "VSD Decisions 109/QD-VSD (clearing & settlement rules) and 110/QD-VSD (depository members), effective 29/8/2022; trades of 25/8/2022 (T+0) are the first "
             "that can be sold in the afternoon of T+2 (29/8) 'instead of waiting until T+3 as before'; VSD settlement moved from 15:30-16:00 to 11:00-11:30 on T+2, members allocate to clients before 13:00. "
             "https://thitruongtaichinhtiente.vn/tu-ngay-29-8-chinh-thuc-rut-ngan-thoi-gian-thanh-toan-giao-dich-chung-khoan-xuong-con-t-2-41949.html . "
             "Decision 109/QD-VSD is dated 19/8/2022 (luatvietnam.vn listing).")
    L.append("- NOT confirmed from the primary VSD document (full text behind a login). Also not confirmed: that regime-1 shares were sellable at the T+3 ATO "
             "(the source says only 'T+3'); that the 25 Aug 2022 entry is the first one in regime 2 is from the news source, not the decision text.")
    L.append("- T+k uses the VNINDEX trading calendar. Period P1 ends the day before the cutover, so P1 = regime 1 exactly; the 5 entry dates 25-31 Aug 2022 are in P2.\n")
    L.append("## Assumptions (parameters, not facts)")
    L.append(f"- Sale tax {TAX_BP:.0f} bp on the sell leg; brokerage swept over {BROKER_BP} bp per side; round trip = 2 x brokerage + tax = 30 / 40 / 60 bp.")
    L.append("- Slippage 0: ATC/ATO fills at the official print. This is idealized (no market impact, no queue risk at the ATC).")
    L.append("- One round trip per hold. 'Per overnight' = net per hold / number of overnight legs in the hold (2 in regime 2, 3 in regime 1).")
    L.append("- Headline returns are simple (EW basket P&L); legs are log returns (additive). Log means sit below simple means by about sigma^2/2.")
    L.append("- Limit filters: entry excluded if Close[T] >= +6.9% vs prior close (limit-up, unbuyable); excluded if the exit price is <= -6.9% vs prior close (limit-down, unsellable). "
             "Prices are back-adjusted (data-quality flag 8), consistent with the exchange's adjusted reference price on ex-dates. New-listing and ex-right bands are ignored.")
    L.append("- Cap-weighted basket: reuses pit_dayofweek_2x2.build_weights('pit','B') (shares x free float x capping factor, latest-shares variant B) x Close[T]. "
             "Back-adjusted prices mix with historical share counts (flag 8), so cap weights are approximate.")
    L.append(f"- Baskets need >= {MIN_K} eligible stocks on the date. Newey-West (Bartlett) lags = hold length for pooled all-days series; within a weekday entries are weekly and non-overlapping, so plain t.\n")
    L.append("## Filter counts (stock-entries)")
    L.append(tab(CNT[CNT.period == "ALL (detail)"], ["rule", "candidates", "skip_missing_bar", "excl_buy_limit_up", "excl_sell_limit_down",
                                                     "eligible_close_set", "dropped_suspicious_open", "dropped_suspicious_share_%", "decomp_set"]))
    L.append("\nBy period (stock-entries):")
    L.append(tab(CNT[CNT.period != "ALL (detail)"], ["rule", "period", "candidates", "eligible_close_set", "decomp_set"]))
    L.append("\n## Executable hold, gross (EW basket, simple returns, all entry dates)")
    ex = HO[HO.executable & (HO["sample"] == "all")]
    L.append(tab(ex[ex.weighting == "EW"], ["rule", "period", "weekday", "n_dates", "mean_k", "mean_bp", "mean_log_bp", "sd_bp", "t", "t_nw", "hit_pct", "net_bp_brk10", "net_bp_brk25"]))
    L.append("\nCap-weighted:")
    L.append(tab(ex[ex.weighting == "cap"], ["rule", "period", "weekday", "n_dates", "mean_bp", "t", "t_nw", "net_bp_brk10"]))
    L.append("\nClean subset (all nights in the hold are one-day nights). Regime 2 Thu/Fri entries and regime 1 Wed/Thu/Fri entries always span a weekend, so those cells are empty by construction:")
    cl = HO[HO.executable & (HO["sample"] == "clean") & (HO.weighting == "EW")]
    L.append(tab(cl, ["rule", "period", "weekday", "n_dates", "mean_bp", "t", "t_nw"]))
    L.append("\n## Leg decomposition (EW, log, decomposition subset: all opens in the window not suspicious; hold on the SAME subset)")
    lg = LG[LG.executable.fillna(False).astype(bool) & (LG.n_dates >= 3)]
    legcols = lambda rule: [c for c in LG.columns if c.endswith("_bp") and c[:2] in ("ON", "ID") and LG[LG.rule == rule][c].notna().any()]
    for rule in RULES:
        x = lg[lg.rule == rule]
        if x.empty: continue
        L.append(f"\n{rule}:")
        L.append(tab(x, ["period", "sample", "weekday", "n_dates", "mean_k"] + legcols(rule) + ["overnight_only_bp", "intraday_drag_bp", "hold_log_bp", "t_overnight_only", "t_intraday", "t_hold"]))
    L.append("\n## Cross-weekday tests (HAC, Bartlett, lags = hold length). 5 weekdays x several periods = many comparisons; descriptive only, no 'best' weekday is selected.")
    L.append(tab(HAC, ["rule", "period", "weighting", "wald_equal_weekdays", "wald_p", "montue_minus_wedthu_bp", "montue_minus_wedthu_t_hac"]))
    L.append("\n## Cost grid: breakeven round-trip cost = gross mean (executable, EW)")
    gg = G[(G.weighting == "EW") & (G.brokerage_bp_side == 10)]
    L.append(tab(gg, ["rule", "period", "weekday", "n_dates", "gross_bp", "gross_t", "breakeven_roundtrip_bp"]))
    L.append("\nNet per hold at each brokerage level (All days, EW):")
    L.append(tab(G[(G.weighting == "EW") & (G.weekday == "All")], ["rule", "period", "brokerage_bp_side", "roundtrip_cost_bp", "gross_bp", "net_bp_per_hold", "net_t", "net_bp_per_overnight"]))
    L.append("\n## Secondary: Level B 1-night day-of-week, date-level EW baskets")
    L.append(tab(LBT[LBT.period.str.startswith("Full")], ["night", "pooled_mean_bp", "pooled_naive_t", "levelb_csv_ew_mean_bp", "levelb_csv_ew_t",
                                                          "cur30_ew_mean_bp", "cur30_ew_t", "pit_ew_dates", "pit_ew_mean_bp", "pit_ew_t"]))
    L.append("\nPIT EW by period:")
    L.append(tab(LBT[~LBT.period.str.startswith("Full")], ["period", "night", "pit_ew_dates", "pit_ew_mean_bp", "pit_ew_t"]))

    # ---------------- verdict ----------------
    h2 = hrow("R2_T2close", R2); h1 = hrow("R1_T3close", P1); h1o = hrow("R1_T3open", P1)
    l2 = lrow("R2_T2close", R2); l2x = lrow("R2_T2close", R2, "ex2021")
    l1 = lrow("R1_T3open", P1); l1x = lrow("R1_T3open", P1, "ex2021")
    def cls(g, rt): return "(a) positive net" if g - rt > 0 else ("(b) positive gross, consumed by costs" if g > 0 else "(c) not positive even gross")
    v = []
    v.append(f"VERDICT (current regime 2, T+2 ATC exit, EW, {int(h2.n_dates)} entry dates {CUTOVER.date()}..): gross {h2.mean_bp:.1f} bp per 2-night hold "
             f"(NW t {h2.t_nw:.2f}; log {h2.mean_log_bp:.1f} bp), breakeven round trip {h2.mean_bp:.1f} bp vs cost 30/40/60 bp -> "
             + "; ".join(f"brokerage {bb} bp/side: {cls(h2.mean_bp, 2*bb+TAX_BP)} (net {h2.mean_bp-2*bb-TAX_BP:.1f} bp)" for bb in BROKER_BP) + ".")
    if abs(h2.t_nw) < 2: v.append(f"The gross mean is not distinguishable from zero (|t| {abs(h2.t_nw):.2f} < 2).")
    v.append(f"Give-back (same decomposition subset, n {int(l2.n_dates)}): overnight-only ON1+ON2 {l2.overnight_only_bp:.1f} bp (t {l2.t_overnight_only:.2f}), "
             f"intraday ID1+ID2 {l2.intraday_drag_bp:.1f} bp (t {l2.t_intraday:.2f}), executable hold {l2.hold_log_bp:.1f} bp (log)"
             + (f"; the intraday legs give back {100*l2.giveback_share_of_overnight:.0f}% of the overnight edge" if pd.notna(l2.giveback_share_of_overnight) else "")
             + ". (Regime 2 has no 2021 entries, so its ex-2021 cut equals the full cut.)")
    v.append(f"Regime 1 (T+3, {int(h1.n_dates)} dates): close-to-close T+3 gross {h1.mean_bp:.1f} bp (NW t {h1.t_nw:.2f}); ATO T+3 exit on the open-clean subset "
             f"{h1o.mean_bp:.1f} bp (n {int(h1o.n_dates)}). Decomposition ON1+ON2+ON3 {l1.overnight_only_bp:.1f} bp vs intraday {l1.intraday_drag_bp:.1f} bp "
             f"(n {int(l1.n_dates)}); ex-2021 ON {l1x.overnight_only_bp:.1f} / ID {l1x.intraday_drag_bp:.1f} bp (n {int(l1x.n_dates)}).")
    hE = hrow("R2_T2close", R2); lN = lrow("R2_T2close", R2, "no_open_filter"); lC = lrow("R2_T2close", R2, "clean")
    v.append(f"Filter sensitivity: single-stock 'open == prior close' flags run 20-38% in EVERY year (mostly genuine ATO-at-reference prints, not the 2021 feed artifact), "
             f"so the open filter removes ~45% of regime-2 stock-entries and is selective: on the filtered subset the hold is {l2.hold_log_bp:.1f} bp log vs {hE.mean_log_bp:.1f} bp on the close-only set. "
             f"Without the open filter (same close-only set as the headline) ON1+ON2 {lN.overnight_only_bp:.1f} bp (t {lN.t_overnight_only:.2f}), ID1+ID2 {lN.intraday_drag_bp:.1f} bp (t {lN.t_intraday:.2f}), "
             f"give-back {100*lN.giveback_share_of_overnight:.0f}%. Clean (no weekend/holiday in the hold) filtered subset: give-back {100*lC.giveback_share_of_overnight:.0f}%; the weekend-spanning Thu/Fri entries carry much of the intraday drag. "
             "So 'the intraday legs give back most of the overnight edge' is robust; the exact share is filter-sensitive.")
    l1N = lrow("R1_T3close", P1, "no_open_filter")
    v.append(f"Regime 1 is not read as a give-back: there is no overnight edge to give back. ON1+ON2+ON3 is about zero filtered ({l1.overnight_only_bp:.1f} bp) and unfiltered "
             f"({l1N.overnight_only_bp:.1f} bp, close-exit variant), negative ex-2021, consistent with the 1-night PIT basket for P1 (2-4 bp, t < 0.7); the T+3 hold's return came from intraday legs. "
             "Opens in 2019-2021 are the least reliable in the data, so treat the regime-1 split as unreliable. The regime-1 close-to-close hold does not use opens.")
    pc = {nm: hrow("R2_T2close", per) for nm, per in (("P2 2022-08-25..2025", "P2 2022-08-25..2025 (regime 2)"), ("P3 2026", "P3 2026-only (regime 2)"))}
    hc = hrow("R2_T2close", R2, wgt="cap")
    v.append("Per period (regime 2, 30 bp lowest round trip): " + "; ".join(f"{k} gross {x.mean_bp:.1f} bp (NW t {x.t_nw:.2f}) -> {cls(x.mean_bp, 30)}" for k, x in pc.items())
             + f"; cap-weighted regime 2 gross {hc.mean_bp:.1f} bp (NW t {hc.t_nw:.2f}) -> {cls(hc.mean_bp, 30)}.")
    hx = HAC[(HAC.rule == "R2_T2close") & (HAC.period == R2) & (HAC.weighting == "EW")].iloc[0]
    v.append(f"Weekday pattern (descriptive; 5 weekdays x 3 periods = 15 cells, Bonferroni |t| ~2.9; no weekday is selected): the pre-specified Mon+Tue minus Wed+Thu contrast "
             f"carried over from Level B / futures is {hx.montue_minus_wedthu_bp:.1f} bp per hold in regime 2 (HAC t {hx.montue_minus_wedthu_t_hac:.2f}); "
             f"equal-weekday Wald p {hx.wald_p:.3f}. Per-weekday net figures are in option_c_cost_grid.csv and are not a strategy.")
    verdict = " ".join(v)
    L.append("\n## Verdict\n" + verdict)
    (OUT / "option_c_summary.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
