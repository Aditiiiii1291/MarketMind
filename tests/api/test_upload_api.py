"""Upload API tests."""


def test_valid_upload_and_history(authenticated_client, valid_upload_csv):
    """Authenticated users can upload a valid CSV and read upload history."""
    upload = authenticated_client.post(
        "/uploads",
        files={"file": ("probe.csv", valid_upload_csv, "text/csv")},
    )
    history = authenticated_client.get("/uploads/history")
    detail = authenticated_client.get(f"/uploads/{upload.json()['upload']['id']}")

    assert upload.status_code == 201
    assert upload.json()["summary"]["reviews_added"] == 3
    assert upload.json()["summary"]["products_added"] == 1
    assert history.status_code == 200
    assert len(history.json()["uploads"]) == 1
    assert detail.status_code == 200
    assert detail.json()["filename"] == "probe.csv"


def test_duplicate_upload_skips_duplicate_reviews(authenticated_client, valid_upload_csv):
    """Uploading the same source twice preserves duplicate-review handling."""
    first = authenticated_client.post(
        "/uploads",
        files={"file": ("probe.csv", valid_upload_csv, "text/csv")},
    )
    second = authenticated_client.post(
        "/uploads",
        files={"file": ("probe.csv", valid_upload_csv, "text/csv")},
    )

    assert first.status_code == 201
    assert second.status_code == 201
    assert second.json()["summary"]["reviews_added"] == 0
    assert second.json()["summary"]["duplicates_skipped"] == 3


def test_invalid_and_malformed_uploads_return_400(
    authenticated_client,
    invalid_upload_csv,
    malformed_upload_csv,
):
    """Invalid upload payloads map to current 400 responses."""
    wrong_extension = authenticated_client.post(
        "/uploads",
        files={"file": ("probe.txt", invalid_upload_csv, "text/plain")},
    )
    invalid_columns = authenticated_client.post(
        "/uploads",
        files={"file": ("invalid.csv", invalid_upload_csv, "text/csv")},
    )
    malformed = authenticated_client.post(
        "/uploads",
        files={"file": ("malformed.csv", malformed_upload_csv, "text/csv")},
    )

    assert wrong_extension.status_code == 400
    assert wrong_extension.json()["detail"] == "Only CSV uploads are supported."
    assert invalid_columns.status_code == 400
    assert "missing required columns" in invalid_columns.json()["detail"]
    assert malformed.status_code == 400
    assert malformed.json()["detail"] == "Uploaded CSV could not be parsed."


def test_upload_requires_authentication(client, valid_upload_csv):
    """Upload endpoint remains protected by authentication."""
    response = client.post(
        "/uploads",
        files={"file": ("probe.csv", valid_upload_csv, "text/csv")},
    )

    assert response.status_code == 401
