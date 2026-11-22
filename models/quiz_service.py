"""Quiz question delivery, answer submission, scoring, and attempt history.

Student-facing question retrieval deliberately omits correct answers and
explanations. Answer feedback is available only after an answer row with a
non-NULL submitted option has been saved.
"""

from __future__ import annotations

from typing import Any

try:
    from db.connection import db_session
except ModuleNotFoundError as exc:
    if exc.name != "db.connection":
        raise
    from db.connections import db_session


_VALID_OPTIONS = frozenset({"A", "B", "C", "D"})


def _require_positive_id(value: int, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer.")


def _normalize_option(selected_option: str | None) -> str | None:
    if selected_option is None:
        return None
    if not isinstance(selected_option, str):
        raise ValueError("selected_option must be A, B, C, D, or None.")
    option = selected_option.strip().upper()
    if option not in _VALID_OPTIONS:
        raise ValueError("selected_option must be one of A, B, C, or D, or None.")
    return option


def get_quiz_questions(lesson_id: int, limit: int = 5) -> list[dict]:
    """Return active quiz questions for a lesson without revealing answer keys."""
    _require_positive_id(lesson_id, "lesson_id")
    if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0:
        raise ValueError("limit must be a positive integer.")

    with db_session() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(
                """
                SELECT q.question_id, q.lesson_id, q.question_text,
                       q.choice_a, q.choice_b, q.choice_c, q.choice_d
                FROM questions AS q
                INNER JOIN lessons AS l ON l.lesson_id = q.lesson_id
                WHERE q.lesson_id = %s
                  AND q.is_active = %s
                  AND l.is_active = %s
                ORDER BY RAND(), q.question_id
                LIMIT %s
                """,
                (lesson_id, 1, 1, limit),
            )
            return list(cursor.fetchall())
        finally:
            cursor.close()


def start_attempt(user_id: int, lesson_id: int, question_ids: list[int]) -> int:
    """Create an in-progress attempt for a nonempty set of active lesson questions."""
    _require_positive_id(user_id, "user_id")
    _require_positive_id(lesson_id, "lesson_id")
    if not isinstance(question_ids, list) or not question_ids:
        raise ValueError("question_ids must be a nonempty list of question IDs.")
    for question_id in question_ids:
        _require_positive_id(question_id, "question_id")
    if len(set(question_ids)) != len(question_ids):
        raise ValueError("question_ids must not contain duplicates.")

    placeholders = ", ".join(["%s"] * len(question_ids))
    with db_session() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT user_id FROM users WHERE user_id = %s",
                (user_id,),
            )
            if cursor.fetchone() is None:
                raise ValueError(f"No user exists with user_id {user_id}.")

            cursor.execute(
                "SELECT lesson_id FROM lessons WHERE lesson_id = %s AND is_active = %s",
                (lesson_id, 1),
            )
            if cursor.fetchone() is None:
                raise ValueError(f"No active lesson exists with lesson_id {lesson_id}.")

            cursor.execute(
                f"""SELECT question_id
                    FROM questions
                    WHERE lesson_id = %s AND is_active = %s
                      AND question_id IN ({placeholders})""",
                (lesson_id, 1, *question_ids),
            )
            found_ids = {row["question_id"] for row in cursor.fetchall()}
            missing_ids = [question_id for question_id in question_ids if question_id not in found_ids]
            if missing_ids:
                raise ValueError(
                    "Every question must be active and belong to the selected lesson; "
                    f"invalid question ID(s): {', '.join(map(str, missing_ids))}."
                )

            cursor.execute(
                """INSERT INTO attempts (user_id, lesson_id, total_questions, status)
                   VALUES (%s, %s, %s, %s)""",
                (user_id, lesson_id, len(question_ids), "in_progress"),
            )
            attempt_id = int(cursor.lastrowid)
            cursor.executemany(
                """INSERT INTO attempt_answers
                       (attempt_id, lesson_id, question_id, selected_option, is_correct)
                   VALUES (%s, %s, %s, NULL, %s)""",
                [(attempt_id, lesson_id, question_id, 0) for question_id in question_ids],
            )
            return attempt_id
        finally:
            cursor.close()


