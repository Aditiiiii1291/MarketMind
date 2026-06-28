"""Read-only SQLite repository functions for MarketMind reviews.

Phase 9B introduces this query layer without changing the existing CSV-based
modules or Streamlit dashboard. The functions return pandas DataFrames shaped
like the current CSV workflows expect, so later phases can adopt them safely.
"""

from pathlib import Path

import pandas as pd

try:
    from src.database import get_connection, normalize_product_name
except ImportError:
    from database import get_connection, normalize_product_name


DEFAULT_DATABASE_PATH = Path("data") / "marketmind.db"
PRODUCT_COLUMNS = [
    "product_id",
    "product_name",
    "normalized_name",
    "category",
    "clean_price",
]
REVIEW_COLUMNS = [
    "product_name",
    "clean_price",
    "rating",
    "full_review",
    "cleaned_review",
    "sentiment",
    "category",
    "product_id",
]
SUMMARY_COLUMNS = [
    "product_id",
    "product_name",
    "review_count",
    "average_rating",
    "negative_review_count",
    "neutral_review_count",
    "positive_review_count",
]


def _empty_dataframe(columns):
    """Return an empty DataFrame with a predictable column order."""
    return pd.DataFrame(columns=columns)


def _escape_like_value(value):
    """Escape user text for a SQL LIKE pattern."""
    return (
        str(value)
        .replace("\\", "\\\\")
        .replace("%", "\\%")
        .replace("_", "\\_")
    )


def _make_console_safe(value):
    """Return text that can be printed on basic Windows consoles."""
    return str(value).encode("ascii", errors="replace").decode("ascii")


def _make_dataframe_console_safe(df):
    """Return a display-only copy with text converted to console-safe ASCII."""
    display_df = df.copy()
    for column in display_df.columns:
        column_dtype = display_df[column].dtype
        if (
            pd.api.types.is_object_dtype(column_dtype)
            or pd.api.types.is_string_dtype(column_dtype)
        ):
            display_df[column] = display_df[column].apply(_make_console_safe)

    return display_df


def get_database_connection(db_path=DEFAULT_DATABASE_PATH):
    """Open the local MarketMind SQLite database.

    Raises:
        FileNotFoundError: If the database has not been created yet.
    """
    db_path = Path(db_path)
    if not db_path.exists():
        raise FileNotFoundError(
            f"SQLite database not found: {db_path}. "
            "Run scripts/migrate_csv_to_sqlite.py first."
        )

    return get_connection(db_path)


def search_products(query, db_path=DEFAULT_DATABASE_PATH, limit=20):
    """Search products by partial normalized product name.

    Args:
        query: Product search text, such as "AWC-38".
        db_path: SQLite database path.
        limit: Maximum number of product rows to return.

    Returns:
        A DataFrame with product_id, product_name, normalized_name, category,
        and clean_price columns.
    """
    normalized_query = normalize_product_name(query)
    if normalized_query == "":
        return _empty_dataframe(PRODUCT_COLUMNS)

    safe_limit = max(int(limit), 1)
    like_query = f"%{_escape_like_value(normalized_query)}%"
    starts_with_query = f"{_escape_like_value(normalized_query)}%"

    sql = """
        SELECT
            products.product_id,
            products.product_name,
            products.normalized_name,
            products.category,
            products.clean_price,
            COUNT(reviews.review_id) AS review_count
        FROM products
        LEFT JOIN reviews ON reviews.product_id = products.product_id
        WHERE products.normalized_name LIKE ? ESCAPE '\\'
        GROUP BY
            products.product_id,
            products.product_name,
            products.normalized_name,
            products.category,
            products.clean_price
        ORDER BY
            CASE
                WHEN products.normalized_name = ? THEN 0
                WHEN products.normalized_name LIKE ? ESCAPE '\\' THEN 1
                ELSE 2
            END,
            review_count DESC,
            products.product_name ASC
        LIMIT ?
    """

    with get_database_connection(db_path) as connection:
        products_df = pd.read_sql_query(
            sql,
            connection,
            params=(
                like_query,
                normalized_query,
                starts_with_query,
                safe_limit,
            ),
        )

    if products_df.empty:
        return _empty_dataframe(PRODUCT_COLUMNS)

    return products_df[PRODUCT_COLUMNS]


def get_reviews_for_product_ids(product_ids, db_path=DEFAULT_DATABASE_PATH):
    """Return review rows for one or more product IDs.

    The returned columns are compatible with current CSV-based modules, with
    category and product_id included for future database-backed workflows.
    """
    product_id_list = [str(product_id) for product_id in product_ids if product_id]
    if not product_id_list:
        return _empty_dataframe(REVIEW_COLUMNS)

    placeholders = ", ".join(["?"] * len(product_id_list))
    sql = f"""
        SELECT
            products.product_name,
            products.clean_price,
            reviews.rating,
            reviews.full_review,
            reviews.cleaned_review,
            reviews.sentiment,
            products.category,
            products.product_id
        FROM reviews
        JOIN products ON products.product_id = reviews.product_id
        WHERE reviews.product_id IN ({placeholders})
        ORDER BY products.product_name ASC, reviews.review_id ASC
    """

    with get_database_connection(db_path) as connection:
        return pd.read_sql_query(sql, connection, params=product_id_list)


