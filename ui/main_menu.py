"""Main terminal menu and role-based routing for East Africa Connect.

This module connects the UI files shared by the team:
- ui.auth_menu: run_auth(), account_menu(user)
- ui.learning_menu: browse_and_learn(user), show_progress(user)
- ui.admin_menu: run_admin_menu(user)
- ui.terminal: shared terminal/menu helpers
"""

from ui import admin_menu, auth_menu, learning_menu
from ui import terminal as t


def _with_learning_id_alias(user: dict) -> dict:
    """Provide both ID keys until learning_menu is standardized on user_id.

    auth_menu.login_screen() returns {user_id, username, role}, while the
    supplied learning_menu currently reads user["id"]. This adapter lets the
    files work together without requiring changes to either shared module.
    """
    if not isinstance(user, dict):
        raise TypeError("The login menu must return a user dictionary.")

    user_id = user.get("user_id")
    if user_id is None:
        user_id = user.get("id")
    if user_id is None:
        raise ValueError("The logged-in user has no user_id or id.")

    normalized = dict(user)
    normalized["user_id"] = user_id
    normalized["id"] = user_id
    return normalized


def _run_screen(label: str, screen, *args) -> None:
    """Run one feature screen without letting an error end the CLI loop."""
    try:
        screen(*args)
    except Exception as err:
        print(f"\n  Could not open {label}: {err}")
    t.pause()


def _student_session(user: dict) -> None:
    """Show student actions until the student logs out or returns."""
    user = _with_learning_id_alias(user)
    options = ["Learn a lesson", "View my learning progress", "Manage my account"]

    while True:
        t.clear_screen()
        t.show_menu("STUDENT MENU", options)
        choice = t.choose("Select an option: ", ["0", "1", "2", "3"])

        if choice == "0":
            print("\n  Returning to the welcome menu.")
            return
        if choice == "1":
            _run_screen("the learning menu", learning_menu.browse_and_learn, user)
        elif choice == "2":
            _run_screen("your progress", learning_menu.show_progress, user)
        elif choice == "3":
            try:
                updated_user = auth_menu.account_menu(user)
            except Exception as err:
                print(f"\n  Could not open account settings: {err}")
                t.pause()
                continue

            if updated_user is None:
                print("\n  You are logged out.")
                t.pause()
                return

            try:
                user = _with_learning_id_alias(updated_user)
            except (TypeError, ValueError) as err:
                print(f"\n  Account data error: {err}")
                t.pause()
                return


def _teacher_session(user: dict) -> None:
    """Route an authenticated teacher to content/score tools and account options."""
    if not isinstance(user, dict) or user.get("role") != "teacher":
        print("\n  Access denied: a teacher account is required.")
        t.pause()
        return

    options = ["Manage content and review student scores", "Manage my account"]
    while True:
        t.clear_screen()
        t.show_menu("TEACHER MENU", options)
        choice = t.choose("Select an option: ", ["0", "1", "2"])

        if choice == "0":
            print("\n  You are logged out.")
            return
        if choice == "1":
            # run_admin_menu checks the teacher role and includes content CRUD
            # and the all-student quiz-score view.
            try:
                admin_menu.run_admin_menu(user)
            except Exception as err:
                print(f"\n  Could not open teacher tools: {err}")
                t.pause()
            # The admin menu's 0 option is labelled Logout / Return to Main Menu.
            return

        try:
            updated_user = auth_menu.account_menu(user)
        except Exception as err:
            print(f"\n  Could not open account settings: {err}")
            t.pause()
            continue

        if updated_user is None:
            print("\n  You are logged out.")
            t.pause()
            return
        user = updated_user


def run_app() -> None:
    """Authenticate, then route to a menu using the stored account role."""
    while True:
        t.welcome()
        t.show_menu("MAIN MENU", ["Register / log in"])
        choice = t.choose("Select an option: ", ["0", "1"])

        if choice == "0":
            print(f"\nGoodbye from {t.APP_NAME}!")
            return

        try:
            user = auth_menu.run_auth()
        except Exception as err:
            print(f"\n  Sign-in could not be completed: {err}")
            t.pause()
            continue

        # run_auth() returns None when the user chooses Exit in the account menu.
        if user is None:
            continue

        role = user.get("role") if isinstance(user, dict) else None
        if role == "student":
            _student_session(user)
        elif role == "teacher":
            _teacher_session(user)
        else:
            print("\n  This account has no recognized role; access was not granted.")
            t.pause()


if __name__ == "__main__":
    run_app()
