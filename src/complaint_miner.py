"""Basic complaint mining for processed MarketMind reviews.

This module extracts common words and short phrases from negative reviews.
It is intentionally simple for Phase 4A: no topic modeling, clustering, or
model training is performed here.
"""

from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer, ENGLISH_STOP_WORDS


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_PATH = PROJECT_ROOT / "data" / "processed" / "marketmind_clean_reviews.csv"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "reports" / "top_complaints.csv"
DEFAULT_CATEGORY_SUMMARY_PATH = (
    PROJECT_ROOT / "reports" / "complaint_category_summary.csv"
)
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


def load_processed_data(file_path):
    """Load the processed review dataset from a CSV file.

    Args:
        file_path: Path to the processed CSV file.

    Returns:
        A pandas DataFrame containing the processed reviews.
    """
    return pd.read_csv(file_path)


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
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
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
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    category_summary_df.to_csv(output_path, index=False)


if __name__ == "__main__":
    reviews_df = load_processed_data(DEFAULT_INPUT_PATH)
    negative_reviews_df = get_negative_reviews(reviews_df)
    top_complaints_df = extract_top_complaints(negative_reviews_df, top_n=20)
    categorized_complaints_df = add_complaint_categories(top_complaints_df)
    category_summary_df = build_category_summary(categorized_complaints_df)

    print("Categorized complaint phrases:")
    print(categorized_complaints_df)

    print("\nComplaint category summary:")
    print(category_summary_df)

    save_complaint_report(categorized_complaints_df, DEFAULT_OUTPUT_PATH)
    save_category_summary(category_summary_df, DEFAULT_CATEGORY_SUMMARY_PATH)

    print(f"\nComplaint report saved to: {DEFAULT_OUTPUT_PATH}")
    print(f"Complaint category summary saved to: {DEFAULT_CATEGORY_SUMMARY_PATH}")
