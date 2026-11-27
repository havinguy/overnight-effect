"""Composition diagnostics: VN30 tenure of the 30 current members and day-of-week overnight split by tenure.
Membership comes only from vn30_freefloat_history.csv (15 quarterly snapshots, 2023-01..2026-07)."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).parent))
from level_a import RAW_DIR, OUT_DIR, decompose

MEM = Path.home() / "Documents/vn30_scraper/data/vn30_freefloat_history.csv"
NAMES = {0: "Mon->Tue", 1: "Tue->Wed", 2: "Wed->Thu", 3: "Thu->Fri"}
syms = (RAW_DIR.parent / "universe_vn30.txt").read_text().split()

m = pd.read_csv(MEM, parse_dates=["rebalance_date"])
m = m[m.in_main_30 == 1]
quarters = sorted(m.rebalance_date.unique()); nq = len(quarters)
qlabel = lambda t: f"{pd.Timestamp(t).year}Q{(pd.Timestamp(t).month - 1) // 3 + 1}"
rows = []
for s in syms:
    q = sorted(m[m.ticker == s].rebalance_date)
    present = len(q)
    contiguous = present > 0 and (quarters.index(q[-1]) - quarters.index(q[0]) + 1 == present)
    rows.append({"ticker": s, "first_vn30_quarter": qlabel(q[0]) if q else "", "last_vn30_quarter": qlabel(q[-1]) if q else "",
                 "quarters_present": present, "quarters_total": nq, "full_tenure": present == nq,
                 "pct_present": present / nq * 100, "contiguous": contiguous})
ten = pd.DataFrame(rows)
ten["group"] = np.where(ten.pct_present >= 75, "long_tenure", "recent_joiner")
print(f"Membership file covers {qlabel(quarters[0])}..{qlabel(quarters[-1])} ({nq} snapshots); nothing before 2023 is in it.\n")
print(ten.sort_values(["quarters_present", "ticker"]).to_string(index=False))
print(f"\nFull tenure over the {nq} quarters: {int(ten.full_tenure.sum())}/30; >=75%: {(ten.group=='long_tenure').sum()}/30")
gone = sorted(set(m.ticker) - set(syms))
print("Members in the file that are NOT in the current 30 (removed during 2023-26):", gone)
ten.to_csv(OUT_DIR / "composition_tenure.csv", index=False)

# ---------- diagnostic 2 ----------
frames = []
for s in syms:
    # 2018-11-21 first-night fix (2026-11-27): gap / prior close taken from the RAW series BEFORE decompose() drops row 0
    raw = pd.read_csv(RAW_DIR / f"{s}.csv", parse_dates=["date"]).sort_values("date").reset_index(drop=True)
    raw["gap"] = raw["date"].diff().dt.days
    d = decompose(raw)
    d["wd"] = (d["date"].dt.weekday - d["gap"]) % 7
    d = d[d.gap == 1]
    d = d[~(d["open_suspicious"].astype(bool) | (d["r_overnight"].abs() > 0.07))]
    d = d[d.wd.isin(NAMES)]
    d["ticker"] = s
    frames.append(d[["date", "ticker", "wd", "r_overnight"]])
p = pd.concat(frames).merge(ten[["ticker", "group"]], on="ticker")

def tstat(x): return x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))
def panel(p, label, min_k=3):
    out = []
    for g, gg in p.groupby("group"):
        ew = gg.groupby("date").agg(r=("r_overnight", "mean"), wd=("wd", "first"), k=("ticker", "size"))
        ew = ew[ew.k >= min_k]
        yrs = (ew.index[-1] - ew.index[0]).days / 365.25
        res = {}
        for wd, nm in NAMES.items():
            b = ew[ew.wd == wd]["r"]
            out.append({"sample": label, "group": g, "night": nm, "dates": len(b), "mean_bp": b.mean() * 1e4,
                        "sharpe_own_freq": b.mean() / b.std() * np.sqrt(len(b) / yrs), "t": tstat(b), "hit_%": (b > 0).mean() * 100})
            res[wd] = b
        mt, wt = pd.concat([res[0], res[1]]), pd.concat([res[2], res[3]])
        out.append({"sample": label, "group": g, "night": "Mon+Tue minus Wed+Thu", "mean_bp": (mt.mean() - wt.mean()) * 1e4,
                    "t": (mt.mean() - wt.mean()) / np.sqrt(mt.var() / len(mt) + wt.var() / len(wt))})
    return out
rows = panel(p, "all dates")
# same dates for both groups: restrict to nights on which the recent group has >=3 stocks
rec_dates = p[p.group == "recent_joiner"].groupby("date").size()
rec_dates = rec_dates[rec_dates >= 3].index
rows += panel(p[p.date.isin(rec_dates)], "matched dates (recent_joiner has >=3 stocks)")
rows += panel(p[p.date >= "2023-01-01"], "2023-2026 only")
res = pd.DataFrame(rows); res.to_csv(OUT_DIR / "composition_diagnostic.csv", index=False)
print("\n", ten.groupby("group").ticker.apply(lambda x: " ".join(x)).to_string())
with pd.option_context("display.width", 250, "display.float_format", "{:.2f}".format):
    for lab in res["sample"].unique():
        r = res[res["sample"] == lab]
        print(f"\n== {lab} ==")
        print(r.drop(columns="sample").pivot(index="night", columns="group", values=["dates", "mean_bp", "sharpe_own_freq", "t", "hit_%"])
              .reindex(list(NAMES.values()) + ["Mon+Tue minus Wed+Thu"]).to_string())
