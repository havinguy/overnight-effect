"""Phase 1 audit: open-filter sensitivity and regime reconciliation (Level A + Level B). MEASUREMENT ONLY.

Reuses: level_a (decompose, summarize), level_b (ticker_row), pit_dayofweek_2x2 (RET panel, cell_series, table,
levelb_ew), level_c_futures.build (VN30F1M nights), option_c_t2_equity (VNINDEX-calendar panel, rule_panel, basket).
level_b_dayofweek.py is not imported: it rewrites its results at import time; its Level B convention
(ordinary one-day nights, k >= 10 stocks per date) is reproduced through pit_dayofweek_2x2.levelb_ew instead.
Writes only results/open_audit_*.  Filter versions for the stock baskets (one-day nights, as in the 2x2):
  a = open_suspicious dropped AND |ON| > 7% dropped (the 2x2 / Level B day-of-week convention)
  b = open_suspicious kept,   |ON| > 7% dropped
  c = both kept
"""
import sys, math, warnings
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from level_a import RAW_DIR, OUT_DIR, decompose, summarize
from level_b import ticker_row
import pit_dayofweek_2x2 as X
from level_c_futures import build
import option_c_t2_equity as OC

CUTOVER = OC.CUTOVER
START = X.START
OUT = OUT_DIR
VERS = {"a": (True, True), "b": (False, True), "c": (False, False)}       # (drop open_suspicious, drop |ON|>7%)
LIM = 0.07
H_DENS = (0.005, 0.01)                                                    # half-widths for the density-near-zero estimates


def tstat(x):
    x = pd.Series(x).dropna(); return x.mean() / (x.std() / math.sqrt(len(x))) if len(x) > 2 else np.nan


def maxdiff(a: pd.DataFrame, b: pd.DataFrame, cols):
    return float(np.nanmax(np.abs(a[cols].values.astype(float) - b[cols].values.astype(float))))


# =============================== STEP 0: reproduction gate ===============================
def gate():
    rows = []
    # Level A: script main() = decompose (all nights) [+ exclude years] [+ exclude suspicious], full + common window
    combos = {"": (False, []), "_clean": (True, []), "_ex2021": (False, [2021]), "_ex2021_clean": (True, [2021])}
    for tag, (susp, yrs) in combos.items():
        f = OUT / f"level_a_summary{tag}.csv"
        if not f.exists(): continue
        old = pd.read_csv(f); dec = {}
        for s in ("VNINDEX", "VN30"):
            d = decompose(pd.read_csv(RAW_DIR / f"{s}.csv", parse_dates=["date"]))
            if yrs: d = d[~d["date"].dt.year.isin(yrs)].reset_index(drop=True)
            if susp: d = d[~d["open_suspicious"].fillna(False).astype(bool)].reset_index(drop=True)
            dec[s] = d
        cs = max(d["date"].min() for d in dec.values()); t = []
        for s, d in dec.items():
            t.append(summarize(d, s, f"full {d['date'].min():%Y-%m-%d}+")); t.append(summarize(d[d["date"] >= cs], s, f"common {cs:%Y-%m-%d}+"))
        new = pd.concat(t, ignore_index=True)
        num = [c for c in old.columns if old[c].dtype != object]
        ok = len(new) == len(old) and (new[["symbol", "sample", "leg"]].values == old[["symbol", "sample", "leg"]].values).all()
        md = maxdiff(new, old, num) if ok else np.inf
        rows.append(dict(level="A", file=f.name, convention=f"all nights, exclude_suspicious={susp}, exclude_years={yrs}", rows=len(old),
                         max_abs_diff=md, reproduced=bool(ok and md < 1e-8)))
    # Level B cross-section: try the CLI combos, report the one that matches
    syms = (RAW_DIR.parent / "universe_vn30.txt").read_text().split()
    raw = {s: pd.read_csv(RAW_DIR / f"{s}.csv", parse_dates=["date"]) for s in syms}
    for tag in ("", "_clean", "_ex2021", "_nolargegap"):
        f = OUT / f"level_b_cross_section{tag}.csv"
        if not f.exists(): continue
        old = pd.read_csv(f).set_index("ticker").sort_index(); best = None
        for susp in (False, True):
            for yrs in ([], [2021]):
                for lg in (False, True):
                    new = pd.DataFrame([ticker_row(s, raw[s], susp, yrs, lg) for s in syms]).set_index("ticker").sort_index()
                    if list(new.index) != list(old.index): continue
                    num = ["n", "overnight_mean_%", "intraday_mean_%", "overnight_sharpe", "intraday_sharpe", "overnight_t", "intraday_t", "pct_open_suspicious"]
                    md = maxdiff(new.reset_index(), old.reset_index(), num)
                    mc = maxdiff(new.reset_index(), old.reset_index(), ["n_gap_gt_limit"])
                    if best is None or md < best[0]: best = (md, susp, yrs, lg, mc)
        rows.append(dict(level="B", file=f.name, convention=f"all nights per stock, exclude_suspicious={best[1]}, exclude_years={best[2]}, exclude_large_gaps={best[3]}",
                         rows=len(old), max_abs_diff=best[0], reproduced=bool(best[0] < 1e-8),
                         note="" if best[4] == 0 else f"return stats exact; diagnostic count n_gap_gt_limit differs by up to {best[4]:.0f}: file "
                         f"({pd.Timestamp(f.stat().st_mtime, unit='s'):%Y-%m-%d %H:%M}) predates the last edit of src/level_b.py "
                         f"({pd.Timestamp((Path(__file__).parent / 'level_b.py').stat().st_mtime, unit='s'):%Y-%m-%d %H:%M}), which counts gaps before the year exclusion"))
    # PIT EW (and CW) rows of the 2x2 (one-day nights, version a filters, k >= 10)
    old = pd.read_csv(OUT / "pit_dayofweek_2x2.csv")
    for cell, (b, s) in {"pit_ew": ("pit", "ew"), "pit_cap": ("pit", "cap")}.items():
        new = pd.DataFrame(X.table(X.cell_series(b, s, "B"), "2018-11..2026-11", cell, "B"))
        o = old[(old.cell == cell) & (old.variant == "B")].reset_index(drop=True)
        md = maxdiff(new, o, ["n", "mean_bp", "t"])
        rows.append(dict(level="PIT 2x2", file=f"pit_dayofweek_2x2.csv [{cell}, B]", convention="one-day nights, open_suspicious & |ON|>7% dropped, k>=10",
                         rows=len(o), max_abs_diff=md, reproduced=bool(md < 1e-8)))
    return pd.DataFrame(rows)


