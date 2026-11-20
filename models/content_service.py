from mysql.connector import IntegrityError
from db.connection import db_session

VALID_OPTIONS = {"A", "B", "C", "D"}
VALID_LEVELS = {"beginner", "intermediate", "advanced"}


def _require_teacher(user_id: int) -> None:
    """Enforce teacher-only access in the service layer."""
    with db_session() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT role FROM users WHERE user_id = %s", (user_id,))
            user = cursor.fetchone()
            if not user or user.get("role") != "teacher":
                raise PermissionError("Access denied: Teacher privileges are required.")
        finally:
            cursor.close()


# ==================== LESSONS CRUD & ARCHIVE ====================

def list_lessons(language_id: int, active_only: bool = True) -> list[dict]:
    with db_session() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            if active_only:
                cursor.execute(
                    """
                    SELECT * FROM lessons
                    WHERE language_id = %s AND is_active = 1
                    ORDER BY lesson_number ASC, lesson_id ASC
                    """,
                    (language_id,),
                )
            else:
                cursor.execute(
                    """
                    SELECT * FROM lessons
                    WHERE language_id = %s
                    ORDER BY lesson_number ASC, lesson_id ASC
                    """,
                    (language_id,),
                )
            return cursor.fetchall()
        finally:
            cursor.close()


def get_lesson(lesson_id: int) -> dict | None:
    with db_session() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM lessons WHERE lesson_id = %s", (lesson_id,))
            return cursor.fetchone()
        finally:
            cursor.close()


def create_lesson(
    language_id: int,
    support_language_id: int,
    title: str,
    level: str = "beginner",
    lesson_number: int = 1,
    created_by: int | None = None,
    description: str | None = None,
) -> int:
    if created_by is not None:
        _require_teacher(created_by)
    if not title or not title.strip():
        raise ValueError("Lesson title is required.")
    if lesson_number <= 0:
        raise ValueError("Lesson number must be greater than 0.")

    clean_level = (level or "beginner").strip().lower()
    if clean_level not in VALID_LEVELS:
        raise ValueError("Level must be 'beginner', 'intermediate', or 'advanced'.")

    with db_session() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO lessons
                (language_id, support_language_id, title, description, level, lesson_number, created_by, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 1)
                """,
                (
                    language_id,
                    support_language_id,
                    title.strip(),
                    description.strip() if description else None,
                    clean_level,
                    lesson_number,
                    created_by,
                ),
            )
            return cursor.lastrowid
        except IntegrityError as err:
            raise ValueError(f"Could not create lesson (duplicate lesson number/title or invalid language ID): {err}")
        finally:
            cursor.close()


def update_lesson(
    lesson_id: int,
    title: str,
    level: str,
    lesson_number: int,
    user_id: int | None = None,
    description: str | None = None,
) -> None:
    if user_id is not None:
        _require_teacher(user_id)
    if not title or not title.strip():
        raise ValueError("Lesson title cannot be empty.")
    if lesson_number <= 0:
        raise ValueError("Lesson number must be greater than 0.")

    clean_level = (level or "beginner").strip().lower()
    if clean_level not in VALID_LEVELS:
        raise ValueError("Level must be 'beginner', 'intermediate', or 'advanced'.")

    with db_session() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                UPDATE lessons
                SET title = %s, description = %s, level = %s, lesson_number = %s
                WHERE lesson_id = %s
                """,
                (
                    title.strip(),
                    description.strip() if description else None,
                    clean_level,
                    lesson_number,
                    lesson_id,
                ),
            )
            if cursor.rowcount == 0:
                raise ValueError(f"Lesson ID {lesson_id} does not exist.")
        except IntegrityError as err:
            raise ValueError(f"Could not update lesson (duplicate lesson number or title): {err}")
        finally:
            cursor.close()


