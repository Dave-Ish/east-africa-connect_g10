"""Main menu and role-based routing."""
import importlib

from ui import terminal as t


def _call(module_name, func_name, *args):
    """Call a teammate's function and return its result.

    Returns None if the function is missing or raises, so the app never crashes.
    """
    try:
        module = importlib.import_module(module_name)
        func = getattr(module, func_name)
    except (ImportError, AttributeError):
        print(f"\n  '{module_name}.{func_name}' is not available yet.")
        return None
    try:
        return func(*args)
    except Exception as err:  # keep the app alive during the demo
        print(f"\n  Something went wrong: {err}")
        return None


def login_student():
    """Get the logged-in student's user ID, or None to go back."""
    try:
        getattr(importlib.import_module("auth"), "login_user")
        has_auth = True
    except (ImportError, AttributeError):
        has_auth = False

    if has_auth:
        # Teammate's login: auth.login_user(username, password) -> user_id or None
        username = t.ask("Username: ")
        password = t.ask("Password: ")
        user_id = _call("auth", "login_user", username, password)
        if user_id is None:
            print("  Login failed.")
        return user_id

    # Fallback until the login module exists: type your user ID
    while True:
        raw = t.ask("Enter your user ID (0 to go back): ")
        if raw == "0":
            return None
        if raw.isdigit():
            return int(raw)
        print(f"  Invalid user ID '{raw}'. Please enter a number.")


def student_menu(user_id):
    options = ["Learn", "Take a quiz", "View my history"]
    while True:
        t.clear_screen()
        t.show_menu("STUDENT MENU", options)
        choice = t.choose("Select an option: ", ["0", "1", "2", "3"])
        if choice == "0":
            return  # back to main menu
        if choice == "1":
            _call("learn", "start_learning")
        elif choice == "2":
            _call("quiz", "start_quiz")
        elif choice == "3":
            _call("history", "show_history", user_id)  # sends the student's ID
        t.pause()


def teacher_menu():
    options = ["Manage content (add / edit / delete)"]
    while True:
        t.clear_screen()
        t.show_menu("TEACHER MENU", options)
        choice = t.choose("Select an option: ", ["0", "1"])
        if choice == "0":
            return
        _call("content", "manage_content")
        t.pause()


def run_app():
    options = ["I am a Student", "I am a Teacher"]
    while True:
        t.welcome()
        t.show_menu("MAIN MENU", options)
        choice = t.choose("Select an option: ", ["0", "1", "2"])
        if choice == "1":
            user_id = login_student()
            if user_id is not None:
                student_menu(user_id)
        elif choice == "2":
            teacher_menu()
        else:
            print(f"\nGoodbye from {t.APP_NAME}!")
            return
