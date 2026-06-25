"""Create review persona segments from MarketMind product feedback.

These are feedback personas, or review segments, based on review behavior and
sentiment patterns. They are not real customer identities or demographics.
"""

from pathlib import Path

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import CountVectorizer, ENGLISH_STOP_WORDS
from sklearn.preprocessing import StandardScaler

try:
    from complaint_miner import (
        add_complaint_categories,
        build_category_summary,
        extract_top_complaints,
        get_negative_reviews,
    )
except ImportError:
    from src.complaint_miner import (
        add_complaint_categories,
        build_category_summary,
        extract_top_complaints,
        get_negative_reviews,
    )


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_PATH = PROJECT_ROOT / "data" / "processed" / "marketmind_clean_reviews.csv"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "reports" / "review_personas.csv"
DEFAULT_PROFILE_OUTPUT_PATH = PROJECT_ROOT / "reports" / "persona_profiles.csv"
SENTIMENT_SCORE_MAP = {
    "negative": 0,
    "neutral": 1,
    "positive": 2,
}
NEGATION_WORDS = {"no", "not", "never", "without"}
NO_USABLE_PHRASES_MESSAGE = "No usable review phrases found"
NO_MAJOR_COMPLAINT_MESSAGE = "No major complaint pattern found"


def load_processed_data(file_path):
    """Load the processed review CSV file.

    Args:
        file_path: Path to the processed CSV file.

    Returns:
        A pandas DataFrame containing processed reviews.
    """
    return pd.read_csv(file_path)


def create_persona_features(df):
    """Create simple numeric features for review persona clustering.

    Clustering finds patterns in reviews, not real demographic personas.

    Args:
        df: DataFrame with rating, sentiment, and cleaned_review columns.

    Returns:
        A DataFrame with rating, review_length, and sentiment_score columns.
    """
    required_columns = ["rating", "sentiment", "cleaned_review"]
    reviews_df = df.dropna(subset=required_columns).copy()

    reviews_df["rating"] = pd.to_numeric(reviews_df["rating"], errors="coerce")
    reviews_df["sentiment_score"] = reviews_df["sentiment"].map(SENTIMENT_SCORE_MAP)
    reviews_df["review_length"] = reviews_df["cleaned_review"].apply(
        lambda review: len(str(review).split())
    )

    reviews_df = reviews_df.dropna(
        subset=["rating", "sentiment_score", "review_length"]
    )

    features_df = reviews_df[["rating", "review_length", "sentiment_score"]].copy()

    return features_df


def cluster_review_personas(features_df, n_clusters=3):
    """Cluster reviews into feedback persona segments using KMeans.

    Args:
        features_df: DataFrame returned by create_persona_features.
        n_clusters: Number of review segments to create.

    Returns:
        The clustered feature DataFrame and fitted KMeans model.
    """
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(features_df)

    kmeans_model = KMeans(
        n_clusters=n_clusters,
        random_state=42,
        n_init=10,
    )
    cluster_labels = kmeans_model.fit_predict(scaled_features)

    clustered_features_df = features_df.copy()
    clustered_features_df["cluster"] = cluster_labels

    return clustered_features_df, kmeans_model


def summarize_personas(clustered_features_df):
    """Summarize each review persona segment.

    Args:
        clustered_features_df: Feature DataFrame with a cluster column.

    Returns:
        A summary DataFrame with review counts and feature averages.
    """
    persona_summary_df = (
        clustered_features_df.groupby("cluster")
        .agg(
            review_count=("cluster", "size"),
            average_rating=("rating", "mean"),
            average_review_length=("review_length", "mean"),
            average_sentiment_score=("sentiment_score", "mean"),
        )
        .reset_index()
    )

    return persona_summary_df


def assign_persona_names(persona_summary_df):
    """Add clear rule-based names to each review persona segment.

    These names describe review patterns only. They should not be interpreted as
    demographic customer identities.

    Args:
        persona_summary_df: Summary DataFrame returned by summarize_personas.

    Returns:
        A copy of the summary DataFrame with a persona_name column.
    """
    named_summary_df = persona_summary_df.copy()
    persona_names = []
    used_names = set()

    for _, persona_row in named_summary_df.iterrows():
        cluster_id = int(persona_row["cluster"])
        average_rating = persona_row["average_rating"]
        average_sentiment_score = persona_row["average_sentiment_score"]

        if average_rating >= 4 and average_sentiment_score >= 1.5:
            base_name = "Highly Satisfied Buyers"
        elif average_rating <= 2 or average_sentiment_score <= 0.5:
            base_name = "Critical Reviewers"
        else:
            base_name = "Mixed / Neutral Evaluators"

        persona_name = base_name
        if persona_name in used_names:
            persona_name = f"{base_name} - Cluster {cluster_id}"

        used_names.add(persona_name)
        persona_names.append(persona_name)

    named_summary_df["persona_name"] = persona_names

    return named_summary_df


