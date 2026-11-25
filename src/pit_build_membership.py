"""Build data/vn30_pit_membership.csv : one row per (effective_date, ticker).
Sources (column `source`): pdf (HOSE CBTT), mirror (KBSV copy of HOSE table, Jan 2020), csv (vn30_freefloat_history.csv,
2023+ quarterly snapshots), interp (membership from set algebra; shares/ff interpolated from bracketing references)."""
import re, sys
from pathlib import Path
import numpy as np, pandas as pd, pdfplumber
sys.path.insert(0, "src")
from pit_parse import shares as _sh

CSV = Path.home() / "Documents/vn30_scraper/data/vn30_freefloat_history.csv"
LOG = []
def log(m): LOG.append(m); print(m)

pdfs = pd.read_csv("data/raw_pdf/parsed_pdfs.csv")
pdfs["effective"] = pdfs.effective.astype(str)

# ---- KBSV mirror of HOSE Jan-2020 table (Bang 1) ----
rows = []
with pdfplumber.open("data/raw_pdf/p10/kbsv_jan2020.pdf") as p:
    txt = (p.pages[1].extract_text() or "")
for l in txt.split("\n"):
    m = re.match(r"^(\d{1,2}) ([A-Z]{3}) ([\d,]+) (\d+)% ([\d.]+)%$", l.strip())
    if m and int(m.group(1)) <= 30 and len(rows) < 30:
        rows.append(dict(ticker=m.group(2), shares=int(m.group(3).replace(",", "")), free_float=int(m.group(4)), cap_pct=float(m.group(5))))
mirror = pd.DataFrame(rows); mirror["effective"] = "2020-02-03"
assert len(mirror) == 30, len(mirror)

# ---- references for interpolation ----
allsh = pd.read_csv("data/raw_pdf/ref_allshare.csv").rename(columns={"ref_date": "date"})
refs = [allsh[["ticker", "date", "shares", "free_float"]].assign(kind="allshare")]
refs.append(pdfs.rename(columns={"effective": "date"})[["ticker", "date", "shares", "free_float"]].assign(kind="pdf"))
refs.append(mirror.rename(columns={"effective": "date"})[["ticker", "date", "shares", "free_float"]].assign(kind="mirror"))
csv = pd.read_csv(CSV)
def eff_of_snapshot(s):
    d = pd.Timestamp(s); m = {1: 2, 4: 5, 7: 8, 10: 11}[d.month]
    y = d.year; first = pd.Timestamp(y, m, 1)
    return (first + pd.offsets.Week(weekday=0)) if first.weekday() != 0 else first
csv["effective"] = csv.rebalance_date.map(eff_of_snapshot).dt.strftime("%Y-%m-%d")
refs.append(csv.rename(columns={"effective": "date", "shares_for_index": "shares", "free_float_pct": "free_float"})[["ticker", "date", "shares", "free_float"]].assign(kind="csv"))
R = pd.concat(refs); R["date"] = pd.to_datetime(R["date"])
R = R.sort_values(["ticker", "date"])

def ff_round(x):
    return float(round(x)) if x < 15 else float(5 * round(x / 5))
def interp(tk, d):
    r = R[R.ticker == tk].drop_duplicates("date", keep="last")
    if r.empty: return None
    t = r.date.map(pd.Timestamp.toordinal).values.astype(float); x = d.toordinal()
    return (float(np.interp(x, t, r.shares.values.astype(float))), ff_round(float(np.interp(x, t, r.free_float.values.astype(float)))))

# ---- membership chain ----
jan18 = set(pdfs[pdfs.period_key == 20180115].ticker)
chain = {}
chain["2018-01-22"] = jan18
chain["2018-07-23"] = (chain["2018-01-22"] - {"BID", "BVH", "NT2"}) | {"PNJ", "VPB", "VRE"}
chain["2019-02-11"] = (chain["2018-07-23"] - {"PLX", "KDC", "BMP", "HSG"}) | {"VHM", "TCB", "HDB", "EIB"}
chain["2019-08-05"] = (chain["2019-02-11"] - {"CII", "DHG"}) | {"BID", "BVH"}
chain["2020-02-03"] = (chain["2019-08-05"] - {"DPM", "GMD"}) | {"PLX", "POW"}
chain["2020-08-03"] = (chain["2020-02-03"] - {"CTD", "BVH"}) | {"KDH", "TCH"}
chain["2021-02-01"] = (chain["2020-08-03"] - {"SAB", "ROS", "EIB"}) | {"BVH", "TPB", "PDR"}
chain["2021-08-02"] = (chain["2021-02-01"] - {"REE", "SBT", "TCH"}) | {"ACB", "GVR", "SAB"}
p21 = set(pdfs[pdfs.period_key == 20210719].ticker); p22 = set(pdfs[pdfs.period_key == 20220718].ticker)
m20 = set(mirror.ticker)
for k, s in chain.items(): assert len(s) == 30, (k, len(s))
log(f"CLOSURE chain(Jul-2021) == Jul-2021 PDF: {chain['2021-08-02'] == p21}  | chain(Jan-2020) == KBSV mirror: {chain['2020-02-03'] == m20}")
assert chain["2021-08-02"] == p21 and chain["2020-02-03"] == m20
log(f"Jan-2022 (no source): Jul-2022 PDF - VIB + PNJ == Jul-2021 PDF: {(p22 - {'VIB'}) | {'PNJ'} == p21} -> Jan-2022 membership = Jul-2021 (confidence: inferred)")

