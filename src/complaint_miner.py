"""Basic complaint mining for processed MarketMind reviews.

This module extracts common words and short phrases from negative reviews.
It is intentionally simple for Phase 4A: no topic modeling, clustering, or
model training is performed here.
"""

import argparse

import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer, ENGLISH_STOP_WORDS

try:
    from src.config import (
        COMPLAINT_CATEGORY_SUMMARY_PATH,
        TOP_COMPLAINTS_REPORT_PATH,
    )
    from src.logger import logger
    from src.review_repository import DEFAULT_DATABASE_PATH, get_all_reviews
    from src.utils.file_io import ensure_parent_dir
except ImportError:
    from config import (
        COMPLAINT_CATEGORY_SUMMARY_PATH,
        TOP_COMPLAINTS_REPORT_PATH,
    )
    from logger import logger
    from review_repository import DEFAULT_DATABASE_PATH, get_all_reviews
    from utils.file_io import ensure_parent_dir

DEFAULT_INPUT_PATH = DEFAULT_DATABASE_PATH
DEFAULT_OUTPUT_PATH = TOP_COMPLAINTS_REPORT_PATH
DEFAULT_CATEGORY_SUMMARY_PATH = COMPLAINT_CATEGORY_SUMMARY_PATH
NEGATION_WORDS = {"no", "not", "nor", "never", "without"}
NOISY_WORDS = {
    "product",
    "products",
    "item",
    "items",
    "buy",
    "purchase",
    "dont",
    "don",
    "really",
    "very",
    "also",
    "one",
    "use",
    "used",
    "got",
    "get",
}
COMPLAINT_CATEGORY_KEYWORDS = {
    "Quality": ["quality", "rubbish", "poor", "defective", "damaged"],
    "Value for Money": ["money", "price", "expensive", "costly", "worth"],
    "Functionality": ["working", "work", "charger", "battery", "broken", "machine"],
    "Expectation Mismatch": ["expect", "expected", "meet", "better", "different"],
    "Overall Dissatisfaction": [
        "bad",
        "worst",
        "disappointed",
        "recommended",
        "useless",
        "good",
    ],
}


def load_processed_data(db_path):
    """Load persisted review data from SQLite.

    Args:
        db_path: Path to the SQLite database.

    Returns:
        A pandas DataFrame containing the processed reviews.
    """
    return get_all_reviews(db_path)


def normalize_product_name(product_name):
    """Normalize product names for simple matching.

    Args:
        product_name: Product name value from a DataFrame or user input.

    Returns:
        A lower-case product name with extra spaces removed.
    """
    if pd.isna(product_name):
        return ""

    return " ".join(str(product_name).lower().split())


def list_top_products(df, top_n=10):
    """List products with the highest number of reviews.

    Args:
        df: DataFrame with a product_name column.
        top_n: Number of products to return.

    Returns:
        A DataFrame with product_name and review_count columns.
    """
    product_names = df["product_name"].dropna().astype(str).str.strip()
    product_names = product_names[product_names != ""]

    top_products_df = (
        product_names.value_counts()
        .rename_axis("product_name")
        .reset_index(name="review_count")
        .head(top_n)
    )

    return top_products_df


def get_product_reviews(df, product_name):
    """Return reviews for one selected product.

    Matching is case-insensitive and ignores extra spaces.

    Args:
        df: DataFrame with a product_name column.
        product_name: Product name selected by the user.

    Returns:
        A DataFrame containing reviews for the selected product.
    """
    selected_product = normalize_product_name(product_name)

    if selected_product == "":
        return df.iloc[0:0].copy()

    normalized_product_names = df["product_name"].apply(normalize_product_name)
    matching_reviews = df[normalized_product_names == selected_product].copy()

    if matching_reviews.empty:
        # Some product names contain hidden encoding text, so partial matching
        # lets users search by the clean visible part of the product title.
        partial_matches = normalized_product_names.apply(
            lambda product: selected_product in product
        )
        matching_reviews = df[partial_matches].copy()

        if not matching_reviews.empty:
            print("Matched product names:")
            matched_product_names = matching_reviews["product_name"].dropna().unique()
            for matched_product_name in matched_product_names:
                display_product_name = (
                    str(matched_product_name)
                    .encode("ascii", errors="replace")
                    .decode("ascii")
                )
                print(f"- {display_product_name}")

    return matching_reviews