def extract_persona_keywords(df, clustered_features_df, top_n=8):
    """Extract top words and short phrases for each review persona segment.

    Args:
        df: Original processed review DataFrame.
        clustered_features_df: Feature DataFrame with cluster labels.
        top_n: Number of keywords or bigrams to keep per cluster.

    Returns:
        A DataFrame with cluster and top_keywords columns.
    """
    review_clusters_df = df.loc[clustered_features_df.index, ["cleaned_review"]].copy()
    review_clusters_df["cluster"] = clustered_features_df["cluster"]

    keyword_rows = []

    for cluster_id in sorted(review_clusters_df["cluster"].unique()):
        cluster_reviews = review_clusters_df[
            review_clusters_df["cluster"] == cluster_id
        ]["cleaned_review"].dropna()

        if cluster_reviews.empty:
            top_keywords = []
        else:
            vectorizer = CountVectorizer(
                stop_words="english",
                ngram_range=(1, 2),
                max_features=top_n,
            )
            try:
                word_counts = vectorizer.fit_transform(cluster_reviews.astype(str))
            except ValueError:
                top_keywords = []
            else:
                total_counts = word_counts.sum(axis=0).A1
                words = vectorizer.get_feature_names_out()

                keyword_counts_df = pd.DataFrame(
                    {
                        "keyword": words,
                        "count": total_counts,
                    }
                )
                top_keywords = (
                    keyword_counts_df.sort_values(by="count", ascending=False)[
                        "keyword"
                    ]
                    .head(top_n)
                    .tolist()
                )

        keyword_rows.append(
            {
                "cluster": cluster_id,
                "top_keywords": ", ".join(top_keywords),
            }
        )

    keyword_df = pd.DataFrame(keyword_rows)

    return keyword_df


def attach_clusters_to_reviews(df, clustered_features_df):
    """Attach persona cluster labels back to the original review rows.

    Args:
        df: Original processed review DataFrame.
        clustered_features_df: Feature DataFrame with cluster labels and the
            original review row index.

    Returns:
        A DataFrame with product_name, rating, sentiment, cleaned_review, and
        cluster columns.
    """
    review_columns = ["product_name", "rating", "sentiment", "cleaned_review"]
    clustered_reviews_df = df.loc[clustered_features_df.index, review_columns].copy()
    cluster_labels = clustered_features_df[["cluster"]].copy()

    clustered_reviews_df = clustered_reviews_df.join(cluster_labels)

    return clustered_reviews_df


def extract_persona_sentiment_phrases(cluster_reviews, sentiment_label, top_n=5):
    """Extract top bigram phrases for one persona and sentiment label.

    Args:
        cluster_reviews: DataFrame containing reviews for one persona cluster.
        sentiment_label: Sentiment label to filter on, such as positive or negative.
        top_n: Number of phrases to return.

    Returns:
        A comma-separated string of top phrases, or a clear fallback string.
    """
    sentiment_reviews = cluster_reviews[
        cluster_reviews["sentiment"] == sentiment_label
    ]["cleaned_review"].dropna()

    sentiment_reviews = sentiment_reviews.astype(str).str.strip()
    sentiment_reviews = sentiment_reviews[sentiment_reviews != ""]

    if sentiment_reviews.empty:
        return NO_USABLE_PHRASES_MESSAGE

    stop_words = set(ENGLISH_STOP_WORDS) - NEGATION_WORDS
    vectorizer = CountVectorizer(
        stop_words=sorted(stop_words),
        ngram_range=(2, 2),
    )

    try:
        phrase_counts = vectorizer.fit_transform(sentiment_reviews)
    except ValueError:
        return NO_USABLE_PHRASES_MESSAGE

    total_counts = phrase_counts.sum(axis=0).A1
    phrases = vectorizer.get_feature_names_out()
    phrase_counts_df = pd.DataFrame(
        {
            "phrase": phrases,
            "count": total_counts,
        }
    )

    top_phrases = (
        phrase_counts_df.sort_values(by="count", ascending=False)["phrase"]
        .head(top_n)
        .tolist()
    )

    if not top_phrases:
        return NO_USABLE_PHRASES_MESSAGE

    return ", ".join(top_phrases)