def archive_lesson(lesson_id: int, user_id: int | None = None) -> None:
    """Safely deactivate a lesson while preserving historic progress and attempts."""
    if user_id is not None:
        _require_teacher(user_id)
    with db_session() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE lessons SET is_active = 0 WHERE lesson_id = %s", (lesson_id,))
            if cursor.rowcount == 0:
                raise ValueError(f"Lesson ID {lesson_id} does not exist.")
        finally:
            cursor.close()


def delete_lesson(lesson_id: int, user_id: int | None = None) -> None:
    """Physically delete a lesson only if unreferenced; otherwise block with clear guidance."""
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

            cursor.execute("DELETE FROM lessons WHERE lesson_id = %s", (lesson_id,))
            if cursor.rowcount == 0:
                raise ValueError(f"Lesson ID {lesson_id} does not exist.")
        except IntegrityError:
            raise ValueError(
                "Delete blocked: Lesson is referenced by existing records. Archive it instead."
            )
        finally:
            cursor.close()


# ==================== LESSON ITEMS CRUD ====================

def list_lesson_items(lesson_id: int) -> list[dict]:
    with db_session() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(
                """
                SELECT * FROM lesson_items
                WHERE lesson_id = %s
                ORDER BY item_number ASC, item_id ASC
                """,
                (lesson_id,),
            )
            return cursor.fetchall()
        finally:
            cursor.close()


def add_lesson_item(
    lesson_id: int,
    term_text: str,
    translation_text: str,
    pronunciation: str | None = None,
    example_sentence: str | None = None,
    example_translation: str | None = None,
    item_number: int = 1,
    created_by: int | None = None,
) -> int:
    if created_by is not None:
        _require_teacher(created_by)
    if not term_text or not term_text.strip() or not translation_text or not translation_text.strip():
        raise ValueError("Both term and translation are required.")
    if item_number <= 0:
        raise ValueError("Item number must be greater than 0.")

    with db_session() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO lesson_items
                (lesson_id, item_number, term_text, translation_text, pronunciation, example_sentence, example_translation)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    lesson_id,
                    item_number,
                    term_text.strip(),
                    translation_text.strip(),
                    pronunciation.strip() if pronunciation else None,
                    example_sentence.strip() if example_sentence else None,
                    example_translation.strip() if example_translation else None,
                ),
            )
            return cursor.lastrowid
        except IntegrityError as err:
            raise ValueError(f"Could not add lesson item (duplicate item number or invalid lesson ID): {err}")
        finally:
            cursor.close()


def update_lesson_item(
    item_id: int,
    term_text: str,
    translation_text: str,
    pronunciation: str | None = None,
    example_sentence: str | None = None,
    example_translation: str | None = None,
    item_number: int = 1,
    user_id: int | None = None,
) -> None:
    if user_id is not None:
        _require_teacher(user_id)
    if not term_text or not term_text.strip() or not translation_text or not translation_text.strip():
        raise ValueError("Both term and translation are required.")
    if item_number <= 0:
        raise ValueError("Item number must be greater than 0.")

    with db_session() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                UPDATE lesson_items
                SET item_number = %s, term_text = %s, translation_text = %s,
                    pronunciation = %s, example_sentence = %s, example_translation = %s
                WHERE item_id = %s
                """,
                (
                    item_number,
                    term_text.strip(),
                    translation_text.strip(),
                    pronunciation.strip() if pronunciation else None,
                    example_sentence.strip() if example_sentence else None,
                    example_translation.strip() if example_translation else None,
                    item_id,
                ),
            )
            if cursor.rowcount == 0:
                raise ValueError(f"Lesson item ID {item_id} does not exist.")
        except IntegrityError as err:
            raise ValueError(f"Could not update lesson item (duplicate item number): {err}")
        finally:
            cursor.close()


def delete_lesson_item(item_id: int, user_id: int | None = None) -> None:
    if user_id is not None:
        _require_teacher(user_id)
    with db_session() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM lesson_items WHERE item_id = %s", (item_id,))
            if cursor.rowcount == 0:
                raise ValueError(f"Lesson item ID {item_id} does not exist.")
        finally:
            cursor.close()


# ==================== QUESTIONS CRUD & ARCHIVE ====================

def create_question(
    lesson_id: int,
    question_text: str,
    choice_a: str,
    choice_b: str,
    choice_c: str,
    choice_d: str,
    correct_option: str,
    explanation: str | None = None,
    created_by: int | None = None,
) -> int:
    if created_by is not None:
        _require_teacher(created_by)
    clean_opt = (correct_option or "").strip().upper()
    if clean_opt not in VALID_OPTIONS:
        raise ValueError("Correct option must be A, B, C, or D.")
    if not all((val or "").strip() for val in (question_text, choice_a, choice_b, choice_c, choice_d)):
        raise ValueError("Question text and all four choices (A-D) are required.")

    with db_session() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO questions
                (lesson_id, question_text, choice_a, choice_b, choice_c, choice_d, correct_option, explanation, created_by, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 1)
                """,
                (
                    lesson_id,
                    question_text.strip(),
                    choice_a.strip(),
                    choice_b.strip(),
                    choice_c.strip(),
                    choice_d.strip(),
                    clean_opt,
                    explanation.strip() if explanation else None,
                    created_by,
                ),
            )
            return cursor.lastrowid
        except IntegrityError as err:
            raise ValueError(f"Could not create question (invalid lesson ID): {err}")
        finally:
            cursor.close()


