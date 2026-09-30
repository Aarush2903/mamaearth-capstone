"""
Mamaearth Returns & Growth Intelligence Pipeline
Part 2 / Task 11 -- Visualizations

Must be run AFTER analysis/clean_and_eda.py, which writes the two small
intermediate CSVs this script reads (analysis/_return_rate_by_payment.csv
and analysis/_monthly_corrected.csv) so the numbers plotted here can never
drift from the numbers computed and asserted in clean_and_eda.py.

Run with:  python analysis/clean_and_eda.py   (first)
           python analysis/visualize.py       (then)
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ANALYSIS_DIR = os.path.dirname(__file__)
VIS_DIR = os.path.join(ANALYSIS_DIR, "..", "visualizations")
os.makedirs(VIS_DIR, exist_ok=True)

RETURN_RATE_CSV = os.path.join(ANALYSIS_DIR, "_return_rate_by_payment.csv")
MONTHLY_CSV = os.path.join(ANALYSIS_DIR, "_monthly_corrected.csv")

if not (os.path.exists(RETURN_RATE_CSV) and os.path.exists(MONTHLY_CSV)):
    raise SystemExit(
        "Missing intermediate files. Run `python analysis/clean_and_eda.py` first -- "
        "it writes the numbers this script plots."
    )


# ------------------------------------------------------------------
# Chart 1 -- return_rate_by_payment.png
# ------------------------------------------------------------------
rr = pd.read_csv(RETURN_RATE_CSV, index_col=0)["return_rate_pct"].sort_values(ascending=False)

fig, ax = plt.subplots(figsize=(7, 5))
colors = ["#d62728" if pm == "COD" else "#4c72b0" for pm in rr.index]
bars = ax.bar(rr.index, rr.values, color=colors)

for bar, val in zip(bars, rr.values):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.8,
             f"{val:.1f}%", ha="center", va="bottom", fontweight="bold")

cod_rate = rr.get("COD")
card_rate = rr.get("CARD")
multiplier = round(cod_rate / card_rate, 1) if card_rate else None
title = f"COD Returns at {cod_rate:.1f}% -- {multiplier}x Card" if multiplier else "Return Rate by Payment Method"
ax.set_title(title, fontsize=13, fontweight="bold")
ax.set_xlabel("Payment Method")
ax.set_ylabel("Return Rate (%)")
ax.set_ylim(0, max(rr.values) * 1.25)
fig.tight_layout()
out1 = os.path.join(VIS_DIR, "return_rate_by_payment.png")
fig.savefig(out1, dpi=150)
plt.close(fig)
print(f"Saved {out1}")


# ------------------------------------------------------------------
# Chart 2 -- monthly_revenue_trend.png (outlier-corrected)
# ------------------------------------------------------------------
monthly = pd.read_csv(MONTHLY_CSV, index_col=0)["order_value"]

peak_month = monthly.idxmax()
peak_value = monthly[peak_month]

fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(monthly.index, monthly.values, marker="o", linewidth=2, color="#4c72b0")
peak_idx = list(monthly.index).index(peak_month)
ax.scatter([peak_month], [peak_value], color="#d62728", zorder=5, s=80)
ax.annotate(f"Peak: {peak_value:,.0f}", (peak_month, peak_value),
            textcoords="offset points", xytext=(0, 14), ha="center", fontweight="bold")

ax.set_title(f"Monthly Revenue (Outlier-Corrected) -- {peak_month} is the Real Peak", fontsize=13, fontweight="bold")
ax.set_xlabel("Month")
ax.set_ylabel("Revenue (INR)")
ax.set_ylim(top=max(monthly.values) * 1.15)
ax.grid(axis="y", linestyle="--", alpha=0.4)
fig.tight_layout()
out2 = os.path.join(VIS_DIR, "monthly_revenue_trend.png")
fig.savefig(out2, dpi=150)
plt.close(fig)
print(f"Saved {out2}")
