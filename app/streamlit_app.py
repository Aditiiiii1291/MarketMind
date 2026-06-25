"""Beginner-friendly Streamlit dashboard for MarketMind product insights."""

from pathlib import Path
import sys

import pandas as pd
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.scoring_engine import analyze_product_health  # noqa: E402


st.set_page_config(
    page_title="MarketMind Product Insights",
    layout="wide",
)

DATA_PATH = PROJECT_ROOT / "data" / "processed" / "marketmind_clean_reviews.csv"


@st.cache_data
def load_reviews(data_path):
    """Load the processed review dataset for dashboard analysis."""
    return pd.read_csv(data_path)


def build_sentiment_table(sentiment_distribution):
    """Convert the scoring-engine sentiment dictionary into a display table."""
    rows = []

    for sentiment, values in sentiment_distribution.items():
        rows.append(
            {
                "Sentiment": sentiment.title(),
                "Review Count": values["count"],
                "Percentage": f"{values['percentage']}%",
            }
        )

    return pd.DataFrame(rows)


def show_matched_products(product_names):
    """Display matched products without making long names hard to scan."""
    st.subheader("Matched Product Name(s)")

    if len(product_names) == 1:
        st.write(product_names[0])
    else:
        matched_products_df = pd.DataFrame({"Product Name": product_names})
        st.dataframe(matched_products_df, use_container_width=True, hide_index=True)


def show_analysis_result(result):
    """Render a successful product health analysis result."""
    metrics = result["metrics"]
    negative_percentage = metrics["negative_percentage"]

    show_matched_products(result["matched_product_names"])

    st.subheader("Product Summary")
    st.write(f"Review count: **{metrics['review_count']}**")
    st.write(f"Average rating: **{metrics['average_rating']} / 5**")
    st.write(f"Health score: **{result['health_score']} / 100**")
    st.write(f"Health label: **{result['health_label']}**")

    metric_columns = st.columns(3)
    metric_columns[0].metric("Health Score", f"{result['health_score']} / 100")
    metric_columns[1].metric("Average Rating", f"{metrics['average_rating']} / 5")
    metric_columns[2].metric("Negative Review Percentage", f"{negative_percentage}%")

    st.subheader("Sentiment Distribution")
    sentiment_table = build_sentiment_table(result["sentiment_distribution"])
    st.dataframe(sentiment_table, use_container_width=True, hide_index=True)

    st.subheader("Complaint Category Summary")
    category_summary = result["category_summary"]
    if category_summary.empty:
        st.info("No complaint categories were found for this product.")
    else:
        st.dataframe(category_summary, use_container_width=True, hide_index=True)

    st.subheader("Recommendations")
    for recommendation in result["recommendations"]:
        st.markdown(f"- {recommendation}")


st.title("MarketMind — Product Feedback Intelligence")
st.write(
    "Analyze product reviews using sentiment, complaint categories, and a "
    "transparent product health score."
)

st.sidebar.header("Product Analysis")
product_query = st.sidebar.text_input("Product query", value="AWC-38")
analyze_clicked = st.sidebar.button("Analyze Product", type="primary")

if analyze_clicked:
    if product_query.strip() == "":
        st.warning("Please enter a product query before running the analysis.")
    else:
        try:
            reviews_df = load_reviews(DATA_PATH)
            analysis_result = analyze_product_health(reviews_df, product_query)
        except FileNotFoundError:
            st.error(f"Processed dataset not found: {DATA_PATH}")
        except Exception as exc:
            st.error(f"Unable to analyze this product: {exc}")
        else:
            if "error" in analysis_result:
                st.warning(analysis_result["error"])
                st.write(
                    "Try a more specific product name, a visible model number, "
                    "or another keyword from the product title."
                )
            else:
                show_analysis_result(analysis_result)
else:
    st.info("Enter a product query in the sidebar, then click Analyze Product.")

st.divider()
st.caption(
    "Scores are based on review ratings and sentiment distribution. Complaint "
    "categories are keyword/rule-based. This is a review-analysis prototype, "
    "not a real product launch decision system."
)
