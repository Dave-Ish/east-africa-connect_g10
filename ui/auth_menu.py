"""Registration, login and account menus (Keji)."""
from getpass import getpass

from models import user_service as svc
from ui import terminal as t


def _secret(prompt):
    try:
        return getpass(prompt)
    except (EOFError, KeyboardInterrupt):
        print()
        return ""


def register_screen():
    t.banner("REGISTER (STUDENT)")
    username = t.ask("Choose a username: ")
    password = _secret("Choose a password: ")
    if password != _secret("Confirm password: "):
        print("  Passwords do not match.")
        return
    try:
        svc.register_user(username, password)
        print("  Registration successful. You can now log in.")
    except svc.UserError as err:
        print(f"  Error: {err}")


def login_screen():
    """Returns the user dict ({user_id, username, role}) or None."""
    t.banner("LOGIN")
    username = t.ask("Username: ")
    password = _secret("Password: ")
    try:
        user = svc.login_user(username, password)
    except svc.UserError as err:
        print(f"  Error: {err}")
        return None
    print(f"  Welcome, {user['username']} ({user['role']})!")
    return user


def account_menu(user):
    """Profile / username / password / delete / log out.

    Returns the (possibly updated) user dict if the person just goes Back
    (still logged in), or None if they logged out or deleted the account.
    The caller should treat None as 'nobody is logged in'."""
    options = ["View profile", "Change username", "Change password",
               "Delete my account", "Log out"]
    while True:
        t.show_menu("MY ACCOUNT", options)
        choice = t.choose("Select an option: ", ["0", "1", "2", "3", "4", "5"])
        try:
            if choice == "0":
                return user
            if choice == "1":
                p = svc.get_profile(user["user_id"])
                print(f"  Username: {p['username']}\n  Role:     {p['role']}")
            elif choice == "2":
                svc.change_username(user["user_id"], t.ask("New username: "))
                user = {**user, "username": svc.get_profile(user["user_id"])["username"]}
                print("  Username updated.")
            elif choice == "3":
                old = _secret("Current password: ")
                new = _secret("New password: ")
                svc.change_password(user["user_id"], old, new)
                print("  Password updated.")
            elif choice == "4":
                pw = _secret("Re-enter your password: ")
                conf = t.ask("Type DELETE to confirm: ")
                svc.delete_account(user["user_id"], pw, conf)
                print("  Account deleted.")
                return None
            elif choice == "5":
                print("  You have been logged out.")
                return None
        except svc.UserError as err:
            print(f"  Error: {err}")
        t.pause()


def run_auth():
    """Entry point for the rest of the app. Returns the logged-in user dict,
    or None if the person chose Exit."""
    options = ["Register as a student", "Log in"]
    while True:
        t.show_menu("ACCOUNT", options)
        choice = t.choose("Select an option: ", ["0", "1", "2"])
        if choice == "0":
            return None
        if choice == "1":
            register_screen()
        else:
            user = login_screen()
            if user:
                return user


if __name__ == "__main__":      # quick manual demo: python -m ui.auth_menu
    current = run_auth()
    if current:
        account_menu(current)
