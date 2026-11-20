
from db.connection import db_session

def open_lesson(user_id: int, lesson_id: int) -> tuple[dict, list[dict]]:
    with db_session() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM lessons WHERE id = %s AND is_active = 1", (lesson_id,))
        lesson = cur.fetchone()
        if not lesson:
            cur.close()
            raise ValueError("Lesson not found or inactive.")
        cur.execute(
            """SELECT * FROM lesson_items
               WHERE lesson_id = %s AND is_active = 1
               ORDER BY display_order ASC, id ASC""",
            (lesson_id,)
        )
        items = cur.fetchall()
        cur.execute(
            "SELECT status FROM lesson_progress WHERE user_id = %s AND lesson_id = %s",
            (user_id, lesson_id)
        )
        existing = cur.fetchone()
        if not existing:
            cur.execute(
                "INSERT INTO lesson_progress (user_id, lesson_id, status) VALUES (%s, %s, 'in_progress')",
                (user_id, lesson_id)
            )
        cur.close()
        return lesson, items

def mark_lesson_complete(user_id: int, lesson_id: int) -> None:
    with db_session() as conn:
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO lesson_progress (user_id, lesson_id, status)
               VALUES (%s, %s, 'completed')
               ON DUPLICATE KEY UPDATE status = 'completed'""",
            (user_id, lesson_id)
        )
        cur.close()

def get_learning_progress(user_id: int) -> list[dict]:
    with db_session() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """SELECT lp.lesson_id, lp.status, lp.updated_at,
                      l.title AS lesson_title, l.level,
                      lang.name AS language_name
               FROM lesson_progress lp
               JOIN lessons l ON l.id = lp.lesson_id
               JOIN languages lang ON lang.id = l.language_id
               WHERE lp.user_id = %s
               ORDER BY lp.updated_at DESC""",
            (user_id,)
        )
        rows = cur.fetchall()
        cur.close()
        return rows