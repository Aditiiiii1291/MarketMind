"""Simulate product concept feedback from historical review patterns.

This module estimates how existing MarketMind feedback personas might react to
a new product concept. Results are data-backed simulations from similar review
patterns, not real customer quotes, guaranteed demand, or a launch decision.
"""

import argparse
from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

try:
    from persona_generator import (
        SENTIMENT_SCORE_MAP,
        assign_persona_names,
        attach_clusters_to_reviews,
        build_persona_profiles,
        cluster_review_personas,
        create_persona_features,
        summarize_personas,
    )
    from sentiment_model import VECTORIZER_OUTPUT_PATH
except ImportError:
    from src.persona_generator import (
        SENTIMENT_SCORE_MAP,
        assign_persona_names,
        attach_clusters_to_reviews,
        build_persona_profiles,
        cluster_review_personas,
        create_persona_features,
        summarize_personas,
    )
    from src.sentiment_model import VECTORIZER_OUTPUT_PATH


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_PATH = PROJECT_ROOT / "data" / "processed" / "marketmind_clean_reviews.csv"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "reports" / "concept_simulation.csv"
DEFAULT_VECTORIZER_PATH = VECTORIZER_OUTPUT_PATH
MIN_EVIDENCE_REVIEWS = 15
HIGH_CONFIDENCE_REVIEWS = 50
SIMULATION_NOTE = (
    "Data-backed estimate from similar historical review patterns; not real "
    "customer feedback or guaranteed market demand."
)


def resolve_project_path(file_path):
    """Resolve project-relative paths while preserving absolute paths."""
    path = Path(file_path)

    if path.is_absolute():
        return path

    return PROJECT_ROOT / path


def load_processed_data(file_path):
    """Load the processed review CSV file.

    Args:
        file_path: Path to the processed CSV file.

    Returns:
        A pandas DataFrame containing processed reviews.
    """
    return pd.read_csv(file_path)


def clean_text_field(value):
    """Convert optional user input into clean text."""
    if value is None:
        return ""

    return " ".join(str(value).strip().split())


def build_concept_text(product_name, category, price, features, description):
    """Combine non-empty concept fields into one clean text string."""
    fields = [product_name, category, price, features, description]
    clean_fields = []

    for field in fields:
        field_text = clean_text_field(field)
        if field_text:
            clean_fields.append(field_text)

    return " ".join(clean_fields)


def prepare_persona_reviews(df):
    """Build feedback personas and attach persona clusters to review rows.

    Args:
        df: Processed review DataFrame.

    Returns:
        A tuple of clustered review rows and persona profile rows.
    """
    persona_features_df = create_persona_features(df)
    clustered_features_df, _ = cluster_review_personas(
        persona_features_df,
        n_clusters=3,
    )
    persona_summary_df = summarize_personas(clustered_features_df)
    persona_summary_df = assign_persona_names(persona_summary_df)
    clustered_reviews_df = attach_clusters_to_reviews(df, clustered_features_df)
    persona_profiles_df = build_persona_profiles(
        clustered_reviews_df,
        persona_summary_df,
    )

    return clustered_reviews_df, persona_profiles_df


def retrieve_similar_reviews(
    concept_text,
    reviews_df,
    vectorizer_path=DEFAULT_VECTORIZER_PATH,
    top_k=300,
):
    """Retrieve the most similar historical reviews for a concept.

    Args:
        concept_text: Combined product concept text.
        reviews_df: Review DataFrame with cleaned_review text.
        vectorizer_path: Saved TF-IDF vectorizer path.
        top_k: Maximum number of matching reviews to return.

    Returns:
        Matching review rows with a similarity_score column.
    """
    clean_concept_text = str(concept_text).strip()
    if clean_concept_text == "":
        return reviews_df.iloc[0:0].copy()

    usable_reviews_df = reviews_df.dropna(subset=["cleaned_review"]).copy()
    usable_reviews_df["cleaned_review"] = (
        usable_reviews_df["cleaned_review"].astype(str).str.strip()
    )
    usable_reviews_df = usable_reviews_df[usable_reviews_df["cleaned_review"] != ""]

    if usable_reviews_df.empty:
        return reviews_df.iloc[0:0].copy()

    vectorizer = joblib.load(resolve_project_path(vectorizer_path))
    concept_vector = vectorizer.transform([clean_concept_text])
    review_vectors = vectorizer.transform(usable_reviews_df["cleaned_review"])
    similarity_scores = cosine_similarity(concept_vector, review_vectors).ravel()

    matched_reviews_df = usable_reviews_df.copy()
    matched_reviews_df["similarity_score"] = similarity_scores
    matched_reviews_df = matched_reviews_df[matched_reviews_df["similarity_score"] > 0]

    if matched_reviews_df.empty:
        return matched_reviews_df

    matched_reviews_df = matched_reviews_df.sort_values(
        by="similarity_score",
        ascending=False,
    ).head(top_k)

    return matched_reviews_df.reset_index(drop=True)