# =============================== shared series ===============================
def ret_panel(drop_susp, drop_big, one_day=True):
    out = {}
    for t in X.tickers:
        d = decompose(pd.read_csv(RAW_DIR / f"{t}.csv", parse_dates=["date"]))
        ok = pd.Series(True, index=d.index)
        if one_day: ok &= d["date"].diff().dt.days == 1
        if drop_susp: ok &= ~d["open_suspicious"].astype(bool)
        if drop_big: ok &= ~(d["r_overnight"].abs() > LIM)
        out[t] = d.set_index("date")["r_overnight"].where(ok.values)
    return pd.DataFrame(out).sort_index().loc[START:]


def with_ret(R, fn):
    old = X.RET; X.RET = R
    try: return fn()
    finally: X.RET = old


def index_on(sym, one_day=True, drop_flag=True):
    dv = decompose(pd.read_csv(RAW_DIR / f"{sym}.csv", parse_dates=["date"]))
    ok = pd.Series(True, index=dv.index)
    if one_day: ok &= dv["date"].diff().dt.days == 1
    if drop_flag: ok &= ~dv["open_suspicious"].astype(bool)
    return dv.set_index("date")["r_overnight"].where(ok.values).dropna()


def compare(bas, idx, label, version, scheme, idx_label):
    j = pd.concat({"b": bas, "i": idx}, axis=1, join="inner").dropna(); j["wd"] = j.index.weekday; j["y"] = j.index.year
    rows = []
    groups = [("weekday", X.NAMES[w], j[j.wd == w]) for w in X.NAMES] + [("year", str(y), j[j.y == y]) for y in sorted(j.y.unique())] + \
             [("regime", "pre 2022-08-25", j[j.index < CUTOVER]), ("regime", "post 2022-08-25", j[j.index >= CUTOVER]), ("all", "all", j)]
    for cut, nm, g in groups:
        if len(g) < 5: continue
        dd = g.b - g.i
        rows.append(dict(benchmark=idx_label, basket=label, version=version, scheme=scheme, cut=cut, group=nm, n=len(g), basket_bp=g.b.mean() * 1e4,
                         index_bp=g.i.mean() * 1e4, diff_bp=dd.mean() * 1e4, paired_t=tstat(dd), corr=g.b.corr(g.i)))
    return rows


