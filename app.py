"""
Streamlit dashboard for e-commerce sales analysis.

Run with:
    streamlit run app.py
"""

import sys

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, ".")
from business_metrics import (
    calculate_aov,
    calculate_aov_growth,
    calculate_avg_monthly_growth,
    calculate_delivery_metrics,
    calculate_monthly_revenue,
    calculate_order_count,
    calculate_order_count_growth,
    calculate_revenue_by_category,
    calculate_revenue_by_state,
    calculate_revenue_growth,
    calculate_review_metrics,
    calculate_total_revenue,
)
from data_loader import build_sales_data, filter_by_period, get_period_label, load_datasets

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="E-Commerce Sales Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
    .block-container { padding-top: 1.2rem; padding-bottom: 1rem; }

    /* KPI cards */
    .kpi-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 18px 22px;
        height: 110px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }
    .kpi-label {
        font-size: 11px;
        color: #64748b;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.07em;
    }
    .kpi-value {
        font-size: 26px;
        font-weight: 700;
        color: #0f172a;
        line-height: 1;
    }
    .trend-pos  { font-size: 12px; color: #16a34a; font-weight: 600; }
    .trend-neg  { font-size: 12px; color: #dc2626; font-weight: 600; }
    .trend-neu  { font-size: 12px; color: #64748b; font-weight: 500; }

    /* Bottom cards */
    .bottom-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 22px 28px;
        height: 130px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }
    .bottom-label {
        font-size: 11px;
        color: #64748b;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.07em;
        margin-bottom: 6px;
    }
    .bottom-value {
        font-size: 32px;
        font-weight: 700;
        color: #0f172a;
        line-height: 1.15;
    }
    .bottom-subtitle { font-size: 12px; color: #64748b; margin-top: 4px; }
    .stars { color: #f59e0b; font-size: 20px; letter-spacing: 3px; }

    /* Section divider */
    hr { border-color: #e2e8f0; margin: 0.6rem 0; }
</style>
""",
    unsafe_allow_html=True,
)

# ── Helpers ───────────────────────────────────────────────────────────────────

MONTH_OPTIONS = {
    "Full Year": None,
    "January": 1, "February": 2, "March": 3, "April": 4,
    "May": 5, "June": 6, "July": 7, "August": 8,
    "September": 9, "October": 10, "November": 11, "December": 12,
}


def fmt_currency(val: float) -> str:
    """Format a value as $300K or $2.1M."""
    if val >= 1_000_000:
        return f"${val / 1_000_000:.1f}M"
    if val >= 1_000:
        return f"${val / 1_000:.0f}K"
    return f"${val:.0f}"


def nice_ticks(max_val: float, n: int = 5):
    """Return (tick_vals, tick_texts) with nicely rounded intervals."""
    if max_val == 0:
        return [0], ["$0"]
    raw_step = max_val / n
    magnitude = 10 ** int(np.floor(np.log10(raw_step)))
    nice_step = np.ceil(raw_step / magnitude) * magnitude
    vals = [i * nice_step for i in range(n + 1)]
    return vals, [fmt_currency(v) for v in vals]


def trend_html(growth: float, inverted: bool = False) -> str:
    """
    Return an HTML trend indicator.
    inverted=True flips the colour logic (lower is better, e.g. delivery time).
    """
    pct = growth * 100
    arrow = "▲" if pct >= 0 else "▼"
    if inverted:
        css = "trend-neg" if pct >= 0 else "trend-pos"
    else:
        css = "trend-pos" if pct >= 0 else "trend-neg"
    return f'<span class="{css}">{arrow} {abs(pct):.2f}% vs prev year</span>'


def stars_html(score: float) -> str:
    full = int(round(score))
    return "★" * full + "☆" * (5 - full)


def blue_gradient(n: int):
    """Return n colors from a light-to-dark Blues scale."""
    return px.colors.sample_colorscale("Blues", [0.25 + 0.75 * i / max(n - 1, 1) for i in range(n)])


# ── Data loading (cached) ─────────────────────────────────────────────────────

@st.cache_data
def load_all():
    raw = load_datasets("ecommerce_data")
    sales = build_sales_data(raw["order_items"], raw["orders"])
    return sales, raw["products"], raw["orders"], raw["customers"], raw["reviews"]


sales_data, products, orders_df, customers, reviews = load_all()
available_years = sorted(sales_data["year"].unique().tolist(), reverse=True)
default_year_index = available_years.index(2023) if 2023 in available_years else 0

# ── Header row ────────────────────────────────────────────────────────────────
col_title, _, col_yr, col_mo = st.columns([5, 0.2, 1, 1])

with col_title:
    st.markdown("## E-Commerce Sales Dashboard")

with col_yr:
    selected_year = st.selectbox("Year", options=available_years, index=default_year_index, label_visibility="visible")

with col_mo:
    month_label = st.selectbox("Month", options=list(MONTH_OPTIONS.keys()), index=0)
    selected_month = MONTH_OPTIONS[month_label]

comparison_year = selected_year - 1
period_label = get_period_label(selected_year, selected_month)

# ── Filter data ───────────────────────────────────────────────────────────────
sales_cur = filter_by_period(sales_data, selected_year, selected_month)
sales_prev = filter_by_period(sales_data, comparison_year, selected_month)

# ── Compute metrics ───────────────────────────────────────────────────────────
total_rev = calculate_total_revenue(sales_cur)
prev_rev = calculate_total_revenue(sales_prev)
rev_growth = calculate_revenue_growth(total_rev, prev_rev) if prev_rev > 0 else 0.0

aov = calculate_aov(sales_cur)
prev_aov = calculate_aov(sales_prev)
aov_growth = calculate_aov_growth(aov, prev_aov) if prev_aov > 0 else 0.0

total_orders = calculate_order_count(sales_cur)
prev_orders = calculate_order_count(sales_prev)
order_growth = calculate_order_count_growth(total_orders, prev_orders) if prev_orders > 0 else 0.0

avg_mom = calculate_avg_monthly_growth(sales_cur) if selected_month is None else None

sales_cur_del = calculate_delivery_metrics(sales_cur)
sales_prev_del = calculate_delivery_metrics(sales_prev)
review_cur = calculate_review_metrics(sales_cur_del, reviews)
review_prev = calculate_review_metrics(sales_prev_del, reviews)

avg_delivery = review_cur["avg_delivery_speed"]
prev_delivery = review_prev["avg_delivery_speed"]
delivery_growth = (avg_delivery - prev_delivery) / prev_delivery if prev_delivery > 0 else 0.0
avg_score = review_cur["avg_score"]

# ── KPI Row ───────────────────────────────────────────────────────────────────
st.markdown("<hr>", unsafe_allow_html=True)
k1, k2, k3, k4 = st.columns(4)

with k1:
    st.markdown(
        f"""<div class="kpi-card">
            <div class="kpi-label">Total Revenue</div>
            <div class="kpi-value">{fmt_currency(total_rev)}</div>
            {trend_html(rev_growth)}
        </div>""",
        unsafe_allow_html=True,
    )

with k2:
    mom_display = f"{avg_mom * 100:.2f}%" if avg_mom is not None else "N/A"
    mom_subtitle = (
        f'<span class="trend-neu">Month-over-month avg</span>'
        if avg_mom is not None
        else '<span class="trend-neu">Select full year for MoM</span>'
    )
    st.markdown(
        f"""<div class="kpi-card">
            <div class="kpi-label">Avg Monthly Growth</div>
            <div class="kpi-value">{mom_display}</div>
            {mom_subtitle}
        </div>""",
        unsafe_allow_html=True,
    )

with k3:
    st.markdown(
        f"""<div class="kpi-card">
            <div class="kpi-label">Average Order Value</div>
            <div class="kpi-value">{fmt_currency(aov)}</div>
            {trend_html(aov_growth)}
        </div>""",
        unsafe_allow_html=True,
    )

with k4:
    st.markdown(
        f"""<div class="kpi-card">
            <div class="kpi-label">Total Orders</div>
            <div class="kpi-value">{total_orders:,}</div>
            {trend_html(order_growth)}
        </div>""",
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# ── Charts Grid (2x2) ─────────────────────────────────────────────────────────
CHART_H = 370
CHART_BG = "white"
GRID_COLOR = "#f1f5f9"

c1, c2 = st.columns(2)

# ── Chart 1: Revenue Trend ────────────────────────────────────────────────────
with c1:
    monthly_cur = (
        calculate_monthly_revenue(filter_by_period(sales_data, selected_year))
        .reindex(range(1, 13), fill_value=0)
    )
    monthly_prv = (
        calculate_monthly_revenue(filter_by_period(sales_data, comparison_year))
        .reindex(range(1, 13), fill_value=0)
    )
    month_names = [pd.Timestamp(2020, m, 1).strftime("%b") for m in range(1, 13)]

    all_vals = list(monthly_cur.values) + list(monthly_prv.values)
    tick_vals, tick_text = nice_ticks(max(all_vals) if all_vals else 1)

    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(
        x=month_names, y=monthly_prv.values,
        name=str(comparison_year),
        mode="lines+markers",
        line=dict(color="#93c5fd", width=2, dash="dash"),
        marker=dict(size=5),
    ))
    fig_trend.add_trace(go.Scatter(
        x=month_names, y=monthly_cur.values,
        name=str(selected_year),
        mode="lines+markers",
        line=dict(color="#1e3a5f", width=2.5),
        marker=dict(size=6),
    ))
    if selected_month is not None:
        fig_trend.add_vline(
            x=month_names[selected_month - 1],
            line_dash="dot", line_color="#94a3b8", line_width=1.5,
        )
    fig_trend.update_layout(
        title=dict(text=f"Monthly Revenue Trend ({selected_year} vs {comparison_year})", font_size=14),
        xaxis=dict(title="Month", showgrid=True, gridcolor=GRID_COLOR),
        yaxis=dict(title="Revenue", tickvals=tick_vals, ticktext=tick_text,
                   showgrid=True, gridcolor=GRID_COLOR),
        plot_bgcolor=CHART_BG, paper_bgcolor=CHART_BG,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(t=55, b=45, l=70, r=20),
        height=CHART_H,
    )
    st.plotly_chart(fig_trend, use_container_width=True)

# ── Chart 2: Top 10 Categories ────────────────────────────────────────────────
with c2:
    cat_rev = calculate_revenue_by_category(sales_cur, products).head(10)
    cat_df = cat_rev.reset_index()
    cat_df.columns = ["category", "revenue"]
    cat_df = cat_df.sort_values("revenue", ascending=True)  # ascending → highest at top

    n = len(cat_df)
    colors = blue_gradient(n)

    tick_vals_cat, tick_text_cat = nice_ticks(cat_df["revenue"].max() if n > 0 else 1)

    fig_cat = go.Figure(go.Bar(
        x=cat_df["revenue"],
        y=cat_df["category"],
        orientation="h",
        marker_color=colors,
        text=[fmt_currency(v) for v in cat_df["revenue"]],
        textposition="outside",
        cliponaxis=False,
    ))
    fig_cat.update_layout(
        title=dict(text=f"Top 10 Categories by Revenue ({period_label})", font_size=14),
        xaxis=dict(title="Revenue", tickvals=tick_vals_cat, ticktext=tick_text_cat,
                   showgrid=True, gridcolor=GRID_COLOR),
        yaxis=dict(showgrid=False, automargin=True),
        plot_bgcolor=CHART_BG, paper_bgcolor=CHART_BG,
        margin=dict(t=55, b=45, l=10, r=80),
        height=CHART_H,
        showlegend=False,
    )
    st.plotly_chart(fig_cat, use_container_width=True)

c3, c4 = st.columns(2)

# ── Chart 3: Revenue by State ─────────────────────────────────────────────────
with c3:
    state_rev = calculate_revenue_by_state(sales_cur, orders_df, customers)

    rev_min = state_rev["price"].min()
    rev_max = state_rev["price"].max()
    cbar_tick_vals = [rev_min, (rev_min + rev_max) / 2, rev_max]
    cbar_tick_text = [fmt_currency(v) for v in cbar_tick_vals]

    fig_map = px.choropleth(
        state_rev,
        locations="customer_state",
        color="price",
        locationmode="USA-states",
        scope="usa",
        color_continuous_scale="Blues",
        labels={"price": "Revenue", "customer_state": "State"},
        title=f"Revenue by State ({period_label})",
        hover_data={"price": False, "customer_state": True},
        custom_data=["customer_state", "price"],
    )
    fig_map.update_traces(
        hovertemplate="<b>%{customdata[0]}</b><br>Revenue: %{customdata[1]:$,.0f}<extra></extra>"
    )
    fig_map.update_coloraxes(
        colorbar=dict(
            title="Revenue",
            tickvals=cbar_tick_vals,
            ticktext=cbar_tick_text,
        )
    )
    fig_map.update_layout(
        paper_bgcolor=CHART_BG,
        margin=dict(t=55, b=10, l=10, r=10),
        height=CHART_H,
    )
    st.plotly_chart(fig_map, use_container_width=True)

# ── Chart 4: Review Score by Delivery Time ────────────────────────────────────
with c4:
    bucket_order = ["1-3 days", "4-7 days", "8+ days"]
    score_df = review_cur["score_by_delivery_bucket"].copy()
    score_df["delivery_time"] = pd.Categorical(
        score_df["delivery_time"], categories=bucket_order, ordered=True
    )
    score_df = score_df.sort_values("delivery_time")

    fig_sat = go.Figure(go.Bar(
        x=score_df["delivery_time"],
        y=score_df["review_score"],
        marker_color="#2E86AB",
        text=[f"{v:.2f}" for v in score_df["review_score"]],
        textposition="outside",
        cliponaxis=False,
    ))
    fig_sat.update_layout(
        title=dict(text=f"Review Score by Delivery Time ({period_label})", font_size=14),
        xaxis=dict(title="Delivery Time", showgrid=False),
        yaxis=dict(title="Average Review Score", range=[0, 5.5],
                   showgrid=True, gridcolor=GRID_COLOR),
        plot_bgcolor=CHART_BG, paper_bgcolor=CHART_BG,
        margin=dict(t=55, b=45, l=60, r=20),
        height=CHART_H,
        showlegend=False,
    )
    st.plotly_chart(fig_sat, use_container_width=True)

# ── Bottom Row ────────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
b1, b2 = st.columns(2)

with b1:
    st.markdown(
        f"""<div class="bottom-card">
            <div class="bottom-label">Average Delivery Time</div>
            <div class="bottom-value">{avg_delivery:.1f} days</div>
            {trend_html(delivery_growth, inverted=True)}
        </div>""",
        unsafe_allow_html=True,
    )

with b2:
    score_rounded = round(avg_score, 2)
    stars = stars_html(avg_score)
    st.markdown(
        f"""<div class="bottom-card">
            <div class="bottom-label">Customer Satisfaction</div>
            <div class="bottom-value">
                {score_rounded} <span class="stars">{stars}</span>
            </div>
            <div class="bottom-subtitle">Average Review Score</div>
        </div>""",
        unsafe_allow_html=True,
    )
