from mysql.connector import IntegrityError
from db.connection import db_session

VALID_OPTIONS = {"A", "B", "C", "D"}


def _require_teacher(user_id: int) -> None:
    """Enforce teacher-only access in the service layer."""
    with db_session() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT role FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            if not user or user.get("role") != "teacher":
                raise PermissionError("Access denied: Teacher privileges are required.")
        finally:
            cursor.close()


def list_lessons(language_id: int, active_only: bool = True) -> list[dict]:
    with db_session() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            if active_only:
                cursor.execute(
                    "SELECT * FROM lessons WHERE language_id = %s AND is_active = 1 ORDER BY display_order ASC, id ASC",
                    (language_id,),
                )
            else:
                cursor.execute(
                    "SELECT * FROM lessons WHERE language_id = %s ORDER BY display_order ASC, id ASC",
                    (language_id,),
                )
            return cursor.fetchall()
        finally:
            cursor.close()


def get_lesson(lesson_id: int) -> dict | None:
    with db_session() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM lessons WHERE id = %s", (lesson_id,))
            return cursor.fetchone()
        finally:
            cursor.close()


def create_lesson(
    language_id: int,
    support_language: str,
    title: str,
    level: str,
    display_order: int,
    created_by: int,
) -> int:
    _require_teacher(created_by)
    if not title or not title.strip():
        raise ValueError("Lesson title is required.")

    with db_session() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO lessons (language_id, support_language, title, level, display_order, is_active, created_by)
                VALUES (%s, %s, %s, %s, %s, 1, %s)
                """,
                (language_id, support_language.strip(), title.strip(), level.strip(), display_order, created_by),
            )
            return cursor.lastrowid
        finally:
            cursor.close()


def update_lesson(
    lesson_id: int,
    title: str,
    level: str,
    display_order: int,
    user_id: int | None = None,
) -> None:
    if user_id is not None:
        _require_teacher(user_id)
    if not title or not title.strip():
        raise ValueError("Lesson title cannot be empty.")

    with db_session() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE lessons SET title = %s, level = %s, display_order = %s WHERE id = %s",
                (title.strip(), level.strip(), display_order, lesson_id),
            )
            if cursor.rowcount == 0:
                raise ValueError(f"Lesson ID {lesson_id} does not exist.")
        finally:
            cursor.close()


def archive_lesson(lesson_id: int, user_id: int | None = None) -> None:
    if user_id is not None:
        _require_teacher(user_id)
    with db_session() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE lessons SET is_active = 0 WHERE id = %s", (lesson_id,))
            if cursor.rowcount == 0:
                raise ValueError(f"Lesson ID {lesson_id} does not exist.")
        finally:
            cursor.close()


def delete_lesson(lesson_id: int, user_id: int | None = None) -> None:
    if user_id is not None:
        _require_teacher(user_id)
    with db_session() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT COUNT(*) AS cnt FROM attempts WHERE lesson_id = %s", (lesson_id,))
            attempt_refs = cursor.fetchone()["cnt"]
            cursor.execute("SELECT COUNT(*) AS cnt FROM lesson_progress WHERE lesson_id = %s", (lesson_id,))
            progress_refs = cursor.fetchone()["cnt"]

            if attempt_refs > 0 or progress_refs > 0:
                raise ValueError(
                    "Cannot delete lesson because learners have progress or quiz attempts tied to it. "
                    "Use archive_lesson() instead to preserve history."
                )

            cursor.execute("DELETE FROM lessons WHERE id = %s", (lesson_id,))
            if cursor.rowcount == 0:
                raise ValueError(f"Lesson ID {lesson_id} does not exist.")
        except IntegrityError:
            raise ValueError("Delete blocked: Lesson is referenced by existing records. Archive it instead.")
        finally:
            cursor.close()


def list_lesson_items(lesson_id: int, active_only: bool = True) -> list[dict]:
    with db_session() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            if active_only:
                cursor.execute(
                    "SELECT * FROM lesson_items WHERE lesson_id = %s AND is_active = 1 ORDER BY display_order ASC, id ASC",
                    (lesson_id,),
                )
            else:
                cursor.execute(
                    "SELECT * FROM lesson_items WHERE lesson_id = %s ORDER BY display_order ASC, id ASC",
                    (lesson_id,),
                )
            return cursor.fetchall()
        finally:
            cursor.close()


def add_lesson_item(
    lesson_id: int,
    term: str,
    translation: str,
    pronunciation: str | None = None,
    example: str | None = None,
    display_order: int = 1,
    created_by: int | None = None,
) -> int:
    if created_by is not None:
        _require_teacher(created_by)
    if not term or not term.strip() or not translation or not translation.strip():
        raise ValueError("Both term and translation are required.")

    with db_session() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO lesson_items
                (lesson_id, term, translation, pronunciation, example, display_order, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, 1)
                """,
                (
                    lesson_id,
                    term.strip(),
                    translation.strip(),
                    pronunciation.strip() if pronunciation else None,
                    example.strip() if example else None,
                    display_order,
                ),
            )
            return cursor.lastrowid
        finally:
            cursor.close()


