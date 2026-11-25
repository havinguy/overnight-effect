"""Regime re-basing audit. READ-ONLY on data/raw/ and results/ (writes only results/regime_rebase_audit.md and regime_rebase_*.csv).
KBS index history (vnstock Quote source=KBS) cached in data/raw_kbs_index/ (new directory, fetched with --fetch).

Pre-registered (fixed before the first run):
 Step 1  KBS VN30 overnight = ln(KBS open / KBS prior close). Per quarter on common one-day nights (KBS, VCI, CW basket all present):
         SD(index ON)/SD(basket ON) for KBS and for VCI (flagged VCI opens KEPT, so both indices are treated alike).
         "KBS tracks the basket and VCI does not" in a quarter if KBS ratio >= the minimum KBS ratio over verified quarters (2023Q1-2026Q4)
         AND VCI ratio < the minimum VCI ratio over verified quarters.
 Step 2  RE-BASING RUN (regime restriction lifted for this step only): no index open anywhere. CW and EW PIT baskets (all stock-days kept,
         version c) and VN30F1M futures overnight (log, roll-fixed entry as build()), one-day nights, common dates, from 2018-11-21.
         Mean bp, NW t (lag 5), n, by year and pre/post 2022-08-25; constituent flat-open share per period.
         "Near zero" pre-cutover = |NW t| < 2 (stated before running).
 Step 3  Degraded-index flag (report only, applied nowhere): |index ON| < 10 bp AND |CW basket ON| > 50 bp, one-day nights, by quarter.
Usage: python3 src/regime_rebase_audit.py [--fetch]
"""
from __future__ import annotations
import argparse, math, sys, warnings
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from level_a import RAW_DIR, OUT_DIR

OUT = OUT_DIR
KD = RAW_DIR.parent / "raw_kbs_index"
NEW = {"regime_rebase_kbs_quarterly_vnindex.csv", "regime_rebase_audit.md", "regime_rebase_kbs_quarterly.csv", "regime_rebase_kbs_covid.csv", "regime_rebase_regime.csv", "regime_rebase_flag.csv"}
import index_open_degradation_audit as IO          # its import hashes the tree; we re-hash below with our own exclusions
IO.NEW = IO.NEW | NEW


def tree_hash():
    import hashlib
    H = {}
    for d in (RAW_DIR, OUT):
        for p in sorted(d.glob("*")):
            if p.is_file() and p.name not in NEW and p.name not in IO.NEW: H[str(p)] = hashlib.md5(p.read_bytes()).hexdigest()
    return H


H0 = tree_hash()
RG, X = IO.RG, IO.X
from futures_basis_decomp import nw_t

CUT = pd.Timestamp("2022-08-25")
VER_LO = "2022-11-03"


def fetch():
    from vnstock import Quote
    KD.mkdir(exist_ok=True)
    for s in ("VN30", "VNINDEX"):
        d = Quote(symbol=s, source="KBS").history(start="2018-01-01", end="2026-11-17", interval="1D"); d.to_csv(KD / f"KBS_{s}_1D.csv", index=False)


def kbs(sym):
    p = KD / f"KBS_{sym}_1D.csv"
    if not p.exists(): return None
    d = pd.read_csv(p, parse_dates=["time"]); d["date"] = d.time.dt.normalize()
    d = d.drop_duplicates("date", keep="last").set_index("date").sort_index()
    d["prev_close"] = d.close.shift(1); d["gap"] = d.index.to_series().diff().dt.days
    d["ON"] = np.log(d.open / d.prev_close); d["flat"] = (d.open - d.prev_close).abs() < 0.005
    return d


def vci(sym):
    d = RG.rd(sym).sort_index(); d["prev_close"] = d.close.shift(1); d["gap"] = d.index.to_series().diff().dt.days
    d["ON"] = np.log(d.open / d.prev_close); d["flat"] = d.open_suspicious.astype(bool); return d


def mstat(x):
    x = pd.Series(x).dropna(); return dict(n=len(x), mean_bp=x.mean() * 1e4 if len(x) else np.nan, nw_t=nw_t(x) if len(x) > 3 else np.nan)


