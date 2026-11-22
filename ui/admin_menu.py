from models.language_service import list_active_languages
from models.content_service import (
    list_lessons,
    create_lesson,
    update_lesson,
    archive_lesson,
    delete_lesson,
    list_lesson_items,
    add_lesson_item,
    update_lesson_item,
    delete_lesson_item,
    create_question,
    list_questions,
    update_question,
    archive_question,
    delete_question,
)
from models.quiz_service import get_all_attempts


def _prompt_int(message: str) -> int | None:
    raw = input(message).strip()
    try:
        return int(raw)
    except ValueError:
        print("Invalid input: please enter a whole number.")
        return None


def _select_language(prompt_label: str = "Select Language ID: ") -> int | None:
    languages = list_active_languages()
    if not languages:
        print("No active languages available.")
        return None
    print("\n--- Active Languages ---")
    for lang in languages:
        lang_id = lang.get("language_id") or lang.get("id")
        lang_name = lang.get("language_name") or lang.get("name")
        lang_code = lang.get("language_code") or lang.get("code")
        print(f"{lang_id}. {lang_name} ({lang_code})")
    return _prompt_int(prompt_label)


def run_admin_menu(current_user: dict) -> None:
    """Teacher content management and student results CLI menu."""
    if not current_user or current_user.get("role") != "teacher":
        print("Access denied: Teacher account required.")
        return

    teacher_id = current_user.get("user_id") or current_user.get("id")
    if isinstance(teacher_id, bool) or not isinstance(teacher_id, int) or teacher_id <= 0:
        print("Access denied: the logged-in teacher has no valid user ID.")
        return

    while True:
        print("\n==============================================")
        print("   EAST AFRICA CONNECT — TEACHER ADMIN MENU")
        print("==============================================")
        print("1. Manage Lessons (List / Create / Update / Archive / Delete)")
        print("2. Manage Lesson Items (List / Add / Update / Delete)")
        print("3. Manage Quiz Questions (List / Create / Update / Archive / Delete)")
        print("4. View All Student Quiz Scores")
        print("0. Logout / Return to Main Menu")

        choice = input("Choose an option (0-4): ").strip()

        try:
            if choice == "1":
                _manage_lessons(teacher_id)
            elif choice == "2":
                _manage_items(teacher_id)
            elif choice == "3":
                _manage_questions(teacher_id)
            elif choice == "4":
                attempts = get_all_attempts()
                if not attempts:
                    print("No student quiz attempts recorded yet.")
                else:
                    print("\n--- All Student Quiz Results ---")
                    for att in attempts:
                        att_id = att.get("attempt_id") or att.get("id")
                        print(
                            f"Attempt #{att_id} | Student: {att.get('username', att.get('user_id'))} "
                            f"| Lesson: {att.get('lesson_title', att.get('lesson_id'))} "
                            f"| Score: {att['score']}/{att['total_questions']} "
                            f"| Status: {att.get('status', 'unknown')}"
                        )
            elif choice == "0":
                break
            else:
                print("Invalid option. Enter 0, 1, 2, 3, or 4.")
        except (ValueError, PermissionError) as err:
            print(f"Notice: {err}")
        except Exception as err:
            print(f"System/Database error: {err}")


def _manage_lessons(teacher_id: int) -> None:
    print("\n--- Lessons Menu ---")
    print("1. List Lessons by Language")
    print("2. Create Lesson")
    print("3. Update Lesson")
    print("4. Archive Lesson (Safe Deactivate)")
    print("5. Delete Lesson (Unreferenced Only)")
    sub = input("Select action (1-5): ").strip()

    if sub == "1":
        lang_id = _select_language()
        if lang_id is None:
            return
        lessons = list_lessons(lang_id, active_only=False)
        if not lessons:
            print("No lessons found for that language.")
        for lsn in lessons:
            state = "ACTIVE" if lsn.get("is_active", 1) else "ARCHIVED"
            print(f"[{lsn['lesson_id']}] {lsn['title']} | Level: {lsn['level']} | Lesson #{lsn['lesson_number']} | {state}")

    elif sub == "2":
        lang_id = _select_language("Select Target Language ID: ")
        if lang_id is None:
            return
        support_lang_id = _select_language("Select Support (Translation) Language ID: ")
        if support_lang_id is None:
            return
        title = input("Lesson Title: ")
        description = input("Description (optional): ")
        level = input("Level (beginner/intermediate/advanced, default: beginner): ").strip() or "beginner"
        lesson_num = _prompt_int("Lesson Number (e.g., 1): ")
        if lesson_num is not None:
            new_id = create_lesson(lang_id, support_lang_id, title, level, lesson_num, teacher_id, description)
            print(f"Lesson created with ID {new_id}.")

    elif sub == "3":
        lesson_id = _prompt_int("Lesson ID to update: ")
        if lesson_id is None:
            return
        title = input("Updated Title: ")
        description = input("Updated Description (optional): ")
        level = input("Updated Level (beginner/intermediate/advanced): ").strip() or "beginner"
        lesson_num = _prompt_int("Updated Lesson Number: ")
        if lesson_num is not None:
            update_lesson(lesson_id, title, level, lesson_num, teacher_id, description)
            print("Lesson updated successfully.")

    elif sub == "4":
        lesson_id = _prompt_int("Lesson ID to archive: ")
        if lesson_id is not None:
            archive_lesson(lesson_id, teacher_id)
            print("Lesson archived (history preserved).")

    elif sub == "5":
        lesson_id = _prompt_int("Lesson ID to delete: ")
        if lesson_id is not None:
            delete_lesson(lesson_id, teacher_id)
            print("Lesson permanently deleted.")
    else:
        print("Invalid selection.")