def find_primary_risk_area(cluster_reviews):
    """Find the top complaint category for one persona cluster."""
    negative_reviews = get_negative_reviews(cluster_reviews)

    if negative_reviews.empty:
        return NO_MAJOR_COMPLAINT_MESSAGE

    top_complaints = extract_top_complaints(negative_reviews, top_n=20)
    categorized_complaints = add_complaint_categories(top_complaints)
    category_summary = build_category_summary(categorized_complaints)

    if category_summary.empty:
        return NO_MAJOR_COMPLAINT_MESSAGE

    top_category = category_summary.sort_values(
        by="total_frequency",
        ascending=False,
    ).iloc[0]

    return str(top_category["category"])


def build_persona_profiles(clustered_reviews_df, persona_summary_df):
    """Build data-backed persona profiles from clustered review behavior.

    Args:
        clustered_reviews_df: DataFrame returned by attach_clusters_to_reviews.
        persona_summary_df: Persona summary DataFrame with persona names.

    Returns:
        A DataFrame with one profile row per persona cluster.
    """
    profile_rows = []

    for _, persona_row in persona_summary_df.sort_values("cluster").iterrows():
        cluster_id = int(persona_row["cluster"])
        cluster_reviews = clustered_reviews_df[
            clustered_reviews_df["cluster"] == cluster_id
        ].copy()

        ratings = pd.to_numeric(cluster_reviews["rating"], errors="coerce")
        sentiment_scores = cluster_reviews["sentiment"].map(SENTIMENT_SCORE_MAP)
        review_lengths = cluster_reviews["cleaned_review"].fillna("").apply(
            lambda review: len(str(review).split())
        )

        profile_rows.append(
            {
                "cluster": cluster_id,
                "persona_name": persona_row["persona_name"],
                "review_count": len(cluster_reviews),
                "average_rating": round(float(ratings.mean()), 2),
                "average_review_length": round(float(review_lengths.mean()), 2),
                "average_sentiment_score": round(float(sentiment_scores.mean()), 2),
                "top_positive_phrases": extract_persona_sentiment_phrases(
                    cluster_reviews,
                    "positive",
                    top_n=5,
                ),
                "top_negative_phrases": extract_persona_sentiment_phrases(
                    cluster_reviews,
                    "negative",
                    top_n=5,
                ),
                "primary_risk_area": find_primary_risk_area(cluster_reviews),
            }
        )

    persona_profiles_df = pd.DataFrame(profile_rows)

    return persona_profiles_df


def save_persona_report(persona_summary_df, keyword_df, output_path):
    """Save the review persona summary and keywords to a CSV report.

    Args:
        persona_summary_df: Persona summary DataFrame.
        keyword_df: Keyword DataFrame returned by extract_persona_keywords.
        output_path: Destination path for the report CSV.
    """
    report_df = persona_summary_df.merge(keyword_df, on="cluster", how="left")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report_df.to_csv(output_path, index=False)


def save_persona_profiles(persona_profiles_df, output_path):
    """Save data-backed persona profiles to a CSV report.

    Args:
        persona_profiles_df: DataFrame returned by build_persona_profiles.
        output_path: Destination path for the persona profile CSV.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    persona_profiles_df.to_csv(output_path, index=False)


if __name__ == "__main__":
    reviews_df = load_processed_data(DEFAULT_INPUT_PATH)
    persona_features_df = create_persona_features(reviews_df)
    clustered_personas_df, persona_model = cluster_review_personas(
        persona_features_df,
        n_clusters=3,
    )
    persona_summary = summarize_personas(clustered_personas_df)
    persona_summary = assign_persona_names(persona_summary)
    persona_keywords = extract_persona_keywords(
        reviews_df,
        clustered_personas_df,
        top_n=8,
    )
    clustered_reviews = attach_clusters_to_reviews(reviews_df, clustered_personas_df)
    persona_profiles = build_persona_profiles(clustered_reviews, persona_summary)

    print("Review Persona Summary:")
    print(persona_summary)

    print("\nTop Keywords by Persona:")
    print(persona_keywords)

    print("\nPersona Profiles:")
    print(persona_profiles)

    save_persona_report(persona_summary, persona_keywords, DEFAULT_OUTPUT_PATH)
    print(f"\nReview persona report saved to: {DEFAULT_OUTPUT_PATH}")

    save_persona_profiles(persona_profiles, DEFAULT_PROFILE_OUTPUT_PATH)
    print(f"Persona profiles saved to: {DEFAULT_PROFILE_OUTPUT_PATH}")