def fm(x, f="{:.2f}"): return "" if pd.isna(x) else f.format(x)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--fetch", action="store_true"); a = ap.parse_args()
    if a.fetch: fetch()
    K30, KVN = kbs("VN30"), kbs("VNINDEX"); V30, VVN = vci("VN30"), vci("VNINDEX")
    bas_cw = IO.basket_series("c", "cap").r; bas_ew = IO.basket_series("c", "ew").r
    F, Lm, _ = IO.stock_flags(); W, ed = IO.member_weights(); CS = IO.constituent_shares(W, ed, F, Lm, X.PC)
    fut = RG.futures_nights_from(RG.rd("VN30F1M")); fut1 = fut.fut_ON[(fut.hold_type == "") & fut.invested].dropna()   # one-day nights
    M = ["# Regime re-basing audit", "",
         "Read-only on data/raw/ and results/. Step 2 is a clearly labelled RE-BASING RUN (the 'do not recompute regime' restriction is lifted for step 2 only). "
         "Script: `src/regime_rebase_audit.py`. KBS index history fetched on 2026-11-24 (`--fetch` re-creates the cache; vendor history can change) through vnstock (source KBS) into the new directory `data/raw_kbs_index/`.", "",
         "Pre-registered rules: see script header (KBS 'tracks' rule; 'near zero' = |NW t| < 2; flag = |index ON| < 10 bp and |CW basket ON| > 50 bp).", ""]

    # ---------------- Step 1
    M += ["## 1. Independent index open (KBS)", ""]
    if K30 is None:
        M += ["KBS index history not available: step skipped.", ""]; KQ = pd.DataFrame(); KC = pd.DataFrame()
    else:
        M += [f"KBS VN30 daily: {len(K30)} rows {K30.index.min().date()}..{K30.index.max().date()}; KBS VNINDEX: {len(KVN)} rows {KVN.index.min().date()}..{KVN.index.max().date()}.",
              f"KBS VN30 flat opens (open == own prior close) by year: " + ", ".join(f"{y} {v:.1%}" for y, v in K30.flat.groupby(K30.index.year).mean().items()),
              f"VCI VN30 flat opens by year: " + ", ".join(f"{y} {v:.1%}" for y, v in V30.flat.groupby(V30.index.year).mean().items()), ""]
        cm = K30.index.intersection(V30.index)
        agree = (K30.open.reindex(cm) - V30.open.reindex(cm)).abs() < 0.05
        M += ["KBS vs VCI VN30 open agreement (|diff| < 0.05 pt) by year: " + ", ".join(f"{y} {v:.0%}" for y, v in agree.groupby(agree.index.year).mean().items()), ""]
        J = pd.concat({"kbs": K30.ON[K30.gap == 1], "vci": V30.ON[V30.gap == 1], "bas": bas_cw, "vci_flag": V30.flat, "kbs_flag": K30.flat}, axis=1, join="inner").dropna(subset=["kbs", "vci", "bas"])
        J = J.loc["2018-11-21":]
        rows = []
        def qrow(g, s):
            if len(s) < 10: return None
            rk = IO.SA.ols(s.kbs * 1e4, s.bas * 1e4); rv = IO.SA.ols(s.vci * 1e4, s.bas * 1e4)
            return dict(period=g, n=len(s), sd_bas_bp=s.bas.std() * 1e4, sd_kbs_bp=s.kbs.std() * 1e4, sd_vci_bp=s.vci.std() * 1e4,
                        ratio_kbs=s.kbs.std() / s.bas.std(), ratio_vci=s.vci.std() / s.bas.std(), r2_kbs_on_bas=rk["r2"], r2_vci_on_bas=rv["r2"],
                        kbs_flat=s.kbs_flag.astype(bool).mean(), vci_flat=s.vci_flag.astype(bool).mean(), corr_kbs_vci=s.kbs.corr(s.vci))
        for q in sorted(set(IO.qlabel(J.index))):
            r = qrow(q, J[IO.qlabel(J.index) == q]); rows.append(r) if r else None
        for g, lo, hi in (("POOLED 2020Q1-2021Q2", "2020-01-01", "2021-06-30"), ("POOLED 2019", "2019-01-01", "2019-12-31"), (f"POOLED verified {VER_LO}..", VER_LO, "2026-12-31")):
            rows.append(qrow(g, J.loc[lo:hi]))
        KQ = pd.DataFrame(rows)
        vq = KQ[(KQ.period >= "2023Q1") & (KQ.period <= "2026Q4")]; kmin, vmin = vq.ratio_kbs.min(), vq.ratio_vci.min()
        KQ["kbs_tracks_vci_not"] = (KQ.ratio_kbs >= kmin) & (KQ.ratio_vci < vmin) & KQ.period.str.match(r"^\d{4}Q\d$")
        T = KQ.copy()
        for c in T.columns[2:-1]: T[c] = T[c].map(lambda v: fm(v, "{:.1f}") if str(c).endswith("_bp") else fm(v, "{:.3f}"))
        M += ["Per quarter, one-day nights, common dates (KBS, VCI with flagged opens kept, CW basket version c). ratio = SD(index ON)/SD(basket ON).", "", "```", T.to_string(index=False), "```", "",
              f"- Verified-quarter minima: KBS ratio {kmin:.3f}, VCI ratio {vmin:.3f}. Quarters where KBS tracks the basket and VCI does not: "
              f"{', '.join(KQ[KQ.kbs_tracks_vci_not].period) or 'none'}.", ""]
        # VNINDEX pair (same rule; VNINDEX is broader than the VN30 basket, so read ratios relative to verified)
        JV = pd.concat({"kbs": KVN.ON[KVN.gap == 1], "vci": VVN.ON[VVN.gap == 1], "bas": bas_cw, "vci_flag": VVN.flat, "kbs_flag": KVN.flat}, axis=1, join="inner").dropna(subset=["kbs", "vci", "bas"]).loc["2018-11-21":]
        rows = []
        for q in sorted(set(IO.qlabel(JV.index))):
            r = qrow(q, JV[IO.qlabel(JV.index) == q]); rows.append(r) if r else None
        for g, lo, hi in (("POOLED 2020Q1-2021Q2", "2020-01-01", "2021-06-30"), ("POOLED 2019", "2019-01-01", "2019-12-31"), (f"POOLED verified {VER_LO}..", VER_LO, "2026-12-31")):
            rows.append(qrow(g, JV.loc[lo:hi]))
        KV = pd.DataFrame(rows); vv = KV[(KV.period >= "2023Q1") & (KV.period <= "2026Q4")]
        KV["kbs_tracks_vci_not"] = (KV.ratio_kbs >= vv.ratio_kbs.min()) & (KV.ratio_vci < vv.ratio_vci.min()) & KV.period.str.match(r"^\d{4}Q\d$")
        KV["vci_tracks_kbs_not"] = (KV.ratio_vci >= vv.ratio_vci.min()) & (KV.ratio_kbs < vv.ratio_kbs.min()) & KV.period.str.match(r"^\d{4}Q\d$")
        T = KV.copy()
        for c in [c for c in T.columns if c not in ("period", "n", "kbs_tracks_vci_not", "vci_tracks_kbs_not")]: T[c] = T[c].map(lambda v: fm(v, "{:.1f}") if str(c).endswith("_bp") else fm(v, "{:.3f}"))
        M += ["VNINDEX (KBS and VCI) vs the same CW VN30 basket. Not a replica pair (VNINDEX is broader), so read each ratio against its own verified quarters.", "", "```", T.to_string(index=False), "```", "",
              f"- VNINDEX verified-quarter minima: KBS {vv.ratio_kbs.min():.3f}, VCI {vv.ratio_vci.min():.3f}. KBS tracks and VCI does not: {', '.join(KV[KV.kbs_tracks_vci_not].period) or 'none'}; "
              f"VCI tracks and KBS does not: {', '.join(KV[KV.vci_tracks_kbs_not].period) or 'none'}.", ""]
        globals()["_KV"] = KV; KV.assign(index_pair="VNINDEX").to_csv(OUT / "regime_rebase_kbs_quarterly_vnindex.csv", index=False)
        # COVID nights (same 10 as the degradation audit)
        C = pd.read_csv(OUT / "index_open_degradation_covid.csv", parse_dates=["date"])
        C["kbs_prev_close"] = C.date.map(K30.prev_close); C["kbs_open"] = C.date.map(K30.open); C["kbs_ON_bp"] = C.date.map(K30.ON) * 1e4
        C["kbs_vnindex_ON_bp"] = C.date.map(KVN.ON) * 1e4; C["vci_vnindex_ON_bp"] = C.date.map(VVN.ON) * 1e4
        KC = C[["date", "weekday", "fut_ON_bp", "f2m_ON_bp", "basket_cw_all_nights_bp", "idx_ON_bp", "idx_flag", "kbs_prev_close", "kbs_open", "kbs_ON_bp", "vci_vnindex_ON_bp", "kbs_vnindex_ON_bp"]].rename(
            columns={"idx_ON_bp": "vci_vn30_ON_bp", "idx_flag": "vci_flag"})
        KC["date"] = KC.date.dt.date.astype(str)
        M += ["10 largest |futures ON| nights in 2020-03 (from index_open_degradation_covid.csv) with KBS added (VN30 and VNINDEX; overnight vs each source's own prior close):", "",
              "```", KC.to_string(index=False, float_format=lambda v: f"{v:.1f}"), "```", ""]
        kq = KC[(KC.kbs_ON_bp.abs() >= 0.5 * KC.basket_cw_all_nights_bp.abs())]; vq_ = KC[(KC.vci_vn30_ON_bp.abs() >= 0.5 * KC.basket_cw_all_nights_bp.abs())]
        M += [f"- Index registered >= half the basket move: KBS VN30 on {len(kq)}/10 ({', '.join(kq.date) or 'none'}), VCI VN30 on {len(vq_)}/10 ({', '.join(vq_.date) or 'none'}).", ""]

    # ---------------- Step 2
    M += ["## 2. RE-BASING RUN: regime evidence with no index open (one-day nights, common dates, stock flat opens kept)", ""]
    R = pd.concat({"cw": bas_cw, "ew": bas_ew, "fut": fut1}, axis=1, join="inner").dropna().loc["2018-11-21":]
    groups = [(str(y), R[R.index.year == y]) for y in sorted(R.index.year.unique())] + [("pre 2022-08-25", R[R.index < CUT]), ("post 2022-08-25", R[R.index >= CUT]),
              ("pre excl. 2020Q1-2021Q2", R[(R.index < CUT) & ~((R.index >= "2020-01-01") & (R.index <= "2021-06-30"))]), ("all", R)]
    rows = []
    for g, s in groups:
        cs = CS[CS.index.isin(s.index)]
        row = dict(period=g)
        for c in ("cw", "ew", "fut"):
            m = mstat(s[c]); row.update({f"{c}_n": m["n"], f"{c}_mean_bp": m["mean_bp"], f"{c}_nw_t": m["nw_t"]})
        row.update(flat_share_cw=cs.share_flat_cw.mean(), flat_share_ew=cs.share_flat_ew.mean())
        rows.append(row)
    RR = pd.DataFrame(rows)
    # futures on its own one-day nights (not restricted to basket dates)
    fo = fut1.loc["2018-11-21":]
    fown = [dict(period=g, **mstat(x)) for g, x in [(str(y), fo[fo.index.year == y]) for y in sorted(fo.index.year.unique())] + [("pre 2022-08-25", fo[fo.index < CUT]), ("post 2022-08-25", fo[fo.index >= CUT])]]
    T = RR.copy()
    for c in T.columns[1:]: T[c] = T[c].map(lambda v: fm(v, "{:.0f}") if c.endswith("_n") else fm(v, "{:.3f}") if c.startswith("flat") else fm(v))
    M += ["```", T.to_string(index=False), "```", "",
          "Futures on all its own one-day nights from 2018-11-21 (not restricted to basket dates):", "", "```", pd.DataFrame(fown).round(2).to_string(index=False), "```", ""]
    pre = RR.set_index("period").loc["pre 2022-08-25"]; post = RR.set_index("period").loc["post 2022-08-25"]
    nz = {c: abs(pre[f"{c}_nw_t"]) < 2 for c in ("cw", "ew", "fut")}
    M += [f"- Pre-cutover: CW {pre.cw_mean_bp:.2f} bp (t {pre.cw_nw_t:.2f}), EW {pre.ew_mean_bp:.2f} bp (t {pre.ew_nw_t:.2f}), futures {pre.fut_mean_bp:.2f} bp (t {pre.fut_nw_t:.2f}), n {int(pre.cw_n)}. "
          f"Post: CW {post.cw_mean_bp:.2f} (t {post.cw_nw_t:.2f}), EW {post.ew_mean_bp:.2f} (t {post.ew_nw_t:.2f}), futures {post.fut_mean_bp:.2f} (t {post.fut_nw_t:.2f}), n {int(post.cw_n)}.",
          f"- Near zero pre-cutover (|NW t| < 2): CW {nz['cw']}, EW {nz['ew']}, futures {nz['fut']}.",
          "- Reference only, quoted not recomputed: published VCI VN30 index overnight pre 0.89 bp (t 0.70), post 9.99 bp (t 6.42), all nights (open_audit_summary.md).", ""]
    # ADDED AFTER FIRST RUN: pre minus post, NW SE = sqrt(se_pre^2 + se_post^2), se = |mean / NW t|
    DD = []
    for c, nm in (("cw", "CW basket"), ("ew", "EW basket"), ("fut", "futures")):
        sp, so = abs(pre[f"{c}_mean_bp"] / pre[f"{c}_nw_t"]), abs(post[f"{c}_mean_bp"] / post[f"{c}_nw_t"]); d = post[f"{c}_mean_bp"] - pre[f"{c}_mean_bp"]; se = math.hypot(sp, so)
        DD.append(dict(series=nm, pre_bp=pre[f"{c}_mean_bp"], post_bp=post[f"{c}_mean_bp"], post_minus_pre_bp=d, nw_se=se, t=d / se))
    DD = pd.DataFrame(DD); globals()["_DD"] = DD
    M += ["Post minus pre (ADDED AFTER THE FIRST RUN; NW SE combined across the two independent subsamples):", "", "```", DD.to_string(index=False, float_format=lambda v: f"{v:.2f}"), "```", ""]
    # ADDED AFTER FIRST RUN: impossible stock gaps (|open/prior close - 1| > 7.5%, beyond the +/-7% limit) - contribution to the CW/EW basket means
    Rc = IO.OA.ret_panel(False, False)
    bad = (np.exp(Rc) - 1).abs() > 0.075
    Rz = Rc.mask(bad, 0.0)
    cw0 = IO.OA.with_ret(Rz, lambda: X.cell_series("pit", "cap", "B")).r; ew0 = IO.OA.with_ret(Rz, lambda: X.cell_series("pit", "ew", "B")).r
    G = []
    for g, lo, hi in (("pre 2022-08-25", "2018-11-21", "2022-08-24"), ("post 2022-08-25", "2022-08-25", "2026-12-31")):
        dts = R.loc[lo:hi].index; b_ = bad.reindex(dts)
        G.append(dict(period=g, stock_days_beyond_7_5pct=int(b_.values.sum()), dates_affected=int(b_.any(axis=1).sum()),
                      cw_contribution_bp=(R.cw.loc[dts] - cw0.reindex(dts)).mean() * 1e4, ew_contribution_bp=(R.ew.loc[dts] - ew0.reindex(dts)).mean() * 1e4))
    G = pd.DataFrame(G); globals()["_G"] = G
    mem_hits = sum(1 for t, row in bad.loc[R.index.min():].iterrows() if row.any() for tk in row[row].index
                   if [x for x in ed if x <= t] and tk in W[[x for x in ed if x <= t][-1]].index)
    bl = Rc[bad].stack().reset_index(); bl.columns = ["date", "ticker", "r_overnight"]; bl = bl[bl.date.isin(R.index)]
    M += ["Impossible stock gaps (ADDED AFTER THE FIRST RUN): stock-days in the baskets with |open/prior close - 1| > 7.5% (beyond the +/-7% limit; usually unadjusted corporate actions or bad prints), "
          "and their contribution to the basket means (basket minus the same basket with those returns set to 0, denominators unchanged):", "", "```", G.to_string(index=False, float_format=lambda v: f"{v:.2f}"), "```", "",
          f"Counts are over the whole stock universe; stock-days that are PIT VN30 members on their date: {mem_hits}. Hence the exact-zero contribution: no impossible gap enters either basket.", "",
          "Largest such stock-days (all non-members on the date): " + "; ".join(f"{r.date.date()} {r.ticker} {r.r_overnight * 1e4:.0f} bp" for _, r in bl.reindex(bl.r_overnight.abs().sort_values(ascending=False).index).head(8).iterrows()), ""]

    # ---------------- Step 3
    M += ["## 3. Degraded-index flag (report only; applied nowhere)", "",
          "Flag = |index ON| < 10 bp and |CW basket ON| > 50 bp, one-day nights, common dates. Shown for VCI VN30 (with the subset already VCI-flagged as open == prior close) and KBS VN30.", ""]
    Fg = pd.concat({"vci": V30.ON[V30.gap == 1], "vflat": V30.flat, "bas": bas_cw}, axis=1, join="inner").dropna(subset=["vci", "bas"]).loc["2018-11-21":]
    if K30 is not None: Fg = Fg.join(K30.ON[K30.gap == 1].rename("kbs"), how="left")
    Fg["flag_vci"] = (Fg.vci.abs() < 10e-4) & (Fg.bas.abs() > 50e-4); Fg["flag_vci_new"] = Fg.flag_vci & ~Fg.vflat.astype(bool)
    Fg["flag_kbs"] = (Fg.kbs.abs() < 10e-4) & (Fg.bas.abs() > 50e-4) & Fg.kbs.notna() if "kbs" in Fg else False
    Fg["basket_big"] = Fg.bas.abs() > 50e-4
    FQ = Fg.groupby(IO.qlabel(Fg.index)).agg(n=("bas", "size"), basket_big=("basket_big", "sum"), flag_vci=("flag_vci", "sum"), flag_vci_not_flat=("flag_vci_new", "sum"), flag_kbs=("flag_kbs", "sum"))
    FQ["rate_vci_given_big"] = FQ.flag_vci / FQ.basket_big.replace(0, np.nan)
    per = {"2018-11..2022-11-02": Fg.loc[:"2022-11-02"], f"verified {VER_LO}..": Fg.loc[VER_LO:], "2020Q1-2021Q2": Fg.loc["2020-01-01":"2021-06-30"]}
    FS = pd.DataFrame([dict(period=k, n=len(v), basket_big=int(v.basket_big.sum()), flag_vci=int(v.flag_vci.sum()), flag_vci_not_flat=int(v.flag_vci_new.sum()), flag_kbs=int(v.flag_kbs.sum()),
                            flag_vci_per_100=100 * v.flag_vci.mean(), flag_vci_share_of_big=v.flag_vci.sum() / max(v.basket_big.sum(), 1)) for k, v in per.items()])
    M += ["```", FQ.reset_index().rename(columns={"index": "quarter"}).to_string(index=False, float_format=lambda v: f"{v:.2f}"), "```", "", "```", FS.to_string(index=False, float_format=lambda v: f"{v:.2f}"), "```", ""]

    KQ.to_csv(OUT / "regime_rebase_kbs_quarterly.csv", index=False); KC.to_csv(OUT / "regime_rebase_kbs_covid.csv", index=False)
    RR.to_csv(OUT / "regime_rebase_regime.csv", index=False); FQ.reset_index().to_csv(OUT / "regime_rebase_flag.csv", index=False)
    globals().update(dict(_KQ=KQ, _KC=KC, _RR=RR, _FS=FS, _FQ=FQ, _nz=nz))
    KQi = KQ.set_index("period"); KVi = _KV.set_index("period"); RRi = RR.set_index("period"); FSi = FS.set_index("period")
    ph, pv = "POOLED 2020Q1-2021Q2", f"POOLED verified {VER_LO}.."
    M += ["## 4. Pre-cutover claims that would need rewording", "",
          "No memory file exists for this project (the Claude memory directory is empty and the repo has no notes file), so the claims below are taken from the published "
          "results summaries. Outcomes of step 2: A = baskets and futures both near zero pre-cutover; B = baskets near zero, futures positive (OBSERVED); C = baskets positive.", "",
          "| Claim (source) | A | B (observed) | C |", "|---|---|---|---|",
          "| 'Regime 1: published VN30 overnight ~0 before 2022-08-25 (0.89 bp, t 0.70); positive after' (open_audit_summary.md) | keep, re-source to stocks+futures | "
          "reword: 'stock overnight ~0 pre-cutover (CW " + f"{RRi.loc['pre 2022-08-25','cw_mean_bp']:.2f}" + " bp, t " + f"{RRi.loc['pre 2022-08-25','cw_nw_t']:.2f}" + "); futures overnight positive (" + f"{RRi.loc['pre 2022-08-25','fut_mean_bp']:.2f}" + " bp, t " + f"{RRi.loc['pre 2022-08-25','fut_nw_t']:.2f}" + "); the index number is index-open-dependent; the claim is now carried by stock-only evidence' | reword: regime-1 zero is an index artifact |",
          "| 'Level A full-sample positive overnight comes from outside 2018-11..2022-08' (open_audit_summary.md) | keep | keep for stocks; not true for futures | drop |",
          "| 'Levels A/B unfiltered overnight positive after, not before (Level A VN30 0.89 bp; Level B 1.95 bp, t 0.79)' (open_audit_summary.md) | keep | keep for Level B (stocks); Level A VN30 pre value flagged as index-open-dependent | reword both |",
          "| 'Index positive, stocks ~0 hypothesis rejected: basket minus index regime 1 = -3.63 bp' (open_audit_summary.md) | keep, caveat index | keep conclusion (stocks ~0 confirmed without the index); the -3.63 bp gap itself is index-open-dependent | reword |",
          "| R1 'Monday futures edge is mostly basis, 82% in 2018-11..2021' (futures_basis_summary.md) | reword: basis vs ~0 stocks | reword: 'futures minus stocks' is positive on average pre-cutover (one-day nights; not tested for Mon->Tue here), but the 82% share is computed against a degraded index open; Monday share not recomputed here | reword: share overstated |",
          "| Pre-cutover Mon->Tue dbasis +12.82 bp; follow-up pre-cutover weekday tests t 2.09 / 2.24 | caveat | caveat: index leg degraded 2020-21Q2; sign plausibly survives vs stocks (not tested by weekday here) | caveat |",
          "| Option C P1 'regime 1' holds (option_c_summary.md) | none (stock prices, CUTOVER is the T+2 rule date) | none | none |",
          "| R3 slopes 2019-21, pre-cutover offset k 0.64 | flag | flag (index-open-dependent; no rebase done) | flag |", "",
          "## Reading", "",
          f"**KBS.** KBS VN30 is not an independent open: identical to VCI from 2021Q3 (corr ~1.00) and worse before (flat opens {KQi.loc[ph,'kbs_flat']:.0%} pooled 2020Q1-2021Q2 vs VCI {KQi.loc[ph,'vci_flat']:.0%}; SD ratio {KQi.loc[ph,'ratio_kbs']:.2f} vs VCI {KQi.loc[ph,'ratio_vci']:.2f}). "
          "Under the pre-registered rule no quarter has KBS VN30 tracking the basket while VCI does not. On the COVID nights KBS VN30 registered the move on 0/10. "
          f"VNINDEX is different: both vendors' VNINDEX opens track the VN30 basket through 2019-2021Q2 (pooled 2020Q1-2021Q2 ratio KBS {KVi.loc[ph,'ratio_kbs']:.2f}, VCI {KVi.loc[ph,'ratio_vci']:.2f}; R^2 {KVi.loc[ph,'r2_kbs_on_bas']:.2f} / {KVi.loc[ph,'r2_vci_on_bas']:.2f}; verified {KVi.loc[pv,'ratio_kbs']:.2f} / {KVi.loc[pv,'ratio_vci']:.2f}), "
          "and register the COVID moves (e.g. 2020-03-30: VNINDEX -473 bp both vendors, VN30 -5 bp both vendors). KBS VNINDEX tracks where VCI VNINDEX does not only in 2021Q3-Q4 (VCI's known 2021 VNINDEX fill). "
          "So the 2020-21Q2 degradation is specific to the VN30 index open: both vendors' VN30 opens are degraded (in different forms - KBS mostly exact-flat, VCI mostly near-flat; KBS-VCI corr 0.02-0.74 in several quarters), "
          "while both vendors' VNINDEX opens and the constituent opens are normal. Whether it originates in the exchange's VN30 calculation or in common vendor processing cannot be determined from these data.", "",
          f"**Re-based regime (stocks and futures only).** Pre-cutover, both baskets are near zero (CW {RRi.loc['pre 2022-08-25','cw_mean_bp']:.2f} bp, t {RRi.loc['pre 2022-08-25','cw_nw_t']:.2f}; EW {RRi.loc['pre 2022-08-25','ew_mean_bp']:.2f}, t {RRi.loc['pre 2022-08-25','ew_nw_t']:.2f}; n {int(RRi.loc['pre 2022-08-25','cw_n'])}) "
          f"and strongly positive after (CW {RRi.loc['post 2022-08-25','cw_mean_bp']:.2f}, t {RRi.loc['post 2022-08-25','cw_nw_t']:.2f}). The near-zero pre-cutover overnight is therefore NOT only an index artifact for stocks. "
          f"It does not hold for futures: {RRi.loc['pre 2022-08-25','fut_mean_bp']:.2f} bp, t {RRi.loc['pre 2022-08-25','fut_nw_t']:.2f} pre vs {RRi.loc['post 2022-08-25','fut_mean_bp']:.2f}, t {RRi.loc['post 2022-08-25','fut_nw_t']:.2f} post. "
          f"Excluding 2020Q1-2021Q2 changes nothing material (CW {RRi.loc['pre excl. 2020Q1-2021Q2','cw_mean_bp']:.2f}, futures {RRi.loc['pre excl. 2020Q1-2021Q2','fut_mean_bp']:.2f} bp, t {RRi.loc['pre excl. 2020Q1-2021Q2','fut_nw_t']:.2f}). "
          f"Flat-open share is similar pre and post (cw {RRi.loc['pre 2022-08-25','flat_share_cw']:.3f} vs {RRi.loc['post 2022-08-25','flat_share_cw']:.3f}), so differential constituent anchoring does not explain the stock pre/post gap. "
          "Caveats: the futures window (prior 14:45 close -> 08:45/09:00 open) differs from the stock window (prior close -> stock ATO); pre-2022-06 futures opens are unverified (open-definition and stability audits); one-day nights only (Mondays and holidays excluded).", "",
          f"**Flag (report only).** {int(FSi.loc['2018-11..2022-11-02','flag_vci'])} VCI-VN30 nights flagged in 2018-11..2022-11-02 ({FSi.loc['2018-11..2022-11-02','flag_vci_per_100']:.1f} per 100 one-day nights; {int(FSi.loc['2018-11..2022-11-02','flag_vci_not_flat'])} not already VCI-flagged), "
          f"{int(FSi.loc['2020Q1-2021Q2','flag_vci'])} of them in 2020Q1-2021Q2 ({FSi.loc['2020Q1-2021Q2','flag_vci_share_of_big']:.0%} of large-basket nights); verified window {int(FSi.loc[pv.replace('POOLED ','verified ').replace('verified verified','verified') if False else f'verified {VER_LO}..','flag_vci'])} "
          f"({FSi.loc[f'verified {VER_LO}..','flag_vci_per_100']:.1f} per 100, {FSi.loc[f'verified {VER_LO}..','flag_vci_share_of_big']:.0%} of large-basket nights) - that is the flag's floor on good opens. KBS VN30: {int(FSi.loc['2018-11..2022-11-02','flag_kbs'])} vs {int(FSi.loc[f'verified {VER_LO}..','flag_kbs'])}.", "",
          "## Summary (5 lines)", "",
          f"1. KBS: VN30 history exists (2018-01+) but is not independent - identical to VCI from 2021Q3 and more degraded before (flat {KQi.loc[ph,'kbs_flat']:.0%} in 2020Q1-2021Q2); no quarter where KBS VN30 tracks the basket and VCI does not; VNINDEX (both vendors) tracks the basket normally in 2019-2021Q2, so the degradation is specific to the VN30 index open (both vendors, different forms; exchange vs vendor origin not determinable).",
          f"2. Pre-cutover weakness survives in stocks (CW {RRi.loc['pre 2022-08-25','cw_mean_bp']:.2f} bp, t {RRi.loc['pre 2022-08-25','cw_nw_t']:.2f}; EW {RRi.loc['pre 2022-08-25','ew_mean_bp']:.2f}, t {RRi.loc['pre 2022-08-25','ew_nw_t']:.2f}) but not in futures ({RRi.loc['pre 2022-08-25','fut_mean_bp']:.2f} bp, t {RRi.loc['pre 2022-08-25','fut_nw_t']:.2f}); post-cutover all three positive (CW {RRi.loc['post 2022-08-25','cw_mean_bp']:.1f}, futures {RRi.loc['post 2022-08-25','fut_mean_bp']:.1f} bp); the break is in stocks only (post minus pre CW {_DD.iloc[0].post_minus_pre_bp:.1f} bp, t {_DD.iloc[0].t:.1f}; futures {_DD.iloc[2].post_minus_pre_bp:.1f} bp, t {_DD.iloc[2].t:.1f}); impossible stock gaps contribute 0 (none on PIT members).",
          f"3. Flag counts (|index ON| < 10 bp, |basket ON| > 50 bp): VCI VN30 {int(FSi.loc['2018-11..2022-11-02','flag_vci'])} nights 2018-11..2022 ({int(FSi.loc['2020Q1-2021Q2','flag_vci'])} in 2020Q1-2021Q2) vs {int(FSi.loc[f'verified {VER_LO}..','flag_vci'])} in the verified window ({FSi.loc['2018-11..2022-11-02','flag_vci_per_100']:.1f} vs {FSi.loc[f'verified {VER_LO}..','flag_vci_per_100']:.1f} per 100 nights); not applied anywhere.",
          "4. Reword (outcome B): the regime-1 claim and any 'change at the cutover' claim must name stocks only (stock overnight ~0 pre holds without the index; futures were positive pre and show no break); Level A VN30 pre value and the -3.63 bp basket-minus-index gap flagged as index-open-dependent; R1 82% Monday basis share and pre-cutover dbasis tests caveated (computed against a degraded index open). No memory file exists; claims taken from results summaries.",
          "5. Open question: why were futures overnight returns positive pre-cutover while stocks were ~0 - the timing difference (08:45 futures open vs stock ATO), basis convergence (the earlier decomposition put the pre-cutover excess in dbasis), or unverified pre-2022-06 futures opens? Next run (not done): pre-cutover futures close-to-close minus basket close-to-close - an excess at a similar daily rate points to carry/convergence, an excess confined to the overnight points to the open.", ""]
    H1 = tree_hash()
    M += [f"Integrity: md5 of every file in data/raw/ and results/ (excluding this audit's and the degradation audit's outputs) identical before and after: {H0 == H1} ({len(H0)} files)."]
    (OUT / "regime_rebase_audit.md").write_text("\n".join(M) + "\n"); print("\n".join(M))


if __name__ == "__main__":
    main()