def _manage_items(teacher_id: int) -> None:
    print("\n--- Lesson Items Menu ---")
    print("1. List Lesson Items")
    print("2. Add Lesson Item")
    print("3. Update Lesson Item")
    print("4. Delete Lesson Item")
    sub = input("Select action (1-4): ").strip()

    if sub == "1":
        lesson_id = _prompt_int("Lesson ID: ")
        if lesson_id is None:
            return
        items = list_lesson_items(lesson_id)
        if not items:
            print("No items found for this lesson.")
        for item in items:
            print(f"[{item['item_id']}] #{item['item_number']} {item['term_text']} = {item['translation_text']}")

    elif sub == "2":
        lesson_id = _prompt_int("Lesson ID: ")
        if lesson_id is None:
            return
        term_text = input("Word/Phrase: ")
        translation_text = input("Translation: ")
        pronunciation = input("Pronunciation (optional): ")
        example_sentence = input("Example Sentence (optional): ")
        example_translation = input("Example Translation (optional): ")
        item_num = _prompt_int("Item Number (e.g., 1): ")
        if item_num is not None:
            item_id = add_lesson_item(
                lesson_id,
                term_text,
                translation_text,
                pronunciation,
                example_sentence,
                example_translation,
                item_num,
                teacher_id,
            )
            print(f"Lesson item added with ID {item_id}.")

    elif sub == "3":
        item_id = _prompt_int("Lesson Item ID to update: ")
        if item_id is None:
            return
        term_text = input("Updated Word/Phrase: ")
        translation_text = input("Updated Translation: ")
        pronunciation = input("Updated Pronunciation (optional): ")
        example_sentence = input("Updated Example Sentence (optional): ")
        example_translation = input("Updated Example Translation (optional): ")
        item_num = _prompt_int("Updated Item Number: ")
        if item_num is not None:
            update_lesson_item(
                item_id,
                term_text,
                translation_text,
                pronunciation,
                example_sentence,
                example_translation,
                item_num,
                teacher_id,
            )
            print("Lesson item updated.")

    elif sub == "4":
        item_id = _prompt_int("Lesson Item ID to delete: ")
        if item_id is not None:
            delete_lesson_item(item_id, teacher_id)
            print("Lesson item deleted.")
    else:
        print("Invalid selection.")


def _manage_questions(teacher_id: int) -> None:
    print("\n--- Quiz Questions Menu ---")
    print("1. List Questions by Lesson")
    print("2. Create Question")
    print("3. Update Question")
    print("4. Archive Question (Safe Deactivate)")
    print("5. Delete Question (Unreferenced Only)")
    sub = input("Select action (1-5): ").strip()

    if sub == "1":
        lesson_id = _prompt_int("Lesson ID: ")
        if lesson_id is None:
            return
        questions = list_questions(lesson_id, active_only=False)
        if not questions:
            print("No questions found for this lesson.")
        for q in questions:
            state = "ACTIVE" if q.get("is_active", 1) else "ARCHIVED"
            print(f"[{q['question_id']}] {q['question_text']} (Correct: {q['correct_option']}) [{state}]")

    elif sub == "2":
        lesson_id = _prompt_int("Lesson ID: ")
        if lesson_id is None:
            return
        question_text = input("Question Text: ")
        choice_a = input("Choice A: ")
        choice_b = input("Choice B: ")
        choice_c = input("Choice C: ")
        choice_d = input("Choice D: ")
        correct = input("Correct Option (A/B/C/D): ")
        explanation = input("Explanation (optional): ")
        q_id = create_question(
            lesson_id, question_text, choice_a, choice_b, choice_c, choice_d, correct, explanation, teacher_id
        )
        print(f"Question created with ID {q_id}.")

    elif sub == "3":
        q_id = _prompt_int("Question ID to update: ")
        if q_id is None:
            return
        question_text = input("Updated Question Text: ")
        choice_a = input("Choice A: ")
        choice_b = input("Choice B: ")
        choice_c = input("Choice C: ")
        choice_d = input("Choice D: ")
        correct = input("Correct Option (A/B/C/D): ")
        explanation = input("Updated Explanation (optional): ")
        update_question(
            q_id, question_text, choice_a, choice_b, choice_c, choice_d, correct, explanation, teacher_id
        )
        print("Question updated.")

    elif sub == "4":
        q_id = _prompt_int("Question ID to archive: ")
        if q_id is not None:
            archive_question(q_id, teacher_id)
            print("Question archived.")

    elif sub == "5":
        q_id = _prompt_int("Question ID to delete: ")
        if q_id is not None:
            delete_question(q_id, teacher_id)
            print("Question deleted.")
    else:
        print("Invalid selection.")
