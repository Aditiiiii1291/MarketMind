"""Central configuration values for MarketMind paths."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
REPORTS_DIR = PROJECT_ROOT / "reports"
MODELS_DIR = PROJECT_ROOT / "models"

DATABASE_PATH = DATA_DIR / "marketmind.db"
RAW_REVIEWS_PATH = RAW_DATA_DIR / "Equal.csv"
MINI_ELECTRONICS_REVIEWS_PATH = RAW_DATA_DIR / "mini_electronics_reviews.csv"
PROCESSED_REVIEWS_PATH = PROCESSED_DATA_DIR / "marketmind_clean_reviews.csv"

SENTIMENT_MODEL_PATH = MODELS_DIR / "sentiment_model.pkl"
TFIDF_VECTORIZER_PATH = MODELS_DIR / "tfidf_vectorizer.pkl"

TOP_COMPLAINTS_REPORT_PATH = REPORTS_DIR / "top_complaints.csv"
COMPLAINT_CATEGORY_SUMMARY_PATH = REPORTS_DIR / "complaint_category_summary.csv"
REVIEW_PERSONAS_REPORT_PATH = REPORTS_DIR / "review_personas.csv"
PERSONA_PROFILES_REPORT_PATH = REPORTS_DIR / "persona_profiles.csv"
PRODUCT_HEALTH_REPORT_PATH = REPORTS_DIR / "product_health_score.csv"
PRODUCT_COMPARISON_REPORT_PATH = REPORTS_DIR / "product_comparison.csv"
CONCEPT_SIMULATION_REPORT_PATH = REPORTS_DIR / "concept_simulation.csv"
