"""Shared pytest fixtures for isolated MarketMind tests."""

import os
from pathlib import Path

import joblib
import pytest
from fastapi.testclient import TestClient
from sklearn.feature_extraction.text import TfidfVectorizer


os.environ.setdefault("MARKETMIND_JWT_SECRET_KEY", "marketmind-test-secret")
os.environ.setdefault("OPENAI_API_KEY", "")
os.environ.setdefault("GOOGLE_API_KEY", "")


SAMPLE_REVIEWS = [
    {
        "product_name": "Alpha Charger AWC-38",
        "clean_price": 19.99,
        "rating": 1,
        "full_review": "Bad quality not working after one day.",
        "cleaned_review": "bad quality not working after one day",
        "sentiment": "negative",
        "category": "Electronics",
    },
    {
        "product_name": "Alpha Charger AWC-38",
        "clean_price": 19.99,
        "rating": 1,
        "full_review": "Bad quality not working after two days.",
        "cleaned_review": "bad quality not working after two days",
        "sentiment": "negative",
        "category": "Electronics",
    },
    {
        "product_name": "Alpha Charger AWC-38",
        "clean_price": 19.99,
        "rating": 2,
        "full_review": "Bad quality not working with my phone.",
        "cleaned_review": "bad quality not working with my phone",
        "sentiment": "negative",
        "category": "Electronics",
    },
    {
        "product_name": "Alpha Charger AWC-38",
        "clean_price": 19.99,
        "rating": 2,
        "full_review": "Bad quality not working during travel.",
        "cleaned_review": "bad quality not working during travel",
        "sentiment": "negative",
        "category": "Electronics",
    },
    {
        "product_name": "Alpha Charger AWC-38",
        "clean_price": 19.99,
        "rating": 1,
        "full_review": "Bad quality not working and poor charger.",
        "cleaned_review": "bad quality not working and poor charger",
        "sentiment": "negative",
        "category": "Electronics",
    },
    {
        "product_name": "Alpha Charger AWC-38",
        "clean_price": 19.99,
        "rating": 5,
        "full_review": "Good compact charger for daily use.",
        "cleaned_review": "good compact charger for daily use",
        "sentiment": "positive",
        "category": "Electronics",
    },
    {
        "product_name": "Beta Headphones",
        "clean_price": 49.99,
        "rating": 5,
        "full_review": "Excellent sound quality and comfortable design.",
        "cleaned_review": "excellent sound quality comfortable design",
        "sentiment": "positive",
        "category": "Electronics",
    },
    {
        "product_name": "Beta Headphones",
        "clean_price": 49.99,
        "rating": 4,
        "full_review": "Good headphones with decent battery life.",
        "cleaned_review": "good headphones decent battery life",
        "sentiment": "positive",
        "category": "Electronics",
    },
    {
        "product_name": "Beta Headphones",
        "clean_price": 49.99,
        "rating": 3,
        "full_review": "Average fit but acceptable value.",
        "cleaned_review": "average fit acceptable value",
        "sentiment": "neutral",
        "category": "Electronics",
    },
]


