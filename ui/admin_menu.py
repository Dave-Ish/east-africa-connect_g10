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


def _select_language() -> int | None:
    languages = list_active_languages()
    if not languages:
        print("No active languages available.")
        return None
    print("\n--- Active Languages ---")
    for lang in languages:
        print(f"{lang['id']}. {lang['name']} ({lang['code']})")
    return _prompt_int("Select Language ID: ")


def run_admin_menu(current_user: dict) -> None:
    """Teacher content management and student results CLI menu."""
    if not current_user or current_user.get("role") != "teacher":
        print("Access denied: Teacher account required.")
        return

    teacher_id = current_user.get("user_id") or current_user.get("id")

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
                        print(
                            f"Attempt #{att['id']} | Student: {att.get('username', att.get('user_id'))} "
                            f"| Lesson: {att.get('lesson_title', att.get('lesson_id'))} "
                            f"| Score: {att['score']}/{att['total_questions']}"
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
            print(f"[{lsn['id']}] {lsn['title']} | Level: {lsn['level']} | Order: {lsn['display_order']} | {state}")

    elif sub == "2":
        lang_id = _select_language()
        if lang_id is None:
            return
        title = input("Lesson Title: ")
        level = input("Level (default: Beginner): ") or "Beginner"
        support = input("Support Language (default: English): ") or "English"
        order = _prompt_int("Display Order (e.g., 1): ")
        if order is not None:
            new_id = create_lesson(lang_id, support, title, level, order, teacher_id)
            print(f"Lesson created with ID {new_id}.")

    elif sub == "3":
        lesson_id = _prompt_int("Lesson ID to update: ")
        if lesson_id is None:
            return
        title = input("Updated Title: ")
        level = input("Updated Level: ") or "Beginner"
        order = _prompt_int("Updated Display Order: ")
        if order is not None:
            update_lesson(lesson_id, title, level, order, teacher_id)
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
        items = list_lesson_items(lesson_id, active_only=False)
        if not items:
            print("No items found for this lesson.")
        for item in items:
            print(f"[{item['id']}] {item['term']} = {item['translation']} (Order: {item['display_order']})")

    elif sub == "2":
        lesson_id = _prompt_int("Lesson ID: ")
        if lesson_id is None:
            return
        term = input("Word/Phrase: ")
        translation = input("Translation: ")
        pronunciation = input("Pronunciation (optional): ")
        example = input("Example Sentence (optional): ")
        order = _prompt_int("Display Order (e.g., 1): ")
        if order is not None:
            item_id = add_lesson_item(lesson_id, term, translation, pronunciation, example, order, teacher_id)
            print(f"Lesson item added with ID {item_id}.")

    elif sub == "3":
        item_id = _prompt_int("Lesson Item ID to update: ")
        if item_id is None:
            return
        term = input("Updated Word/Phrase: ")
        translation = input("Updated Translation: ")
        pronunciation = input("Updated Pronunciation (optional): ")
        example = input("Updated Example (optional): ")
        order = _prompt_int("Updated Display Order: ")
        if order is not None:
            update_lesson_item(item_id, term, translation, pronunciation, example, order, teacher_id)
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
            print(f"[{q['id']}] {q['prompt']} (Correct: {q['correct_option']}) [{state}]")

    elif sub == "2":
        lesson_id = _prompt_int("Lesson ID: ")
        if lesson_id is None:
            return
        prompt = input("Question Prompt: ")
        opt_a = input("Option A: ")
        opt_b = input("Option B: ")
        opt_c = input("Option C: ")
        opt_d = input("Option D: ")
        correct = input("Correct Option (A/B/C/D): ")
        explanation = input("Explanation (optional): ")
        q_id = create_question(lesson_id, prompt, opt_a, opt_b, opt_c, opt_d, correct, explanation, teacher_id)
        print(f"Question created with ID {q_id}.")

    elif sub == "3":
        q_id = _prompt_int("Question ID to update: ")
        if q_id is None:
            return
        prompt = input("Updated Prompt: ")
        opt_a = input("Option A: ")
        opt_b = input("Option B: ")
        opt_c = input("Option C: ")
        opt_d = input("Option D: ")
        correct = input("Correct Option (A/B/C/D): ")
        explanation = input("Updated Explanation (optional): ")
        update_question(q_id, prompt, opt_a, opt_b, opt_c, opt_d, correct, explanation, teacher_id)
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
