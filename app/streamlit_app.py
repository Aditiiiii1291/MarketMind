"""Beginner-friendly Streamlit dashboard for MarketMind product insights."""

import html
from pathlib import Path
import sys

import pandas as pd
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.logger import logger  # noqa: E402
from src.services import dashboard_service  # noqa: E402


st.set_page_config(
    page_title="MarketMind Product Insights",
    layout="wide",
)

DATA_PATH = dashboard_service.DEFAULT_DASHBOARD_DATA_PATH


def apply_custom_styles():
    """Add a restrained visual layer for a cleaner dashboard presentation."""
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 1180px;
        }

        .marketmind-hero {
            border: 1px solid rgba(120, 120, 120, 0.22);
            border-radius: 10px;
            padding: 1.35rem 1.5rem;
            margin-bottom: 1.2rem;
            background: rgba(127, 127, 127, 0.06);
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.06);
        }

        .marketmind-hero h1 {
            margin: 0 0 0.35rem 0;
            font-size: 2.35rem;
            line-height: 1.1;
            letter-spacing: 0;
        }

        .marketmind-hero h2 {
            margin: 0 0 0.65rem 0;
            font-size: 1.05rem;
            line-height: 1.45;
            font-weight: 600;
            color: inherit;
            opacity: 0.86;
        }

        .marketmind-hero p {
            margin: 0;
            max-width: 840px;
            line-height: 1.55;
            opacity: 0.82;
        }

        .quote-block {
            border-left: 4px solid rgba(77, 124, 254, 0.75);
            border-radius: 6px;
            padding: 0.85rem 1rem;
            margin-top: 0.45rem;
            background: rgba(127, 127, 127, 0.08);
            font-size: 1.02rem;
            line-height: 1.6;
        }

        div.stButton > button[kind="primary"] {
            width: 100%;
            min-height: 3rem;
            font-weight: 700;
        }

        div[data-testid="stMetric"] {
            border: 1px solid rgba(120, 120, 120, 0.2);
            border-radius: 8px;
            padding: 0.85rem 1rem;
            background: rgba(127, 127, 127, 0.05);
            box-shadow: 0 4px 14px rgba(0, 0, 0, 0.04);
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 0.4rem;
        }

        .stTabs [data-baseweb="tab"] {
            border-radius: 8px 8px 0 0;
            padding-left: 1rem;
            padding-right: 1rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def show_hero():
    """Render the MarketMind dashboard hero."""
    st.markdown(
        """
        <section class="marketmind-hero">
            <h1>MarketMind</h1>
            <h2>Data-backed product feedback simulation and review intelligence</h2>
            <p>
                Test a product concept against simulated feedback personas and
                review existing product health signals.
            </p>
        </section>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data
def load_reviews(data_path):
    """Load the processed review dataset for dashboard analysis."""
    return dashboard_service.load_dashboard_data(data_path)


def build_sentiment_table(sentiment_distribution):
    """Convert sentiment distribution values into a dashboard table."""
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
        matched_products_table = pd.DataFrame({"Product Name": product_names})
        st.dataframe(
            matched_products_table,
            use_container_width=True,
            hide_index=True,
        )


def show_launch_status_message(launch_label):
    """Display a clear interpretation of the concept launch label."""
    if launch_label == "Promising Concept":
        st.success(
            "Promising concept: the simulated signals suggest this idea has a "
            "stronger starting point for customer interest."
        )
    elif launch_label == "Needs Refinement":
        st.warning(
            "Needs refinement: the concept shows potential, but the feedback "
            "signals point to areas worth tightening before launch."
        )
    elif launch_label == "High Launch Risk":
        st.error(
            "High launch risk: the historical patterns suggest meaningful "
            "concerns that should be addressed before moving forward."
        )
    else:
        st.info("Review the launch score and persona feedback before taking action.")


def show_recommendations(recommendations):
    """Render recommendations in a bordered section."""
    with st.container(border=True):
        st.subheader("Recommended Next Actions")
        for recommendation in recommendations:
            st.markdown(f"- {recommendation}")


def show_analysis_result(result):
    """Render a successful product health analysis result."""
    metrics = result.metrics
    dashboard_metrics = dashboard_service.prepare_dashboard_metrics(result)
    dashboard_tables = dashboard_service.prepare_dashboard_tables(result)
    negative_percentage = dashboard_metrics.negative_percentage

    show_matched_products(dashboard_tables.matched_product_names)

    st.subheader("Product Summary")
    st.write(f"Review count: **{metrics['review_count']}**")
    st.write(f"Health label: **{result.health_label}**")

    metric_columns = st.columns(3)
    metric_columns[0].metric("Health Score", f"{result.health_score} / 100")
    metric_columns[1].metric("Average Rating", f"{metrics['average_rating']} / 5")
    metric_columns[2].metric("Negative Review Percentage", f"{negative_percentage}%")

    st.progress(min(max(result.health_score, 0), 100) / 100)

    st.subheader("Sentiment Distribution")
    sentiment_table = build_sentiment_table(dashboard_tables.sentiment_distribution)
    st.dataframe(sentiment_table, use_container_width=True, hide_index=True)

    st.subheader("Complaint Category Summary")
    category_summary = dashboard_tables.category_summary
    if category_summary.empty:
        st.info("No complaint categories were found for this product.")
    else:
        st.dataframe(category_summary, use_container_width=True, hide_index=True)

    show_recommendations(result.recommendations)


def show_concept_simulation_result(result):
    """Render a product concept simulation result."""
    st.subheader("Product Concept Summary")
    with st.container(border=True):
        st.write(f"Product name: **{result.product_name}**")
        st.write(f"Category: **{result.category or 'Not specified'}**")
        st.write(f"Price: **{result.price or 'Not specified'}**")
        st.write(f"Key features: **{result.features or 'Not specified'}**")
        st.write(f"Description: {result.description}")

    summary_columns = st.columns(3)
    summary_columns[0].metric("Launch Score", f"{result.launch_score} / 100")
    summary_columns[1].metric("Launch Label", result.launch_label)
    summary_columns[2].metric(
        "Similar Historical Reviews",
        result.similar_review_count,
    )

    st.progress(min(max(result.launch_score, 0), 100) / 100)
    show_launch_status_message(result.launch_label)

    st.info(
        "Persona responses are simulated, data-backed estimates based on similar "
        "historical review patterns. They are not real customer feedback or "
        "guaranteed market demand."
    )

    st.subheader("Persona Feedback Simulation")
    persona_simulations = result.persona_simulations

    for persona_row in persona_simulations:
        with st.container(border=True):
            st.markdown(f"#### {persona_row.persona_name}")
            persona_columns = st.columns(3)
            persona_columns[0].metric(
                "Simulated Rating",
                f"{persona_row.simulated_rating} / 5",
            )
            persona_columns[1].metric("Confidence", persona_row.confidence)
            evidence_review_count = persona_row.evidence_review_count
            if evidence_review_count is None:
                evidence_review_count = persona_row.review_count_used
            persona_columns[2].metric(
                "Evidence Reviews",
                evidence_review_count,
            )

            st.markdown(f"**Likely Concern:** {persona_row.likely_concern}")
            st.markdown("**Persona Response**")
            persona_response = html.escape(str(persona_row.persona_response))
            st.markdown(
                f"<div class='quote-block'>{persona_response}</div>",
                unsafe_allow_html=True,
            )

    show_recommendations(result.recommendations)


apply_custom_styles()
show_hero()

concept_tab, existing_product_tab = st.tabs(
    ["Product Concept Simulator", "Existing Product Analyzer"]
)

with concept_tab:
    st.header("Product Concept Simulator")
    st.write(
        "Enter a new product concept to estimate how feedback personas may respond "
        "based on similar historical review patterns."
    )

    with st.container(border=True):
        first_row = st.columns(2)
        product_name = first_row[0].text_input("Product name")
        category = first_row[1].text_input("Category")

        second_row = st.columns(2)
        price = second_row[0].text_input("Price")
        features = second_row[1].text_area("Key features", height=100)

        description = st.text_area("Product description", height=140)

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
                    concept_response = dashboard_service.simulate_concept_for_dashboard(
                        product_name=product_name,
                        category=category,
                        price=price,
                        features=features,
                        description=description,
                    )
            except Exception as exc:
                logger.error("Concept simulation failed: %s", exc)
                st.error(f"Unable to simulate this product concept: {exc}")
            else:
                if concept_response.error:
                    st.warning(concept_response.error)
                else:
                    show_concept_simulation_result(concept_response.result)
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
                analysis_response = dashboard_service.analyze_product_for_dashboard(
                    product_query,
                    reviews_df=reviews_df,
                )
            except FileNotFoundError as exc:
                logger.error(exc)
                st.error(f"Processed dataset not found: {DATA_PATH}")
            except Exception as exc:
                logger.error("Product analysis failed: %s", exc)
                st.error(f"Unable to analyze this product: {exc}")
            else:
                if analysis_response.error:
                    st.warning(analysis_response.error)
                    st.write(
                        "Try a more specific product name, a visible model number, "
                        "or another keyword from the product title."
                    )
                else:
                    show_analysis_result(analysis_response.result)
    else:
        st.info("Enter a product query, then click Analyze Product.")

st.divider()
st.caption(
    "MarketMind is a review-analysis prototype. Persona feedback is simulated "
    "from historical review patterns."
)