out = []
NEWS_FF = {("2018-07-23", "PNJ"): 70, ("2018-07-23", "VPB"): 60, ("2018-07-23", "VRE"): 45}
def add(date, tk, sh, ff, cap, src, conf):
    out.append(dict(effective_date=date, ticker=tk, shares=int(round(sh)), free_float=ff, cap_published=cap, source=src, confidence=conf))
exact = {"2018-01-22": pdfs[pdfs.period_key == 20180115], "2020-02-03": mirror, "2021-08-02": pdfs[pdfs.period_key == 20210719],
         "2022-08-01": pdfs[pdfs.period_key == 20220718], "2023-02-06": pdfs[pdfs.period_key == 20230116],
         "2023-08-07": pdfs[pdfs.period_key == 20230717], "2024-02-05": pdfs[pdfs.period_key == 20240115],
         "2024-08-05": pdfs[pdfs.period_key == 20240715], "2025-02-03": pdfs[pdfs.period_key == 20250120]}
# quarterly schedule 2018-2022 (first Mondays of Feb/May/Aug/Nov) + semi-annual special dates
semi = {"2018-01-22", "2018-07-23", "2019-02-11", "2019-08-05", "2020-02-03", "2020-08-03", "2021-02-01", "2021-08-02", "2022-02-07", "2022-08-01"}
qdates = set(semi)
for y in range(2018, 2023):
    for m in (2, 5, 8, 11):
        f = pd.Timestamp(y, m, 1); f = f + pd.offsets.Week(weekday=0) if f.weekday() != 0 else f
        if pd.Timestamp("2018-01-22") < f < pd.Timestamp("2022-12-01"): qdates.add(f.strftime("%Y-%m-%d"))
qdates = sorted(qdates)
# drop first-Monday dates that sit within 5 days of a special semi date (they ARE that date)
keep = []
for d in qdates:
    if d in semi or all(abs((pd.Timestamp(d) - pd.Timestamp(s)).days) > 6 for s in semi): keep.append(d)
qdates = keep
def membership_on(d):
    ks = [k for k in chain if k <= d]; ks.append("2022-02-07") if False else None
    if d >= "2022-02-07": return p21  # Jan-2022 review: no net change; replaced by Jul-2022 PDF from 2022-08-01
    return chain[max(ks)]
for d in qdates:
    if d >= "2022-08-01": continue
    mem = membership_on(d)
    ex = exact.get(d)
    for tk in sorted(mem):
        if ex is not None and tk in set(ex.ticker):
            r = ex[ex.ticker == tk].iloc[0]
            add(d, tk, r.shares, r.free_float, r.cap_pct, "pdf" if d != "2020-02-03" else "mirror", "high")
        else:
            sf = interp(tk, pd.Timestamp(d))
            ff = NEWS_FF.get((d, tk), sf[1])
            add(d, tk, sf[0], ff, np.nan, "interp", "low" if (d in semi) else "low")
# 2022-08-01 .. 2022-11 from PDF then CSV-based quarterly + PDFs
for d in sorted(set(csv.effective) | {"2022-08-01", "2022-11-07"}):
    if d in ("2022-08-01",):
        for _, r in exact[d].iterrows(): add(d, r.ticker, r.shares, r.free_float, r.cap_pct, "pdf", "high")
    elif d == "2022-11-07":
        for _, r in exact["2022-08-01"].iterrows():
            sf = interp(r.ticker, pd.Timestamp(d)); add(d, r.ticker, sf[0], sf[1], np.nan, "interp", "medium")
    else:
        if d in exact:
            for _, r in exact[d].iterrows(): add(d, r.ticker, r.shares, r.free_float, r.cap_pct, "pdf", "high")
        else:
            for _, r in csv[csv.effective == d].iterrows(): add(d, r.ticker, r.shares_for_index, r.free_float_pct, np.nan, "csv", "high")
M = pd.DataFrame(out).sort_values(["effective_date", "ticker"])
# reconcile PDFs vs CSV on overlap (log mismatches)
for d, ex in exact.items():
    c = csv[csv.effective == d]
    if c.empty: continue
    j = ex.set_index("ticker").join(c.set_index("ticker"), how="outer", rsuffix="_c")
    mm = j[(j.shares != j.shares_for_index) | (j.free_float != j.free_float_pct)]
    log(f"RECONCILE {d}: PDF vs CSV rows={len(j)} membership_diff={int(j.shares.isna().sum()+j.shares_for_index.isna().sum())} value_mismatch={len(mm)}")
    for tk, r in mm.iterrows(): log(f"   {tk}: pdf shares={r.shares:.0f}/ff={r.free_float:.0f} csv shares={r.shares_for_index:.0f}/ff={r.free_float_pct:.0f}")
cnt = M.groupby("effective_date").ticker.count()
assert (cnt == 30).all(), cnt[cnt != 30]
M.to_csv("data/vn30_pit_membership.csv", index=False)
log(f"wrote data/vn30_pit_membership.csv: {len(M)} rows, {M.effective_date.nunique()} effective dates, sources {M.source.value_counts().to_dict()}")
Path("results/pit_build_log.txt").write_text("\n".join(LOG))
