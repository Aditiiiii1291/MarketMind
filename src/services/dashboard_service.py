"""Dashboard preparation services for MarketMind."""

import pandas as pd

try:
    from src.config import PROCESSED_REVIEWS_PATH
    from src.services import concept_service, product_service
except ImportError:
    from config import PROCESSED_REVIEWS_PATH
    from services import concept_service, product_service


DEFAULT_DASHBOARD_DATA_PATH = PROCESSED_REVIEWS_PATH


def load_dashboard_data(data_path=PROCESSED_REVIEWS_PATH):
    """Load review data for dashboard workflows."""
    return product_service.load_product_data(data_path)


def prepare_dashboard_metrics(result):
    """Prepare metric values from a product or concept result."""
    if "metrics" in result:
        metrics = result["metrics"]
        return {
            "review_count": metrics["review_count"],
            "average_rating": metrics["average_rating"],
            "negative_percentage": metrics["negative_percentage"],
            "health_score": result["health_score"],
            "health_label": result["health_label"],
        }

    return concept_service.build_launch_summary(result)


def prepare_dashboard_tables(result):
    """Prepare dashboard table data from product analysis results."""
    sentiment_rows = []
    for sentiment, values in result["sentiment_distribution"].items():
        sentiment_rows.append(
            {
                "Sentiment": sentiment.title(),
                "Review Count": values["count"],
                "Percentage": f"{values['percentage']}%",
            }
        )

    return {
        "sentiment_table": pd.DataFrame(sentiment_rows),
        "category_summary": result["category_summary"],
        "matched_products_table": pd.DataFrame(
            {"Product Name": result["matched_product_names"]}
        ),
    }


def analyze_product_for_dashboard(product_query, reviews_df=None):
    """Analyze one product for dashboard display."""
    return product_service.analyze_product(product_query, reviews_df=reviews_df)


def simulate_concept_for_dashboard(
    product_name,
    category,
    price,
    features,
    description,
):
    """Simulate a product concept for dashboard display."""
    return concept_service.simulate_concept(
        product_name=product_name,
        category=category,
        price=price,
        features=features,
        description=description,
    )
