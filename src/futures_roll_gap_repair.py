"""Audit and repair of the missing VN30F1M roll days; impact on earlier results. MEASUREMENT ONLY.

Step 0  list calendar trading days missing from data/raw/VN30F1M.csv (calendar = VN30 u VNINDEX daily files).
Step 1  contract identity (VN30F2M relabelling) on the PRESENT post-expiry days; candidate sources validated
        against VCI VN30F1M (contract tickers VN30Fyymm via VCI, KBS daily, KRX codes, MSN).
Step 2  write data/raw/VN30F1M_repaired.csv (+ `source` column) only from a validated source; never interpolate.
Step 3  before/after: futures all-nights, Monday / Mon+Tue, weekday dbasis tests, offset regression, 2023 index ON;
        plus the logged 2018-11-21 bug fix (futures_basis_decomp.index_nights lost the prior date of the first row).
Existing scripts and files are not modified: build(), futures_nights() and panel() are replicated here with an
injectable futures file and verified to reproduce the originals exactly on the original file.
Usage: python3 src/futures_roll_gap_repair.py [--fetch]     (--fetch re-queries vnstock into data/raw_rollgap/)
"""
from __future__ import annotations
import argparse, glob, math, re, sys, time, warnings
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
pd.set_option("future.no_silent_downcasting", True)
from level_a import RAW_DIR, OUT_DIR, decompose
import level_c_futures as LCF
from level_c_futures import build, roll_days, stats, MULT
import level_c_phase2 as P2
import futures_basis_decomp as FB
import futures_basis_followup as FU

OUT = OUT_DIR
RG = RAW_DIR.parent / "raw_rollgap"
REPAIRED = RAW_DIR / "VN30F1M_repaired.csv"
CUTOVER = FB.CUTOVER
TOL = 0.051                                   # price match tolerance (index points; tick is 0.1)


from data_cap import futures_csv
def rd(name): return pd.read_csv(futures_csv(name), parse_dates=["date"]).set_index("date")   # futures via DATA_CAP snapshot


def calendar():
    return rd("VN30").index.union(rd("VNINDEX").index)


def expiry_of(y, m, cal):
    s = pd.Timestamp(y, m, 1); th = pd.date_range(s, s + pd.offsets.MonthEnd(0), freq="W-THU")[2]
    return th if th in cal else cal[cal <= th].max()


# ------------------------------------------------------------------ Step 0
def step0():
    f1, f2, v30, vni = rd("VN30F1M"), rd("VN30F2M"), rd("VN30"), rd("VNINDEX")
    cal = calendar(); lo, hi = f1.index.min(), f1.index.max(); calr = cal[(cal >= lo) & (cal <= hi)]
    rows = []
    for m in pd.period_range(lo, hi, freq="M"):
        e = expiry_of(m.year, m.month, cal); n = cal[cal > e]
        if len(n) == 0 or n[0] > hi: continue
        rows.append(dict(month=str(m), expiry=e, post_expiry_day=n[0], in_F1M=n[0] in f1.index, F2M_has_bar=n[0] in f2.index,
                         in_VN30=n[0] in v30.index, in_VNINDEX=n[0] in vni.index))
    E = pd.DataFrame(rows)
    miss = calr.difference(f1.index)
    other = [d for d in miss if d not in set(E.post_expiry_day)]
    info = dict(cal_days=len(calr), f1_days=len(f1), missing=len(miss), f1_not_in_cal=len(f1.index.difference(cal)),
                other_missing=other, n_post_expiry=len(E))
    return E, info


def reconcile_counts():
    v = FB.index_nights(); v = v[v.index >= "2018-11-21"]; f = FB.futures_nights(); j = FB.panel()
    nobar = v[~v.index.isin(f.index)]; mis = j[~j.aligned]
    return dict(index_nights=len(v), no_futures_bar=len(nobar), misaligned=len(mis), decomposition=int(j.aligned.sum()),
                nobar_dates=[str(x.date()) for x in nobar.index], mis_dates=[str(x.date()) for x in mis.index],
                y2023=(int((nobar.index.year == 2023).sum()), int((mis.index.year == 2023).sum())),
                y2022=(int((nobar.index.year == 2022).sum()), int((mis.index.year == 2022).sum())))


