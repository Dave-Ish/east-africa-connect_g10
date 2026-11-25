from models import language_service, content_service, learning_service

def _ask_int(prompt: str):
    try:
        return int(input(prompt).strip())
    except ValueError:
        print("Please enter a number.")
        return None

def browse_and_learn(user):
    print("\n--- Learn ---")
    langs = language_service.list_active_languages()
    if not langs:
        print("No active languages yet.")
        return
    for lang in langs:
        print(f"{lang['id']}. {lang['name']} ({lang['code']})")

    lang_id = _ask_int("Choose language ID: ")
    if lang_id is None:
        return

    lessons = content_service.list_lessons(lang_id, active_only=True)
    if not lessons:
        print("No active lessons for this language yet.")
        return
    for les in lessons:
        print(f"{les['lesson_id']}. {les['title']} - Level: {les['level']}")

    lesson_id = _ask_int("Choose lesson ID: ")
    if lesson_id is None:
        return

    try:
        lesson, items = learning_service.open_lesson(user["id"], lesson_id)
    except ValueError as e:
        print(str(e))
        return
    except Exception:
        print("Could not open lesson. Please try again.")
        return

    print(f"\n=== {lesson['title']} ===")
    if not items:
        print("This lesson has no items yet. It is saved as in progress.")
        return

    for i, item in enumerate(items, start=1):
        print(f"\n{i}. {item['term']} -> {item['translation']}")
        if item.get("pronunciation"):
            print(f"   Pronunciation: {item['pronunciation']}")
        if item.get("example"):
            print(f"   Example: {item['example']}")

    choice = input("\nMark this lesson as complete? (y/n): ").strip().lower()
    if choice == "y":
        learning_service.mark_lesson_complete(user["id"], lesson_id)
        print("Lesson marked as completed!")
    else:
        print("Saved as in progress. You can revisit anytime.")

def show_progress(user):
    print("\n--- My Progress ---")
    rows = learning_service.get_learning_progress(user["id"])
    if not rows:
        print("No progress yet. Open a lesson to start.")
        return
    for r in rows:
        print(f"{r['language_name']} - {r['lesson_title']} [{r['level']}] : {r['status']}")