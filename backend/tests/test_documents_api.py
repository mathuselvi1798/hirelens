import io


def _upload(client, name: str, data: bytes):
    return client.post("/api/v1/documents", files={"file": (name, io.BytesIO(data), "text/plain")})


def test_upload_returns_summary(client, resume_bytes):
    response = _upload(client, "resume.txt", resume_bytes)
    assert response.status_code == 201
    body = response.json()
    assert body["file_type"] == "txt"
    assert body["word_count"] > 50
    assert "experience" in body["section_names"]
    assert body["contact"]["email"] == "karthik@example.com"
    # The full text is intentionally not echoed back.
    assert "raw_text" not in body


def test_rejects_unsupported_extension(client, resume_bytes):
    response = _upload(client, "resume.pages", resume_bytes)
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "unsupported_file_type"


def test_rejects_near_empty_file(client):
    response = _upload(client, "resume.txt", b"hello")
    assert response.status_code == 422
    assert response.json()["error"]["code"] in {"empty_document", "corrupt_document"}


def test_document_can_be_fetched_again(client, resume_bytes):
    document_id = _upload(client, "resume.txt", resume_bytes).json()["id"]
    assert client.get(f"/api/v1/documents/{document_id}").status_code == 200


def test_unknown_document_returns_404(client):
    response = client.get("/api/v1/documents/does-not-exist")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "document_not_found"
