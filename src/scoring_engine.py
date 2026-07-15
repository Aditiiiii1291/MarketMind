"""Score product health from transparent MarketMind review signals.

This module uses ratings, sentiment labels, and complaint categories to create
a readable product health score. It does not train a new model or use an LLM.
"""

import argparse

import pandas as pd

try:
    from src.config import PROCESSED_REVIEWS_PATH, PRODUCT_HEALTH_REPORT_PATH
    from src.logger import logger
    from src.utils.file_io import ensure_parent_dir, load_csv
except ImportError:
    from config import PROCESSED_REVIEWS_PATH, PRODUCT_HEALTH_REPORT_PATH
    from logger import logger
    from utils.file_io import ensure_parent_dir, load_csv

try:
    from complaint_miner import (
        add_complaint_categories,
        build_category_summary,
        extract_top_complaints,
        get_negative_reviews,
        get_product_reviews,
    )
except ImportError:
    from src.complaint_miner import (
        add_complaint_categories,
        build_category_summary,
        extract_top_complaints,
        get_negative_reviews,
        get_product_reviews,
    )


DEFAULT_INPUT_PATH = PROCESSED_REVIEWS_PATH
DEFAULT_OUTPUT_PATH = PRODUCT_HEALTH_REPORT_PATH
SENTIMENT_LABELS = ["negative", "neutral", "positive"]


def load_processed_data(file_path):
    """Load the processed review CSV file.

    Args:
        file_path: Path to the processed CSV file.

    Returns:
        A pandas DataFrame containing processed reviews.
    """
    return load_csv(file_path, description="Processed review CSV")


def calculate_sentiment_distribution(product_reviews):
    """Calculate sentiment counts and percentages for one product.

    Args:
        product_reviews: DataFrame containing reviews for one product.

    Returns:
        A dictionary with counts and percentages for each sentiment label.
    """
    review_count = len(product_reviews)
    sentiment_counts = product_reviews["sentiment"].value_counts()
    distribution = {}

    for sentiment in SENTIMENT_LABELS:
        count = int(sentiment_counts.get(sentiment, 0))
        if review_count == 0:
            percentage = 0.0
        else:
            percentage = round((count / review_count) * 100, 2)

        distribution[sentiment] = {
            "count": count,
            "percentage": percentage,
        }

    return distribution


def calculate_product_metrics(product_reviews):
    """Calculate the main review metrics used by the health score.

    Args:
        product_reviews: DataFrame containing reviews for one product.

    Returns:
        A dictionary with review count, average rating, and sentiment percentages.
    """
    sentiment_distribution = calculate_sentiment_distribution(product_reviews)
    ratings = pd.to_numeric(product_reviews["rating"], errors="coerce")
    average_rating = ratings.mean()

    if pd.isna(average_rating):
        average_rating = 0.0

    metrics = {
        "review_count": len(product_reviews),
        "average_rating": round(float(average_rating), 2),
        "positive_percentage": sentiment_distribution["positive"]["percentage"],
        "neutral_percentage": sentiment_distribution["neutral"]["percentage"],
        "negative_percentage": sentiment_distribution["negative"]["percentage"],
    }

    return metrics


def calculate_health_score(metrics):
    """Calculate a transparent product health score from 0 to 100.

    The formula gives 45% weight to average rating, 35% weight to positive
    sentiment, and 20% weight to avoiding negative sentiment.

    Args:
        metrics: Dictionary returned by calculate_product_metrics.

    Returns:
        A health score rounded to 2 decimal places.
    """
    average_rating = metrics["average_rating"]
    positive_percentage = metrics["positive_percentage"]
    negative_percentage = metrics["negative_percentage"]

    # Convert the 1-5 star rating into a 0-45 point component.
    rating_component = (average_rating / 5) * 45

    # Reward products with a high share of positive reviews.
    positive_component = positive_percentage * 0.35

    # Reward products that keep negative feedback low.
    negative_resilience_component = (100 - negative_percentage) * 0.20

    health_score = (
        rating_component + positive_component + negative_resilience_component
    )

    return round(health_score, 2)


def get_health_label(health_score):
    """Convert a numeric health score into a readable label."""
    if health_score >= 80:
        return "Strong Product Health"
    if health_score >= 65:
        return "Moderate Product Health"

    return "Needs Improvement"


def generate_recommendations(category_summary_df, health_label):
    """Create short rule-based recommendations from complaint categories.

    Args:
        category_summary_df: Complaint category summary DataFrame.
        health_label: Label returned by get_health_label.

    Returns:
        A list of 2 to 4 recommendations.
    """
    if category_summary_df.empty:
        return [
            "No major complaint categories found; continue monitoring new reviews.",
            "Maintain the strengths reflected in current rating and sentiment trends.",
        ]

    recommendation_map = {
        "Quality": "Prioritize quality-control improvements.",
        "Functionality": "Investigate reliability and product-performance issues.",
        "Value for Money": "Review pricing, perceived value, or product expectations.",
        "Expectation Mismatch": "Improve listing accuracy and product communication.",
        "Overall Dissatisfaction": (
            "Review recurring negative feedback and customer support issues."
        ),
    }
    recommendations = []
    sorted_categories = category_summary_df.sort_values(
        by="total_frequency",
        ascending=False,
    )

    for category in sorted_categories["category"]:
        recommendation = recommendation_map.get(
            category,
            "Review other recurring complaint themes for improvement opportunities.",
        )
        if recommendation not in recommendations:
            recommendations.append(recommendation)

        if len(recommendations) == 3:
            break

    if health_label == "Needs Improvement":
        recommendations.append("Set a short-term action plan for the top complaint area.")
    elif health_label == "Strong Product Health":
        recommendations.append("Protect current strengths while monitoring new complaints.")
    else:
        recommendations.append("Focus on the highest complaint area to improve consistency.")

    return recommendations[:4]


