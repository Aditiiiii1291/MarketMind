"""Create review persona segments from MarketMind product feedback.

These are feedback personas, or review segments, based on review behavior and
sentiment patterns. They are not real customer identities or demographics.
"""

from pathlib import Path

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.preprocessing import StandardScaler


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_PATH = PROJECT_ROOT / "data" / "processed" / "marketmind_clean_reviews.csv"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "reports" / "review_personas.csv"
SENTIMENT_SCORE_MAP = {
    "negative": 0,
    "neutral": 1,
    "positive": 2,
}


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

    print("Review Persona Summary:")
    print(persona_summary)

    print("\nTop Keywords by Persona:")
    print(persona_keywords)

    save_persona_report(persona_summary, persona_keywords, DEFAULT_OUTPUT_PATH)
    print(f"\nReview persona report saved to: {DEFAULT_OUTPUT_PATH}")
