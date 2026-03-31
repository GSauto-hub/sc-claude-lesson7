"""
Data loading, processing, and cleaning utilities for e-commerce analysis.

Functions
---------
load_datasets       : Load all five CSV datasets into a dictionary of DataFrames.
build_sales_data    : Merge and clean the base sales dataset.
filter_by_period    : Filter sales data to a specific year and optional month.
get_period_label    : Return a human-readable label for an analysis period.
"""

import os
import pandas as pd


def load_datasets(data_dir: str = 'ecommerce_data') -> dict:
    """
    Load all e-commerce datasets from CSV files.

    Parameters
    ----------
    data_dir : str
        Path to the directory containing the CSV files.

    Returns
    -------
    dict
        Dictionary with keys: 'orders', 'order_items', 'products',
        'customers', 'reviews'.  Each value is a pandas DataFrame.
    """
    datasets = {
        'orders':      pd.read_csv(os.path.join(data_dir, 'orders_dataset.csv')),
        'order_items': pd.read_csv(os.path.join(data_dir, 'order_items_dataset.csv')),
        'products':    pd.read_csv(os.path.join(data_dir, 'products_dataset.csv')),
        'customers':   pd.read_csv(os.path.join(data_dir, 'customers_dataset.csv')),
        'reviews':     pd.read_csv(os.path.join(data_dir, 'order_reviews_dataset.csv')),
    }
    return datasets


def build_sales_data(order_items: pd.DataFrame, orders: pd.DataFrame) -> pd.DataFrame:
    """
    Build the base sales dataset by merging order items with order metadata,
    filtering to delivered orders only, and extracting date features.

    Transformations applied
    -----------------------
    - Inner join of order_items and orders on order_id.
    - Filter to rows where order_status == 'delivered'.
    - Convert timestamp columns to datetime.
    - Add 'month' and 'year' integer columns derived from order_purchase_timestamp.

    Parameters
    ----------
    order_items : pd.DataFrame
        DataFrame from order_items_dataset.csv.
    orders : pd.DataFrame
        DataFrame from orders_dataset.csv.

    Returns
    -------
    pd.DataFrame
        Cleaned and enriched sales DataFrame with columns:
        order_id, order_item_id, product_id, price, order_status,
        order_purchase_timestamp, order_delivered_customer_date, month, year.
    """
    sales_data = pd.merge(
        left=order_items[['order_id', 'order_item_id', 'product_id', 'price']],
        right=orders[['order_id', 'order_status', 'order_purchase_timestamp',
                      'order_delivered_customer_date']],
        on='order_id'
    )

    sales_delivered = sales_data[sales_data['order_status'] == 'delivered'].copy()

    sales_delivered['order_purchase_timestamp'] = pd.to_datetime(
        sales_delivered['order_purchase_timestamp']
    )
    sales_delivered['order_delivered_customer_date'] = pd.to_datetime(
        sales_delivered['order_delivered_customer_date']
    )

    sales_delivered['month'] = sales_delivered['order_purchase_timestamp'].dt.month
    sales_delivered['year'] = sales_delivered['order_purchase_timestamp'].dt.year

    return sales_delivered


def filter_by_period(df: pd.DataFrame, year: int, month: int = None) -> pd.DataFrame:
    """
    Filter the sales DataFrame to a specific year, and optionally a specific month.

    Parameters
    ----------
    df : pd.DataFrame
        Sales DataFrame containing 'year' and 'month' integer columns.
    year : int
        The year to filter to.
    month : int, optional
        Month number (1-12).  If None, returns the full year.

    Returns
    -------
    pd.DataFrame
        A copy of the filtered DataFrame.
    """
    mask = df['year'] == year
    if month is not None:
        mask = mask & (df['month'] == month)
    return df[mask].copy()


def get_period_label(year: int, month: int = None) -> str:
    """
    Return a human-readable label for the given analysis period.

    Parameters
    ----------
    year : int
        The year of the analysis period.
    month : int, optional
        Month number (1-12).  If None, the label covers the full year.

    Returns
    -------
    str
        Period label, e.g., '2023' or 'March 2023'.
    """
    if month is None:
        return str(year)
    month_name = pd.Timestamp(year=year, month=month, day=1).strftime('%B')
    return f'{month_name} {year}'
