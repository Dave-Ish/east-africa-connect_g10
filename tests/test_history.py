import history


class FakeCursor:
    def __init__(self, rows):
        self.rows = rows

    def execute(self, query, params):
        self.query = query
        self.params = params

    def fetchall(self):
        return self.rows

    def close(self):
        pass


class FakeConnection:
    def __init__(self, cursor):
        self.fake_cursor = cursor

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def cursor(self, dictionary=False):
        return self.fake_cursor


def test_history_shows_attempts_for_student(monkeypatch, capsys):
    rows = [{
        "attempt_id": 1,
        "lesson_title": "Greetings",
        "score": 4,
        "total_questions": 5,
        "status": "completed",
        "started_at": "2026-11-20 10:00:00",
        "completed_at": "2026-11-20 10:05:00",
    }]
    cursor = FakeCursor(rows)
    connection = FakeConnection(cursor)
    monkeypatch.setattr(history, "db_session", lambda: connection)

    history.show_history(42)

    output = capsys.readouterr().out
    assert cursor.params == (42,)
    assert "WHERE a.user_id = %s" in cursor.query
    assert "Greetings" in output
    assert "4/5" in output