"""
Business metric calculations for e-commerce analysis.

All functions accept pre-filtered DataFrames and return scalar values,
Series, or DataFrames depending on the metric type.  No filtering logic
lives here; callers are expected to pass already-filtered data.

Functions
---------
Revenue
    calculate_total_revenue
    calculate_revenue_growth
    calculate_monthly_revenue
    calculate_monthly_growth
    calculate_avg_monthly_growth

Orders
    calculate_aov
    calculate_aov_growth
    calculate_order_count
    calculate_order_count_growth

Product
    calculate_revenue_by_category

Geographic
    calculate_revenue_by_state

Customer experience
    categorize_delivery_speed
    calculate_delivery_metrics
    calculate_review_metrics
"""

import pandas as pd


# ---------------------------------------------------------------------------
# Revenue metrics
# ---------------------------------------------------------------------------

def calculate_total_revenue(sales_df: pd.DataFrame) -> float:
    """
    Calculate total revenue from all line items in the supplied DataFrame.

    Parameters
    ----------
    sales_df : pd.DataFrame
        Sales DataFrame with a 'price' column.

    Returns
    -------
    float
        Sum of all item prices.
    """
    return sales_df['price'].sum()


def calculate_revenue_growth(current_revenue: float, previous_revenue: float) -> float:
    """
    Calculate the period-over-period revenue growth rate.

    Parameters
    ----------
    current_revenue : float
        Revenue for the current period.
    previous_revenue : float
        Revenue for the comparison period.

    Returns
    -------
    float
        Growth rate as a decimal (e.g., 0.15 represents 15% growth).
    """
    return (current_revenue - previous_revenue) / previous_revenue


def calculate_monthly_revenue(sales_df: pd.DataFrame) -> pd.Series:
    """
    Calculate total revenue grouped by month number.

    Parameters
    ----------
    sales_df : pd.DataFrame
        Sales DataFrame with 'month' and 'price' columns.

    Returns
    -------
    pd.Series
        Monthly revenue indexed by month number (1-12).
    """
    return sales_df.groupby('month')['price'].sum()


def calculate_monthly_growth(sales_df: pd.DataFrame) -> pd.Series:
    """
    Calculate the month-over-month revenue growth rate.

    Parameters
    ----------
    sales_df : pd.DataFrame
        Sales DataFrame with 'month' and 'price' columns.

    Returns
    -------
    pd.Series
        Month-over-month growth rate indexed by month number.
        The first month will be NaN (no prior month to compare against).
    """
    return calculate_monthly_revenue(sales_df).pct_change()


def calculate_avg_monthly_growth(sales_df: pd.DataFrame) -> float:
    """
    Calculate the mean month-over-month revenue growth rate, excluding the
    first month (which has no prior-month baseline).

    Parameters
    ----------
    sales_df : pd.DataFrame
        Sales DataFrame with 'month' and 'price' columns.

    Returns
    -------
    float
        Mean monthly growth rate as a decimal.
    """
    return calculate_monthly_growth(sales_df).mean()


# ---------------------------------------------------------------------------
# Order metrics
# ---------------------------------------------------------------------------

def calculate_aov(sales_df: pd.DataFrame) -> float:
    """
    Calculate the Average Order Value (AOV).

    AOV is computed as the mean of per-order revenue sums, which accounts
    for multi-item orders correctly.

    Parameters
    ----------
    sales_df : pd.DataFrame
        Sales DataFrame with 'order_id' and 'price' columns.

    Returns
    -------
    float
        Mean revenue per order.
    """
    return sales_df.groupby('order_id')['price'].sum().mean()


def calculate_aov_growth(current_aov: float, previous_aov: float) -> float:
    """
    Calculate the period-over-period AOV growth rate.

    Parameters
    ----------
    current_aov : float
        AOV for the current period.
    previous_aov : float
        AOV for the comparison period.

    Returns
    -------
    float
        Growth rate as a decimal.
    """
    return (current_aov - previous_aov) / previous_aov


def calculate_order_count(sales_df: pd.DataFrame) -> int:
    """
    Count the total number of unique orders.

    Parameters
    ----------
    sales_df : pd.DataFrame
        Sales DataFrame with an 'order_id' column.

    Returns
    -------
    int
        Number of unique orders.
    """
    return sales_df['order_id'].nunique()


def calculate_order_count_growth(current_count: int, previous_count: int) -> float:
    """
    Calculate the period-over-period order count growth rate.

    Parameters
    ----------
    current_count : int
        Order count for the current period.
    previous_count : int
        Order count for the comparison period.

    Returns
    -------
    float
        Growth rate as a decimal.
    """
    return (current_count - previous_count) / previous_count


# ---------------------------------------------------------------------------
# Product metrics
# ---------------------------------------------------------------------------