def _seed_review_database(db_path, reviews):
    """Create the production schema and insert deterministic review rows."""
    from src.database import (
        create_stable_product_id,
        create_stable_review_id,
        get_connection,
        initialize_database,
        normalize_product_name,
    )

    connection = get_connection(db_path)
    try:
        initialize_database(connection)
        with connection:
            cursor = connection.execute(
                """
                INSERT INTO dataset_sources (
                    source_name,
                    source_path,
                    imported_at,
                    description
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    "pytest_seed",
                    "pytest",
                    "2026-01-01T00:00:00+00:00",
                    "Seed data for automated tests.",
                ),
            )
            source_id = cursor.lastrowid

            for index, row in enumerate(reviews):
                normalized_name = normalize_product_name(row["product_name"])
                product_id = create_stable_product_id(normalized_name)
                connection.execute(
                    """
                    INSERT OR IGNORE INTO products (
                        product_id,
                        product_name,
                        normalized_name,
                        category,
                        clean_price,
                        source_id,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        product_id,
                        row["product_name"],
                        normalized_name,
                        row["category"],
                        row["clean_price"],
                        source_id,
                        "2026-01-01T00:00:00+00:00",
                    ),
                )
                review_id = create_stable_review_id(
                    product_id,
                    f"{row['cleaned_review']} {index}",
                    row["rating"],
                    "pytest_seed",
                )
                connection.execute(
                    """
                    INSERT INTO reviews (
                        review_id,
                        product_id,
                        rating,
                        full_review,
                        cleaned_review,
                        sentiment,
                        source_id,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        review_id,
                        product_id,
                        row["rating"],
                        row["full_review"],
                        row["cleaned_review"],
                        row["sentiment"],
                        source_id,
                        "2026-01-01T00:00:00+00:00",
                    ),
                )
    finally:
        connection.close()


def _patch_runtime_paths(monkeypatch, db_path, upload_dir):
    """Point already-imported modules at the per-test SQLite database."""
    from api.auth import security
    from src import complaint_miner, concept_simulator, config, persona_generator
    from src import review_repository, scoring_engine
    from src.repository import upload_repository, user_repository
    from src.services import concept_service, dashboard_service, product_service
    from src.services import upload_service

    monkeypatch.setattr(config, "DATABASE_PATH", db_path)
    monkeypatch.setattr(config, "UPLOADS_DIR", upload_dir)
    monkeypatch.setattr(security, "JWT_SECRET_KEY", "marketmind-test-secret")

    monkeypatch.setattr(review_repository, "DEFAULT_DATABASE_PATH", db_path)
    monkeypatch.setattr(review_repository.get_database_connection, "__defaults__", (db_path,))
    monkeypatch.setattr(review_repository._read_reviews, "__defaults__", (None, db_path))
    monkeypatch.setattr(review_repository.get_all_reviews, "__defaults__", (db_path,))
    monkeypatch.setattr(review_repository.search_products, "__defaults__", (db_path, 20))
    monkeypatch.setattr(
        review_repository.get_reviews_for_product_ids,
        "__defaults__",
        (db_path,),
    )
    monkeypatch.setattr(
        review_repository.get_product_reviews_by_query,
        "__defaults__",
        (db_path,),
    )
    monkeypatch.setattr(
        review_repository.get_category_reviews,
        "__defaults__",
        (db_path, None),
    )
    monkeypatch.setattr(
        review_repository.get_review_summary_by_product,
        "__defaults__",
        (db_path,),
    )
    monkeypatch.setattr(review_repository.get_database_overview, "__defaults__", (db_path,))

    monkeypatch.setattr(user_repository, "DATABASE_PATH", db_path)
    monkeypatch.setattr(user_repository._get_connection, "__defaults__", (db_path,))
    monkeypatch.setattr(user_repository.create_user, "__defaults__", (db_path,))
    monkeypatch.setattr(user_repository.get_user_by_id, "__defaults__", (db_path,))
    monkeypatch.setattr(user_repository.get_user_by_email, "__defaults__", (db_path,))
    monkeypatch.setattr(user_repository.get_user_by_username, "__defaults__", (db_path,))

    monkeypatch.setattr(upload_repository, "DATABASE_PATH", db_path)
    monkeypatch.setattr(upload_repository._get_connection, "__defaults__", (db_path,))
    monkeypatch.setattr(upload_repository.create_upload_record, "__defaults__", (db_path,))
    monkeypatch.setattr(upload_repository.get_upload_history, "__defaults__", (db_path,))
    monkeypatch.setattr(upload_repository.get_upload_by_id, "__defaults__", (db_path,))

    monkeypatch.setattr(upload_service, "DATABASE_PATH", db_path)
    monkeypatch.setattr(upload_service, "UPLOADS_DIR", upload_dir)

    monkeypatch.setattr(product_service, "DEFAULT_DATABASE_PATH", db_path)
    monkeypatch.setattr(product_service.load_product_data, "__defaults__", (db_path,))
    monkeypatch.setattr(product_service._get_reviews_dataframe, "__defaults__", (None, db_path))
    monkeypatch.setattr(product_service.analyze_product, "__defaults__", (None, db_path))
    monkeypatch.setattr(product_service.compare_products, "__defaults__", (None, db_path))
    monkeypatch.setattr(product_service.get_product_reviews, "__defaults__", (None, db_path))
    monkeypatch.setattr(product_service.get_product_health, "__defaults__", (None, db_path))

    monkeypatch.setattr(dashboard_service, "DEFAULT_DASHBOARD_DATA_PATH", db_path)
    monkeypatch.setattr(dashboard_service.load_dashboard_data, "__defaults__", (db_path,))

    monkeypatch.setattr(concept_service, "DEFAULT_DATABASE_PATH", db_path)
    monkeypatch.setattr(concept_service._get_reviews_dataframe, "__defaults__", (None, db_path))
    monkeypatch.setattr(concept_service.simulate_concept, "__defaults__", (None, db_path))

    monkeypatch.setattr(scoring_engine, "DEFAULT_INPUT_PATH", db_path)
    monkeypatch.setattr(complaint_miner, "DEFAULT_INPUT_PATH", db_path)
    monkeypatch.setattr(persona_generator, "DEFAULT_INPUT_PATH", db_path)
    monkeypatch.setattr(concept_simulator, "DEFAULT_INPUT_PATH", db_path)
    monkeypatch.setattr(concept_simulator.simulate_product_concept, "__defaults__", (None, db_path))


@pytest.fixture()
def temporary_database(tmp_path, monkeypatch):
    """Return an isolated SQLite database seeded with sample review data."""
    db_path = tmp_path / "marketmind_test.db"
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    _seed_review_database(db_path, SAMPLE_REVIEWS)
    _patch_runtime_paths(monkeypatch, db_path, upload_dir)
    return db_path


@pytest.fixture()
def test_vectorizer(tmp_path, temporary_database, monkeypatch):
    """Create a temporary TF-IDF vectorizer for concept simulation tests."""
    from src import concept_simulator
    from src.review_repository import get_all_reviews

    reviews_df = get_all_reviews()
    training_text = reviews_df["cleaned_review"].astype(str).tolist()
    training_text.append(
        "smart water bottle hydration reminder temperature display usb charging"
    )
    vectorizer = TfidfVectorizer().fit(training_text)
    vectorizer_path = tmp_path / "tfidf_vectorizer.pkl"
    joblib.dump(vectorizer, vectorizer_path)

    monkeypatch.setattr(concept_simulator, "DEFAULT_VECTORIZER_PATH", vectorizer_path)
    monkeypatch.setattr(
        concept_simulator.retrieve_similar_reviews,
        "__defaults__",
        (vectorizer_path, 300),
    )
    return vectorizer_path


@pytest.fixture()
def client(temporary_database):
    """Return a FastAPI test client bound to the isolated database."""
    from api.main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def auth_headers(client):
    """Register and authenticate a test user."""
    credentials = {
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "Password123",
    }
    client.post("/auth/register", json=credentials)
    response = client.post(
        "/auth/login",
        json={
            "username_or_email": credentials["email"],
            "password": credentials["password"],
        },
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def authenticated_client(client, auth_headers):
    """Return a FastAPI client with default bearer auth headers."""
    client.headers.update(auth_headers)
    return client


@pytest.fixture()
def valid_upload_csv():
    """Return a valid external review CSV payload."""
    return (
        "product_title,review_body,stars,label,price\n"
        "Upload Probe Bottle,Great bottle works well,5,positive,10\n"
        "Upload Probe Bottle,Average but usable bottle,3,neutral,10\n"
        "Upload Probe Bottle,Leaks after one week,1,negative,10\n"
    ).encode("utf-8")


@pytest.fixture()
def invalid_upload_csv():
    """Return a CSV payload with invalid upload columns."""
    return b"name,body\nMissing columns,Nope\n"


@pytest.fixture()
def malformed_upload_csv():
    """Return a malformed CSV payload."""
    return b'product_title,review_body,stars,label,price\n"Unclosed,review,5,positive,10\n'


@pytest.fixture()
def sample_concept_payload():
    """Return a concept payload accepted by the existing API."""
    return {
        "product_name": "Smart Water Bottle",
        "category": "Electronics",
        "price": "999",
        "features": "USB charging, temperature display, hydration reminder",
        "description": "A smart bottle that tracks hydration and shows water temperature.",
    }
