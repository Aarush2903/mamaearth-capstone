# Mamaearth Returns & Growth Intelligence Pipeline

Capstone project — Data Analytics with AI & Gen AI, E&ICT Academy IIT Roorkee.

A Data Analyst on Mamaearth's Growth Analytics team suspects returns are
eating into margins on a subset of orders. This repo proves it end-to-end
with three connected layers:

1. **SQL** (`sql/`) — a relational store for the raw order data and the
   report queries that find the patterns.
2. **Python/Pandas** (`analysis/`) — an independent cleaning + EDA pipeline
   over the same raw CSVs, which reconciles its numbers against the SQL
   layer and writes the verified findings to `narrator/findings.json`.
3. **GenAI Narrator** (`narrator/`) — turns those verified findings into a
   Situation–Complication–Resolution business narrative for regional ops
   and finance heads, with a fully offline fallback.

No layer reports a number it did not itself compute or receive from the
layer before it.

```
├── README.md
├── sql/
│   ├── schema.sql
│   ├── seed_data.sql
│   └── reports.sql
├── data/
│   ├── customers.csv
│   ├── products.csv
│   └── orders.csv
├── analysis/
│   ├── clean_and_eda.py
│   └── visualize.py
├── visualizations/
│   ├── return_rate_by_payment.png
│   └── monthly_revenue_trend.png
└── narrator/
    ├── findings.json
    ├── generate_narrative.py
```

## Requirements

- Python 3.9+
- `pip install pandas numpy matplotlib`
- Optional, only for the live Gemini path: `pip install google-genai`
- SQLite (via Python's built-in `sqlite3` module — no separate install
  needed; any SQL engine that supports the exact `CREATE TABLE` /
  `FOREIGN KEY` syntax in `sql/schema.sql` also works)

> **Windows note:** use `python`, not `python3`, for every command below —
> Windows doesn't ship a `python3` alias, and typing it may trigger a
> Microsoft Store prompt instead of running your installed Python.

## 1. Run the SQL layer

`sql/schema.sql` creates three tables (`customers`, `products`, `orders`)
with primary keys and foreign keys. `sql/seed_data.sql` loads
`data/customers.csv`, `data/products.csv`, and `data/orders.csv` into
those tables via generated `INSERT` statements (blank `discount_pct` /
`rating` cells become true SQL `NULL`, never an empty string).
`sql/reports.sql` holds the nine report queries, each with its verified
output pasted as a comment directly above it.

Using the included runner script (works identically on Windows/macOS/Linux
since it's plain Python — no `sqlite3` CLI needed):

```bash
python sql/run_sql.py
```

(On Windows, use `python`, not `python3` — see note below.)

Or, if you have the `sqlite3` CLI installed:

```bash
sqlite3 mamaearth.db < sql/schema.sql
sqlite3 mamaearth.db < sql/seed_data.sql
sqlite3 mamaearth.db < sql/reports.sql
```

After loading: `customers` has 45 rows, `products` has 16, `orders` has
180. Report (a)'s raw `total_revenue` is **₹99,860.20** — this is the
number Part 2 reconciles against after cleaning.

## 2. Run the Python/Pandas layer

`analysis/clean_and_eda.py` is an **independent** pipeline over the raw
CSVs in `data/` — it does not read the SQLite database, so Part 1 and
Part 2 can be run in either order and will still agree on every number.
It standardizes `payment_method` casing, drops 5 duplicate orders,
imputes missing `discount_pct`/`rating`, reconciles its cleaned total
(**₹97,358.30**) against Part 1's raw total (the ₹2,501.90 gap is the 5
duplicates, proven independently), flags 2 quantity outliers via IQR,
tests the "COD returns more" and "discounts reduce returns" hypotheses,
segments return rate by payment method × city tier, and produces an
outlier-corrected monthly revenue series.

```bash
python analysis/clean_and_eda.py
```

This prints every intermediate result the acceptance criteria reference,
and — as its last step — **writes `narrator/findings.json`**, the
handoff file Part 3 consumes. It also writes two small intermediate CSVs
(`analysis/_monthly_corrected.csv`, `analysis/_return_rate_by_payment.csv`)
so the chart script below can plot the exact same numbers without
re-deriving them.

Then generate the two charts:

```bash
python analysis/visualize.py
```

This writes `visualizations/return_rate_by_payment.png` (COD at 44.4%,
~3x Card) and `visualizations/monthly_revenue_trend.png` (March 2026 is
the genuine peak once the two outlier bulk orders are excluded).

**Run `clean_and_eda.py` before `visualize.py`** — the chart script reads
the intermediate CSVs the first script produces.

## 3. Run the GenAI narrator

`narrator/findings.json` (written by step 2, never hand-typed) is turned
into a three-section SCR narrative by `narrator/generate_narrative.py`,
using the `google-genai` client and the Gemini API's free tier.

**With a Gemini API key** (get a free key, on the free usage tier, from
[Google AI Studio](https://aistudio.google.com/apikey) — never a
paid-only key):

```bash
export GEMINI_API_KEY="your-free-api-key"     # Linux / macOS
setx GEMINI_API_KEY "your-free-api-key"       # Windows (new shell after)
python narrator/generate_narrative.py
```

**With no key at all** (fully offline, zero network, zero config):

```bash
python narrator/generate_narrative.py
```

Either way the script prints which path it used, the narrative, and a
per-figure PASS/FAIL numeric-accuracy checklist against the five figures
that must appear in the output (cleaned revenue, COD return rate, the
COD+Tier-2 risk segment, the duplicate-reconciliation delta, and the
true peak month). `narrator/sample_output.txt` holds one saved real run
so the pipeline is gradable without live API access — the grader checks
that saved file, not a live call.

## Reproducing every number in this brief

1. Run the SQL layer (step 1) → confirms the raw totals and the 9 report
   queries.
2. Run `analysis/clean_and_eda.py` (step 2) → confirms every cleaning,
   reconciliation, outlier, hypothesis-test, segmentation, correlation,
   and time-series number, and writes `findings.json`.
3. Run `analysis/visualize.py` (step 2) → produces the two PNGs.
4. Run `narrator/generate_narrative.py` (step 3), with or without a
   Gemini key → produces the business narrative and its accuracy check.

No step requires editing any committed CSV by hand, and every script is
re-runnable end-to-end from the raw source data.