def record_answer(
    attempt_id: int,
    question_id: int,
    selected_option: str | None,
) -> bool:
    """Save one answer and return whether it is correct.

    ``start_attempt`` stores the selected question roster as unanswered rows.
    Passing ``None`` leaves that question unanswered (and therefore incorrect
    in the final score); a non-NULL answer can still be submitted later. The
    attempt row is locked so concurrent submissions cannot both pass the
    status and duplicate-answer checks.
    """
    _require_positive_id(attempt_id, "attempt_id")
    _require_positive_id(question_id, "question_id")
    option = _normalize_option(selected_option)

    with db_session() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(
                """SELECT attempt_id, lesson_id, total_questions, status
                   FROM attempts WHERE attempt_id = %s FOR UPDATE""",
                (attempt_id,),
            )
            attempt = cursor.fetchone()
            if attempt is None:
                raise ValueError(f"No attempt exists with attempt_id {attempt_id}.")
            if attempt["status"] != "in_progress":
                raise ValueError("Answers can only be recorded for an in-progress attempt.")

            cursor.execute(
                """SELECT aa.selected_option, q.correct_option
                   FROM attempt_answers AS aa
                   INNER JOIN questions AS q
                     ON q.question_id = aa.question_id AND q.lesson_id = aa.lesson_id
                   WHERE aa.attempt_id = %s AND aa.question_id = %s
                   FOR UPDATE""",
                (attempt_id, question_id),
            )
            answer = cursor.fetchone()
            if answer is None:
                raise ValueError("The question was not selected for this attempt.")
            if answer["selected_option"] is not None:
                raise ValueError("An answer for this question has already been recorded.")
            if option is None:
                return False

            is_correct = option == answer["correct_option"]
            cursor.execute(
                """UPDATE attempt_answers
                   SET selected_option = %s, is_correct = %s,
                       answered_at = CURRENT_TIMESTAMP
                   WHERE attempt_id = %s AND question_id = %s
                     AND selected_option IS NULL""",
                (
                    option,
                    1 if is_correct else 0,
                    attempt_id,
                    question_id,
                ),
            )
            if cursor.rowcount != 1:
                raise ValueError("An answer for this question has already been recorded.")
            return bool(is_correct)
        finally:
            cursor.close()


def finish_attempt(attempt_id: int) -> dict:
    """Finalize an attempt using its persisted correct-answer rows.

    Finishing an already completed attempt is idempotent and returns its saved
    result. An abandoned attempt cannot be finalized.
    """
    _require_positive_id(attempt_id, "attempt_id")

    with db_session() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(
                """SELECT attempt_id, user_id, lesson_id, score, total_questions,
                          status, started_at, completed_at
                   FROM attempts WHERE attempt_id = %s FOR UPDATE""",
                (attempt_id,),
            )
            attempt = cursor.fetchone()
            if attempt is None:
                raise ValueError(f"No attempt exists with attempt_id {attempt_id}.")
            if attempt["status"] == "abandoned":
                raise ValueError("An abandoned attempt cannot be completed.")
            if attempt["status"] == "in_progress":
                cursor.execute(
                    """SELECT COUNT(*) AS score
                       FROM attempt_answers
                       WHERE attempt_id = %s AND is_correct = %s""",
                    (attempt_id, 1),
                )
                score = int(cursor.fetchone()["score"])
                cursor.execute(
                    """UPDATE attempts
                       SET score = %s, status = %s,
                           completed_at = CURRENT_TIMESTAMP
                       WHERE attempt_id = %s AND status = %s""",
                    (score, "completed", attempt_id, "in_progress"),
                )

            cursor.execute(
                """SELECT attempt_id, user_id, lesson_id, score, total_questions,
                          status, started_at, completed_at
                   FROM attempts WHERE attempt_id = %s""",
                (attempt_id,),
            )
            result = cursor.fetchone()
            return dict(result)
        finally:
            cursor.close()


def get_user_attempts(user_id: int) -> list[dict]:
    """Return a user's saved attempts, newest first."""
    _require_positive_id(user_id, "user_id")
    with db_session() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(
                """SELECT a.attempt_id, a.user_id, a.lesson_id, l.title AS lesson_title,
                          a.score, a.total_questions, a.status, a.started_at, a.completed_at
                   FROM attempts AS a
                   INNER JOIN lessons AS l ON l.lesson_id = a.lesson_id
                   WHERE a.user_id = %s
                   ORDER BY a.started_at DESC, a.attempt_id DESC""",
                (user_id,),
            )
            return list(cursor.fetchall())
        finally:
            cursor.close()


def get_all_attempts() -> list[dict]:
    """Return the teacher results list with username and lesson title."""
    with db_session() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(
                """SELECT a.attempt_id, u.username, l.title AS lesson_title,
                          a.score, a.total_questions, a.status, a.started_at, a.completed_at
                   FROM attempts AS a
                   INNER JOIN users AS u ON u.user_id = a.user_id
                   INNER JOIN lessons AS l ON l.lesson_id = a.lesson_id
                   ORDER BY a.started_at DESC, a.attempt_id DESC"""
            )
            return list(cursor.fetchall())
        finally:
            cursor.close()


def get_answer_feedback(attempt_id: int, question_id: int) -> dict[str, Any] | None:
    """Return correctness and explanation only for a saved submitted option.

    ``None`` is returned when there is no saved non-NULL answer for this
    attempt/question pair; the answer key is never exposed before submission.
    """
    _require_positive_id(attempt_id, "attempt_id")
    _require_positive_id(question_id, "question_id")
    with db_session() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(
                """SELECT aa.question_id, aa.selected_option, aa.is_correct,
                          q.correct_option, q.explanation
                   FROM attempt_answers AS aa
                   INNER JOIN questions AS q
                     ON q.question_id = aa.question_id AND q.lesson_id = aa.lesson_id
                   WHERE aa.attempt_id = %s
                     AND aa.question_id = %s
                     AND aa.selected_option IS NOT NULL""",
                (attempt_id, question_id),
            )
            row = cursor.fetchone()
            return dict(row) if row is not None else None
        finally:
            cursor.close()
