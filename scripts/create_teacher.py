"""Create a teacher account securely.

    export TEACHER_ADMIN_CODE="something-secret"
    python scripts/create_teacher.py
"""
import hmac
import os
import sys
from getpass import getpass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import user_service as svc  # noqa: E402


def main():
    expected = os.environ.get("TEACHER_ADMIN_CODE")
    if not expected:
        sys.exit("Set the TEACHER_ADMIN_CODE environment variable first.")
    if not hmac.compare_digest(getpass("Admin code: "), expected):
        sys.exit("Not authorized.")
    username = input("Teacher username: ")
    password = getpass("Teacher password: ")
    if password != getpass("Confirm password: "):
        sys.exit("Passwords do not match.")
    try:
        svc.create_teacher_account(username, password)
    except svc.UserError as err:
        sys.exit(f"Error: {err}")
    print("Teacher account created.")


if __name__ == "__main__":
    main()