def get_negative_reviews(df):
    """Return negative reviews that have cleaned review text.

    Args:
        df: DataFrame with sentiment and cleaned_review columns.

    Returns:
        A filtered DataFrame containing only negative reviews with text.
    """
    negative_reviews = df[
        (df["sentiment"] == "negative") & df["cleaned_review"].notna()
    ].copy()

    return negative_reviews


def get_custom_stop_words():
    """Build stop words that preserve complaint negation phrases."""
    custom_stop_words = set(ENGLISH_STOP_WORDS)

    # Keep negation words so phrases like "not working" stay meaningful.
    custom_stop_words = custom_stop_words - NEGATION_WORDS
    custom_stop_words.update(NOISY_WORDS)

    return sorted(custom_stop_words)


def extract_top_complaints(negative_reviews, top_n=20):
    """Extract the most frequent complaint bigrams.

    Args:
        negative_reviews: DataFrame containing negative reviews.
        top_n: Number of complaint phrases to return.

    Returns:
        A DataFrame with complaint_phrase and frequency columns.
    """
    if negative_reviews.empty:
        return pd.DataFrame(columns=["complaint_phrase", "frequency"])

    review_text = negative_reviews["cleaned_review"].astype(str)

    vectorizer = CountVectorizer(
        stop_words=get_custom_stop_words(),
        ngram_range=(2, 2),
        min_df=5,
    )
    try:
        term_counts = vectorizer.fit_transform(review_text)
    except ValueError:
        return pd.DataFrame(columns=["complaint_phrase", "frequency"])

    complaint_counts = term_counts.sum(axis=0).A1
    complaint_phrases = vectorizer.get_feature_names_out()

    complaints_df = pd.DataFrame(
        {
            "complaint_phrase": complaint_phrases,
            "frequency": complaint_counts,
        }
    )

    complaints_df = complaints_df.sort_values(
        by="frequency",
        ascending=False,
    ).head(top_n)

    return complaints_df.reset_index(drop=True)


def save_complaint_report(complaints_df, output_path):
    """Save the complaint mining report as a CSV file.

    Args:
        complaints_df: DataFrame containing complaint phrases and frequencies.
        output_path: Destination path for the report CSV.
    """
    output_path = ensure_parent_dir(output_path)
    complaints_df.to_csv(output_path, index=False)


def categorize_complaint_phrase(phrase):
    """Convert one complaint phrase into a business-friendly category.

    Args:
        phrase: Complaint phrase such as "bad quality" or "not working".

    Returns:
        A complaint category name.
    """
    phrase_text = str(phrase).lower()

    # Category order matters: "bad quality" should be Quality, not Overall.
    for category, keywords in COMPLAINT_CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in phrase_text:
                return category

    return "Other"


def add_complaint_categories(complaints_df):
    """Add a category column to the complaint phrases DataFrame.

    Args:
        complaints_df: DataFrame with a complaint_phrase column.

    Returns:
        A copy of the DataFrame with a new category column.
    """
    categorized_df = complaints_df.copy()
    categorized_df["category"] = categorized_df["complaint_phrase"].apply(
        categorize_complaint_phrase
    )

    return categorized_df


