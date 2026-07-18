"""Simulate product concept feedback from historical review patterns.

This module estimates how existing MarketMind feedback personas might react to
a new product concept. Results are data-backed simulations from similar review
patterns, not real customer quotes, guaranteed demand, or a launch decision.
"""

import argparse
import re

import joblib
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

try:
    from src.config import CONCEPT_SIMULATION_REPORT_PATH
    from src.logger import logger
    from src.review_repository import DEFAULT_DATABASE_PATH, get_all_reviews
    from src.utils.file_io import ensure_parent_dir, require_file
    from src.utils.file_io import resolve_project_path
except ImportError:
    from config import CONCEPT_SIMULATION_REPORT_PATH
    from logger import logger
    from review_repository import DEFAULT_DATABASE_PATH, get_all_reviews
    from utils.file_io import ensure_parent_dir, require_file
    from utils.file_io import resolve_project_path

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


DEFAULT_INPUT_PATH = DEFAULT_DATABASE_PATH
DEFAULT_OUTPUT_PATH = CONCEPT_SIMULATION_REPORT_PATH
DEFAULT_VECTORIZER_PATH = VECTORIZER_OUTPUT_PATH
MIN_EVIDENCE_REVIEWS = 15
HIGH_CONFIDENCE_REVIEWS = 50
SIMULATION_NOTE = (
    "Data-backed estimate from similar historical review patterns; not real "
    "customer feedback or guaranteed market demand."
)
CONCERN_LANGUAGE = {
    "Functionality": "battery life, charging reliability, water resistance, durability, maintenance, and everyday performance",
    "Value for Money": "price justification, benefits versus cost, and comparison with cheaper alternatives",
    "Quality": "build quality, long-term durability, materials, and finish",
    "Expectation Mismatch": (
        "feature promises, listing clarity, and whether real use matches expectations"
    ),
    "Overall Dissatisfaction": (
        "trust, proof of reliability, warranty, after-sales support, and customer confidence"
    ),
    "No major complaint pattern found": (
        "value confirmation, ease of use, and practical reliability"
    ),
}
VAGUE_FEATURE_WORDS = {
    "feature",
    "good",
    "product",
    "quality",
    "smart",
    "sturdy",
}
FORBIDDEN_PERSONA_RESPONSE_PHRASES = (
    "simulation",
    "simulated",
    "historical review",
    "similar review",
    "confidence",
    "evidence",
    "dataset",
    "ml",
    "rating",
    "persona",
    "the listed price",
    "would affect how i judge value",
)


def load_processed_data(db_path):
    """Load persisted review data from SQLite.

    Args:
        db_path: Path to the SQLite database.

    Returns:
        A pandas DataFrame containing processed reviews.
    """
    return get_all_reviews(db_path)


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


def get_short_description_phrase(description):
    """Return a compact fallback phrase from the product description."""
    clean_description = clean_text_field(description)
    if clean_description == "":
        return "the main promise"

    sentence = re.split(r"[.!?]", clean_description, maxsplit=1)[0]
    candidate = sentence
    with_match = re.search(r"\bwith\b", sentence, flags=re.IGNORECASE)
    if with_match:
        candidate = sentence[with_match.end() :].strip()
        candidate = re.split(
            r"\bfor\b|\bthat\b|\bto\b|,",
            candidate,
            maxsplit=1,
            flags=re.IGNORECASE,
        )[0].strip()

    candidate = re.sub(r"^(a|an|the)\s+", "", candidate, flags=re.IGNORECASE)
    if candidate == "":
        candidate = sentence

    words = candidate.split()
    if len(words) <= 8:
        return candidate

    return " ".join(words[:8])


def select_meaningful_features(features, description):
    """Choose one or two concrete product features for natural responses."""
    clean_features = clean_text_field(features)
    feature_parts = []

    if clean_features:
        feature_parts = [
            clean_text_field(feature)
            for feature in clean_features.split(",")
        ]
        feature_parts = [feature for feature in feature_parts if feature]

    meaningful_features = [
        feature
        for feature in feature_parts
        if feature.lower() not in VAGUE_FEATURE_WORDS
    ]

    if meaningful_features:
        return meaningful_features[:3]
    if clean_text_field(description):
        return [get_short_description_phrase(description)]
    if feature_parts:
        return feature_parts[:3]

    return [get_short_description_phrase(description)]


def normalize_feature_for_response(feature):
    """Clean feature text for natural response templates."""
    clean_feature = clean_text_field(feature)
    lower_feature = clean_feature.lower()

    if "usb" in lower_feature and "charging" in lower_feature:
        return "USB charging"
    if "temperature" in lower_feature and "display" in lower_feature:
        return "temperature display"
    if "hydration" in lower_feature and "reminder" in lower_feature:
        return "hydration reminders"

    return re.sub(r"^(a|an|the)\s+", "", clean_feature, flags=re.IGNORECASE)


