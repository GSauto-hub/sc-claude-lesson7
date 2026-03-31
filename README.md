# E-Commerce EDA

Exploratory data analysis of e-commerce sales data, structured as a modular Python project with a Jupyter notebook for interactive analysis.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running the Dashboard

```bash
streamlit run app.py
```

The dashboard opens at `http://localhost:8501`. Use the **Year** and **Month** dropdowns in the top-right to filter all charts and KPIs. Selecting "Full Year" shows the average month-over-month growth KPI and highlights the full year in the revenue trend chart; selecting a specific month scopes all metrics to that month.

## Running the Notebook

```bash
jupyter notebook
```

Open `EDA_Refactored.ipynb`. To change the analysis period, update the `ANALYSIS_YEAR` and `ANALYSIS_MONTH` variables near the top of the notebook — the rest of the analysis updates automatically.

To run headlessly:

```bash
jupyter nbconvert --to notebook --execute EDA_Refactored.ipynb
```

## Project Structure

```
ecommerce_data/        # Raw CSV datasets
data_loader.py         # Data loading, merging, cleaning, and period filtering
business_metrics.py    # Pure metric calculation functions (no I/O or filtering)
app.py                 # Streamlit dashboard
EDA_Refactored.ipynb   # Analysis notebook
requirements.txt       # Python dependencies
```

### Modules

**`data_loader.py`** handles all I/O and data preparation. Use `load_datasets()` to load the raw CSVs, `build_sales_data()` to produce the cleaned base DataFrame (delivered orders only), and `filter_by_period(df, year, month=None)` to scope data to a period.

**`business_metrics.py`** contains pure calculation functions grouped into five areas: Revenue, Orders, Product, Geographic, and Customer Experience. All functions accept pre-filtered DataFrames — no filtering logic lives here.

## Data

The `ecommerce_data/` directory contains six CSV files:

| File | Description |
|------|-------------|
| `orders_dataset.csv` | Order status and timestamps |
| `order_items_dataset.csv` | Line items with price per order |
| `products_dataset.csv` | Product category and attributes |
| `customers_dataset.csv` | Customer location data |
| `order_reviews_dataset.csv` | Review scores and comments |
| `order_payments_dataset.csv` | Payment method and values |

Only orders with `order_status == 'delivered'` are included in the analysis.