def analyze_product_health(df, product_query):
    """Run product health scoring for one product query.

    Args:
        df: DataFrame containing all processed reviews.
        product_query: Exact or partial product name query.

    Returns:
        A dictionary containing metrics, score, label, complaints, and recommendations.
    """
    clean_query = str(product_query).strip()

    if clean_query == "":
        return {
            "error": "Please provide a non-empty product query.",
            "product_query": product_query,
        }

    product_reviews = get_product_reviews(df, clean_query)

    if product_reviews.empty:
        return {
            "error": f'No reviews found for product: "{clean_query}"',
            "product_query": clean_query,
        }

    metrics = calculate_product_metrics(product_reviews)
    health_score = calculate_health_score(metrics)
    health_label = get_health_label(health_score)

    negative_reviews = get_negative_reviews(product_reviews)
    top_complaints = extract_top_complaints(negative_reviews, top_n=20)
    categorized_complaints = add_complaint_categories(top_complaints)
    category_summary = build_category_summary(categorized_complaints)
    recommendations = generate_recommendations(category_summary, health_label)
    sentiment_distribution = calculate_sentiment_distribution(product_reviews)
    matched_product_names = product_reviews["product_name"].dropna().unique().tolist()

    return {
        "product_query": clean_query,
        "matched_product_names": matched_product_names,
        "product_reviews": product_reviews,
        "metrics": metrics,
        "sentiment_distribution": sentiment_distribution,
        "health_score": health_score,
        "health_label": health_label,
        "negative_reviews": negative_reviews,
        "category_summary": category_summary,
        "recommendations": recommendations,
    }


def save_product_health_report(result, output_path):
    """Save a one-row product health report as a CSV file.

    Args:
        result: Dictionary returned by analyze_product_health.
        output_path: Destination path for the report CSV.
    """
    metrics = result["metrics"]
    report_df = pd.DataFrame(
        [
            {
                "product_query": result["product_query"],
                "review_count": metrics["review_count"],
                "average_rating": metrics["average_rating"],
                "positive_percentage": metrics["positive_percentage"],
                "neutral_percentage": metrics["neutral_percentage"],
                "negative_percentage": metrics["negative_percentage"],
                "health_score": result["health_score"],
                "health_label": result["health_label"],
            }
        ]
    )

    output_path = ensure_parent_dir(output_path)
    report_df.to_csv(output_path, index=False)


def parse_args():
    """Parse command line arguments for product health scoring."""
    parser = argparse.ArgumentParser(
        description="Score product health using ratings, sentiment, and complaints."
    )
    parser.add_argument(
        "--product",
        required=True,
        help="Exact or partial product name to score.",
    )

    return parser.parse_args()


def print_product_health_result(result):
    """Print a readable product health analysis result."""
    print("Matched product name(s):")
    for product_name in result["matched_product_names"]:
        display_product_name = (
            str(product_name).encode("ascii", errors="replace").decode("ascii")
        )
        print(f"- {display_product_name}")

    metrics = result["metrics"]
    print(f"\nReview count: {metrics['review_count']}")
    print(f"Average rating: {metrics['average_rating']}")

    print("\nSentiment distribution:")
    for sentiment, values in result["sentiment_distribution"].items():
        print(
            f"- {sentiment}: {values['count']} reviews "
            f"({values['percentage']}%)"
        )

    print(f"\nHealth score: {result['health_score']}")
    print(f"Health label: {result['health_label']}")

    print("\nTop complaint categories:")
    if result["category_summary"].empty:
        print("No complaint categories found.")
    else:
        print(result["category_summary"])

    print("\nRecommendations:")
    for recommendation in result["recommendations"]:
        print(f"- {recommendation}")


if __name__ == "__main__":
    args = parse_args()

    if args.product.strip() == "":
        print("Please provide a non-empty product query.")
    else:
        try:
            reviews_df = load_processed_data(DEFAULT_INPUT_PATH)
        except FileNotFoundError as error:
            logger.error(error)
            raise SystemExit(1)

        analysis_result = analyze_product_health(reviews_df, args.product)

        if "error" in analysis_result:
            print(analysis_result["error"])
        else:
            print_product_health_result(analysis_result)
            save_product_health_report(analysis_result, DEFAULT_OUTPUT_PATH)
            print(f"\nProduct health report saved to: {DEFAULT_OUTPUT_PATH}")