# ------------------------------------------------------------------ Step 1: identity tests
def identity(E):
    f1, f2, v = rd("VN30F1M"), rd("VN30F2M"), rd("VN30")
    T = pd.DatetimeIndex(E[E.in_F1M].post_expiry_day); pos = pd.Series(np.arange(len(f1)), index=f1.index)
    P = pd.DatetimeIndex([f1.index[pos[t] - 1] for t in T])
    ok = T.isin(f2.index) & P.isin(f2.index) & T.isin(v.index) & P.isin(v.index); T, P = T[ok], P[ok]
    g = lambda s, idx: s.reindex(idx).values
    io = np.log(g(v.open, T) / g(v.close, P)); ic = np.log(g(v.close, T) / g(v.close, P))
    spread_T = np.log(g(f2.close, T) / g(f1.close, T)) * 1e4
    nonroll = f1.index.difference(T).intersection(f2.index)
    spread_ord = (np.log(f2.close.reindex(nonroll) / f1.close.reindex(nonroll)) * 1e4).dropna()
    res_f2 = (np.log(g(f1.open, T) / g(f2.close, P)) - io) * 1e4
    res_f1 = (np.log(g(f1.open, T) / g(f1.close, P)) - io) * 1e4
    ordn = ((np.log(f1.open / f1.close.shift(1)) - np.log(v.open / v.close.shift(1))).drop(T, errors="ignore").dropna() * 1e4)
    volr = g(f2.volume, T) / g(f2.volume, P)
    cc_f2 = (np.log(g(f2.close, T) / g(f2.close, P)) - ic) * 1e4
    cc_new = (np.log(g(f1.close, T) / g(f2.close, P)) - ic) * 1e4
    rows = [
        ("n present post-expiry days with F1M, F2M and VN30 on T and T-1", len(T), ""),
        ("(a) F2M(T)-F1M(T) close spread on roll day T, median bp [IQR]", np.median(spread_T), f"[{np.percentile(spread_T,25):.1f}, {np.percentile(spread_T,75):.1f}]"),
        ("(a) same spread on all other days, median bp [IQR]", spread_ord.median(), f"[{spread_ord.quantile(.25):.1f}, {spread_ord.quantile(.75):.1f}]"),
        ("(b) |ln F1M_open(T)/F2M_close(T-1) - idx ON|, median bp", np.median(np.abs(res_f2)), "F2M(T-1) as the prior close"),
        ("(b) |ln F1M_open(T)/F1M_close(T-1) - idx ON|, median bp", np.median(np.abs(res_f1)), "F1M(T-1) = expiring contract"),
        ("(b) ordinary nights |fut ON - idx ON|, median bp", ordn.abs().median(), "reference"),
        ("(c) F2M volume(T) / F2M volume(T-1), median", np.median(volr), f"share < 0.2: {(volr < 0.2).mean():.3f}"),
        ("(c) F1M volume(T) / F2M volume(T-1), median", np.median(g(f1.volume, T) / g(f2.volume, P)), ""),
        ("(d) |F2M(T)/F2M(T-1) cc - idx cc|, median bp", np.median(np.abs(cc_f2)), "if F2M were one contract across T"),
        ("(d) |F1M(T)/F2M(T-1) cc - idx cc|, median bp", np.median(np.abs(cc_new)), "new front month = old F2M"),
    ]
    return pd.DataFrame(rows, columns=["test", "value", "note"])


# ------------------------------------------------------------------ Step 1: sources
PROBE_LOG = [  # first probe run (this session): candidates that are not monthly VCI contract tickers
    ("KBS", "VN30F1M", "ok: 149 rows 2026-04-17..2026-11-23 (no contract identity)"), ("KBS", "VN30F2M", "ok: 2 rows 2026-11-20..2026-11-23"),
    ("KBS", "VN30F2212", "error (ValueError via RetryError)"), ("KBS", "VN30F2302", "error"), ("KBS", "VN30F2512", "error"), ("KBS", "VN30F2601", "error"),
    ("MSN", "VN30F1M", "error (ConnectionError)"), ("VCI", "VN30F2601", "error (post-May-2025 contracts use KRX codes)"),
    ("VCI", "41I1G1000", "ok: 38 rows 2025-11-21..2026-01-15 (KRX code of the Jan-2026 contract)")]


def fetch():
    from vnstock import Quote
    RG.mkdir(parents=True, exist_ok=True); log = []
    cands = [("VCI", "VN30F" + f"{y % 100:02d}{m:02d}") for y in range(2017, 2026) for m in range(1, 13)] + \
            [("KBS", "VN30F1M"), ("KBS", "VN30F2M"), ("KBS", "VN30F2212"), ("MSN", "VN30F1M"), ("VCI", "41I1G1000")]
    for src, sym in cands:
        try:
            df = Quote(symbol=sym, source=src).history(start="2017-01-01", end=pd.Timestamp.today().strftime("%Y-%m-%d"), interval="1D")
            st = "empty" if df is None or df.empty else f"ok {len(df)}"
            if st.startswith("ok"): df.to_csv(RG / f"{src}_{sym}_1D.csv", index=False)
        except BaseException as e: st = f"error {type(e).__name__}"
        log.append((src, sym, st)); print(src, sym, st, flush=True); time.sleep(5)
    pd.DataFrame(log, columns=["source", "symbol", "status"]).to_csv(RG / "_fetch_log_refetch.csv", index=False)


def load_src(src, sym):
    p = RG / f"{src}_{sym}_1D.csv"
    if not p.exists(): return None
    d = pd.read_csv(p, parse_dates=["time"]); d["date"] = d.time.dt.normalize()
    return d.drop(columns="time").drop_duplicates("date", keep="last").set_index("date")


def contract_front_series():
    """Front-month bars stitched from VCI contract tickers: on date t the front contract is the one whose expiry is the
    first expiry >= t (calendar-based, independent of which files exist)."""
    cal = calendar(); C = {}
    for p in glob.glob(str(RG / "VCI_VN30F[0-9][0-9][0-9][0-9]_1D.csv")):
        ym = re.search(r"VN30F(\d{4})_", p).group(1); C[ym] = load_src("VCI", f"VN30F{ym}")
    months = pd.period_range("2017-08", "2026-12", freq="M")
    exps = pd.Series({f"{m.year % 100:02d}{m.month:02d}": expiry_of(m.year, m.month, cal) for m in months})
    rows = []
    for t in cal[cal >= "2017-08-10"]:
        ym = exps[exps >= t].idxmin() if (exps >= t).any() else None
        d = C.get(ym)
        if d is None or t not in d.index: continue
        r = d.loc[t]; rows.append(dict(date=t, contract=f"VN30F{ym}", open=r.open, high=r.high, low=r.low, close=r.close, volume=r.volume))
    return pd.DataFrame(rows).set_index("date"), sorted(C)


