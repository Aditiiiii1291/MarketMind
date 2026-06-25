"""Beginner-friendly Streamlit dashboard for MarketMind product insights."""

from pathlib import Path
import sys

import pandas as pd
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.scoring_engine import analyze_product_health  # noqa: E402
from src.concept_simulator import simulate_product_concept  # noqa: E402


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


def show_concept_simulation_result(result):
    """Render a product concept simulation result."""
    st.subheader("Product Concept Summary")
    st.write(f"Product name: **{result['product_name']}**")
    st.write(f"Category: **{result['category'] or 'Not specified'}**")
    st.write(f"Price: **{result['price'] or 'Not specified'}**")
    st.write(f"Key features: **{result['features'] or 'Not specified'}**")
    st.write(f"Description: {result['description']}")

    summary_columns = st.columns(3)
    summary_columns[0].metric(
        "Similar Historical Reviews",
        result["similar_review_count"],
    )
    summary_columns[1].metric("Launch Score", f"{result['launch_score']} / 100")
    summary_columns[2].metric("Launch Label", result["launch_label"])

    st.info(
        "Persona responses are simulated, data-backed estimates based on similar "
        "historical review patterns. They are not real customer feedback or "
        "guaranteed market demand."
    )

    st.subheader("Persona Feedback Simulation")
    persona_simulations = result["persona_simulations"]

    for _, persona_row in persona_simulations.iterrows():
        with st.expander(str(persona_row["persona_name"]), expanded=True):
            persona_columns = st.columns(3)
            persona_columns[0].metric(
                "Simulated Rating",
                f"{persona_row['simulated_rating']} / 5",
            )
            persona_columns[1].metric("Confidence", persona_row["confidence"])
            persona_columns[2].metric(
                "Evidence Reviews",
                persona_row.get(
                    "evidence_review_count",
                    persona_row["review_count_used"],
                ),
            )

            st.write(f"Likely concern: **{persona_row['likely_concern']}**")
            st.markdown("**Simulated Persona Response**")
            st.write(persona_row["persona_response"])

    st.subheader("Launch Recommendations")
    for recommendation in result["recommendations"]:
        st.markdown(f"- {recommendation}")


st.title("MarketMind — Product Feedback Intelligence")
st.write(
    "Analyze existing product reviews and simulate concept feedback using "
    "sentiment, complaint categories, feedback personas, and product health signals."
)

concept_tab, existing_product_tab = st.tabs(
    ["Product Concept Simulator", "Existing Product Analyzer"]
)

with concept_tab:
    st.header("Product Concept Simulator")
    st.write(
        "Enter a new product concept to estimate how feedback personas may respond "
        "based on similar historical review patterns."
    )

    product_name = st.text_input("Product name")
    category = st.text_input("Category")
    price = st.text_input("Price")
    features = st.text_area("Key features")
    description = st.text_area("Product description")

    simulate_clicked = st.button("Simulate Persona Feedback", type="primary")

    if simulate_clicked:
        if product_name.strip() == "":
            st.warning("Please enter a product name before running the simulation.")
        elif description.strip() == "":
            st.warning(
                "Please enter a product description before running the simulation."
            )
        else:
            try:
                with st.spinner("Finding similar reviews and simulating personas..."):
                    concept_result = simulate_product_concept(
                        product_name=product_name,
                        category=category,
                        price=price,
                        features=features,
                        description=description,
                    )
            except Exception as exc:
                st.error(f"Unable to simulate this product concept: {exc}")
            else:
                if "error" in concept_result:
                    st.warning(concept_result["error"])
                else:
                    show_concept_simulation_result(concept_result)
    else:
        st.info(
            "Fill in the product name and description, then click "
            "Simulate Persona Feedback."
        )

with existing_product_tab:
    st.header("Existing Product Analyzer")
    st.write(
        "Analyze a product already present in the processed review dataset using "
        "ratings, sentiment distribution, complaint categories, and a product "
        "health score."
    )

    product_query = st.text_input("Product query", value="AWC-38")
    analyze_clicked = st.button("Analyze Product", type="primary")

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
        st.info("Enter a product query, then click Analyze Product.")

    st.divider()
    st.caption(
        "Scores are based on review ratings and sentiment distribution. Complaint "
        "categories are keyword/rule-based. This is a review-analysis prototype, "
        "not a real product launch decision system."
    )
