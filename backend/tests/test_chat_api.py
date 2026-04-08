from unittest.mock import MagicMock, patch

from backend.models import Conversation


def _mock_claude(api_key):
    client = MagicMock()
    msg = MagicMock()
    msg.content = [MagicMock(text="That's a great question about Zone 2 training.")]
    client.messages.create.return_value = msg
    return client


def test_send_message_no_api_key(client, monkeypatch):
    monkeypatch.setattr("backend.config.settings.anthropic_api_key", "")
    resp = client.post("/chat/", json={"message": "Hello"})
    assert resp.status_code == 503


def test_send_message_empty(client, monkeypatch):
    monkeypatch.setattr("backend.config.settings.anthropic_api_key", "sk-test")
    resp = client.post("/chat/", json={"message": "   "})
    assert resp.status_code == 400


def test_send_message_success(client, monkeypatch):
    monkeypatch.setattr("backend.config.settings.anthropic_api_key", "sk-test")
    with patch("anthropic.Anthropic", side_effect=_mock_claude):
        resp = client.post("/chat/", json={"message": "Tell me about Zone 2"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["role"] == "assistant"
    assert "Zone 2" in data["content"]


def test_send_message_stores_both_turns(client, db, monkeypatch):
    monkeypatch.setattr("backend.config.settings.anthropic_api_key", "sk-test")
    with patch("anthropic.Anthropic", side_effect=_mock_claude):
        client.post("/chat/", json={"message": "Hello"})

    from sqlalchemy import select
    rows = db.execute(select(Conversation).order_by(Conversation.created_at)).scalars().all()
    assert len(rows) == 2
    assert rows[0].role == "user"
    assert rows[1].role == "assistant"


def test_get_history_empty(client):
    resp = client.get("/chat/history")
    assert resp.status_code == 200
    assert resp.json() == []


def test_get_history_returns_messages(client, db):
    db.add(Conversation(role="user", content="Hello"))
    db.add(Conversation(role="assistant", content="Hi there"))
    db.commit()
    resp = client.get("/chat/history")
    assert len(resp.json()) == 2
    assert resp.json()[0]["role"] == "user"


def test_clear_history(client, db):
    db.add(Conversation(role="user", content="Hello"))
    db.commit()
    resp = client.delete("/chat/history")
    assert resp.status_code == 204
    assert client.get("/chat/history").json() == []
