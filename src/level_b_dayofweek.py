"""Level B follow-up: day-of-week overnight pattern across the 30 VN30 constituents (measurement only).

Nights are tagged by the weekday of the entry close; only ordinary one-day nights (next trading day
is 1 calendar day later) are used, same as the futures split. Filters (as Level B): drop
open_suspicious days and |overnight log return| > 7% (HOSE limit).

Pooled stats are given two ways: (a) naive stock-night pooling (t overstated, because stocks move
together on the same night) and (b) the equal-weighted cross-sectional mean per date, whose t-stat
and Sharpe are comparable to the futures figures.
"""
import sys
from pathlib import Path
import numpy as np, pandas as pd
from math import comb
sys.path.insert(0, str(Path(__file__).parent))
from level_a import RAW_DIR, OUT_DIR, decompose

NAMES = {0: "Mon->Tue", 1: "Tue->Wed", 2: "Wed->Thu", 3: "Thu->Fri"}
syms = (RAW_DIR.parent / "universe_vn30.txt").read_text().split()

def load(filtered=True):
    out = []
    for s in syms:
        d = decompose(pd.read_csv(RAW_DIR / f"{s}.csv", parse_dates=["date"]))
        d["gap_days"] = d["date"].diff().dt.days
        d["entry_wd"] = (d["date"].dt.weekday - d["gap_days"]) % 7
        d = d[d["gap_days"] == 1].copy()
        d["ticker"] = s
        d["flag"] = d["open_suspicious"].astype(bool) | (d["r_overnight"].abs() > 0.07)
        if filtered:
            d = d[~d["flag"]]
        out.append(d[["date", "ticker", "entry_wd", "r_overnight"]])
    return pd.concat(out, ignore_index=True)

def welch(a, b):
    return (a.mean() - b.mean()) / np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))

def binom_sf(k, n):  # P(X >= k), p = 0.5
    return sum(comb(n, i) for i in range(k, n + 1)) / 2 ** n

def tstat(x):
    return x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))

rows, per_stock = [], []
for filt in (True, False):
    p = load(filt)
    p = p[p["entry_wd"].isin(NAMES)]
    ew = p.groupby(["date"]).agg(r=("r_overnight", "mean"), wd=("entry_wd", "first"), k=("ticker", "size"))
    ew = ew[ew["k"] >= 10]                       # need a reasonable cross-section on the night
    years = (ew.index[-1] - ew.index[0]).days / 365.25
    label = "filtered" if filt else "unfiltered"
    for wd, nm in NAMES.items():
        a, b = p[p.entry_wd == wd]["r_overnight"], ew[ew.wd == wd]["r"]
        ppy = len(b) / years
        rows.append({"filter": label, "night": nm, "stock_nights": len(a), "dates": len(b),
                     "pooled_mean_bp": a.mean() * 1e4, "pooled_naive_t": tstat(a),
                     "ew_mean_bp": b.mean() * 1e4, "ew_sharpe_own_freq": b.mean() / b.std() * np.sqrt(ppy),
                     "ew_sharpe_per252": b.mean() / b.std() * np.sqrt(252), "ew_t": tstat(b),
                     "ew_hit_%": (b > 0).mean() * 100})
    mt, wt = ew[ew.wd.isin([0, 1])]["r"], ew[ew.wd.isin([2, 3])]["r"]
    diff = welch(mt, wt)
    rows.append({"filter": label, "night": "Mon+Tue", "dates": len(mt), "ew_mean_bp": mt.mean() * 1e4,
                 "ew_sharpe_own_freq": mt.mean() / mt.std() * np.sqrt(len(mt) / years), "ew_t": tstat(mt)})
    rows.append({"filter": label, "night": "Wed+Thu", "dates": len(wt), "ew_mean_bp": wt.mean() * 1e4,
                 "ew_sharpe_own_freq": wt.mean() / wt.std() * np.sqrt(len(wt) / years), "ew_t": tstat(wt)})
    rows.append({"filter": label, "night": "Mon+Tue minus Wed+Thu", "ew_mean_bp": (mt.mean() - wt.mean()) * 1e4,
                 "ew_t": diff})
    if filt:
        # per-stock
        for s, g in p.groupby("ticker"):
            m = g.groupby("entry_wd")["r_overnight"].mean().reindex(list(NAMES))
            mt_, wt_ = g[g.entry_wd.isin([0, 1])]["r_overnight"], g[g.entry_wd.isin([2, 3])]["r_overnight"]
            per_stock.append({"ticker": s, "n": len(g), **{f"{NAMES[k]}_bp": m[k] * 1e4 for k in NAMES},
                              "top_night": NAMES[int(m.idxmax())], "top_is_mon_or_tue": int(m.idxmax()) in (0, 1),
                              "monTue_minus_wedThu_bp": (mt_.mean() - wt_.mean()) * 1e4,
                              "diff_t": welch(mt_, wt_),
                              "rank_monTue_top2": sorted(m.rank(ascending=False)[[0, 1]].tolist()) == [1.0, 2.0]})
        # by year for the filtered EW series
        by = ew.assign(yr=ew.index.year, grp=np.where(ew.wd.isin([0, 1]), "MonTue", "WedThu"))
        print("EW overnight bp by year:\n", (by.pivot_table(index="yr", columns="grp", values="r", aggfunc="mean") * 1e4).round(2))
        for nm, cond in (("2018-2021", ew.index.year <= 2021), ("2022-2026", ew.index.year >= 2022)):
            e = ew[cond]
            m_, w_ = e[e.wd.isin([0, 1])]["r"], e[e.wd.isin([2, 3])]["r"]
            rows.append({"filter": f"filtered {nm}", "night": "Mon+Tue", "dates": len(m_), "ew_mean_bp": m_.mean() * 1e4, "ew_t": tstat(m_)})
            rows.append({"filter": f"filtered {nm}", "night": "Wed+Thu", "dates": len(w_), "ew_mean_bp": w_.mean() * 1e4, "ew_t": tstat(w_)})
            rows.append({"filter": f"filtered {nm}", "night": "Mon+Tue minus Wed+Thu",
                         "ew_mean_bp": (m_.mean() - w_.mean()) * 1e4, "ew_t": welch(m_, w_)})

t = pd.DataFrame(rows); t.to_csv(OUT_DIR / "level_b_dayofweek.csv", index=False)
ps = pd.DataFrame(per_stock); ps.to_csv(OUT_DIR / "level_b_dayofweek_by_stock.csv", index=False)
with pd.option_context("display.width", 250, "display.max_columns", 30, "display.float_format", "{:.2f}".format):
    print(t.to_string(index=False)); print(); print(ps.to_string(index=False))
k = int(ps["top_is_mon_or_tue"].sum()); n = len(ps)
print(f"\nStocks whose top night is Mon or Tue: {k}/{n} (chance = 50% -> {n/2:.0f}); binomial p(>=k) = {binom_sf(k, n):.3f}")
print("Top night counts:", ps["top_night"].value_counts().to_dict())
print(f"Mon+Tue mean > Wed+Thu mean in {(ps['monTue_minus_wedThu_bp']>0).sum()}/{n} stocks; individually t>1.5 in {(ps['diff_t']>1.5).sum()}; t<-1.5 in {(ps['diff_t']<-1.5).sum()}")
print("Mon+Tue are the top-2 nights in", int(ps['rank_monTue_top2'].sum()), "stocks")
