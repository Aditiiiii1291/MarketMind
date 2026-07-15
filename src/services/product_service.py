"""Product-oriented service functions for MarketMind workflows."""

try:
    from src.config import PROCESSED_REVIEWS_PATH
    from src.complaint_miner import get_product_reviews as _filter_product_reviews
    from src.product_comparator import (
        compare_products as _build_product_comparison,
        generate_comparison_insight,
        rank_products,
    )
    from src.schemas.product_schema import (
        ProductComparison,
        ProductHealth,
        ProductSummary,
    )
    from src.scoring_engine import analyze_product_health, load_processed_data
except ImportError:
    from config import PROCESSED_REVIEWS_PATH
    from complaint_miner import get_product_reviews as _filter_product_reviews
    from product_comparator import (
        compare_products as _build_product_comparison,
        generate_comparison_insight,
        rank_products,
    )
    from schemas.product_schema import ProductComparison, ProductHealth, ProductSummary
    from scoring_engine import analyze_product_health, load_processed_data


def load_product_data(data_path=PROCESSED_REVIEWS_PATH):
    """Load the processed review data used by product services."""
    return load_processed_data(data_path)


def _get_reviews_dataframe(reviews_df=None, data_path=PROCESSED_REVIEWS_PATH):
    """Return provided reviews or load the default processed dataset."""
    if reviews_df is not None:
        return reviews_df

    return load_product_data(data_path)


def _build_product_health(result):
    """Wrap a raw product health result in a ProductHealth response."""
    if "error" in result:
        return ProductHealth(
            product_query=result.get("product_query"),
            error=result["error"],
        )

    return ProductHealth(
        product_query=result["product_query"],
        matched_product_names=result["matched_product_names"],
        product_reviews=result["product_reviews"],
        metrics=result["metrics"],
        sentiment_distribution=result["sentiment_distribution"],
        health_score=result["health_score"],
        health_label=result["health_label"],
        negative_reviews=result["negative_reviews"],
        category_summary=result["category_summary"],
        recommendations=result["recommendations"],
    )


def analyze_product(product_query, reviews_df=None, data_path=PROCESSED_REVIEWS_PATH):
    """Analyze one product by delegating to the existing health scoring engine."""
    reviews_df = _get_reviews_dataframe(reviews_df, data_path)
    result = analyze_product_health(reviews_df, product_query)
    return _build_product_health(result)


def compare_products(product_queries, reviews_df=None, data_path=PROCESSED_REVIEWS_PATH):
    """Compare product queries using the existing product comparison workflow."""
    reviews_df = _get_reviews_dataframe(reviews_df, data_path)
    comparison_df = _build_product_comparison(reviews_df, product_queries)
    ranked_df = rank_products(comparison_df)
    insight = generate_comparison_insight(ranked_df)

    return ProductComparison(
        comparison=comparison_df,
        ranked_products=ranked_df,
        insight=insight,
    )


def get_product_reviews(
    product_query,
    reviews_df=None,
    data_path=PROCESSED_REVIEWS_PATH,
):
    """Return reviews matching one product query from processed review data."""
    reviews_df = _get_reviews_dataframe(reviews_df, data_path)
    return _filter_product_reviews(reviews_df, product_query)


def get_product_health(
    product_query,
    reviews_df=None,
    data_path=PROCESSED_REVIEWS_PATH,
):
    """Return the existing product health analysis for one product query."""
    return analyze_product(product_query, reviews_df=reviews_df, data_path=data_path)


def get_product_summary(analysis_result):
    """Build a compact product summary from an analysis result."""
    if analysis_result.error:
        return ProductSummary(
            product_query=analysis_result.product_query,
            error=analysis_result.error,
        )

    metrics = analysis_result.metrics
    return ProductSummary(
        product_query=analysis_result.product_query,
        matched_product_names=analysis_result.matched_product_names,
        review_count=metrics["review_count"],
        average_rating=metrics["average_rating"],
        health_score=analysis_result.health_score,
        health_label=analysis_result.health_label,
    )
