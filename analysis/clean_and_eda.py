"""
Mamaearth Returns & Growth Intelligence Pipeline
Part 2 -- Python/Pandas Data Wrangling & EDA

Runs directly against the raw source CSVs in data/ -- independent of
the SQL layer in Part 1, so this script and Part 1 can be run in
either order and still agree on every number.

Run with:  python analysis/clean_and_eda.py
Re-running regenerates identical numbers and writes narrator/findings.json
every time, from the raw CSVs, with no manual edits to any output.
"""

import json
import os

import numpy as np
import pandas as pd

pd.set_option("display.width", 100)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
NARRATOR_DIR = os.path.join(os.path.dirname(__file__), "..", "narrator")


def section(title):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


# ------------------------------------------------------------------
# Task 1 -- Load and inspect
# ------------------------------------------------------------------
section("TASK 1 -- Load and inspect")

orders = pd.read_csv(os.path.join(DATA_DIR, "orders.csv"))
customers = pd.read_csv(os.path.join(DATA_DIR, "customers.csv"))
products = pd.read_csv(os.path.join(DATA_DIR, "products.csv"))

print("orders.shape (before any cleaning):", orders.shape)
assert orders.shape == (180, 9), "Expected raw orders shape (180, 9)"
print("customers.shape:", customers.shape)
print("products.shape:", products.shape)


# ------------------------------------------------------------------
# Task 2 -- Standardize payment_method casing
# ------------------------------------------------------------------
section("TASK 2 -- Standardize payment_method casing")

raw_values = sorted(orders["payment_method"].unique())
print(f"Raw distinct values ({len(raw_values)}):", raw_values)
assert len(raw_values) == 7, "Expected 7 distinct raw payment_method values"

orders["payment_method"] = orders["payment_method"].str.strip().str.upper()

clean_values = sorted(orders["payment_method"].unique())
print(f"Cleaned distinct values ({len(clean_values)}):", clean_values)
assert len(clean_values) == 3, "Expected 3 distinct cleaned payment_method values"

pm_counts = orders["payment_method"].value_counts()
print("Counts after cleaning:\n", pm_counts)
assert pm_counts["CARD"] == 70 and pm_counts["UPI"] == 55 and pm_counts["COD"] == 55


# ------------------------------------------------------------------
# Task 3 -- Remove duplicate orders
# ------------------------------------------------------------------
section("TASK 3 -- Remove duplicate orders")

NATURAL_KEY = [
    "customer_id", "product_id", "order_date", "quantity",
    "discount_pct", "payment_method", "rating", "returned",
]  # everything except order_id, which differs on the duplicated rows by design

dupe_mask = orders.duplicated(subset=NATURAL_KEY, keep="first")
dropped_ids = orders.loc[dupe_mask, "order_id"].tolist()
print("Number of duplicate rows flagged:", dupe_mask.sum())
print("Dropped order_id values:", dropped_ids)
assert dupe_mask.sum() == 5
assert dropped_ids == ["O0176", "O0177", "O0178", "O0179", "O0180"]

# Keep the dropped rows around only long enough to prove the Task 5 delta
dropped_rows = orders.loc[dupe_mask].copy()

orders_clean = orders.loc[~dupe_mask].reset_index(drop=True)
print("orders_clean.shape after dedup:", orders_clean.shape)
assert orders_clean.shape == (175, 9)


# ------------------------------------------------------------------
# Task 4 -- Impute missing values
# ------------------------------------------------------------------
section("TASK 4 -- Impute missing values")

disc_missing = orders_clean["discount_pct"].isnull().sum()
print("discount_pct missing rows (on deduplicated frame):", disc_missing)
assert disc_missing == 12
orders_clean["discount_pct"] = orders_clean["discount_pct"].fillna(0)  # business rule: no promo applied

rating_missing = orders_clean["rating"].isnull().sum()
rating_median = orders_clean["rating"].median()
print("rating missing rows (on deduplicated frame):", rating_missing)
print("rating median (computed before imputing):", rating_median)
assert rating_missing == 15
assert rating_median == 3.0
orders_clean["rating"] = orders_clean["rating"].fillna(rating_median)

null_check = orders_clean[["discount_pct", "rating"]].isnull().sum()
print("Null check after imputing:\n", null_check)
assert null_check["discount_pct"] == 0 and null_check["rating"] == 0


# ------------------------------------------------------------------
# Task 5 -- Merge and reconcile against Part 1
# ------------------------------------------------------------------
section("TASK 5 -- Merge and reconcile against Part 1")

merged = orders_clean.merge(products, on="product_id").merge(customers, on="customer_id")
merged["order_value"] = merged["quantity"] * merged["price"] * (1 - merged["discount_pct"] / 100)

total_clean_revenue = round(merged["order_value"].sum(), 2)
print(f"Total order_value across {len(merged)} cleaned rows: {total_clean_revenue:,.2f}")
assert total_clean_revenue == 97358.30