def update_lesson_item(
    item_id: int,
    term: str,
    translation: str,
    pronunciation: str | None = None,
    example: str | None = None,
    display_order: int = 1,
    user_id: int | None = None,
) -> None:
    if user_id is not None:
        _require_teacher(user_id)
    if not term or not term.strip() or not translation or not translation.strip():
        raise ValueError("Both term and translation are required.")

    with db_session() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                UPDATE lesson_items
                SET term = %s, translation = %s, pronunciation = %s, example = %s, display_order = %s
                WHERE id = %s
                """,
                (
                    term.strip(),
                    translation.strip(),
                    pronunciation.strip() if pronunciation else None,
                    example.strip() if example else None,
                    display_order,
                    item_id,
                ),
            )
            if cursor.rowcount == 0:
                raise ValueError(f"Lesson item ID {item_id} does not exist.")
        finally:
            cursor.close()


def delete_lesson_item(item_id: int, user_id: int | None = None) -> None:
    if user_id is not None:
        _require_teacher(user_id)
    with db_session() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM lesson_items WHERE id = %s", (item_id,))
            if cursor.rowcount == 0:
                raise ValueError(f"Lesson item ID {item_id} does not exist.")
        finally:
            cursor.close()


def create_question(
    lesson_id: int,
    prompt: str,
    option_a: str,
    option_b: str,
    option_c: str,
    option_d: str,
    correct_option: str,
    explanation: str | None,
    created_by: int,
) -> int:
    _require_teacher(created_by)
    clean_opt = (correct_option or "").strip().upper()
    if clean_opt not in VALID_OPTIONS:
        raise ValueError("Correct option must be A, B, C, or D.")
    if not all((val or "").strip() for val in (prompt, option_a, option_b, option_c, option_d)):
        raise ValueError("Question prompt and all four options (A-D) are required.")

    with db_session() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO questions
                (lesson_id, prompt, option_a, option_b, option_c, option_d, correct_option, explanation, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 1)
                """,
                (
                    lesson_id,
                    prompt.strip(),
                    option_a.strip(),
                    option_b.strip(),
                    option_c.strip(),
                    option_d.strip(),
                    clean_opt,
                    explanation.strip() if explanation else None,
                ),
            )
            return cursor.lastrowid
        finally:
            cursor.close()


def list_questions(lesson_id: int, active_only: bool = True) -> list[dict]:
    with db_session() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            if active_only:
                cursor.execute(
                    "SELECT * FROM questions WHERE lesson_id = %s AND is_active = 1 ORDER BY id ASC",
                    (lesson_id,),
                )
            else:
                cursor.execute(
                    "SELECT * FROM questions WHERE lesson_id = %s ORDER BY id ASC",
                    (lesson_id,),
                )
            return cursor.fetchall()
        finally:
            cursor.close()


def update_question(
    question_id: int,
    prompt: str,
    option_a: str,
    option_b: str,
    option_c: str,
    option_d: str,
    correct_option: str,
    explanation: str | None = None,
    user_id: int | None = None,
) -> None:
    if user_id is not None:
        _require_teacher(user_id)
    clean_opt = (correct_option or "").strip().upper()
    if clean_opt not in VALID_OPTIONS:
        raise ValueError("Correct option must be A, B, C, or D.")
    if not all((val or "").strip() for val in (prompt, option_a, option_b, option_c, option_d)):
        raise ValueError("Question prompt and all four options (A-D) are required.")

    with db_session() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                UPDATE questions
                SET prompt = %s, option_a = %s, option_b = %s, option_c = %s,
                    option_d = %s, correct_option = %s, explanation = %s
                WHERE id = %s
                """,
                (
                    prompt.strip(),
                    option_a.strip(),
                    option_b.strip(),
                    option_c.strip(),
                    option_d.strip(),
                    clean_opt,
                    explanation.strip() if explanation else None,
                    question_id,
                ),
            )
            if cursor.rowcount == 0:
                raise ValueError(f"Question ID {question_id} does not exist.")
        finally:
            cursor.close()


def archive_question(question_id: int, user_id: int | None = None) -> None:
    if user_id is not None:
        _require_teacher(user_id)
    with db_session() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE questions SET is_active = 0 WHERE id = %s", (question_id,))
            if cursor.rowcount == 0:
                raise ValueError(f"Question ID {question_id} does not exist.")
        finally:
            cursor.close()


def delete_question(question_id: int, user_id: int | None = None) -> None:
    if user_id is not None:
        _require_teacher(user_id)
    with db_session() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT COUNT(*) AS cnt FROM attempt_answers WHERE question_id = %s", (question_id,))
            if cursor.fetchone()["cnt"] > 0:
                raise ValueError(
                    "Cannot delete question because it is referenced by saved quiz attempts. "
                    "Use archive_question() instead to preserve student history."
                )

            cursor.execute("DELETE FROM questions WHERE id = %s", (question_id,))
            if cursor.rowcount == 0:
                raise ValueError(f"Question ID {question_id} does not exist.")
        except IntegrityError:
            raise ValueError("Delete blocked: Question is referenced by historic attempt answers. Archive it instead.")
        finally:
            cursor.close()