def match_table(S, ref, label, roll_T=None):
    k = S.join(ref[["open", "high", "low", "close", "volume"]].add_suffix("_v"), how="inner")
    out = []
    subsets = [("all overlap", k)]
    if len(k):
        subsets += [("2022", k[k.index.year == 2022]), ("2023 onward", k[k.index.year >= 2023])]
        if roll_T is not None: subsets.append(("present post-expiry (roll) days", k[k.index.isin(roll_T)]))
    for nm, g in subsets:
        if not len(g): continue
        r = dict(source=label, subset=nm, n=len(g), first=g.index.min().date(), last=g.index.max().date())
        for c in ["open", "high", "low", "close"]: r[f"{c}_match"] = np.isclose(g[c], g[c + "_v"], atol=TOL).mean()
        r["volume_exact"] = (g.volume == g.volume_v).mean(); r["volume_within_1pct"] = (abs(g.volume / g.volume_v - 1) < 0.01).mean()
        out.append(r)
    return out


def sources(E):
    f1, f2 = rd("VN30F1M"), rd("VN30F2M")
    S, have = contract_front_series()
    roll_T = pd.DatetimeIndex(E[E.in_F1M].post_expiry_day)
    V = match_table(S, f1, "VCI contract tickers (stitched front month)", roll_T)
    kb = load_src("KBS", "VN30F1M")
    if kb is not None: V += match_table(kb[kb.index <= f1.index.max()], f1, "KBS VN30F1M daily", roll_T)
    kr = load_src("VCI", "41I1G1000")
    if kr is not None:
        cal = calendar(); lo = cal[cal > expiry_of(2025, 12, cal)][0]; hi = expiry_of(2026, 1, cal)
        V += match_table(kr[(kr.index >= lo) & (kr.index <= hi)], f1, "VCI KRX code 41I1G1000 (Jan-2026) in its front window", roll_T)
    V = pd.DataFrame(V)
    gaps = E[~E.in_F1M].copy()
    gaps["front_contract"] = [S.contract.get(t, "") for t in gaps.post_expiry_day]
    gaps["contract_has_bar"] = gaps.post_expiry_day.isin(S.index)
    for c in ["open", "high", "low", "close", "volume"]:
        gaps[f"c_{c}"] = [S[c].get(t, np.nan) for t in gaps.post_expiry_day]
        gaps[f"f2m_{c}"] = [f2[c].get(t, np.nan) for t in gaps.post_expiry_day]
    gaps["F2M_equals_contract_OHLCV"] = [bool(all(np.isclose(r[f"c_{c}"], r[f"f2m_{c}"]) for c in ["open", "high", "low", "close", "volume"])) if r.F2M_has_bar else False
                                         for _, r in gaps.iterrows()]
    gaps["usable_F2M_as_substitute"] = np.where(gaps.F2M_equals_contract_OHLCV, "yes (F2M on this day IS the new front contract)", "no (no F2M bar)")
    return V, gaps, S, have


# ------------------------------------------------------------------ Step 2: repair
def repair(gaps, S, val_ok):
    f1 = pd.read_csv(futures_csv("VN30F1M"), parse_dates=["date"])
    if not val_ok: return None, None
    ins = []
    for _, g in gaps[gaps.contract_has_bar].iterrows():
        t = g.post_expiry_day; r = S.loc[t]
        src = f"VCI contract {r.contract} (1D)" + (" ; cross-check VCI VN30F2M identical OHLCV" if g.F2M_equals_contract_OHLCV else " ; no cross-check (no VN30F2M bar)")
        ins.append(dict(date=t, open=r.open, high=r.high, low=r.low, close=r.close, volume=int(r.volume), source=src))
    I = pd.DataFrame(ins)
    f1["source"] = "VCI VN30F1M (original)"
    R = pd.concat([f1.drop(columns="open_suspicious"), I], ignore_index=True).sort_values("date").reset_index(drop=True)
    from fetch_indices import FLAG_TOL
    R["open_suspicious"] = ((R["open"] - R["close"].shift(1)).abs() < FLAG_TOL).fillna(False)
    old = f1.set_index("date").open_suspicious; new = R.set_index("date").open_suspicious
    changed = [d for d in old.index if bool(old[d]) != bool(new[d])]
    cols = ["date", "open", "high", "low", "close", "volume", "open_suspicious", "source"]
    R[cols].to_csv(REPAIRED, index=False)
    I["open_suspicious"] = new.reindex(I.date).values
    I.to_csv(OUT / "futures_roll_gap_inserted_rows.csv", index=False)
    return R.set_index("date")[cols[1:]], changed


# ------------------------------------------------------------------ replicas with injectable futures file
def build_from(f1: pd.DataFrame, per_side, roll_cost, fix_rolls=True, fee_vnd=None, slippage=0.0, exclude=()):
    """Exact copy of level_c_futures.build with f1 passed in; `exclude` dates become uninvested (r = 0)."""
    f2 = rd("VN30F2M")
    d = f1[["open", "close", "open_suspicious"]].copy()
    d["is_roll"] = d.index.isin(roll_days(d.index))
    entry = d["close"].shift(1)
    if fix_rolls:
        f2c = f2["close"].reindex(d.index).shift(1)
        entry = entry.where(~d["is_roll"], f2c)
    d["entry"] = entry
    d["invested"] = d["entry"].notna() & ~d.index.isin(pd.DatetimeIndex(exclude))
    d["r_gross"] = (d["open"] / d["entry"] - 1).where(d["invested"]).fillna(0.0)
    side_cost = 2 * per_side if fee_vnd is None else fee_vnd / (MULT * d["entry"]) + fee_vnd / (MULT * d["open"]) + 2 * slippage
    d["cost"] = side_cost + np.where(d["is_roll"], roll_cost, 0.0)
    d["r_net"] = np.where(d["invested"], d["r_gross"] - d["cost"], 0.0)
    prev = d.index.to_series().shift(1)
    d["gap_days"] = (d.index.to_series() - prev).dt.days
    d["hold_type"] = np.where(d["gap_days"] < 2, "", np.where((prev.dt.weekday == 4) & (d["gap_days"] == 3), "weekend", "holiday"))
    d = d.iloc[1:]
    d["eq_gross"] = (1 + d["r_gross"]).cumprod(); d["eq_net"] = (1 + d["r_net"]).cumprod()
    return d


