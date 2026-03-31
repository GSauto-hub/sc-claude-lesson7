# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Environment Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running the Notebooks

```bash
jupyter notebook          # open EDA_Refactored.ipynb in browser
jupyter nbconvert --to notebook --execute EDA_Refactored.ipynb  # run headlessly
```

## Architecture

This is an e-commerce EDA project with a clean separation between data access, metric logic, and presentation:

- **`data_loader.py`** — all I/O and data preparation. Entry point is `load_datasets()` → `build_sales_data()`. `filter_by_period(df, year, month=None)` is the single place where date-range filtering happens; the notebook should always call this rather than filtering inline.
- **`business_metrics.py`** — pure calculation functions; no I/O, no filtering. Functions accept already-filtered DataFrames and return scalars, Series, or DataFrames. Grouped into Revenue, Orders, Product, Geographic, and Customer Experience sections.
- **`EDA_Refactored.ipynb`** — the analysis notebook. Imports from the two modules above. Period is configured via `ANALYSIS_YEAR` / `ANALYSIS_MONTH` variables near the top of the notebook; changing those two variables re-runs the entire analysis for a different date range.
- **`ecommerce_data/`** — raw CSV files (`orders_dataset.csv`, `order_items_dataset.csv`, `products_dataset.csv`, `customers_dataset.csv`, `order_reviews_dataset.csv`, `order_payments_dataset.csv`). Only delivered orders are used in analysis (filtered in `build_sales_data`).

## Key Conventions

- Business metric functions in `business_metrics.py` must not contain filtering logic — callers pass pre-filtered data.
- Growth rates are returned as decimals (0.15 = 15%), not percentages.
- Delivery speed buckets are defined once in `categorize_delivery_speed()` — do not redefine thresholds elsewhere.
- Do not use icons or emoji in markdown cells or print statements.
- Color schemes in plots should be business-oriented and consistent across the notebook.
- Plot titles should include the analysis period (use `get_period_label(year, month)` from `data_loader`).