RAW_TOTAL_FROM_PART1 = 99860.20
delta = round(RAW_TOTAL_FROM_PART1 - total_clean_revenue, 2)
print(f"Part 1 raw total_revenue: {RAW_TOTAL_FROM_PART1:,.2f}")
print(f"Delta vs Part 1 raw total: {delta:,.2f}")
assert delta == 2501.90

# Independent check: sum order_value of the 5 dropped rows on their own
dropped_merged = dropped_rows.merge(products, on="product_id").merge(customers, on="customer_id")
dropped_merged["order_value"] = (
    dropped_merged["quantity"] * dropped_merged["price"]
    * (1 - dropped_merged["discount_pct"].fillna(0) / 100)
)
dropped_total = round(dropped_merged["order_value"].sum(), 2)
print(f"Independent check -- combined order_value of the 5 dropped duplicate rows: {dropped_total:,.2f}")
assert dropped_total == delta

print(
    "\nRECONCILIATION NOTE: The cleaned pipeline's total revenue of Rs "
    f"{total_clean_revenue:,.2f} is exactly Rs {delta:,.2f} lower than Part 1's raw "
    f"total_revenue of Rs {RAW_TOTAL_FROM_PART1:,.2f}. This entire gap is attributable "
    "to the 5 duplicate order rows (O0176-O0180) removed in Task 3 -- their own "
    f"combined order_value, summed independently above, is Rs {dropped_total:,.2f}, "
    "which matches the delta exactly. The Task 4 imputation of discount_pct and "
    "rating does NOT change this delta at all: filling missing discount_pct with 0 "
    "and missing rating with the median only affects rows that were already present "
    "after deduplication, and rating never enters the order_value formula in the "
    "first place. So the full Rs 2,501.90 gap is a duplicate-removal effect, not an "
    "imputation effect."
)


# ------------------------------------------------------------------
# Task 6 -- IQR outlier detection on quantity
# ------------------------------------------------------------------
section("TASK 6 -- IQR outlier detection on quantity")

Q1 = merged["quantity"].quantile(0.25)
Q3 = merged["quantity"].quantile(0.75)
IQR = Q3 - Q1
lower_bound = Q1 - 1.5 * IQR
upper_bound = Q3 + 1.5 * IQR
print(f"Q1={Q1}, Q3={Q3}, IQR={IQR}, lower={lower_bound}, upper={upper_bound}")
assert (Q1, Q3, IQR, lower_bound, upper_bound) == (1.0, 2.0, 1.0, -0.5, 3.5)

merged["is_outlier"] = (merged["quantity"] < lower_bound) | (merged["quantity"] > upper_bound)
outliers = merged.loc[merged["is_outlier"], ["order_id", "quantity", "order_date"]]
print("Outlier rows (flagged, NOT dropped):\n", outliers)
assert set(outliers["order_id"]) == {"O0011", "O0098"}
assert len(outliers) == 2


# ------------------------------------------------------------------
# Task 7 -- Hypothesis: does COD have a higher return rate?
# ------------------------------------------------------------------
section("TASK 7 -- Hypothesis: COD has a higher return rate than Card/UPI")

print("H0: return rate is roughly equal across payment methods.")
print("H1: COD orders return at a materially higher rate than Card/UPI.")

pm_stats = merged.groupby("payment_method")["returned"].agg(["count", "mean"])
pm_stats["return_rate_pct"] = (pm_stats["mean"] * 100).round(1)
print(pm_stats)

cod_rate = pm_stats.loc["COD", "return_rate_pct"]
card_rate = pm_stats.loc["CARD", "return_rate_pct"]
upi_rate = pm_stats.loc["UPI", "return_rate_pct"]
assert card_rate == 14.7 and cod_rate == 44.4 and upi_rate == 18.9

print(
    f"\nHypothesis: CONFIRMED. COD return rate ({cod_rate}%) is roughly 3x Card's "
    f"({card_rate}%) and well above UPI's ({upi_rate}%)."
)


# ------------------------------------------------------------------
# Task 8 -- Multi-level segmentation
# ------------------------------------------------------------------
section("TASK 8 -- Multi-level segmentation (payment_method x city_tier)")

seg = merged.groupby(["payment_method", "city_tier"])["returned"].agg(["count", "mean"])
seg["return_rate_pct"] = (seg["mean"] * 100).round(1)
print(seg)

cod_t1 = seg.loc[("COD", 1), "return_rate_pct"]
cod_t1_n = int(seg.loc[("COD", 1), "count"])
cod_t2 = seg.loc[("COD", 2), "return_rate_pct"]
cod_t2_n = int(seg.loc[("COD", 2), "count"])
assert cod_t2 == 54.5 and cod_t1 == 37.5

print(
    f"\nHIGHEST-RISK SEGMENT: COD + Tier-2 cities at {cod_t2}% "
    f"({cod_t2_n} orders) -- vs {cod_t1_n} Tier-1 COD orders at {cod_t1}%. "
    "COD risk is NOT uniform across tiers: the blended 44.4% COD rate from Task 7 "
    "hides that the real problem is concentrated in Tier-2 cities."
)


# ------------------------------------------------------------------
# Task 9 -- Correlation analysis
# ------------------------------------------------------------------
section("TASK 9 -- Correlation analysis")

