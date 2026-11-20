"""Main menu and role-based routing."""
import importlib

from ui import terminal as t


def _call(module_name, func_name, *args):
    """Call a teammate's function; fail gracefully if missing or crashing."""
    try:
        module = importlib.import_module(module_name)
        func = getattr(module, func_name)
    except (ImportError, AttributeError):
        print(f"\n  '{module_name}.{func_name}' is not available yet.")
        return
    try:
        func(*args)
    except Exception as err:  # keep the app alive during the demo
        print(f"\n  Something went wrong: {err}")


def student_menu():
    options = ["Learn", "Take a quiz", "View my history"]
    actions = {
        "1": ("learn", "start_learning"),
        "2": ("quiz", "start_quiz"),
        "3": ("history", "show_history"),
    }
    while True:
        t.clear_screen()
        t.show_menu("STUDENT MENU", options)
        choice = t.choose("Select an option: ", ["0", "1", "2", "3"])
        if choice == "0":
            return  # back to main menu
        module, func = actions[choice]
        _call(module, func)
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
            student_menu()
        elif choice == "2":
            teacher_menu()
        else:
            print(f"\nGoodbye from {t.APP_NAME}!")
            return