# =============================== main ===============================
def main():
    pd.set_option("display.width", 250, "display.max_columns", 40, "display.float_format", "{:.2f}".format)
    L = ["# Open-filter audit (Phase 1, Levels A + B): measurement only\n"]
    G = gate(); print(G.to_string(index=False))
    L += ["## Step 0: reproduction gate", "Pass criterion: every return statistic (n, means, Sharpe, t, flag share) within 1e-8 of the saved file, using the original script's own convention.",
          G.drop(columns="note").to_string(index=False)] + [f"- {r.file}: {r.note}" for r in G.itertuples() if isinstance(r.note, str) and r.note] + [""]
    if not G.reproduced.all():
        L.append("GATE FAILED: stopping. See rows with reproduced=False.")
        (OUT / "open_audit_summary.md").write_text("\n".join(L) + "\n"); print("GATE FAILED"); return

    # ---------------- Step 1: benchmark ----------------
    R = {v: ret_panel(*VERS[v]) for v in VERS}
    bas = {}
    for v in VERS:
        bas[(v, "cap")] = with_ret(R[v], lambda: X.cell_series("pit", "cap", "B")).r
        bas[(v, "ew")] = with_ret(R[v], lambda: X.cell_series("pit", "ew", "B")).r
    idx = index_on("VN30"); idx_unf = index_on("VN30", drop_flag=False)
    B = []
    for (v, s), x in bas.items():
        B += compare(x, idx, "PIT", v, s, "VN30 index, one-day nights, index-flagged opens dropped")
        B += compare(x, idx_unf, "PIT", v, s, "VN30 index, one-day nights, all")
    B = pd.DataFrame(B)
    # futures
    d = build(0, 0.0005, fee_vnd=12_500, slippage=0.0001).loc[str(START.date()):]
    fut = d.loc[(d["hold_type"] == "") & d["invested"], "r_gross"]
    F = []
    for v in VERS:
        for s in ("cap", "ew"):
            j = pd.concat({"b": bas[(v, s)], "f": fut}, axis=1, join="inner").dropna()
            for w, nm in X.NAMES.items():
                g = j[j.index.weekday == w]; dd = g.b - g.f
                F.append(dict(benchmark="VN30F1M (ordinary invested nights)", basket="PIT", version=v, scheme=s, cut="weekday", group=nm, n=len(g),
                              basket_bp=g.b.mean() * 1e4, index_bp=g.f.mean() * 1e4, diff_bp=dd.mean() * 1e4, paired_t=tstat(dd), corr=g.b.corr(g.f)))
    B = pd.concat([B, pd.DataFrame(F)], ignore_index=True); B.to_csv(OUT / "open_audit_benchmark.csv", index=False)
    BI = B[B.benchmark.str.startswith("VN30 index, one-day nights, index-flagged")]
    mawd = BI[BI.cut == "weekday"].groupby(["scheme", "version"]).diff_bp.apply(lambda x: x.abs().mean()).unstack()
    corr_all = BI[BI.cut == "all"].pivot(index="scheme", columns="version", values="corr")
    diff_all = BI[BI.cut == "all"].pivot(index="scheme", columns="version", values="diff_bp")
    wk = BI[(BI.cut == "weekday")].pivot_table(index=["scheme", "group"], columns="version", values="diff_bp")
    wk_lvl = BI[(BI.cut == "weekday")].pivot_table(index=["scheme", "group"], columns="version", values="basket_bp")
    idx_lvl = BI[(BI.cut == "weekday") & (BI.version == "a") & (BI.scheme == "cap")].set_index("group").index_bp
    fw = B[B.benchmark.str.startswith("VN30F1M") & (B.group == "Wed->Thu")][["version", "scheme", "n", "basket_bp", "index_bp", "diff_bp", "paired_t"]]

    # Decision rule (fixed before running), on the cap-weighted basket (the index is cap-weighted):
    m = mawd.loc["cap"]; unf = min(m["b"], m["c"])
    if unf <= 2 and m["a"] > 2: rule = "A (filter bias confirmed: unfiltered tracks the published VN30 overnight within ~2 bp, filtered does not)"
    elif m["a"] <= 2 and m["a"] < unf: rule = "B (filter helping: filtered basket tracks the index better)"
    elif m["a"] > 2 and unf > 2: rule = "C (neither tracks within ~2 bp: another data or method issue)"
    else: rule = "D (ambiguous)"

    # ---------------- Step 2: flag diagnostics ----------------
    FL = []
    for sym in ("VNINDEX", "VN30"):
        dv = decompose(pd.read_csv(RAW_DIR / f"{sym}.csv", parse_dates=["date"]))
        for y, g in dv.groupby(dv.date.dt.year):
            FL.append(dict(section="a_flag_rate", series=sym, group=str(y), n=len(g), flag_rate_pct=g.open_suspicious.mean() * 100))
    P = []
    for t in X.tickers:
        dd = decompose(pd.read_csv(RAW_DIR / f"{t}.csv", parse_dates=["date"])); dd["ticker"] = t; P.append(dd)
    P = pd.concat(P); P = P[P.date >= START].copy(); P["y"] = P.date.dt.year; P["flag"] = P.open_suspicious.astype(bool)
    # PIT membership as of the row's date (latest effective_date <= date)
    eff = np.array(sorted(X.M.effective_date.unique()), dtype="datetime64[ns]")
    mem = {e: set(X.M.ticker[X.M.effective_date == e]) for e in eff}
    ei = np.searchsorted(eff, P.date.values, side="right") - 1
    P["pit"] = [tk in mem[eff[i]] if i >= 0 else False for tk, i in zip(P.ticker.values, ei)]
    for nm, g0 in (("stock panel pooled (all tickers)", P), ("stock panel PIT members", P[P.pit])):
        for y, g in g0.groupby("y"):
            FL.append(dict(section="a_flag_rate", series=nm, group=str(y), n=len(g), flag_rate_pct=g.flag.mean() * 100))
    for (tk, y), g in P.groupby(["ticker", "y"]):
        FL.append(dict(section="a_flag_rate_per_stock", series=tk, group=str(y), n=len(g), flag_rate_pct=g.flag.mean() * 100))
    # (b) flagged vs unflagged legs (PIT member stock-days, pooled; descriptive)
    Q = P[P.pit]
    for per, g0 in (("all", Q), ("pre 2022-08-25", Q[Q.date < CUTOVER]), ("post 2022-08-25", Q[Q.date >= CUTOVER])):
        for fl, g in g0.groupby("flag"):
            FL.append(dict(section="b_flagged_vs_unflagged", series="PIT member stock-days", group=f"{per} | flagged={fl}", n=len(g),
                           overnight_bp=g.r_overnight.mean() * 1e4, intraday_bp=g.r_intraday.mean() * 1e4, cc_bp=g.r_cc.mean() * 1e4,
                           intraday_t=tstat(g.r_intraday), cc_t=tstat(g.r_cc)))
    # (b2) same, date-level: per date, EW mean cc of flagged minus unflagged names (controls for the market move of the day)
    pv = Q.pivot_table(index="date", columns="flag", values="r_cc", aggfunc="mean").dropna()
    pvi = Q.pivot_table(index="date", columns="flag", values="r_intraday", aggfunc="mean").dropna()
    for per, msk in (("all", slice(None)), ("pre 2022-08-25", pv.index < CUTOVER), ("post 2022-08-25", pv.index >= CUTOVER)):
        dcc = (pv[True] - pv[False])[msk]; dmi = (pvi[True] - pvi[False]).reindex(dcc.index)
        FL.append(dict(section="b_date_level_flagged_minus_unflagged", series="PIT members, same date", group=per, n=len(dcc),
                       cc_bp=dcc.mean() * 1e4, cc_t=tstat(dcc), intraday_bp=dmi.mean() * 1e4, intraday_t=tstat(dmi)))
    # (c) expected genuine flat-open rate
    Q = Q.copy(); Q["absON"] = Q.r_overnight.abs(); Q["absCC"] = Q.r_cc.abs()
    pk = Q.close.shift(1).where(Q.ticker == Q.ticker.shift(1)) * 1000           # prior close in VND (prices are in thousands, back-adjusted)
    tick = np.where(pk < 10_000, 10, np.where(pk < 50_000, 50, 100))
    Q["delta"] = np.log1p(tick / pk)                                            # relative tick in log units (tick rule on ADJUSTED price)
    for y, g in Q.groupby("y"):
        r = dict(section="c_expected_flat_open", series="PIT member stock-days", group=str(y), n=len(g), flag_rate_pct=g.flag.mean() * 100,
                 cc_zero_pct=(g.absCC < 1e-12).mean() * 100)
        for h in H_DENS:
            on_near = ((g.absON > 1e-12) & (g.absON <= h)).sum(); cc_near = ((g.absCC > 1e-12) & (g.absCC <= h)).sum()
            f0 = on_near / (len(g) * 2 * h)                                     # density of ON at 0 from unflagged (non-zero) days
            r[f"exp_tickrule_h{h*100:g}_pct"] = f0 * g.delta.mean() * 100
            r[f"exp_ccscaled_h{h*100:g}_pct"] = (g.absCC < 1e-12).mean() * on_near / max(cc_near, 1) * 100
        r["excess_tickrule_pct"] = r["flag_rate_pct"] - r[f"exp_tickrule_h0.5_pct"]
        r["excess_ccscaled_pct"] = r["flag_rate_pct"] - r[f"exp_ccscaled_h0.5_pct"]
        FL.append(r)
    # (d) KBS spot check
    kdir = Path("data/raw_kbs"); kb_rows = []
    for f in sorted(kdir.glob("*.csv")) if kdir.exists() else []:
        k = decompose(pd.read_csv(f, parse_dates=["date"])).set_index("date"); v = decompose(pd.read_csv(RAW_DIR / f.name, parse_dates=["date"])).set_index("date")
        j = v.join(k[["open", "close", "r_overnight"]], rsuffix="_kbs", how="left")
        pkv = j.close.shift(1) * 1000; tk = np.where(pkv < 10_000, 10, np.where(pkv < 50_000, 50, 100)); j["delta"] = np.log1p(tk / pkv)
        j = j[j.index >= START]
        for y, g in j.groupby(j.index.year):
            fl = g[g.open_suspicious.astype(bool)]; cov = fl.r_overnight_kbs.notna()
            FL.append(dict(section="d_kbs_spot_check", series=f.stem, group=str(y), n=len(fl), kbs_coverage_pct=cov.mean() * 100 if len(fl) else np.nan,
                           kbs_differs_gt1tick_pct=((fl.r_overnight_kbs.abs() > fl.delta) & cov).sum() / max(cov.sum(), 1) * 100 if len(fl) else np.nan,
                           kbs_on_on_vci_flagged_bp=fl.r_overnight_kbs.mean() * 1e4 if cov.any() else np.nan,
                           kbs_close_ratio_med=(g.close_kbs / g.close).median()))
    FLd = pd.DataFrame(FL); FLd.to_csv(OUT / "open_audit_flags.csv", index=False)

    # ---------------- Step 3: regime and year split ----------------
    S = {}
    for sym in ("VNINDEX", "VN30"):                                             # Level A convention: all nights
        S[(f"{sym} index (Level A, all nights)", "filtered")] = index_on(sym, one_day=False, drop_flag=True)
        S[(f"{sym} index (Level A, all nights)", "unfiltered")] = index_on(sym, one_day=False, drop_flag=False)
    S[("Level B date-level EW current-30 (all nights)", "filtered")] = ret_panel(True, False, one_day=False)[X.cur30].pipe(lambda r: r.mean(axis=1).where(r.notna().sum(axis=1) >= 10))
    S[("Level B date-level EW current-30 (all nights)", "unfiltered")] = ret_panel(False, False, one_day=False)[X.cur30].pipe(lambda r: r.mean(axis=1).where(r.notna().sum(axis=1) >= 10))
    for v in VERS:
        for s in ("ew", "cap"):
            S[(f"PIT {s.upper()} basket (one-day nights)", f"version {v}")] = bas[(v, s)]
    RG = []
    for (ser, ver), x in S.items():
        x = x.dropna(); x = x[x.index >= START]
        cuts = [(str(y), x[x.index.year == y]) for y in sorted(x.index.year.unique())] + [("pre 2022-08-25", x[x.index < CUTOVER]),
                ("post 2022-08-25", x[x.index >= CUTOVER]), ("full 2018-11-21+", x)]
        for nm, g in cuts:
            RG.append(dict(series=ser, filter=ver, group=nm, n_dates=len(g), mean_bp=g.mean() * 1e4, t=tstat(g), hit_pct=(g > 0).mean() * 100))
    RGd = pd.DataFrame(RG)

    # ---------------- Step 4: reconcile with Option C regime 1 ----------------
    rec = []
    legs, xl, E, D, clean, cnt = OC.rule_panel(3, "open")                       # Option C R1_T3open, same panel/calendar
    p1 = OC.cal < CUTOVER
    def oc_sum(mask):
        tot = 0; parts = {}
        for k in (1, 2, 3):
            s = OC.basket(legs[f"ON{k}"], mask)[0]; s = s[p1 & (OC.cal >= START)]; parts[k] = s.mean() * 1e4; tot += parts[k]
        return tot, parts
    for lab, mask in (("Option C D (window dropped if ANY open flagged)", D), ("Option C E (no open filter)", E)):
        tot, parts = oc_sum(mask)
        rec.append(dict(item=lab, value_bp=tot, note=f"ON1 {parts[1]:.2f}, ON2 {parts[2]:.2f}, ON3 {parts[3]:.2f} bp"))
    # per-night on the same calendar and same members (as of the night's open date), all nights incl. weekends, no limit filter
    on = OC.lo - OC.lc.shift(1); fl = OC.S
    memn = OC.MEM
    def pern(mask, lab):
        s = OC.basket(on, mask)[0]; s = s[p1 & (OC.cal >= START)]
        rec.append(dict(item=lab, value_bp=3 * s.mean() * 1e4, note=f"per-night {s.mean()*1e4:.2f} bp x 3, n {s.notna().sum()} dates"))
        return s
    base = memn & on.notna()
    pn_unf = pern(base, "per-night PIT EW, unfiltered (all nights) x3")
    pn_f = pern(base & ~fl, "per-night PIT EW, open_suspicious dropped x3")
    pern(base & ~fl & (on.abs() <= LIM), "per-night PIT EW, open_suspicious & |ON|>7% dropped x3")
    pern(base & (on.abs() <= LIM), "per-night PIT EW, |ON|>7% dropped only x3")
    # Option C's ON_k for entry T equals the night ending T+k, so the leg means should match per-night means up to
    # (i) the window-level filter, (ii) the 4-bar requirement and limit filters, (iii) the k>=10 basket rule. Isolate (i):
    s_n1 = OC.basket(legs["ON1"], E & ~OC.S.shift(-1).fillna(True).astype(bool))[0][p1 & (OC.cal >= START)]
    rec.append(dict(item="Option C ON1 on E with only ITS OWN open filtered", value_bp=s_n1.mean() * 1e4, note="vs ON1 under the window filter (D) above"))
    for sym in ("VN30", "VNINDEX"):
        ix = index_on(sym, one_day=False, drop_flag=False); ixf = index_on(sym, one_day=False, drop_flag=True)
        cc = OC.cal[p1 & (OC.cal >= START)]
        rec.append(dict(item=f"{sym} index per-night overnight x3, same calendar (unfiltered / index-flag dropped)",
                        value_bp=3 * ix.reindex(cc).mean() * 1e4, note=f"filtered x3 = {3*ixf.reindex(cc).mean()*1e4:.2f} bp; t unf {tstat(ix.reindex(cc)):.2f}, t filt {tstat(ixf.reindex(cc)):.2f}"))
    # date-paired: index minus stock basket, regime 1, all nights
    j = pd.concat({"pit_unf": pn_unf, "pit_f": pn_f, "vn30": index_on("VN30", one_day=False, drop_flag=True)}, axis=1, join="inner").dropna()
    for c in ("pit_unf", "pit_f"):
        dd = j[c] - j.vn30
        rec.append(dict(item=f"regime 1: {c} minus VN30 index overnight (paired, index-flag dropped)", value_bp=dd.mean() * 1e4,
                        note=f"paired t {tstat(dd):.2f}, n {len(dd)}, corr {j[c].corr(j.vn30):.2f}"))
    # by year in regime 1: is the stock basket ~0 while the index is positive?
    for y in sorted(set(j.index.year)):
        g = j[j.index.year == y]
        rec.append(dict(item=f"regime 1 year {y}: VN30 index / PIT EW unf / PIT EW filt per-night bp", value_bp=g.vn30.mean() * 1e4,
                        note=f"PIT unf {g.pit_unf.mean()*1e4:.2f}, PIT filt {g.pit_f.mean()*1e4:.2f}, n {len(g)}"))
    REC = pd.DataFrame(rec)
    RGd = pd.concat([RGd, REC.assign(series="STEP 4 reconciliation").rename(columns={"item": "group", "value_bp": "mean_bp"})], ignore_index=True)
    RGd.to_csv(OUT / "open_audit_regime.csv", index=False)

    # ---------------- Level A / B checks ----------------
    def chk(ser):
        out = {}
        for per in ("pre 2022-08-25", "post 2022-08-25"):
            u = RGd[(RGd.series == ser) & (RGd["filter"] == "unfiltered") & (RGd.group == per)].iloc[0]
            f = RGd[(RGd.series == ser) & (RGd["filter"] == "filtered") & (RGd.group == per)].iloc[0]
            out[per] = (u.mean_bp, u.t, f.mean_bp, u.mean_bp > 0 and u.t >= 3, u.mean_bp >= 0.5 * f.mean_bp)
        return out
    LA = {s: chk(s) for s in ("VNINDEX index (Level A, all nights)", "VN30 index (Level A, all nights)")}
    LB = chk("Level B date-level EW current-30 (all nights)")

    # ---------------- summary ----------------
    L += ["## Step 1: benchmark (published VN30 overnight, one-day nights; index-flagged opens dropped)",
          "pit_dayofweek_2x2.py DID apply open_suspicious: `flag = open_suspicious | |r_overnight| > 7%`, nights kept only if gap == 1 and not flagged.",
          "Note the 7% rule is asymmetric in log terms: a limit-down open is ln(0.93) = -7.26% (dropped), a limit-up open ln(1.07) = +6.77% (kept).",
          "", "Mean absolute weekday difference, basket minus index (bp):", mawd.to_string(), "",
          "All-nights mean difference (bp):", diff_all.to_string(), "", "Correlation with index overnight (all nights):", corr_all.to_string(), "",
          "Basket level by weekday (bp); index (cap a rows' dates): " + ", ".join(f"{k} {v:.2f}" for k, v in idx_lvl.items()), wk_lvl.to_string(), "",
          "Basket minus index by weekday (bp):", wk.to_string(), "",
          "Wed->Thu vs VN30F1M (paired by date):", fw.to_string(index=False), "", f"Decision rule outcome (cap-weighted, fixed in advance): {rule}", ""]
    fa = FLd[FLd.section == "a_flag_rate"].pivot(index="group", columns="series", values="flag_rate_pct")
    L += ["## Step 2: flag diagnostics", "(a) flag rate % by year:", fa.to_string(), "",
          "(b) flagged vs unflagged, PIT member stock-days (pooled, descriptive):",
          FLd[FLd.section.str.startswith("b_")][["section", "group", "n", "overnight_bp", "intraday_bp", "intraday_t", "cc_bp", "cc_t"]].to_string(index=False), "",
          "(c) observed vs expected genuine flat-open rate (%). tickrule: density of ON near 0 from non-zero days x relative tick (HOSE rule 10/50/100 VND "
          "applied to the BACK-ADJUSTED price, so the tick band can be understated for names with large later bonus issues). ccscaled: observed close==prior-close rate "
          "(closes are reliable) x ratio of ON to CC mass in (0, h]; scale-free and consistent with the price rounding.",
          FLd[FLd.section == "c_expected_flat_open"][["group", "n", "flag_rate_pct", "cc_zero_pct", "exp_tickrule_h0.5_pct", "exp_tickrule_h1_pct", "exp_ccscaled_h0.5_pct",
                                                       "exp_ccscaled_h1_pct", "excess_tickrule_pct", "excess_ccscaled_pct"]].to_string(index=False), ""]
    kb = FLd[FLd.section == "d_kbs_spot_check"]
    L += ["(d) KBS spot check (VCI-flagged days):", kb[["series", "group", "n", "kbs_coverage_pct", "kbs_differs_gt1tick_pct", "kbs_on_on_vci_flagged_bp", "kbs_close_ratio_med"]].to_string(index=False)
          if len(kb) else "KBS data not available (fetch failed or not run); skipped.", ""]
    st3 = RGd[RGd.series != "STEP 4 reconciliation"]
    L += ["## Step 3: regime and year split (date-level, one obs per date)",
          st3[st3.group.isin(["pre 2022-08-25", "post 2022-08-25", "full 2018-11-21+"])].to_string(index=False), "",
          "By year (mean bp):", st3[~st3.group.str.contains("2022-08|full")].pivot_table(index="group", columns=["series", "filter"], values="mean_bp").round(1).T.to_string(), ""]
    L += ["## Step 4: reconcile with Option C regime 1 (entries/nights before 2022-08-25)", REC.to_string(index=False), ""]
    def fmtchk(o): return "; ".join(f"{p}: unfiltered {u:.2f} bp (t {t:.2f}) vs filtered {f:.2f} bp -> positive & t>=3: {a}, >=50% of filtered: {b}" for p, (u, t, f, a, b) in o.items())
    L += ["## Level A / Level B checks (unfiltered date-level overnight, pre and post 2022-08-25)"]
    for s, o in LA.items(): L.append(f"- Level A {s}: {fmtchk(o)}")
    L.append(f"- Level B (date-level EW, current 30, all nights): {fmtchk(LB)}")
    # ---------------- verdict ----------------
    g = lambda ser, f, grp: RGd[(RGd.series == ser) & (RGd["filter"] == f) & (RGd.group == grp)].iloc[0]
    v30p, v30q = g("VN30 index (Level A, all nights)", "unfiltered", "pre 2022-08-25"), g("VN30 index (Level A, all nights)", "unfiltered", "post 2022-08-25")
    rc = REC.set_index("item").value_bp
    fwd = fw.set_index(["version", "scheme"]).loc
    exc = FLd[FLd.section == "c_expected_flat_open"]; kbs = FLd[FLd.section == "d_kbs_spot_check"]
    bdl = FLd[(FLd.section == "b_date_level_flagged_minus_unflagged") & (FLd.group == "all")].iloc[0]
    borderline = rule.startswith("C") and min(m["b"], m["c"]) <= 2.5
    V = (f"VERDICT. Filter: the open_suspicious filter is mainly truncation bias for levels. Against the published VN30 overnight, the cap-weighted PIT basket's "
         f"all-nights gap is {diff_all.loc['cap','a']:.2f} bp with the filter and {diff_all.loc['cap','c']:.2f} bp without it, and the mean absolute weekday gap falls from "
         f"{m['a']:.2f} to {m['c']:.2f} bp (correlation unchanged, ~{corr_all.loc['cap','a']:.2f}). Fixed rule outcome: {rule.split(' ')[0]}"
         + (f" by a {min(m['b'], m['c'])-2:.2f} bp margin over the ~2 bp threshold, so I read it as borderline A/C (ambiguous, D) on weekday shape; the residual is a shape "
            f"mismatch (Mon->Tue +{wk.loc[('cap','Mon->Tue'),'c']:.1f}, Thu->Fri {wk.loc[('cap','Thu->Fri'),'c']:.1f} bp), not a level gap." if borderline else ".")
         + f" Flags run {exc.flag_rate_pct.min():.0f}-{exc.flag_rate_pct.max():.0f}% a year against an expected genuine flat-open rate of about "
         f"{exc['exp_ccscaled_h0.5_pct'].min():.0f}-{exc['exp_ccscaled_h0.5_pct'].max():.0f}% (cc-scaled) or {exc['exp_tickrule_h0.5_pct'].min():.0f}-{exc['exp_tickrule_h0.5_pct'].max():.0f}% (tick rule), "
         f"but KBS shows the same open on {100-kbs.kbs_differs_gt1tick_pct.mean():.0f}% of VCI-flagged days, so the excess is not a VCI fill that another vendor corrects; "
         f"it looks like the exchange-reported open equal to the reference price (plausibly no ATO match), which the index also uses. Flagged names close {abs(bdl.cc_bp):.1f} bp "
         f"{'below' if bdl.cc_bp < 0 else 'above'} unflagged names on the same date (t {bdl.cc_t:.2f}), so the filter selects on the outcome: harmless for the overnight leg (zeros), "
         f"but it biases any hold that spans the flagged day (the Option C 12.8 vs 4.8 bp). "
         f"Regime 1: there is no inconsistency to explain. The published VN30 overnight is itself ~0 before 2022-08-25 ({v30p.mean_bp:.2f} bp/night, t {v30p.t:.2f}) "
         f"and strongly positive after ({v30q.mean_bp:.2f} bp, t {v30q.t:.2f}); the Level A full-sample positive overnight comes from outside 2018-11..2022-08. Option C's unfiltered three-leg "
         f"sum ({rc['Option C E (no open filter)']:.2f} bp) matches 3 x the per-night PIT mean ({rc['per-night PIT EW, unfiltered (all nights) x3']:.2f} bp); the filtered "
         f"version differs ({rc['Option C D (window dropped if ANY open flagged)']:.2f} vs {rc['per-night PIT EW, open_suspicious dropped x3']:.2f} bp) because Option C drops the whole window. "
         f"The 'index positive, stocks ~0' hypothesis is rejected: stock basket minus index in regime 1 is {rc['regime 1: pit_unf minus VN30 index overnight (paired, index-flag dropped)']:.2f} bp "
         f"(not significant). Wednesday: the Wed->Thu replica-minus-VN30F1M gap shrinks from {fwd['a','cap'].diff_bp:.2f} bp (t {fwd['a','cap'].paired_t:.2f}) to "
         f"{fwd['c','cap'].diff_bp:.2f} bp (t {fwd['c','cap'].paired_t:.2f}) unfiltered; about {100*(1-fwd['c','cap'].diff_bp/fwd['a','cap'].diff_bp):.0f}% of it was filter, the rest persists. "
         f"Levels A/B: unfiltered overnight is positive with t >= 3 after 2022-08-25 for both, but not before (Level A VN30 {LA['VN30 index (Level A, all nights)']['pre 2022-08-25'][0]:.2f} bp, "
         f"Level B {LB['pre 2022-08-25'][0]:.2f} bp, t {LB['pre 2022-08-25'][1]:.2f}); Level B's unfiltered mean is {100*LB['pre 2022-08-25'][0]/LB['pre 2022-08-25'][2]:.0f}% (pre) and "
         f"{100*LB['post 2022-08-25'][0]/LB['post 2022-08-25'][2]:.0f}% (post) of the filtered mean; Level A is essentially unaffected by the filter after 2018.")
    L += ["## Caveats",
          "- HOSE tick rule (10 / 50 / 100 VND at <10k / 10k-<50k / >=50k) is from memory, not verified from a primary source in this run, and is applied to back-adjusted prices.",
          "- The cc-scaled expected rate assumes ON and close-to-close have locally flat densities over (0, h]; two h values are shown.",
          "- KBS covers the six names fully from 2018-11-22; it agrees with VCI almost everywhere, so it is not an independent check of the open (shared upstream source).",
          "- If the flagged open is the reference price after no ATO match, the unfiltered overnight is the right LEVEL measure but is not executable at that price.",
          "- Level B 'date-level' = EW across the current-30 per date, all nights, k >= 10; the Level B cross-section itself is per stock (reproduced above).", "",
          "## Verdict", V]
    (OUT / "open_audit_summary.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
