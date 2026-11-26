"""
PRE-REGISTERED (2026-11-26) -- relocation-mechanism cross-section ("why 2022").
Question: does the 2022-08-25 overnight relocation concentrate in stocks more
exposed to retail / short-horizon trading (consistent with the T+2 afternoon-sale
rule), or is it uniform across stocks (a market-wide cause)?
Hypothesis H (settlement-behaviour): the per-stock OVERNIGHT break (post-minus-pre
mean overnight return around D=2022-08-25) is LARGER for LOWER-liquidity (lower avg
daily traded value), HIGHER-turnover, LOWER-price names.
Decision rule: cross-sectional OLS slope of the overnight break on log(ADV).
  slope significantly NEGATIVE (|t|>=2): supports settlement-behaviour mechanism
    (relocation bigger where liquidity is lower / retail share plausibly higher).
  slope ~ 0 (|t|<2): relocation is uniform across liquidity -> points to a
    market-wide cause, not stock-level settlement behaviour; H NOT supported.
Caveats: OHLCV has no retail/institutional split; ADV/turnover/price are LIQUIDITY
proxies, not retail share. N~30 -> low power; read as suggestive, not decisive.
Window: +/-365 calendar days around D. Unfiltered nights (treatment P).
"""
import os
import numpy as np, pandas as pd

D   = pd.Timestamp("2022-08-25")
LO, HI = D - pd.Timedelta(days=365), D + pd.Timedelta(days=365)
MINN = 60
SKIP = {"VN30","VN30F1M","VN30F1M_repaired","VN30F2M","VNINDEX"}
BP = 1e4

mem = pd.read_csv("data/vn30_pit_membership.csv", parse_dates=["effective_date"])
snap_date = mem.loc[mem.effective_date <= D, "effective_date"].max()
snap = mem[mem.effective_date == snap_date].drop_duplicates("ticker").set_index("ticker")
members = [t for t in snap.index if t not in SKIP and os.path.exists(f"data/raw/{t}.csv")]

rows = []
for t in members:
    d = pd.read_csv(f"data/raw/{t}.csv", parse_dates=["date"]).sort_values("date")
    d["on"] = np.log(d.open) - np.log(d.close.shift(1))
    d["id"] = np.log(d.close) - np.log(d.open)
    d["c2c"] = d["on"] + d["id"]
    w = d[(d.date >= LO) & (d.date <= HI)].copy()
    pre, post = w[w.date < D], w[w.date >= D]
    if pre["on"].notna().sum() < MINN or post["on"].notna().sum() < MINN:
        continue
    adv = float((pre.close * pre.volume).mean())            # avg daily traded value (VND)
    sh  = float(snap.loc[t, "shares"]) if "shares" in snap.columns else np.nan
    rows.append(dict(
        ticker=t,
        on_break = (post["on"].mean() - pre["on"].mean())*BP,
        id_break = (post["id"].mean() - pre["id"].mean())*BP,
        c2c_break= (post["c2c"].mean()- pre["c2c"].mean())*BP,
        adv=adv, log_adv=np.log(adv),
        price=float(pre.close.mean()),
        turnover=float(pre.volume.mean()/sh) if sh and not np.isnan(sh) else np.nan,
        n_pre=int(pre["on"].notna().sum()), n_post=int(post["on"].notna().sum()),
    ))
df = pd.DataFrame(rows).sort_values("adv")

def ols_t(x, y):
    x = np.asarray(x, float); y = np.asarray(y, float)
    m = np.isfinite(x) & np.isfinite(y); x, y = x[m], y[m]
    n = len(x)
    b1, b0 = np.polyfit(x, y, 1)
    yhat = b0 + b1*x
    s2 = np.sum((y-yhat)**2)/(n-2)
    se = np.sqrt(s2/np.sum((x-x.mean())**2))
    return b1, b1/se, n

def spearman(x, y):
    x = pd.Series(np.asarray(x, float)); y = pd.Series(np.asarray(y, float))
    m = x.notna() & y.notna()
    return float(np.corrcoef(x[m].rank(), y[m].rank())[0, 1])

out = []
out.append(f"# Relocation-mechanism cross-section (why 2022), pre-registered  D={D.date()}")
out.append(f"Members as of {snap_date.date()} snapshot; {len(df)} stocks with >= {MINN} nights each side; window +/-365d.\n")
out.append(f"Pooled mean overnight break: {df.on_break.mean():.2f} bp  (sanity vs basket ~ +13-14 bp)")
out.append(f"Pooled mean intraday  break: {df.id_break.mean():.2f} bp")
out.append(f"Pooled mean C2C       break: {df.c2c_break.mean():.2f} bp  (relocation => ~0)\n")
for proxy, lbl in [("log_adv","log(ADV) liquidity"),("price","price"),("turnover","turnover")]:
    if df[proxy].notna().sum() < 10: 
        out.append(f"{lbl}: too few values"); continue
    b, tt, n = ols_t(df[proxy], df.on_break)
    sp = spearman(df[proxy], df.on_break)
    out.append(f"ON break on {lbl}:  OLS slope {b:+.3f} bp/unit (t {tt:+.2f}, n {n}); Spearman {sp:+.2f}")
# terciles by ADV
df["adv_group"] = pd.qcut(df.adv, 3, labels=["low-liq","mid","high-liq"])
g = df.groupby("adv_group", observed=True)[["on_break","id_break","c2c_break"]].mean()
out.append("\nMean break by ADV tercile (bp):")
out.append(g.round(2).to_string())
# id break vs liquidity too
b, tt, n = ols_t(df.log_adv, df.id_break)
out.append(f"\nID break on log(ADV): OLS slope {b:+.3f} (t {tt:+.2f})")

txt = "\n".join(out)
print(txt)
df.to_csv("results/relocation_mechanism.csv", index=False)
open("results/relocation_mechanism.md","w").write(txt+"\n")