def get_confidence_label(review_count_used):
    """Convert similar-review evidence volume into a confidence label."""
    if review_count_used >= HIGH_CONFIDENCE_REVIEWS:
        return "High"
    if review_count_used >= MIN_EVIDENCE_REVIEWS:
        return "Medium"

    return "Low"


def clamp_rating(rating):
    """Keep simulated ratings inside the 1 to 5 review-rating range."""
    return round(min(max(float(rating), 1.0), 5.0), 2)


def calculate_persona_simulation(similar_reviews_df, persona_profiles_df):
    """Estimate likely concept feedback for each feedback persona.

    Args:
        similar_reviews_df: Similar historical review rows with cluster labels.
        persona_profiles_df: Data-backed persona profile DataFrame.

    Returns:
        A DataFrame with one simulation row per persona.
    """
    simulation_rows = []

    for _, persona_row in persona_profiles_df.sort_values("cluster").iterrows():
        cluster_id = int(persona_row["cluster"])
        persona_reviews = similar_reviews_df[
            similar_reviews_df["cluster"] == cluster_id
        ].copy()
        review_count_used = len(persona_reviews)

        ratings = pd.to_numeric(persona_reviews["rating"], errors="coerce")
        sentiment_scores = persona_reviews["sentiment"].map(SENTIMENT_SCORE_MAP)
        evidence_average_rating = ratings.mean()
        evidence_sentiment_score = sentiment_scores.mean()

        if review_count_used >= MIN_EVIDENCE_REVIEWS and not pd.isna(
            evidence_average_rating
        ):
            simulated_rating = evidence_average_rating
        else:
            simulated_rating = persona_row["average_rating"]

        simulation_rows.append(
            {
                "cluster": cluster_id,
                "persona_name": persona_row["persona_name"],
                "review_count_used": review_count_used,
                "evidence_average_rating": (
                    round(float(evidence_average_rating), 2)
                    if not pd.isna(evidence_average_rating)
                    else None
                ),
                "evidence_sentiment_score": (
                    round(float(evidence_sentiment_score), 2)
                    if not pd.isna(evidence_sentiment_score)
                    else None
                ),
                "simulated_rating": clamp_rating(simulated_rating),
                "likely_concern": persona_row["primary_risk_area"],
                "confidence": get_confidence_label(review_count_used),
                "simulation_note": SIMULATION_NOTE,
            }
        )

    return pd.DataFrame(simulation_rows)


def generate_persona_reaction(persona_row):
    """Generate a short rule-based persona reaction without real quotes."""
    persona_name = str(persona_row["persona_name"])
    simulated_rating = float(persona_row["simulated_rating"])
    likely_concern = str(persona_row["likely_concern"]).lower()

    if simulated_rating >= 4:
        return (
            f"{persona_name} may respond positively, while still monitoring "
            f"{likely_concern} in similar feedback."
        )
    if simulated_rating >= 3:
        return (
            f"{persona_name} may be open but cautious because {likely_concern} "
            "appears in related historical feedback."
        )

    return (
        f"{persona_name} is likely to be cautious because {likely_concern} is a "
        "recurring concern in similar feedback."
    )


def calculate_launch_readiness(persona_simulations_df):
    """Calculate launch readiness from average simulated persona ratings."""
    if persona_simulations_df.empty:
        launch_score = 0.0
    else:
        average_rating = persona_simulations_df["simulated_rating"].mean()
        launch_score = round((average_rating / 5) * 100, 2)

    if launch_score >= 75:
        launch_label = "Promising Concept"
    elif launch_score >= 55:
        launch_label = "Needs Refinement"
    else:
        launch_label = "High Launch Risk"

    return launch_score, launch_label


def generate_launch_recommendations(persona_simulations_df, launch_label):
    """Generate short recommendations from simulated persona concerns."""
    if (
        persona_simulations_df.empty
        or persona_simulations_df["review_count_used"].sum() == 0
    ):
        return [
            "Treat this as a low-confidence simulation because no similar historical reviews were found.",
            "Collect more direct feedback before making product launch decisions.",
        ]

    concern_recommendations = {
        "Quality": "Improve quality signals before launch.",
        "Functionality": "Validate core functionality with focused product tests.",
        "Value for Money": "Check whether the price and feature set feel worthwhile.",
        "Expectation Mismatch": "Clarify product promises, features, and limitations.",
        "Overall Dissatisfaction": "Review broad negative feedback before launch.",
        "No major complaint pattern found": "Preserve the strengths seen in similar feedback.",
    }
    recommendations = []
    concern_counts = persona_simulations_df["likely_concern"].value_counts()

    for concern in concern_counts.index:
        recommendation = concern_recommendations.get(
            concern,
            "Review recurring concerns in similar historical feedback.",
        )
        if recommendation not in recommendations:
            recommendations.append(recommendation)

        if len(recommendations) == 3:
            break

    if launch_label == "Promising Concept":
        recommendations.append("Proceed with validation while monitoring lower-confidence personas.")
    elif launch_label == "Needs Refinement":
        recommendations.append("Refine the concept around the highest-risk concern before launch.")
    else:
        recommendations.append("Delay launch decisions until the concept risk areas are addressed.")

    return recommendations[:4]


