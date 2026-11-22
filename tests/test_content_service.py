import unittest
from db.connection import init_db, db_session
from models.user_service import register_user
from models.language_service import list_active_languages
from models.content_service import (
    create_lesson,
    list_lessons,
    update_lesson,
    archive_lesson,
    delete_lesson,
    add_lesson_item,
    list_lesson_items,
    update_lesson_item,
    delete_lesson_item,
    create_question,
    list_questions,
    update_question,
    archive_question,
    delete_question,
)


class TestContentService(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        langs = list_active_languages()
        cls.language_id = langs[0].get("language_id") or langs[0].get("id")
        cls.support_language_id = (
            langs[1].get("language_id") or langs[1].get("id") if len(langs) > 1 else cls.language_id
        )

        cls.student_id = register_user("akuol_test_student", "Pass123!")
        cls.teacher_id = register_user("akuol_test_teacher", "Pass123!")
        with db_session() as conn:
            cur = conn.cursor()
            try:
                cur.execute("UPDATE users SET role = 'teacher' WHERE user_id = %s", (cls.teacher_id,))
            finally:
                cur.close()

    def test_non_teacher_blocked(self):
        with self.assertRaises(PermissionError):
            create_lesson(
                self.language_id,
                self.support_language_id,
                "Blocked Lesson",
                "beginner",
                99,
                self.student_id,
            )

    def test_invalid_correct_option_rejected(self):
        lesson_id = create_lesson(
            self.language_id,
            self.support_language_id,
            "Validation Lesson",
            "beginner",
            98,
            self.teacher_id,
        )
        with self.assertRaises(ValueError):
            create_question(
                lesson_id, "Sample?", "Opt1", "Opt2", "Opt3", "Opt4", "Z", "Explanation", self.teacher_id
            )
        delete_lesson(lesson_id, self.teacher_id)

    def test_full_crud_and_archiving(self):
        lesson_id = create_lesson(
            self.language_id,
            self.support_language_id,
            "Greetings Test",
            "beginner",
            97,
            self.teacher_id,
            "Introductory greetings",
        )
        update_lesson(
            lesson_id,
            "Essential Greetings Test",
            "beginner",
            97,
            self.teacher_id,
            "Updated description",
        )

        item_id = add_lesson_item(
            lesson_id,
            "Muraho",
            "Hello",
            "moo-rah-ho",
            "Muraho neza?",
            "Hello, how are you?",
            1,
            self.teacher_id,
        )
        update_lesson_item(
            item_id,
            "Muraho",
            "Hello (formal)",
            "moo-rah-ho",
            "Muraho, amakuru?",
            "Hello, what is the news?",
            1,
            self.teacher_id,
        )
        self.assertEqual(len(list_lesson_items(lesson_id)), 1)
        delete_lesson_item(item_id, self.teacher_id)
        self.assertEqual(len(list_lesson_items(lesson_id)), 0)

        q_id = create_question(
            lesson_id,
            "What is Muraho?",
            "Hello",
            "Bye",
            "Water",
            "Thanks",
            "a",
            "Standard greeting",
            self.teacher_id,
        )
        update_question(
            q_id,
            "Translate Muraho:",
            "Hello",
            "Goodbye",
            "Please",
            "Sorry",
            "A",
            "Means Hello",
            self.teacher_id,
        )
        archive_question(q_id, self.teacher_id)
        self.assertFalse(any(q["question_id"] == q_id for q in list_questions(lesson_id, active_only=True)))
        self.assertTrue(any(q["question_id"] == q_id for q in list_questions(lesson_id, active_only=False)))

        archive_lesson(lesson_id, self.teacher_id)
        self.assertFalse(any(l["lesson_id"] == lesson_id for l in list_lessons(self.language_id, active_only=True)))


if __name__ == "__main__":
    unittest.main()
