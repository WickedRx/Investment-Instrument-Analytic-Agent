from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


# ------------------------------------------------------------
# Retirement Analysis Agent Dashboard
#
# Purpose:
# Display the master scorecard in a readable dashboard instead
# of manually opening multiple spreadsheets.
# ------------------------------------------------------------


# Page setup
st.set_page_config(
    page_title="Retirement Analysis Agent",
    page_icon="📊",
    layout="wide"
)

# Locate project folder
project_folder = Path(__file__).resolve().parent
scorecard_file = project_folder / "03_outputs" / "master_retirement_instrument_scorecard.csv"

st.title("📊 Retirement Analysis Agent Dashboard")
st.caption("Personal instrument scouting dashboard: income, return, NAV behavior, and review priority.")

# ------------------------------------------------------------
# Load data
# ------------------------------------------------------------

if not scorecard_file.exists():
    st.error("Master scorecard file not found.")
    st.write("Expected file here:")
    st.code(str(scorecard_file))
    st.stop()

df = pd.read_csv(scorecard_file)

# ------------------------------------------------------------
# Sidebar filters
# ------------------------------------------------------------

st.sidebar.header("Filters")

categories = sorted(df["category"].dropna().unique())
selected_categories = st.sidebar.multiselect(
    "Category",
    categories,
    default=categories
)

ratings = sorted(df["overall_rating"].dropna().unique())
selected_ratings = st.sidebar.multiselect(
    "Overall rating",
    ratings,
    default=ratings
)

filtered_df = df[
    df["category"].isin(selected_categories)
    & df["overall_rating"].isin(selected_ratings)
].copy()

# ------------------------------------------------------------
# Key metrics
# ------------------------------------------------------------

st.subheader("Portfolio Scout Summary")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Tracked instruments", len(filtered_df))

with col2:
    avg_score = filtered_df["overall_score"].mean()
    st.metric("Average score", f"{avg_score:.1f}" if pd.notna(avg_score) else "N/A")

with col3:
    avg_yield = filtered_df["trailing_12_month_yield_pct"].mean()
    st.metric("Average trailing yield", f"{avg_yield:.2f}%" if pd.notna(avg_yield) else "N/A")

with col4:
    avg_total_return = filtered_df["approx_1y_total_return_pct"].mean()
    st.metric("Average approx. 1Y total return", f"{avg_total_return:.2f}%" if pd.notna(avg_total_return) else "N/A")

with col5:
    high_priority_count = filtered_df[
        filtered_df["review_priority"].str.contains("High priority", case=False, na=False)
    ].shape[0]
    st.metric("High-priority reviews", high_priority_count)

# ------------------------------------------------------------
# Master scorecard table
# ------------------------------------------------------------

st.subheader("Master Scorecard")

display_columns = [
    "ticker",
    "category",
    "role",
    "overall_score",
    "overall_rating",
    "review_priority",
    "trailing_12_month_yield_pct",
    "return_1y_price_pct",
    "approx_1y_total_return_pct",
    "largest_1y_price_decline_pct",
    "number_of_payments_last_12_months",
    "yield_method_warning",
    "nav_erosion_warning",
    "scout_comment",
]

st.dataframe(
    filtered_df[display_columns],
    use_container_width=True,
    hide_index=True
)

# ------------------------------------------------------------
# Charts
# ------------------------------------------------------------

st.subheader("Visual Review")

chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    score_chart = px.bar(
        filtered_df.sort_values("overall_score", ascending=True),
        x="overall_score",
        y="ticker",
        orientation="h",
        title="Overall Score by Ticker",
        labels={"overall_score": "Overall Score", "ticker": "Ticker"}
    )
    st.plotly_chart(score_chart, use_container_width=True)

with chart_col2:
    yield_chart = px.bar(
        filtered_df.sort_values("trailing_12_month_yield_pct", ascending=True),
        x="trailing_12_month_yield_pct",
        y="ticker",
        orientation="h",
        title="Trailing 12-Month Yield by Ticker",
        labels={"trailing_12_month_yield_pct": "Trailing 12-Month Yield (%)", "ticker": "Ticker"}
    )
    st.plotly_chart(yield_chart, use_container_width=True)

chart_col3, chart_col4 = st.columns(2)

with chart_col3:
    total_return_chart = px.bar(
        filtered_df.sort_values("approx_1y_total_return_pct", ascending=True),
        x="approx_1y_total_return_pct",
        y="ticker",
        orientation="h",
        title="Approximate 1-Year Total Return by Ticker",
        labels={"approx_1y_total_return_pct": "Approx. 1Y Total Return (%)", "ticker": "Ticker"}
    )
    st.plotly_chart(total_return_chart, use_container_width=True)

with chart_col4:
    scatter_chart = px.scatter(
        filtered_df,
        x="return_1y_price_pct",
        y="trailing_12_month_yield_pct",
        size="overall_score",
        hover_name="ticker",
        color="overall_rating",
        title="Yield vs. 1-Year Price/NAV Return",
        labels={
            "return_1y_price_pct": "1-Year Price/NAV Return (%)",
            "trailing_12_month_yield_pct": "Trailing 12-Month Yield (%)"
        }
    )
    st.plotly_chart(scatter_chart, use_container_width=True)

# ------------------------------------------------------------
# Red flag review
# ------------------------------------------------------------

st.subheader("Review Flags")

red_flags = filtered_df[
    filtered_df["review_priority"].str.contains("High priority|Review", case=False, na=False)
].copy()

if red_flags.empty:
    st.success("No high-priority review flags based on the current scoring rules.")
else:
    st.dataframe(
        red_flags[
            [
                "ticker",
                "overall_score",
                "review_priority",
                "trailing_12_month_yield_pct",
                "return_1y_price_pct",
                "approx_1y_total_return_pct",
                "yield_method_warning",
                "nav_erosion_warning",
            ]
        ],
        use_container_width=True,
        hide_index=True
    )

# ------------------------------------------------------------
# Ticker detail
# ------------------------------------------------------------

st.subheader("Ticker Detail")

ticker_list = sorted(filtered_df["ticker"].dropna().unique())
selected_ticker = st.selectbox("Select ticker", ticker_list)

ticker_row = filtered_df[filtered_df["ticker"] == selected_ticker].iloc[0]

detail_col1, detail_col2, detail_col3 = st.columns(3)

with detail_col1:
    st.metric("Overall score", ticker_row["overall_score"])
    st.metric("Trailing 12M yield", f"{ticker_row['trailing_12_month_yield_pct']:.2f}%")

with detail_col2:
    st.metric("1Y price/NAV return", f"{ticker_row['return_1y_price_pct']:.2f}%")
    st.metric("Approx. 1Y total return", f"{ticker_row['approx_1y_total_return_pct']:.2f}%")

with detail_col3:
    st.metric("Largest 1Y price decline", f"{ticker_row['largest_1y_price_decline_pct']:.2f}%")
    st.metric("Payment count", int(ticker_row["number_of_payments_last_12_months"]))

st.write("**Review priority:**", ticker_row["review_priority"])
st.write("**Yield method warning:**", ticker_row["yield_method_warning"])
st.write("**NAV/price warning:**", ticker_row["nav_erosion_warning"])
st.write("**Scout comment:**", ticker_row["scout_comment"])
st.write("**Notes:**", ticker_row["notes"])

# ------------------------------------------------------------
# Footer
# ------------------------------------------------------------

st.divider()
st.caption(
    "This dashboard is a scouting tool only. It uses available market/distribution data "
    "and simplified scoring rules. It does not make investment decisions."
)