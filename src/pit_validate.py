"""Step 3 validation: reconstructed vs published VN30 daily returns / level; by period and by data-source quality."""
import sys; sys.path.insert(0, "src")
import numpy as np, pandas as pd, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
import pit_reconstruct as P
res = P.main()
M = pd.read_csv("data/vn30_pit_membership.csv", parse_dates=["effective_date"])
src = M.groupby("effective_date").source.agg(lambda s: s.mode()[0])
rows = []
def stats(R, label, var):
    R = R.dropna(subset=["rec", "pub"]); e = R.rec - R.pub
    return dict(variant=var, slice=label, n=len(R), corr=R.rec.corr(R.pub), mae_bp=e.abs().mean() * 1e4, rmse_bp=np.sqrt((e**2).mean()) * 1e4,
                bias_bp=e.mean() * 1e4, ann_te_pct=e.std() * np.sqrt(252) * 100)
for var, R in res.items():
    R = R.copy(); R["eff"] = pd.to_datetime(R.basket); R["src"] = R.eff.map(src)
    R["exact"] = np.where(R.src.isin(["pdf", "mirror", "csv"]), "exact (pdf/mirror/csv)", "fallback (interp)")
    R["year"] = R.index.year
    rows.append(stats(R, "ALL", var))
    for k, g in R.groupby("exact"): rows.append(stats(g, k, var))
    for k, g in R.groupby("year"): rows.append(stats(g, f"year {k}", var))
    # semi-annual membership window
    sa = pd.cut(R.index, bins=[pd.Timestamp(x) for x in ["2018-01-01", "2019-02-11", "2019-08-05", "2020-02-03", "2020-08-03", "2021-02-01", "2021-08-02", "2022-02-07", "2022-08-01", "2023-02-06", "2024-02-05", "2025-02-03", "2026-02-02", "2027-01-01"]], right=False)
    for k, g in R.groupby(sa, observed=True): rows.append(stats(g, f"window {k.left.date()}", var))
    R.to_csv(f"results/_recon_{var}.csv")
V = pd.DataFrame(rows); V.to_csv("results/vn30_tracking_validation.csv", index=False)
pd.set_option("display.width", 200)
print(V[V.slice.isin(["ALL", "exact (pdf/mirror/csv)", "fallback (interp)"])].round(4).to_string(index=False))
print(V[V.slice.str.startswith("year")].pivot(index="slice", columns="variant", values=["corr", "mae_bp"]).round(4))
print(V[V.slice.str.startswith("window")].pivot(index="slice", columns="variant", values=["n", "corr", "mae_bp", "bias_bp"]).round(3).to_string())
# level overlay
pub = P.load_close()["VN30"].dropna()
fig, ax = plt.subplots(2, 1, figsize=(11, 7), sharex=True, gridspec_kw={"height_ratios": [3, 1.2]})
base = pub.loc[res["A_pit_shares"].index[0]]
ax[0].plot(pub.index, pub / pub.iloc[0] * 100 if False else pub / pub.loc[res["A_pit_shares"].index[0]] * 100, "k", lw=1.6, label="published VN30")
for var, col in [("A_pit_shares", "tab:blue"), ("B_latest_shares", "tab:orange")]:
    R = res[var]; lv = (1 + R.rec.fillna(0)).cumprod() * 100
    ax[0].plot(lv.index, lv, color=col, lw=1, label=f"reconstructed ({var})")
    d = (np.log(lv) - np.log(pub.reindex(lv.index) / pub.loc[R.index[0]] * 100)) * 100
    ax[1].plot(d.index, d, color=col, lw=1)
ax[0].set_ylabel("level (rebased 100)"); ax[0].legend(); ax[0].set_title("Reconstructed vs published VN30 (price index, rebased at first return date)")
ax[1].axhline(0, color="gray", lw=.6); ax[1].set_ylabel("log gap (%)")
for x in ["2019-02-11", "2019-08-05", "2020-02-03", "2020-08-03", "2021-02-01", "2021-08-02", "2022-08-01", "2023-02-06"]: ax[1].axvline(pd.Timestamp(x), color="gray", lw=.4, ls=":")
plt.tight_layout(); plt.savefig("results/vn30_tracking_level_overlay.png", dpi=130)
for var, R in res.items():
    e = (R.rec - R.pub).dropna(); top = e.abs().sort_values(ascending=False).head(8)
    print(var, "worst days (bp):", {str(k.date()): round(e[k] * 1e4, 1) for k in top.index})
