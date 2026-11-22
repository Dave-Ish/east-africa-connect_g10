"""Display quiz attempts for the logged-in student."""

from db.connections import db_session


def show_history(user_id=None):
    """Print the current student's quiz attempts, newest first."""
    if user_id is None:
        print("Quiz history needs the logged-in student's account.")
        return

    if not isinstance(user_id, int) or user_id <= 0:
        print("Cannot show history: invalid student account.")
        return

    with db_session() as connection:
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(
                """
                SELECT
                    a.attempt_id,
                    l.title AS lesson_title,
                    a.score,
                    a.total_questions,
                    a.status,
                    a.started_at,
                    a.completed_at
                FROM attempts AS a
                JOIN lessons AS l ON l.lesson_id = a.lesson_id
                WHERE a.user_id = %s
                ORDER BY COALESCE(a.completed_at, a.started_at) DESC,
                         a.attempt_id DESC
                """,
                (user_id,),
            )
            attempts = cursor.fetchall()
        finally:
            cursor.close()

    if not attempts:
        print("You have no quiz attempts yet.")
        return

    print("\nYour quiz history")    
    print("-" * 55)
    for attempt in attempts:
        date = attempt["completed_at"] or attempt["started_at"]
        print(
            f"{attempt['lesson_title']} | "
            f"Score: {attempt['score']}/{attempt['total_questions']} | "
            f"{attempt['status']} | {date}"
        )