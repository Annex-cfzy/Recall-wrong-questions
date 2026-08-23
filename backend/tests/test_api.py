"""Integration tests for the core API surface using FastAPI TestClient.

Covers AC-M1.3 (notebook CRUD), M2 (text input + list + edit), M5 (export),
and M3 (no-due review path). Runs against the mock-external mode by default.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["code"] == 0


def test_notebook_crud(client):
    r = client.post(
        "/api/notebooks",
        json={"name": "测试本", "subject": "数学", "color": "#007AFF"},
    )
    body = r.json()
    assert body["code"] == 0
    nb_id = body["data"]["id"]

    lst = client.get("/api/notebooks").json()
    assert lst["code"] == 0
    assert any(n["id"] == nb_id for n in lst["data"]["items"])

    upd = client.put(f"/api/notebooks/{nb_id}", json={"name": "改名"})
    assert upd.json()["code"] == 0

    delete = client.delete(f"/api/notebooks/{nb_id}")
    assert delete.json()["code"] == 0


def test_text_error_input_and_edit(client):
    nb = client.post("/api/notebooks", json={"name": "本2", "subject": "数学"})
    nb_id = nb.json()["data"]["id"]

    r = client.post(
        "/api/errors/text",
        json={
            "question": "1+1=?",
            "answer": "2",
            "notebook_id": nb_id,
            "subject": "数学",
        },
    )
    assert r.json()["code"] == 0
    eid = r.json()["data"]["id"]

    lst = client.get("/api/errors", params={"notebook_id": nb_id}).json()
    assert lst["data"]["total"] == 1

    edit = client.put(f"/api/errors/{eid}", json={"question": "2+2=?"})
    assert edit.json()["code"] == 0
    assert edit.json()["data"]["vector_updated"] is True


def test_export_markdown(client):
    nb = client.post("/api/notebooks", json={"name": "本3", "subject": "语文"})
    nb_id = nb.json()["data"]["id"]
    r = client.get(f"/api/export/markdown/{nb_id}")
    assert r.status_code == 200
    assert "错题导出" in r.text


def test_review_no_due(client):
    nb = client.post("/api/notebooks", json={"name": "本4", "subject": "英语"})
    nb_id = nb.json()["data"]["id"]
    r = client.post(
        "/api/review/start", json={"notebook_id": nb_id, "count": 10}
    )
    assert r.json()["code"] == 5001  # no due errors
