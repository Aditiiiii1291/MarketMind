"""Compare and rank products using MarketMind health scoring.

This module reuses the transparent product health analysis from scoring_engine.
It does not duplicate the scoring formula or train a new model.
"""

import argparse

import pandas as pd

try:
    from scoring_engine import DEFAULT_INPUT_PATH, analyze_product_health
    from scoring_engine import load_processed_data
    from config import PRODUCT_COMPARISON_REPORT_PATH
    from logger import logger
    from utils.file_io import ensure_parent_dir
except ImportError:
    from src.scoring_engine import DEFAULT_INPUT_PATH, analyze_product_health
    from src.scoring_engine import load_processed_data
    from src.config import PRODUCT_COMPARISON_REPORT_PATH
    from src.logger import logger
    from src.utils.file_io import ensure_parent_dir


DEFAULT_OUTPUT_PATH = PRODUCT_COMPARISON_REPORT_PATH


def make_console_safe(value):
    """Return text that is safe to print on basic Windows consoles."""
    return str(value).encode("ascii", errors="replace").decode("ascii")


def get_top_concern(category_summary_df):
    """Return the most frequent complaint category for a product."""
    if category_summary_df.empty:
        return "No complaint data"

    sorted_categories = category_summary_df.sort_values(
        by="total_frequency",
        ascending=False,
    )

    return sorted_categories.iloc[0]["category"]


def compare_products(df, product_queries):
    """Compare 2 to 5 products using the existing health-scoring logic.

    Args:
        df: DataFrame containing processed reviews.
        product_queries: List of exact or partial product search queries.

    Returns:
        A DataFrame with one row per successfully matched product query.
    """
    if len(product_queries) < 2 or len(product_queries) > 5:
        raise ValueError("Please provide 2 to 5 product queries.")

    comparison_rows = []

    for product_query in product_queries:
        result = analyze_product_health(df, product_query)

        if "error" in result:
            logger.warning("Product comparison skipped query: %s", result["error"])
            continue

        metrics = result["metrics"]
        matched_product_names = result["matched_product_names"]
        if matched_product_names:
            matched_product_name = make_console_safe(matched_product_names[0])
        else:
            matched_product_name = "Unknown product"

        comparison_rows.append(
            {
                "product_query": result["product_query"],
                "matched_product_name": matched_product_name,
                "review_count": metrics["review_count"],
                "average_rating": metrics["average_rating"],
                "positive_percentage": metrics["positive_percentage"],
                "neutral_percentage": metrics["neutral_percentage"],
                "negative_percentage": metrics["negative_percentage"],
                "health_score": result["health_score"],
                "health_label": result["health_label"],
                "top_concern": get_top_concern(result["category_summary"]),
            }
        )

    comparison_df = pd.DataFrame(comparison_rows)

    return comparison_df


def rank_products(comparison_df):
    """Rank products from highest to lowest health score.

    Args:
        comparison_df: DataFrame returned by compare_products.

    Returns:
        A ranked comparison DataFrame with a rank column starting at 1.
    """
    if comparison_df.empty:
        return comparison_df.copy()

    ranked_df = comparison_df.sort_values(
        by="health_score",
        ascending=False,
    ).reset_index(drop=True)
    ranked_df.insert(0, "rank", range(1, len(ranked_df) + 1))

    return ranked_df


def generate_comparison_insight(ranked_df):
    """Create a short rule-based summary of the ranked products.

    Args:
        ranked_df: DataFrame returned by rank_products.

    Returns:
        A short text insight.
    """
    if len(ranked_df) < 2:
        return "At least 2 valid matched products are needed for comparison insight."

    strongest_product = ranked_df.iloc[0]
    weakest_product = ranked_df.iloc[-1]
    score_difference = round(
        strongest_product["health_score"] - weakest_product["health_score"],
        2,
    )

    return (
        f'The strongest product is "{strongest_product["matched_product_name"]}" '
        f'with a health score of {strongest_product["health_score"]}. '
        f'The weakest product is "{weakest_product["matched_product_name"]}" '
        f'with a health score of {weakest_product["health_score"]}. '
        f"The score difference is {score_difference} points. "
        f'The weakest product\'s top concern is "{weakest_product["top_concern"]}".'
    )


def save_comparison_report(ranked_df, output_path):
    """Save the ranked product comparison report to a CSV file.

    Args:
        ranked_df: DataFrame returned by rank_products.
        output_path: Destination path for the report CSV.
    """
    output_path = ensure_parent_dir(output_path)
    ranked_df.to_csv(output_path, index=False)


def parse_args():
    """Parse command line arguments for product comparison."""
    parser = argparse.ArgumentParser(
        description="Compare 2 to 5 products using product health scores."
    )
    parser.add_argument(
        "--product",
        action="append",
        required=True,
        help="Product search query. Repeat this argument for each product.",
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    product_queries = args.product

    if len(product_queries) < 2 or len(product_queries) > 5:
        logger.error("Please provide 2 to 5 products using repeated --product arguments.")
    else:
        try:
            reviews_df = load_processed_data(DEFAULT_INPUT_PATH)
        except FileNotFoundError as error:
            logger.error(error)
            raise SystemExit(1)
        comparison = compare_products(reviews_df, product_queries)
        ranked_products = rank_products(comparison)
        insight = generate_comparison_insight(ranked_products)

        if ranked_products.empty:
            logger.info("No matching products found for comparison.")
        else:
            logger.info("Ranked Product Comparison:\n%s", ranked_products)

            logger.info("Comparison Insight: %s", insight)

            save_comparison_report(ranked_products, DEFAULT_OUTPUT_PATH)
            logger.info("Product comparison report saved to: %s", DEFAULT_OUTPUT_PATH)