def futures_nights_from(f1, exclude=()):
    """Copy of futures_basis_decomp.futures_nights with f1 passed in."""
    d = build_from(f1, 0, 0.0, exclude=exclude)
    d["high"], d["low"], d["volume"] = f1["high"].reindex(d.index), f1["low"].reindex(d.index), f1["volume"].reindex(d.index)
    d["prev_date"] = d.index.to_series().shift(1)
    d.loc[d.index[0], "prev_date"] = f1.index[f1.index < d.index[0]].max()
    d["fut_ON"] = np.log(d["open"] / d["entry"]).where(d["invested"])
    d["fut_ID"] = np.log(d["close"] / d["open"])
    d["fut_ON_simple"] = (d["open"] / d["entry"] - 1).where(d["invested"])
    ew = d["prev_date"].dt.weekday
    d["night"] = np.where(d["hold_type"] == "", ew.map(FB.NIGHT), np.where(d["hold_type"] == "weekend", "Fri->Mon (weekend)", "holiday"))
    d["entry_weekday"] = ew
    allf = f1.index; rolls = roll_days(allf); exp = pd.DatetimeIndex([allf[allf < r].max() for r in rolls])
    pos = pd.Series(np.arange(len(allf)), index=allf)
    nxt = np.searchsorted(exp.values, d.index.values, side="left")
    d["expiry"] = [exp[i] if i < len(exp) else pd.NaT for i in nxt]
    d["dte"] = [pos[e] - pos[t] if pd.notna(e) else np.nan for t, e in zip(d.index, d["expiry"])]
    near = set()
    for e in exp:
        for k in (-1, 0, 1):
            p = pos[e] + k
            if 0 <= p < len(allf): near.add(allf[p])
    d["near_expiry"] = d.index.isin(list(near))
    return d


def index_nights_fixed():
    """futures_basis_decomp.index_nights with the first-row bug fixed: prior date / close taken before decompose drops row 0."""
    raw = pd.read_csv(RAW_DIR / "VN30.csv", parse_dates=["date"]).sort_values("date").reset_index(drop=True)
    raw["prev_date"] = raw["date"].shift(1); raw["prev_close"] = raw["close"].shift(1)
    v = decompose(raw)
    return v.set_index("date").rename(columns={"r_overnight": "idx_ON", "r_intraday": "idx_ID", "open_suspicious": "idx_flag"})


def panel_from(f, i):
    j = f.join(i[["open", "close", "prev_close", "prev_date", "idx_ON", "idx_ID", "idx_flag"]], how="inner", rsuffix="_idx")
    j = j[j["invested"] & j["idx_ON"].notna()]
    j["aligned"] = j["prev_date"] == j["prev_date_idx"]
    j["b_open"] = np.log(j["open"] / j["open_idx"]); j["b_prevclose"] = np.log(j["entry"] / j["prev_close"])
    j["b_close"] = np.log(j["close"] / j["close_idx"])
    j["dbasis_ON"] = j["b_open"] - j["b_prevclose"]; j["dbasis_ID"] = j["fut_ID"] - j["idx_ID"]
    assert (j["fut_ON"] - j["idx_ON"] - j["dbasis_ON"]).abs().max() < 1e-10
    return j


def verify_replicas(f1o):
    a, b = build(0, **P2.BASE), build_from(f1o, 0, **P2.BASE)
    c1 = all(np.allclose(a[c].astype(float), b[c].astype(float), equal_nan=True) for c in ["entry", "r_gross", "r_net", "cost", "eq_net"]) and (a.invested == b.invested).all() and (a.hold_type == b.hold_type).all()
    fa, fb = FB.futures_nights(), futures_nights_from(f1o)
    c2 = all(np.allclose(fa[c].astype(float), fb[c].astype(float), equal_nan=True) for c in ["fut_ON", "fut_ID", "dte"]) and (fa.night == fb.night).all() and (fa.near_expiry == fb.near_expiry).all()
    pa, pb = FB.panel(), panel_from(fb, FB.index_nights())
    c3 = pa.index.equals(pb.index) and np.allclose(pa.dbasis_ON, pb.dbasis_ON, equal_nan=True) and (pa.aligned == pb.aligned).all()
    return dict(build=c1, futures_nights=c2, panel=c3)