def simulate_product_concept(product_name, category, price, features, description):
    """Run the full data-backed product concept simulation flow."""
    if clean_text_field(product_name) == "":
        return {"error": "Please provide a non-empty product name."}
    if clean_text_field(description) == "":
        return {"error": "Please provide a non-empty product description."}

    reviews_df = load_processed_data(DEFAULT_INPUT_PATH)
    concept_text = build_concept_text(
        product_name,
        category,
        price,
        features,
        description,
    )
    clustered_reviews_df, persona_profiles_df = prepare_persona_reviews(reviews_df)
    similar_reviews_df = retrieve_similar_reviews(concept_text, clustered_reviews_df)
    persona_simulations_df = calculate_persona_simulation(
        similar_reviews_df,
        persona_profiles_df,
    )
    persona_simulations_df["simulated_reaction"] = persona_simulations_df.apply(
        generate_persona_reaction,
        axis=1,
    )
    launch_score, launch_label = calculate_launch_readiness(persona_simulations_df)
    recommendations = generate_launch_recommendations(
        persona_simulations_df,
        launch_label,
    )

    return {
        "product_name": product_name,
        "category": category,
        "price": price,
        "features": features,
        "description": description,
        "concept_text": concept_text,
        "persona_simulations": persona_simulations_df,
        "launch_score": launch_score,
        "launch_label": launch_label,
        "recommendations": recommendations,
        "similar_review_count": len(similar_reviews_df),
        "simulation_note": SIMULATION_NOTE,
    }


def save_concept_simulation_report(result, output_path):
    """Save a readable product concept simulation report to CSV."""
    if "error" in result:
        raise ValueError(result["error"])

    report_rows = []

    for _, persona_row in result["persona_simulations"].iterrows():
        report_rows.append(
            {
                "product_name": result["product_name"],
                "category": result["category"],
                "launch_score": result["launch_score"],
                "launch_label": result["launch_label"],
                "similar_review_count": result["similar_review_count"],
                "persona_name": persona_row["persona_name"],
                "review_count_used": persona_row["review_count_used"],
                "simulated_rating": persona_row["simulated_rating"],
                "likely_concern": persona_row["likely_concern"],
                "confidence": persona_row["confidence"],
                "simulated_reaction": persona_row["simulated_reaction"],
                "simulation_note": result["simulation_note"],
            }
        )

    report_df = pd.DataFrame(report_rows)
    output_path = resolve_project_path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report_df.to_csv(output_path, index=False)


def parse_args():
    """Parse command line arguments for product concept simulation."""
    parser = argparse.ArgumentParser(
        description="Simulate concept feedback from historical review personas."
    )
    parser.add_argument("--name", required=True, help="New product concept name.")
    parser.add_argument("--category", default="", help="Product category.")
    parser.add_argument("--price", default="", help="Expected product price.")
    parser.add_argument("--features", default="", help="Comma-separated features.")
    parser.add_argument(
        "--description",
        required=True,
        help="Short product concept description.",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_PATH),
        help="Path for the concept simulation CSV report.",
    )

    return parser.parse_args()


def print_simulation_result(result):
    """Print a readable CLI summary for a concept simulation."""
    if "error" in result:
        print(result["error"])
        return

    print("Product Concept Summary:")
    print(f"Name: {result['product_name']}")
    print(f"Category: {result['category']}")
    print(f"Price: {result['price']}")
    print(f"Features: {result['features']}")
    print(f"Description: {result['description']}")
    print(f"Simulation note: {result['simulation_note']}")

    print(f"\nSimilar historical review count: {result['similar_review_count']}")

    print("\nPersona Simulation Table:")
    display_columns = [
        "persona_name",
        "review_count_used",
        "simulated_rating",
        "likely_concern",
        "confidence",
        "simulated_reaction",
    ]
    print(result["persona_simulations"][display_columns])

    print(f"\nLaunch score: {result['launch_score']}")
    print(f"Launch label: {result['launch_label']}")

    print("\nRecommendations:")
    for recommendation in result["recommendations"]:
        print(f"- {recommendation}")


if __name__ == "__main__":
    args = parse_args()
    simulation_result = simulate_product_concept(
        product_name=args.name,
        category=args.category,
        price=args.price,
        features=args.features,
        description=args.description,
    )
    print_simulation_result(simulation_result)

    if "error" not in simulation_result:
        save_concept_simulation_report(simulation_result, args.output)
        print(f"\nConcept simulation report saved to: {resolve_project_path(args.output)}")
