import pytest
from unittest.mock import MagicMock, patch
from models import learning_service

def _mock_conn():
    conn = MagicMock()
    cur = MagicMock()
    conn.cursor.return_value = cur
    conn.__enter__.return_value = conn
    conn.__exit__.return_value = False
    return conn, cur

def test_open_lesson_returns_lesson_and_items_and_creates_progress():
    conn, cur = _mock_conn()
    cur.fetchone.side_effect = [
        {"id": 1, "title": "Greetings"},
        None,
    ]
    cur.fetchall.return_value = [{"id": 10, "term": "Muraho"}]
    with patch("models.learning_service.db_session", return_value=conn):
        lesson, items = learning_service.open_lesson(5, 1)
    assert lesson["title"] == "Greetings"
    assert items[0]["term"] == "Muraho"
    assert cur.execute.call_count >= 3

def test_open_lesson_raises_when_not_found():
    conn, cur = _mock_conn()
    cur.fetchone.return_value = None
    with patch("models.learning_service.db_session", return_value=conn):
        with pytest.raises(ValueError):
            learning_service.open_lesson(5, 999)

def test_mark_lesson_complete_upserts():
    conn, cur = _mock_conn()
    with patch("models.learning_service.db_session", return_value=conn):
        learning_service.mark_lesson_complete(5, 1)
    sql = cur.execute.call_args[0][0]
    assert "ON DUPLICATE KEY UPDATE" in sql

def test_get_learning_progress_returns_rows():
    conn, cur = _mock_conn()
    cur.fetchall.return_value = [
        {"lesson_title": "Greetings", "status": "completed"}
    ]
    with patch("models.learning_service.db_session", return_value=conn):
        rows = learning_service.get_learning_progress(5)
    assert rows[0]["status"] == "completed"