corr = merged[["rating", "returned", "discount_pct", "quantity"]].corr().round(3)
print(corr)


def band(r):
    a = abs(r)
    if a < 0.2:
        return "negligible"
    elif a < 0.4:
        return "weak"
    elif a < 0.7:
        return "moderate"
    else:
        return "strong"


print("\nPairwise strength bands (0-0.19 negligible / 0.2-0.39 weak / 0.4-0.69 moderate / 0.7-1.0 strong):")
pairs = [("rating", "returned"), ("rating", "discount_pct"), ("rating", "quantity"),
         ("returned", "discount_pct"), ("returned", "quantity"), ("discount_pct", "quantity")]
for a, b in pairs:
    r = corr.loc[a, b]
    print(f"  {a} vs {b}: r = {r:+.3f} -> {band(r)}")
    assert band(r) == "negligible"

discount_returned_r = corr.loc["discount_pct", "returned"]
print(
    f"\nHypothesis 'higher discounts reduce returns': BUSTED. "
    f"discount_pct vs returned correlation is r = {discount_returned_r:+.3f}, "
    "negligible in both size and (weak negative, not the strong negative the "
    "hypothesis would need) direction."
)


# ------------------------------------------------------------------
# Task 10 -- Outlier-corrected time series
# ------------------------------------------------------------------
section("TASK 10 -- Outlier-corrected time series")

merged["order_date"] = pd.to_datetime(merged["order_date"])
merged["year_month"] = merged["order_date"].dt.to_period("M").astype(str)

monthly_inflated = merged.groupby("year_month")["order_value"].sum().round(2)
print("Monthly revenue INCLUDING the 2 Task-6 outlier orders:")
print(monthly_inflated)

monthly_corrected = merged.loc[~merged["is_outlier"]].groupby("year_month")["order_value"].sum().round(2)
print("\nMonthly revenue EXCLUDING the 2 Task-6 outlier orders (outlier-corrected):")
print(monthly_corrected)

assert monthly_inflated["2026-01"] == 29582.10
assert monthly_inflated["2026-06"] == 11615.40
assert monthly_corrected["2026-01"] == 11637.10
assert monthly_corrected["2026-02"] == 13195.50
assert monthly_corrected["2026-03"] == 20318.90
assert monthly_corrected["2026-04"] == 9495.30
assert monthly_corrected["2026-05"] == 13151.10
assert monthly_corrected["2026-06"] == 11615.40

apparent_peak_month = monthly_inflated.idxmax()
true_peak_month = monthly_corrected.idxmax()
print(
    f"\nJanuary's apparent lead ({monthly_inflated['2026-01']:,.2f}) is an ARTIFACT of "
    "two bulk orders landing in January: O0011 (25 units, 2026-01-28) and O0098 "
    "(30 units, 2026-01-10). Once those two outlier orders are excluded, January "
    f"drops to {monthly_corrected['2026-01']:,.2f} and {true_peak_month} becomes the "
    f"genuine peak month at {monthly_corrected[true_peak_month]:,.2f} -- this is why "
    "Task 6 (outlier detection) had to happen before Task 10 (the time series), not after."
)
assert true_peak_month == "2026-03"


# ------------------------------------------------------------------
# Task 1 (narrator) -- write findings.json for Part 3
# ------------------------------------------------------------------
section("Exporting narrator/findings.json for Part 3")

findings = {
    "cleaned_total_revenue_inr": total_clean_revenue,
    "raw_total_revenue_inr": RAW_TOTAL_FROM_PART1,
    "duplicate_reconciliation_delta_inr": delta,
    "return_rate_by_payment": {
        "COD": float(cod_rate),
        "CARD": float(card_rate),
        "UPI": float(upi_rate),
    },
    "highest_risk_segment": {
        "payment_method": "COD",
        "city_tier": 2,
        "return_rate_pct": float(cod_t2),
    },
    "true_peak_month": {
        "month": true_peak_month,
        "revenue_inr": float(monthly_corrected[true_peak_month]),
    },
    "outlier_inflated_month": {
        "month": "2026-01",
        "apparent_revenue_inr": float(monthly_inflated["2026-01"]),
        "corrected_revenue_inr": float(monthly_corrected["2026-01"]),
    },
}

os.makedirs(NARRATOR_DIR, exist_ok=True)
findings_path = os.path.join(NARRATOR_DIR, "findings.json")
with open(findings_path, "w") as f:
    json.dump(findings, f, indent=2)

print(f"Wrote {findings_path}:")
print(json.dumps(findings, indent=2))

# Persist the outlier-corrected monthly series for visualize.py so the chart
# script doesn't need to re-run the whole pipeline to get the same numbers.
monthly_corrected.to_csv(os.path.join(NARRATOR_DIR, "..", "analysis", "_monthly_corrected.csv"), header=["order_value"])
pm_stats["return_rate_pct"].to_csv(os.path.join(NARRATOR_DIR, "..", "analysis", "_return_rate_by_payment.csv"), header=["return_rate_pct"])

section("DONE -- all Part 2 assertions passed")