def calculate_revenue_by_category(
    sales_df: pd.DataFrame,
    products_df: pd.DataFrame
) -> pd.Series:
    """
    Calculate total revenue by product category, sorted in descending order.

    Parameters
    ----------
    sales_df : pd.DataFrame
        Sales DataFrame with 'product_id' and 'price' columns.
    products_df : pd.DataFrame
        Products DataFrame with 'product_id' and 'product_category_name' columns.

    Returns
    -------
    pd.Series
        Revenue per product category, sorted from highest to lowest,
        indexed by product_category_name.
    """
    sales_categories = pd.merge(
        left=products_df[['product_id', 'product_category_name']],
        right=sales_df[['product_id', 'price']]
    )
    return (
        sales_categories
        .groupby('product_category_name')['price']
        .sum()
        .sort_values(ascending=False)
    )


# ---------------------------------------------------------------------------
# Geographic metrics
# ---------------------------------------------------------------------------

def calculate_revenue_by_state(
    sales_df: pd.DataFrame,
    orders_df: pd.DataFrame,
    customers_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Calculate total revenue by customer state, sorted in descending order.

    Parameters
    ----------
    sales_df : pd.DataFrame
        Sales DataFrame with 'order_id' and 'price' columns.
    orders_df : pd.DataFrame
        Orders DataFrame with 'order_id' and 'customer_id' columns.
    customers_df : pd.DataFrame
        Customers DataFrame with 'customer_id' and 'customer_state' columns.

    Returns
    -------
    pd.DataFrame
        DataFrame with 'customer_state' and 'price' columns,
        sorted by revenue in descending order.
    """
    sales_customers = pd.merge(
        left=sales_df[['order_id', 'price']],
        right=orders_df[['order_id', 'customer_id']],
        on='order_id'
    )
    sales_states = pd.merge(
        left=sales_customers,
        right=customers_df[['customer_id', 'customer_state']],
        on='customer_id'
    )
    return (
        sales_states
        .groupby('customer_state')['price']
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )


# ---------------------------------------------------------------------------
# Customer experience metrics
# ---------------------------------------------------------------------------

def categorize_delivery_speed(days: int) -> str:
    """
    Assign a delivery speed category label based on the number of days.

    Parameters
    ----------
    days : int
        Number of days from purchase to delivery.

    Returns
    -------
    str
        One of '1-3 days', '4-7 days', or '8+ days'.
    """
    if days <= 3:
        return '1-3 days'
    if days <= 7:
        return '4-7 days'
    return '8+ days'


def calculate_delivery_metrics(sales_df: pd.DataFrame) -> pd.DataFrame:
    """
    Add delivery speed columns to the sales DataFrame.

    Requires that 'order_purchase_timestamp' and
    'order_delivered_customer_date' are already datetime columns.

    Parameters
    ----------
    sales_df : pd.DataFrame
        Sales DataFrame with the two datetime timestamp columns.

    Returns
    -------
    pd.DataFrame
        Copy of sales_df with two new columns:
        - 'delivery_speed' (int): days from purchase to delivery.
        - 'delivery_time' (str): speed category ('1-3 days', '4-7 days', '8+ days').
    """
    df = sales_df.copy()
    df['delivery_speed'] = (
        df['order_delivered_customer_date'] - df['order_purchase_timestamp']
    ).dt.days
    df['delivery_time'] = df['delivery_speed'].apply(categorize_delivery_speed)
    return df


def calculate_review_metrics(
    sales_df: pd.DataFrame,
    reviews_df: pd.DataFrame
) -> dict:
    """
    Calculate customer review metrics, including average score and score
    distribution by delivery speed bucket.

    Parameters
    ----------
    sales_df : pd.DataFrame
        Sales DataFrame that already contains 'delivery_speed' and
        'delivery_time' columns (output of calculate_delivery_metrics).
    reviews_df : pd.DataFrame
        Reviews DataFrame with 'order_id' and 'review_score' columns.

    Returns
    -------
    dict with keys:
        'review_speed_df' : pd.DataFrame
            Per-order DataFrame with order_id, delivery_speed,
            delivery_time, and review_score (duplicates removed).
        'avg_score' : float
            Mean review score across all orders.
        'score_distribution' : pd.Series
            Normalized count of each review score (1-5), sorted by score.
        'score_by_delivery_bucket' : pd.DataFrame
            Mean review score grouped by delivery time category.
        'avg_delivery_speed' : float
            Mean delivery speed in days.
    """
    sales_with_reviews = sales_df.merge(
        reviews_df[['order_id', 'review_score']],
        on='order_id'
    )
    review_speed = (
        sales_with_reviews[['order_id', 'delivery_speed', 'delivery_time', 'review_score']]
        .drop_duplicates()
    )

    return {
        'review_speed_df': review_speed,
        'avg_score': review_speed['review_score'].mean(),
        'score_distribution': (
            review_speed['review_score']
            .value_counts(normalize=True)
            .sort_index()
        ),
        'score_by_delivery_bucket': (
            review_speed
            .groupby('delivery_time')['review_score']
            .mean()
            .reset_index()
        ),
        'avg_delivery_speed': review_speed['delivery_speed'].mean(),
    }