def format_feature_phrase(selected_features):
    """Join selected feature phrases into readable first-person speech."""
    selected_features = [
        normalize_feature_for_response(feature)
        for feature in selected_features
    ]

    if len(selected_features) >= 2:
        return f"{selected_features[0]} and {selected_features[1]}"

    return selected_features[0]


def format_feature_subject(selected_features):
    """Make selected features work as a sentence subject."""
    if len(selected_features) >= 2:
        return f"The combination of {format_feature_phrase(selected_features)}"

    return normalize_feature_for_response(selected_features[0])


def get_feature_by_keyword(selected_features, keyword):
    """Find a selected feature by keyword without changing determinism."""
    for feature in selected_features:
        clean_feature = normalize_feature_for_response(feature)
        if keyword.lower() in clean_feature.lower():
            return clean_feature

    return ""


def get_feature_or_default(selected_features, index, default):
    """Return a selected feature by position, falling back to useful wording."""
    if len(selected_features) > index:
        return normalize_feature_for_response(selected_features[index])

    return default


def get_voice_features(selected_features, voice):
    """Choose feature mentions that fit the persona voice."""
    temperature = get_feature_by_keyword(selected_features, "temperature")
    charging = get_feature_by_keyword(selected_features, "charging")
    reminders = get_feature_by_keyword(selected_features, "reminder")

    if voice == "critical":
        first_feature = temperature or get_feature_or_default(
            selected_features,
            0,
            "the main feature",
        )
        second_feature = charging or get_feature_or_default(
            selected_features,
            1,
            "daily reliability",
        )
        support_feature = reminders or get_feature_or_default(
            selected_features,
            2,
            first_feature,
        )
        return first_feature, second_feature, support_feature

    if voice == "positive":
        first_feature = reminders or get_feature_or_default(
            selected_features,
            0,
            "the practical feature",
        )
        second_feature = temperature or get_feature_or_default(
            selected_features,
            1,
            "simple daily use",
        )
        return first_feature, second_feature

    first_feature = temperature or get_feature_or_default(
        selected_features,
        0,
        "the practical feature",
    )
    second_feature = reminders or get_feature_or_default(
        selected_features,
        1,
        "everyday usefulness",
    )
    return first_feature, second_feature


def format_price_for_response(price):
    """Format user-entered price naturally for persona responses."""
    clean_price = clean_text_field(price)
    if clean_price == "":
        return ""

    if clean_price.startswith("\u20b9"):
        return clean_price

    digit_match = re.search(r"\d[\d,]*(?:\.\d+)?", clean_price)
    if digit_match:
        amount = digit_match.group(0).replace(",", "")
        return f"\u20b9{amount}"

    return f"\u20b9{clean_price}"


def get_concern_detail(likely_concern):
    """Convert a broad concern category into more specific language."""
    return CONCERN_LANGUAGE.get(
        str(likely_concern),
        "risk, proof, value, and product consistency",
    )


def get_rating_stance(simulated_rating):
    """Return the response tone and final stance for a simulated rating."""
    if simulated_rating < 2.5:
        return {
            "tone": "skeptical",
            "stance": "I would avoid it for now.",
        }
    if simulated_rating <= 3.5:
        return {
            "tone": "mixed",
            "stance": "I would wait for more proof before buying.",
        }

    return {
        "tone": "positive",
        "stance": "I would consider buying it.",
    }


def get_product_noun(product_name):
    """Use the product name's final word in adaptable response templates."""
    clean_product_name = clean_text_field(product_name)
    if clean_product_name == "":
        return "product"

    return clean_product_name.split()[-1].lower()


def get_feature_verb(feature):
    """Choose a simple verb for a feature phrase."""
    clean_feature = clean_text_field(feature).lower()
    if clean_feature.endswith("s") and not clean_feature.endswith("ss"):
        return "are"

    return "is"


def validate_persona_response_text(response_text):
    """Fail internally if persona speech includes implementation wording."""
    normalized_text = clean_text_field(response_text).lower()
    forbidden_matches = [
        phrase
        for phrase in FORBIDDEN_PERSONA_RESPONSE_PHRASES
        if phrase in normalized_text
    ]

    if forbidden_matches:
        raise ValueError(
            "Persona response contains forbidden wording: "
            + ", ".join(forbidden_matches)
        )