def list_questions(lesson_id: int, active_only: bool = True) -> list[dict]:
    with db_session() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            if active_only:
                cursor.execute(
                    "SELECT * FROM questions WHERE lesson_id = %s AND is_active = 1 ORDER BY question_id ASC",
                    (lesson_id,),
                )
            else:
                cursor.execute(
                    "SELECT * FROM questions WHERE lesson_id = %s ORDER BY question_id ASC",
                    (lesson_id,),
                )
            return cursor.fetchall()
        finally:
            cursor.close()


def update_question(
    question_id: int,
    question_text: str,
    choice_a: str,
    choice_b: str,
    choice_c: str,
    choice_d: str,
    correct_option: str,
    explanation: str | None = None,
    user_id: int | None = None,
) -> None:
    if user_id is not None:
        _require_teacher(user_id)
    clean_opt = (correct_option or "").strip().upper()
    if clean_opt not in VALID_OPTIONS:
        raise ValueError("Correct option must be A, B, C, or D.")
    if not all((val or "").strip() for val in (question_text, choice_a, choice_b, choice_c, choice_d)):
        raise ValueError("Question text and all four choices (A-D) are required.")

    with db_session() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                UPDATE questions
                SET question_text = %s, choice_a = %s, choice_b = %s, choice_c = %s,
                    choice_d = %s, correct_option = %s, explanation = %s
                WHERE question_id = %s
                """,
                (
                    question_text.strip(),
                    choice_a.strip(),
                    choice_b.strip(),
                    choice_c.strip(),
                    choice_d.strip(),
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
    """Safely deactivate a question while preserving historic quiz attempt answers."""
    if user_id is not None:
        _require_teacher(user_id)
    with db_session() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE questions SET is_active = 0 WHERE question_id = %s", (question_id,))
            if cursor.rowcount == 0:
                raise ValueError(f"Question ID {question_id} does not exist.")
        finally:
            cursor.close()


def delete_question(question_id: int, user_id: int | None = None) -> None:
    """Physically delete a question only if never answered; otherwise block and recommend archiving."""
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

            cursor.execute("DELETE FROM questions WHERE question_id = %s", (question_id,))
            if cursor.rowcount == 0:
                raise ValueError(f"Question ID {question_id} does not exist.")
        except IntegrityError:
            raise ValueError(
                "Delete blocked: Question is referenced by historic attempt answers. Archive it instead."
            )
        finally:
            cursor.close()
