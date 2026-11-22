"""Lesson access and student learning-progress operations for East Africa Connect."""

from __future__ import annotations

try:
    from db.connection import db_session
except ModuleNotFoundError as exc:
    if exc.name != "db.connection":
        raise
    from db.connections import db_session


def _require_positive_id(value: int, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer.")


def open_lesson(user_id: int, lesson_id: int) -> tuple[dict, list[dict]]:
    """Load an active lesson and its ordered items, recording learner access."""
    _require_positive_id(user_id, "user_id")
    _require_positive_id(lesson_id, "lesson_id")

    with db_session() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(
                """SELECT lesson_id, lesson_id AS id, language_id,
                          support_language_id, title, description, level,
                          lesson_number, created_by, is_active, created_at, updated_at
                   FROM lessons
                   WHERE lesson_id = %s AND is_active = %s""",
                (lesson_id, 1),
            )
            lesson = cursor.fetchone()
            if lesson is None:
                raise ValueError("Lesson not found or inactive.")

            cursor.execute(
                """SELECT item_id, lesson_id, item_number,
                          term_text, term_text AS term,
                          translation_text, translation_text AS translation,
                          pronunciation,
                          example_sentence, example_sentence AS example,
                          example_translation
                   FROM lesson_items
                   WHERE lesson_id = %s
                   ORDER BY item_number ASC, item_id ASC""",
                (lesson_id,),
            )
            items = list(cursor.fetchall())

            # Preserve completed status when a learner revisits a lesson.
            cursor.execute(
                """INSERT INTO lesson_progress (user_id, lesson_id, status)
                   VALUES (%s, %s, 'in_progress')
                   ON DUPLICATE KEY UPDATE last_accessed_at = CURRENT_TIMESTAMP""",
                (user_id, lesson_id),
            )
            return dict(lesson), items
        finally:
            cursor.close()


def mark_lesson_complete(user_id: int, lesson_id: int) -> None:
    """Mark progress complete and refresh its completion/access timestamps."""
    _require_positive_id(user_id, "user_id")
    _require_positive_id(lesson_id, "lesson_id")

    with db_session() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                """INSERT INTO lesson_progress
                       (user_id, lesson_id, status, last_accessed_at, completed_at)
                   VALUES (%s, %s, 'completed', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                   ON DUPLICATE KEY UPDATE
                       status = 'completed',
                       last_accessed_at = CURRENT_TIMESTAMP,
                       completed_at = CURRENT_TIMESTAMP""",
                (user_id, lesson_id),
            )
        finally:
            cursor.close()


def get_learning_progress(user_id: int) -> list[dict]:
    """Return saved progress joined to its lesson and language, newest first."""
    _require_positive_id(user_id, "user_id")

    with db_session() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(
                """SELECT lp.lesson_id, lp.status, lp.started_at,
                          lp.last_accessed_at, lp.completed_at,
                          l.title AS lesson_title, l.level,
                          lang.language_name AS language_name
                   FROM lesson_progress AS lp
                   INNER JOIN lessons AS l ON l.lesson_id = lp.lesson_id
                   INNER JOIN languages AS lang ON lang.language_id = l.language_id
                   WHERE lp.user_id = %s
                   ORDER BY lp.last_accessed_at DESC, lp.lesson_id DESC""",
                (user_id,),
            )
            return list(cursor.fetchall())
        finally:
            cursor.close()