def validate_persona_responses(persona_simulations_df):
    """Validate every generated persona_response before returning results."""
    for response_text in persona_simulations_df["persona_response"]:
        validate_persona_response_text(response_text)


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

    vectorizer = joblib.load(require_file(vectorizer_path, "TF-IDF vectorizer model"))
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
                "evidence_review_count": review_count_used,
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


def generate_persona_reaction(
    persona_row,
    product_name,
    category,
    price,
    features,
    description,
):
    """Generate a natural first-person simulated persona response.

    The text is deterministic and rule-based. It does not use an LLM, invent
    real customer quotes, or claim the product was tested.
    """
    persona_name = str(persona_row["persona_name"])
    clean_product_name = clean_text_field(product_name) or "this product"
    price_phrase = format_price_for_response(price)
    selected_features = select_meaningful_features(
        features,
        description,
    )
    product_noun = get_product_noun(clean_product_name)

    if "Critical Reviewers" in persona_name:
        first_feature, second_feature, support_feature = get_voice_features(
            selected_features,
            "critical",
        )
        price_intro = f"At {price_phrase}, " if price_phrase else ""
        support_verb = get_feature_verb(support_feature)
        return (
            f"{price_intro}I would need strong proof that {first_feature} and "
            f"{second_feature} will remain reliable with daily use. "
            f"{support_feature.capitalize()} {support_verb} useful, but "
            "electronics can make cleaning and durability more complicated. "
            "I would look for clear warranty, battery-life, and "
            "water-resistance details before trusting it. "
            "I would avoid it for now."
        )

    if "Highly Satisfied Buyers" in persona_name:
        first_feature, second_feature = get_voice_features(
            selected_features,
            "positive",
        )
        price_sentence = f"At {price_phrase}, " if price_phrase else ""
        return (
            f"I like the {first_feature} and {second_feature} because they make "
            f"an everyday {product_noun} more convenient. {price_sentence}I "
            "would still want charging and cleaning to be simple, but the "
            "features could be useful for regular college, gym, or travel use. "
            "I would consider buying it."
        )

    first_feature, second_feature = get_voice_features(
        selected_features,
        "neutral",
    )
    price_sentence = f"Still, {price_phrase} is" if price_phrase else "Still, it is"
    return (
        f"The {first_feature} and {second_feature} are appealing, especially for "
        f"long days outside. {price_sentence} much more than a normal "
        f"{product_noun}, so I would compare it with simpler alternatives and "
        "check how durable the electronics are. "
        "I would wait for more proof before buying."
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


def simulate_product_concept(
    product_name,
    category,
    price,
    features,
    description,
    reviews_df=None,
    db_path=DEFAULT_INPUT_PATH,
):
    """Run the full data-backed product concept simulation flow."""
    if clean_text_field(product_name) == "":
        return {"error": "Please provide a non-empty product name."}
    if clean_text_field(description) == "":
        return {"error": "Please provide a non-empty product description."}

    if reviews_df is None:
        reviews_df = load_processed_data(db_path)
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
    persona_simulations_df["persona_response"] = persona_simulations_df.apply(
        lambda persona_row: generate_persona_reaction(
            persona_row,
            product_name=product_name,
            category=category,
            price=price,
            features=features,
            description=description,
        ),
        axis=1,
    )
    validate_persona_responses(persona_simulations_df)
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
                "evidence_review_count": persona_row["evidence_review_count"],
                "simulated_rating": persona_row["simulated_rating"],
                "likely_concern": persona_row["likely_concern"],
                "confidence": persona_row["confidence"],
                "persona_response": persona_row["persona_response"],
                "simulation_note": result["simulation_note"],
            }
        )

    report_df = pd.DataFrame(report_rows)
    output_path = ensure_parent_dir(output_path)
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
        "persona_response",
    ]
    print(result["persona_simulations"][display_columns])

    print(f"\nLaunch score: {result['launch_score']}")
    print(f"Launch label: {result['launch_label']}")

    print("\nRecommendations:")
    for recommendation in result["recommendations"]:
        print(f"- {recommendation}")


if __name__ == "__main__":
    args = parse_args()
    try:
        simulation_result = simulate_product_concept(
            product_name=args.name,
            category=args.category,
            price=args.price,
            features=args.features,
            description=args.description,
        )
    except (FileNotFoundError, ValueError) as error:
        logger.error(error)
        raise SystemExit(1)

    print_simulation_result(simulation_result)

    if "error" not in simulation_result:
        try:
            save_concept_simulation_report(simulation_result, args.output)
        except (FileNotFoundError, ValueError) as error:
            logger.error(error)
            raise SystemExit(1)

        print(f"\nConcept simulation report saved to: {resolve_project_path(args.output)}")