# ------------------------------------------------------------------ Step 3 metrics
def futures_metrics(f1, exclude=()):
    out = {}
    g = build_from(f1, 0, P2.BASE["roll_cost"], fee_vnd=P2.BASE["fee_vnd"], slippage=P2.BASE["slippage"], exclude=exclude)
    sg = stats(g.r_gross, g.eq_gross, g.invested); sn = stats(g.r_net, g.eq_net, g.invested)
    inv = g[g.invested]; n = len(inv)
    out["all nights | n"] = (n, np.nan)
    out["all nights | gross mean bp"] = (inv.r_gross.mean() * 1e4, inv.r_gross.std() / math.sqrt(n) * 1e4)
    sr_se = lambda sr, n, ppy: math.sqrt((1 + 0.5 * (sr / math.sqrt(ppy)) ** 2) / n) * math.sqrt(ppy)
    out["all nights | gross Sharpe"] = (sg["sharpe"], sr_se(sg["sharpe"], n, 252)); out["all nights | gross t"] = (sg["t_stat"], 1.0)
    out["all nights | net (12,500 VND + 1bp + 5bp roll) mean bp"] = (inv.r_net.mean() * 1e4, inv.r_net.std() / math.sqrt(n) * 1e4)
    out["all nights | net (12,500 VND + 1bp + 5bp roll) Sharpe"] = (sn["sharpe"], sr_se(sn["sharpe"], n, 252)); out["all nights | net (12,500 VND + 1bp + 5bp roll) t"] = (sn["t_stat"], 1.0)
    h = build_from(f1, 0.00021, P2.BASE["roll_cost"], exclude=exclude); sh = stats(h.r_net, h.eq_net, h.invested); ih = h[h.invested]
    out["all nights | net 0.021%/side + 5bp roll mean bp"] = (ih.r_net.mean() * 1e4, ih.r_net.std() / math.sqrt(len(ih)) * 1e4)
    out["all nights | net 0.021%/side + 5bp roll Sharpe"] = (sh["sharpe"], sr_se(sh["sharpe"], len(ih), 252)); out["all nights | net 0.021%/side + 5bp roll t"] = (sh["t_stat"], 1.0)
    for sig, wd in P2.SIGNALS.items():
        for per, (lo, hi) in {"full 2017-2026": ("2017-01-01", "2026-12-31"), "ex-2026 (2017-2025)": ("2017-01-01", "2025-12-31")}.items():
            a, b = max(pd.Timestamp(lo), g.index[0]), min(pd.Timestamp(hi), g.index[-1])
            r = P2.row(g, wd, lo, hi, (b - a).days / 365.25)
            k = f"{sig} {per}"
            se_m = r["mean_net_bp"] / r["net_t"]
            out[f"{k} | n"] = (r["n_obs"], np.nan)
            out[f"{k} | gross mean bp"] = (r["mean_gross_bp"], se_m); out[f"{k} | net mean bp"] = (r["mean_net_bp"], se_m)
            out[f"{k} | net Sharpe"] = (r["net_sharpe"], r["sharpe_se"]); out[f"{k} | net t"] = (r["net_t"], 1.0)
    return out


def decomp_metrics(j):
    out = {"decomposition sample N": (len(j), np.nan)}
    y = j[j.index.year == 2023].idx_ON
    out["2023 index ON in decomposition sample, bp"] = (y.mean() * 1e4, y.std() / math.sqrt(len(y)) * 1e4)
    robust = ~j.is_roll & ~j.near_expiry
    for per, g in FU.periods_1b(j).items():
        for samp, m in [("all days", pd.Series(True, index=g.index)), ("ex roll & expiry-1..+1", robust.reindex(g.index))]:
            gg = g[m]; rows, jt = FU.weekday_test(gg.dbasis_ON, gg.night)
            for r in rows:
                se = abs(r["minus_others_bp"] / r["minus_others_t"])
                out[f"dbasis_ON {per} | {samp} | {r['night']} minus others bp"] = (r["minus_others_bp"], se)
                out[f"dbasis_ON {per} | {samp} | {r['night']} minus others t"] = (r["minus_others_t"], 1.0)
                out[f"dbasis_ON {per} | {samp} | {r['night']} n"] = (r["n"], np.nan)
            out[f"dbasis_ON {per} | {samp} | joint Wald p"] = (jt["wald_p"], np.nan)
            out[f"dbasis_ON {per} | {samp} | grand mean bp"] = (jt["grand_mean_bp"], abs(jt["grand_mean_bp"] / jt["grand_mean_t"]))
    for lab, g in [(str(y), j[j.index.year == y]) for y in range(2022, 2027)] + [("post 2022-08-25 pooled", j[j.index >= CUTOVER])]:
        o = FU.ols_ak(g.fut_ON, g.idx_ON)
        out[f"offset {lab} | a bp"] = (o["a_bp"], o["a_se_bp"]); out[f"offset {lab} | a t"] = (o["a_t"], 1.0)
        out[f"offset {lab} | k"] = (o["k"], o["k_se"]); out[f"offset {lab} | n"] = (o["n"], np.nan)
    return out


# ------------------------------------------------------------------ 2018-11-21 fix: old vs fixed outputs side by side
def rerun_fb_tables():
    """Re-run the futures_basis_decomp / followup table builders exactly as their main() does, with index_nights patched."""
    fut = FB.futures_nights(); j = FB.panel()
    J = {"a_all_days": j[j.aligned], "b_ex_index_flagged": j[j.aligned & ~j.idx_flag.astype(bool)]}
    basket = FB.pit_basket(); outs = {k: [] for k in ("year", "weekday", "monday", "wednesday", "expiry", "robustness")}
    for lab, jj in J.items():
        outs["year"].append(FB.yearly(jj, fut[fut.invested]).assign(sample=lab)); outs["weekday"].append(FB.weekday(jj).assign(sample=lab))
        outs["monday"].append(FB.monday(jj, fut).assign(sample=lab)); outs["wednesday"].append(FB.wednesday(jj, basket).assign(sample=lab))
        outs["expiry"].append(FB.expiry(jj).assign(sample=lab))
        r = jj[~jj.is_roll & ~jj.near_expiry]
        outs["robustness"] += [FB.yearly(r).assign(table="A", sample=lab), FB.weekday(r).assign(table="B", sample=lab),
                               FB.monday(r, fut[~fut.is_roll & ~fut.near_expiry]).assign(table="C", sample=lab), FB.wednesday(r, basket).assign(table="D", sample=lab)]
    T = {f"futures_basis_{k}": pd.concat(v, ignore_index=True) for k, v in outs.items()}
    jA = j[j.aligned]
    RC, LST = FU.reconcile()
    T["futures_basis_followup_reconcile"] = pd.concat([RC.assign(section="waterfall"), LST.assign(section="misaligned nights")], ignore_index=True)
    WT, OF = FU.part1(jA); T["futures_basis_followup_weekday_tests"] = WT; T["futures_basis_followup_offset"] = OF
    return T