def build_category_summary(categorized_complaints_df):
    """Summarize complaint frequency by business-friendly category.

    Args:
        categorized_complaints_df: DataFrame with category and frequency columns.

    Returns:
        A DataFrame with category and total_frequency columns.
    """
    if categorized_complaints_df.empty:
        return pd.DataFrame(columns=["category", "total_frequency"])

    category_summary_df = (
        categorized_complaints_df.groupby("category", as_index=False)["frequency"]
        .sum()
        .rename(columns={"frequency": "total_frequency"})
        .sort_values(by="total_frequency", ascending=False)
        .reset_index(drop=True)
    )

    return category_summary_df


def save_category_summary(category_summary_df, output_path):
    """Save the complaint category summary as a CSV file.

    Args:
        category_summary_df: DataFrame returned by build_category_summary.
        output_path: Destination path for the summary CSV.
    """
    output_path = ensure_parent_dir(output_path)
    category_summary_df.to_csv(output_path, index=False)


def analyze_product_complaints(df, product_name, top_n=15):
    """Run complaint mining for one selected product.

    Args:
        df: DataFrame containing all processed reviews.
        product_name: Product name selected by the user.
        top_n: Number of complaint phrases to return.

    Returns:
        product_reviews, negative_product_reviews, categorized_complaints,
        and category_summary DataFrames.
    """
    product_reviews = get_product_reviews(df, product_name)
    negative_product_reviews = get_negative_reviews(product_reviews)
    top_complaints = extract_top_complaints(negative_product_reviews, top_n=top_n)
    categorized_complaints = add_complaint_categories(top_complaints)
    category_summary = build_category_summary(categorized_complaints)

    return (
        product_reviews,
        negative_product_reviews,
        categorized_complaints,
        category_summary,
    )


def parse_args():
    """Parse command line arguments for complaint analysis."""
    parser = argparse.ArgumentParser(
        description="Mine overall or product-specific complaint phrases."
    )
    parser.add_argument(
        "--product",
        help="Optional exact product name to analyze.",
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    try:
        reviews_df = load_processed_data(DEFAULT_INPUT_PATH)
    except FileNotFoundError as error:
        logger.error(error)
        raise SystemExit(1)

    if args.product:
        (
            product_reviews_df,
            negative_product_reviews_df,
            categorized_complaints_df,
            category_summary_df,
        ) = analyze_product_complaints(reviews_df, args.product, top_n=15)

        if product_reviews_df.empty:
            print(f'No reviews found for product: "{args.product}"')
        else:
            print(f'Product: "{args.product}"')
            print(f"Total reviews: {len(product_reviews_df)}")
            print(f"Negative reviews: {len(negative_product_reviews_df)}")

            if negative_product_reviews_df.empty:
                print("\nNo negative reviews found for this product.")
            elif categorized_complaints_df.empty:
                print("\nNo usable complaint phrases found for this product.")
            else:
                print("\nTop categorized complaint phrases for this product:")
                print(categorized_complaints_df)

                print("\nProduct complaint category summary:")
                print(category_summary_df)
    else:
        top_products_df = list_top_products(reviews_df, top_n=10)

        print("Top 10 products by review count:")
        print(top_products_df)

        negative_reviews_df = get_negative_reviews(reviews_df)
        top_complaints_df = extract_top_complaints(negative_reviews_df, top_n=20)
        categorized_complaints_df = add_complaint_categories(top_complaints_df)
        category_summary_df = build_category_summary(categorized_complaints_df)

        if categorized_complaints_df.empty:
            print("\nNo usable complaint phrases found for overall analysis.")
        else:
            print("\nCategorized complaint phrases:")
            print(categorized_complaints_df)

            print("\nComplaint category summary:")
            print(category_summary_df)

        save_complaint_report(categorized_complaints_df, DEFAULT_OUTPUT_PATH)
        save_category_summary(category_summary_df, DEFAULT_CATEGORY_SUMMARY_PATH)

        print(f"\nComplaint report saved to: {DEFAULT_OUTPUT_PATH}")
        print(f"Complaint category summary saved to: {DEFAULT_CATEGORY_SUMMARY_PATH}")
