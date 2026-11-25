"""Plot the 2022 relocation: overnight/intraday/close-to-close legs of the
point-in-time VN30 basket, before vs after the 2022-08-25 cutover.
Reads results/regime_legs_breaks.csv (already produced by the regime audit)
and writes results/regime_relocation.png. Pure re-plot of existing numbers.
"""
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

df = pd.read_csv("results/regime_legs_breaks.csv")
rows = {r["series"]: r for _, r in df.iterrows()}
legs = [("basket ON", "Overnight\n(close -> open)"),
        ("basket ID", "Intraday\n(open -> close)"),
        ("basket C2C", "Close-to-close\n(the full day)")]

pre = [rows[k]["pre_bp"] for k, _ in legs]
post = [rows[k]["post_bp"] for k, _ in legs]
labels = [lbl for _, lbl in legs]

x = np.arange(len(legs))
w = 0.38
fig, ax = plt.subplots(figsize=(9, 5.2))
b1 = ax.bar(x - w/2, pre, w, label="Before 2022-08-25", color="#9a9a9a")
b2 = ax.bar(x + w/2, post, w, label="After 2022-08-25", color="#1f77b4")
ax.axhline(0, color="black", lw=0.8)
ax.set_xticks(x)
ax.set_xticklabels(labels)
ax.set_ylabel("Mean return (bp per night / day)")
ax.set_title("The 2022 relocation: return moves from the intraday leg to the overnight leg\n(point-in-time VN30 basket, cap-weighted)")
ax.legend(frameon=False)
for bars in (b1, b2):
    for rect in bars:
        h = rect.get_height()
        ax.annotate(f"{h:.1f}", (rect.get_x() + rect.get_width()/2, h),
                    ha="center", va="bottom" if h >= 0 else "top",
                    fontsize=9, xytext=(0, 3 if h >= 0 else -3),
                    textcoords="offset points")
plt.tight_layout()
plt.savefig("results/regime_relocation.png", dpi=150)
print("wrote results/regime_relocation.png")
