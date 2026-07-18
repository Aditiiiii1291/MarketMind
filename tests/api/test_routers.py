"""FastAPI router smoke and contract tests."""


def test_product_router_success_and_validation(client):
    """Product router returns success and current validation errors."""
    search = client.get("/products/search", params={"query": "Alpha"})
    health = client.get("/products/health", params={"query": "Alpha"})
    summary = client.get("/products/summary", params={"query": "Alpha"})
    compare = client.get(
        "/products/compare",
        params=[("products", "Alpha"), ("products", "Beta")],
    )
    missing_query = client.get("/products/health")
    too_few_products = client.get("/products/compare", params={"products": "Alpha"})

    assert search.status_code == 200
    assert search.json()["review_count"] == 6
    assert health.status_code == 200
    assert health.json()["metrics"]["review_count"] == 6
    assert summary.status_code == 200
    assert summary.json()["review_count"] == 6
    assert compare.status_code == 200
    assert compare.json()["ranked_products"]
    assert missing_query.status_code == 422
    assert too_few_products.status_code == 400


def test_concept_router_example_and_simulation(
    authenticated_client,
    test_vectorizer,
    sample_concept_payload,
):
    """Concept router exposes the example and authenticated simulation endpoint."""
    example = authenticated_client.get("/concept/example")
    simulation = authenticated_client.post(
        "/concept/simulate",
        json=sample_concept_payload,
    )
    invalid = authenticated_client.post(
        "/concept/simulate",
        json={**sample_concept_payload, "description": ""},
    )

    assert example.status_code == 200
    assert example.json()["product_name"] == "Smart Water Bottle"
    assert simulation.status_code == 200
    assert len(simulation.json()["persona_simulations"]) == 3
    assert invalid.status_code == 400


def test_dashboard_router_authenticated_response(authenticated_client):
    """Dashboard router returns the current dashboard DTO shape."""
    response = authenticated_client.get("/dashboard", params={"query": "Alpha"})

    assert response.status_code == 200
    assert response.json()["metrics"]["review_count"] == 6
    assert response.json()["tables"]["matched_product_names"] == ["Alpha Charger AWC-38"]


def test_analysis_router_deterministic_and_ai_fallback(
    authenticated_client,
    test_vectorizer,
    sample_concept_payload,
):
    """Analysis router returns deterministic reports and AI fallback responses."""
    product = authenticated_client.get("/analysis/product", params={"query": "Alpha"})
    product_ai = authenticated_client.get("/analysis/product-ai", params={"query": "Alpha"})
    launch = authenticated_client.get("/analysis/launch", params=sample_concept_payload)
    personas = authenticated_client.get("/analysis/personas", params=sample_concept_payload)
    report = authenticated_client.get(
        "/analysis/report",
        params={
            "product_query": "Alpha",
            **sample_concept_payload,
        },
    )

    assert product.status_code == 200
    assert product.json()["product_query"] == "Alpha"
    assert product_ai.status_code == 200
    assert product_ai.json()["source"] == "deterministic"
    assert launch.status_code == 200
    assert launch.json()["launch_label"] in {
        "Promising Concept",
        "Needs Refinement",
        "High Launch Risk",
    }
    assert personas.status_code == 200
    assert len(personas.json()["personas"]) == 3
    assert report.status_code == 200
    assert report.json()["product_insight"]["product_query"] == "Alpha"