def get_product_reviews_by_query(query, db_path=DEFAULT_DATABASE_PATH):
    """Search products, then return all reviews for the matched products."""
    matched_products_df = search_products(query, db_path=db_path)
    if matched_products_df.empty:
        return matched_products_df, _empty_dataframe(REVIEW_COLUMNS)

    product_ids = matched_products_df["product_id"].tolist()
    product_reviews_df = get_reviews_for_product_ids(product_ids, db_path=db_path)

    return matched_products_df, product_reviews_df


def get_category_reviews(category, db_path=DEFAULT_DATABASE_PATH, limit=None):
    """Return reviews for one category.

    Current migrated data is Uncategorized, but this supports future
    category-labelled datasets.
    """
    clean_category = str(category).strip()
    if clean_category == "":
        return _empty_dataframe(REVIEW_COLUMNS)

    params = [clean_category]
    limit_clause = ""
    if limit is not None:
        safe_limit = max(int(limit), 1)
        limit_clause = "LIMIT ?"
        params.append(safe_limit)

    sql = f"""
        SELECT
            products.product_name,
            products.clean_price,
            reviews.rating,
            reviews.full_review,
            reviews.cleaned_review,
            reviews.sentiment,
            products.category,
            products.product_id
        FROM reviews
        JOIN products ON products.product_id = reviews.product_id
        WHERE products.category = ?
        ORDER BY products.product_name ASC, reviews.review_id ASC
        {limit_clause}
    """

    with get_database_connection(db_path) as connection:
        return pd.read_sql_query(sql, connection, params=params)


def get_review_summary_by_product(product_ids, db_path=DEFAULT_DATABASE_PATH):
    """Return review-count and sentiment-count summary rows by product."""
    product_id_list = [str(product_id) for product_id in product_ids if product_id]
    if not product_id_list:
        return _empty_dataframe(SUMMARY_COLUMNS)

    placeholders = ", ".join(["?"] * len(product_id_list))
    sql = f"""
        SELECT
            products.product_id,
            products.product_name,
            COUNT(reviews.review_id) AS review_count,
            ROUND(AVG(reviews.rating), 2) AS average_rating,
            SUM(CASE WHEN reviews.sentiment = 'negative' THEN 1 ELSE 0 END)
                AS negative_review_count,
            SUM(CASE WHEN reviews.sentiment = 'neutral' THEN 1 ELSE 0 END)
                AS neutral_review_count,
            SUM(CASE WHEN reviews.sentiment = 'positive' THEN 1 ELSE 0 END)
                AS positive_review_count
        FROM products
        LEFT JOIN reviews ON reviews.product_id = products.product_id
        WHERE products.product_id IN ({placeholders})
        GROUP BY products.product_id, products.product_name
        ORDER BY review_count DESC, products.product_name ASC
    """

    with get_database_connection(db_path) as connection:
        return pd.read_sql_query(sql, connection, params=product_id_list)


def get_database_overview(db_path=DEFAULT_DATABASE_PATH):
    """Return high-level database counts and distribution DataFrames."""
    with get_database_connection(db_path) as connection:
        total_products = connection.execute(
            "SELECT COUNT(*) FROM products"
        ).fetchone()[0]
        total_reviews = connection.execute(
            "SELECT COUNT(*) FROM reviews"
        ).fetchone()[0]

        category_distribution = pd.read_sql_query(
            """
            SELECT category, COUNT(*) AS product_count
            FROM products
            GROUP BY category
            ORDER BY product_count DESC, category ASC
            """,
            connection,
        )
        sentiment_distribution = pd.read_sql_query(
            """
            SELECT sentiment, COUNT(*) AS review_count
            FROM reviews
            GROUP BY sentiment
            ORDER BY sentiment ASC
            """,
            connection,
        )
        source_distribution = pd.read_sql_query(
            """
            SELECT
                dataset_sources.source_id,
                dataset_sources.source_name,
                COUNT(reviews.review_id) AS review_count
            FROM dataset_sources
            LEFT JOIN reviews ON reviews.source_id = dataset_sources.source_id
            GROUP BY dataset_sources.source_id, dataset_sources.source_name
            ORDER BY review_count DESC, dataset_sources.source_name ASC
            """,
            connection,
        )

    return {
        "total_products": total_products,
        "total_reviews": total_reviews,
        "category_distribution": category_distribution,
        "sentiment_distribution": sentiment_distribution,
        "source_distribution": source_distribution,
    }


def main():
    """Print a small read-only repository demo."""
    overview = get_database_overview()
    print("Database overview")
    print("-----------------")
    print(f"Total products: {overview['total_products']}")
    print(f"Total reviews: {overview['total_reviews']}")

    print("\nCategory distribution:")
    print(overview["category_distribution"].to_string(index=False))

    print("\nSentiment distribution:")
    print(overview["sentiment_distribution"].to_string(index=False))

    print("\nSource distribution:")
    print(overview["source_distribution"].to_string(index=False))

    print("\nSearch: AWC-38")
    matched_products_df, product_reviews_df = get_product_reviews_by_query("AWC-38")
    print("\nMatched products:")
    if matched_products_df.empty:
        print("No products matched.")
    else:
        display_products_df = _make_dataframe_console_safe(matched_products_df)
        print(display_products_df.to_string(index=False))

    print(f"\nTotal reviews returned for match: {len(product_reviews_df)}")


if __name__ == "__main__":
    main()