def diff_tables(T):
    rows = []
    for name, new in T.items():
        old = pd.read_csv(OUT / f"{name}.csv")
        new.to_csv(OUT / f"{name}_fix20181121.csv", index=False)
        new2 = pd.read_csv(OUT / f"{name}_fix20181121.csv")                # same dtypes as the old file
        if old.shape != new2.shape:
            rows.append(dict(file=name, row="(shape)", column="", old=str(old.shape), new=str(new2.shape)));
            continue
        keys = [c for c in old.columns if old[c].dtype == object][:4]
        for c in old.columns:
            if c not in new2.columns or old[c].dtype == object: continue
            a, b = pd.to_numeric(old[c], errors="coerce"), pd.to_numeric(new2[c], errors="coerce")
            ra, rb = a.round(2), b.round(2)
            ch = ~((ra == rb) | (ra.isna() & rb.isna()))
            for i in np.where(ch)[0]:
                rows.append(dict(file=name, row=" | ".join(str(old.iloc[i][k]) for k in keys), column=c, old=a.iloc[i], new=b.iloc[i]))
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ main
def fmt(df): return df.to_string(index=False)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--fetch", action="store_true"); a = ap.parse_args()
    pd.set_option("display.width", 250, "display.max_columns", 40, "display.float_format", "{:.3f}".format, "display.max_colwidth", 90)
    if a.fetch: fetch()
    L = ["# VN30F1M roll-gap audit, repair and impact (measurement only)", ""]
    # ---- Step 0
    E, i0 = step0(); RCN = reconcile_counts()
    L += ["## Step 0: missing days",
          f"Calendar = union of VN30 and VNINDEX daily dates. In the VN30F1M range there are {i0['cal_days']} calendar trading days; VN30F1M.csv has {i0['f1_days']} "
          f"(missing {i0['missing']}; VN30F1M days not in the calendar: {i0['f1_not_in_cal']}). Post-expiry days checked: {i0['n_post_expiry']} "
          "(expiry = 3rd Thursday, or the last trading day before it).", ""]
    # ---- Step 1
    ID = identity(E); V, G, S, have = sources(E)
    gt = G[["month", "expiry", "post_expiry_day", "F2M_has_bar", "usable_F2M_as_substitute", "front_contract", "contract_has_bar", "in_VN30", "in_VNINDEX"]].copy()
    for c in ["expiry", "post_expiry_day"]: gt[c] = pd.to_datetime(gt[c]).dt.date
    L += ["Missing post-expiry days (all are trading days in both index files):", fmt(gt), "",
          f"Other missing calendar days (not post-expiry): {', '.join(str(d.date()) for d in i0['other_missing'])} "
          f"(VN30 bar: {'yes' if all(d in rd('VN30').index for d in i0['other_missing']) else 'no'}; VN30F2M bar: no; front contract VN30F2105 not served by VCI).", "",
          "### Count reconciliation",
          f"Index nights from 2018-11-21: {RCN['index_nights']}. Decomposition sample: {RCN['decomposition']}. Dropped = {RCN['no_futures_bar']} nights with no futures bar "
          f"({', '.join(RCN['nobar_dates'])}) + {RCN['misaligned']} misaligned nights ({', '.join(RCN['mis_dates'])}).",
          f"- 2023: {RCN['y2023'][0]} no-bar + {RCN['y2023'][1]} misaligned = {sum(RCN['y2023'])} index nights (the '24'); 2022: {RCN['y2022'][0]} + {RCN['y2022'][1]}.",
          "- The '16' is the full-sample count of misaligned nights: 14 nights after a missing roll day, 2021-05-04 (after missing 2021-04-29) and 2018-11-21.",
          "- 2018-11-21 is NOT a data gap: VN30.csv starts 2018-11-20 and both series start that night from 2018-11-20. futures_basis_decomp.index_nights() "
          "computed prev_date AFTER decompose() dropped the first row, so the first index night lost its prior date (code bug, fixed below as a logged change).",
          "- Correct count of nights affected by DATA gaps: 15 missing futures days -> 15 index nights without a futures bar + 15 contaminated futures nights "
          "(14 post-roll + 2021-05-04) = 30.", ""]
    L += ["## Step 1: contract identity on the PRESENT post-expiry days", fmt(ID), "",
          "Reading: on present roll days VN30F2M's volume collapses to ~1% of the prior day (all days < 20%) and F1M(T) opens in line with F2M(T-1), "
          "not F1M(T-1). The vendor relabels at expiry: on T, VN30F1M is the old F2M contract and VN30F2M is the next-out contract. "
          "The calendar spread is small (median ~-10 bp), so spread levels alone do not identify the contract; volume does.",
          "On the 14 MISSING days the relabel failed differently: VN30F2M's OHLCV on 13 of them is IDENTICAL to the new front contract (from its own ticker), "
          "i.e. on those days the vendor's F2M series already carried the new front month and the F1M series carried the expired contract (no bar).", ""]
    L += ["## Step 1: candidate sources", "Fetch results (this session):",
          fmt(pd.DataFrame(PROBE_LOG, columns=["source", "symbol", "status"])),
          f"VCI contract tickers VN30Fyymm: served for {have[0]}..{have[-1]} ({len(have)} contracts); contracts expiring before 2022-07 (and 2206) and the "
          "post-May-2025 contracts 2507/2508/2510/2511 under the old naming are not served (error).", "",
          "Validation against VCI VN30F1M on days where VCI is present (price tolerance 0.05 pt):", fmt(V), ""]
    cv = V[(V.source.str.startswith("VCI contract")) & (V.subset == "all overlap")].iloc[0]
    val_ok = cv.close_match >= 0.99
    L += [f"Decision rule (close match >= 99%): VCI contract tickers close match {cv.close_match*100:.2f}% -> {'USABLE' if val_ok else 'NOT USABLE'}. "
          "Open/high/low/volume mismatches are concentrated in 2022 (small differences in O/H/L, volume differing by a few hundred contracts); from 2023 every field matches 100%. "
          "KBS daily starts 2026-04-17 (no history for the gaps) and fails validation anyway: its 'VN30F1M' (auto-converted to KRX code 41I1GC000) trades ~20 contracts/day "
          "vs ~250,000 in VCI VN30F1M (median volume ratio 0.0003), i.e. it is an illiquid non-front contract. The KRX code works only for contracts listed after May 2025; MSN failed. "
          "None of these candidates exposes contract identity except the contract tickers themselves.",
          "2023-01-27: VN30F2M absent; recovered from VN30F2302 only (2023 match rate 100%, no second source). "
          "2021-04-29: no source (VN30F2105 not served, no F2M bar, KBS history too short) -> NOT filled; the 2021-05-04 futures night is excluded explicitly.", ""]
    gv = G.copy(); gv["post_expiry_day"] = pd.to_datetime(gv.post_expiry_day).dt.date
    L += ["Values on the missing days, contract ticker vs VN30F2M:",
          fmt(gv[["post_expiry_day", "front_contract", "c_open", "c_close", "c_volume", "f2m_open", "f2m_close", "f2m_volume", "F2M_equals_contract_OHLCV"]]), ""]
    # ---- Step 2
    R, changed = repair(G, S, val_ok)
    f1o = rd("VN30F1M")
    VR = verify_replicas(f1o); b0 = build(0, **P2.BASE); g0 = b0[b0.invested].r_gross.mean() * 1e4
    L += ["## Step 2: repair",
          f"Written: data/raw/VN30F1M_repaired.csv ({len(R)} rows = {len(f1o)} original + {len(R)-len(f1o)} inserted; column `source`). "
          f"Inserted-row log: results/futures_roll_gap_inserted_rows.csv. VN30F1M.csv untouched. open_suspicious recomputed with fetch_indices' rule on the repaired series; "
          f"flags that changed on ORIGINAL rows: {', '.join(str(d.date()) for d in changed) if changed else 'none'}.",
          f"Reproduction check (original file, original code path level_c_futures.build): all-nights gross {g0:.2f} bp (target 4.99). "
          f"Replicas used for the repaired file reproduce the originals exactly on the original file: {VR}.", ""]
    assert all(VR.values()) and abs(g0 - 4.99) < 0.005
    # ---- Step 3
    E14 = pd.to_datetime(G[~G.month.isna()].post_expiry_day)
    cont = [f1o.index[f1o.index > t][0] for t in E14]                       # 14 contaminated Monday nights in the original
    cont += [pd.Timestamp("2021-05-04")]
    i_old, i_fix = FB.index_nights(), index_nights_fixed()
    V_ = {}
    V_["before (as reported)"] = (f1o, (), i_old)
    V_["2018-11-21 fix only"] = (f1o, (), i_fix)
    V_["original, contaminated nights excluded + fix"] = (f1o, tuple(cont), i_fix)
    V_["repaired file + fix (2021-05-04 excluded)"] = (R, (pd.Timestamp("2021-05-04"),), i_fix)
    res = {}
    for nm, (f1, ex, ii) in V_.items():
        m = futures_metrics(f1, ex)
        fn = futures_nights_from(f1, ex); j = panel_from(fn, ii); j = j[j.aligned]
        m.update(decomp_metrics(j)); res[nm] = m
    keys = list(res["before (as reported)"].keys())
    BA = pd.DataFrame({"metric": keys})
    for nm in V_: BA[nm] = [res[nm].get(k, (np.nan,))[0] for k in keys]
    BA["se_before"] = [res["before (as reported)"][k][1] for k in keys]
    last = "repaired file + fix (2021-05-04 excluded)"
    BA["delta_after_minus_before"] = BA[last] - BA["before (as reported)"]
    BA["moves_gt_half_se"] = (BA.delta_after_minus_before.abs() > 0.5 * BA.se_before) & BA.se_before.notna()
    BA.to_csv(OUT / "futures_roll_gap_before_after.csv", index=False)
    # gross shift reconciliation
    bb = build_from(f1o, 0, 0.0); x = bb.loc[cont]; N = int(bb.invested.sum()); s15 = x.r_gross.sum(); allm = bb[bb.invested].r_gross.mean()
    wo = bb[bb.invested & ~bb.index.isin(cont)].r_gross
    L += ["## Step 3: impact", "### Gross-shift reconciliation (0.50 vs 0.46)",
          f"15 contaminated nights: n = {len(x)}, sum of simple returns = {s15*1e4:.1f} bp, mean = {x.r_gross.mean()*1e4:.1f} bp. All invested nights N = {N}, mean {allm*1e4:.3f} bp. "
          f"Without them: n = {len(wo)}, mean {wo.mean()*1e4:.3f} bp. Shift = {wo.mean()*1e4 - allm*1e4:.3f} bp = (mean_all - mean_15) x 15/(N-15). "
          f"The earlier 0.46 was sum_15 / N = {s15/N*1e4:.3f} bp, the 15 nights' contribution to the all-nights mean, not the change from removing them "
          "(removing also shrinks the denominator). The correct shift from excluding them is 0.50 bp.",
          "Contaminated nights excluded in the 'excluded' variant: " + ", ".join(str(d.date()) for d in cont) + ".", ""]
    L += ["### Before / after (flag = |repaired - before| > 0.5 x SE(before); SE for Sharpe from the Lo formula, for t-stats SE = 1)",
          fmt(BA.drop(columns=["se_before"])), ""]
    # ---- 2018-11-21 fix side by side
    orig = FB.index_nights
    try:
        FB.index_nights = index_nights_fixed
        T = rerun_fb_tables()
    finally:
        FB.index_nights = orig
    DF = diff_tables(T); DF.to_csv(OUT / "futures_roll_gap_fix20181121_changes.csv", index=False)
    L += ["## 2018-11-21 bug fix (logged)",
          "grep: index_nights() is defined only in futures_basis_decomp.py and called by futures_basis_decomp.py and futures_basis_followup.py (not by level_c_phase2.py "
          "or track_forward.py, which do not use the index). The same first-row pattern (`decompose()` then `date.diff()`/`shift(1)`, so the first remaining night has no gap "
          "and fails a gap == 1 filter) exists in level_b_dayofweek.py, pit_dayofweek_2x2.py, pit_residual_split.py, open_filter_audit.py (one_day filter) and "
          "composition_diagnostic.py: each drops the first night of each series. In pit_residual_split.py the index series is cut at 2018-11-21, so the same night is lost there. "
          "These scripts were NOT changed.",
          f"Fixed outputs written next to the old ones as results/<name>_fix20181121.csv; decomposition N 1,962 -> 1,963. Changed cells at 2-decimal precision: {len(DF)} "
          "(full list: results/futures_roll_gap_fix20181121_changes.csv). The intraday tables (2023-09 onward) cannot change.", ""]
    if len(DF):
        L += [fmt(DF.groupby("file").size().rename("n_changed").reset_index()), "", "Changed cells in headline tables (year 'all', Monday, Wednesday, offset, weekday tests):",
              fmt(DF[DF.file.isin(["futures_basis_monday", "futures_basis_wednesday", "futures_basis_followup_offset"]) | DF.row.str.contains("all", na=False)].head(80)), ""]
    v = lambda k, c=last: BA.set_index("metric").loc[k, c]
    b_ = lambda k: v(k, "before (as reported)")
    L += ["## Conclusions checked (not reinterpreted)",
          f"- Monday edge: unchanged to every decimal (Monday full net {b_('Monday full 2017-2026 | net mean bp'):.2f} bp, t {b_('Monday full 2017-2026 | net t'):.2f}; "
          "Mon+Tue likewise). All 14 missing days are Fridays, so no Monday- or Tuesday-entry night touches them; the contaminated nights are weekend/holiday nights.",
          f"- Wednesday gap: Wed->Thu nights are not touched by the repair or the 2018 fix (2018-11-21 is a Tue->Wed night); futures_basis_decomp Tables C/D are unchanged. "
          f"W1 post-cutover Wed->Thu minus others {b_('dbasis_ON post 2022-08-25 | all days | Wed->Thu minus others bp'):.2f} -> {v('dbasis_ON post 2022-08-25 | all days | Wed->Thu minus others bp'):.2f} bp "
          f"(t {v('dbasis_ON post 2022-08-25 | all days | Wed->Thu minus others t'):.2f}): conclusion unchanged.",
          f"- Offset: post-cutover a {b_('offset post 2022-08-25 pooled | a bp'):.2f} -> {v('offset post 2022-08-25 pooled | a bp'):.2f} bp (t {b_('offset post 2022-08-25 pooled | a t'):.2f} -> "
          f"{v('offset post 2022-08-25 pooled | a t'):.2f}); O1 still holds. 2023 a moves {b_('offset 2023 | a bp'):.2f} -> {v('offset 2023 | a bp'):.2f} bp and k "
          f"{b_('offset 2023 | k'):.3f} -> {v('offset 2023 | k'):.3f} (flagged, > 0.5 SE).",
          f"- 2023 index ON: {b_('2023 index ON in decomposition sample, bp'):.2f} -> {v('2023 index ON in decomposition sample, bp'):.2f} bp, equal to the full-index 9.86 bp: the discrepancy is removed.",
          "- Cells crossing |t| = 2 after the repair (below the Bonferroni bar 3.1, no pre-registered read involves them): 2023-on all-days Thu->Fri minus others "
          f"{b_('dbasis_ON 2023-01-01 onward | all days | Thu->Fri minus others t'):.2f} -> {v('dbasis_ON 2023-01-01 onward | all days | Thu->Fri minus others t'):.2f}, "
          f"weekend {b_('dbasis_ON 2023-01-01 onward | all days | Fri->Mon (weekend) minus others t'):.2f} -> {v('dbasis_ON 2023-01-01 onward | all days | Fri->Mon (weekend) minus others t'):.2f}.", "",
          "## Summary",
          f"1. Missing: 15 trading days in VN30F1M.csv: 14 consecutive roll days 2022-11-18..2023-12-22 plus 2021-04-29; 30 nights affected (15 index nights without a futures bar, 15 contaminated futures nights).",
          "2. Validated source: yes. VCI contract tickers (close 100% vs VCI VN30F1M; all fields 100% from 2023) fill all 14 roll days; 13 are cross-confirmed by identical VN30F2M bars; "
          "2021-04-29 has no source and its night is excluded.",
          f"3. Moved (> 0.5 SE): 2023 index ON in the decomposition sample (11.08 -> 9.86 bp, discrepancy removed) and the 2023 offset fit (a, k). All-nights gross "
          f"{b_('all nights | gross mean bp'):.2f} -> {v('all nights | gross mean bp'):.2f} bp (Sharpe {b_('all nights | gross Sharpe'):.2f} -> {v('all nights | gross Sharpe'):.2f}) moved, but < 0.5 SE.",
          "4. Did not move: Monday and Mon+Tue (identical), Wednesday tables, W1/W2/O1 verdicts; the 2018-11-21 fix changes only 2018 / pooled / Tue->Wed cells (N 1,962 -> 1,963).",
          "5. Open: the same first-row pattern drops the first night in five other scripts (not changed); the 2022 contract-ticker O/H/L/volume differences vs the continuous feed are unexplained; "
          "the fallback 'excluded' variant (5.49 bp) and the repaired file (5.25 bp) differ because the repair adds 14 roll and 14 weekend nights back."]
    (OUT / "futures_roll_gap_audit.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
