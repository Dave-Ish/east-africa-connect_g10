"""Shared terminal helpers: banners, safe input, clear screen."""
import os

APP_NAME = "LinguaLearn"
WIDTH = 50


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def line(char="="):
    print(char * WIDTH)


def banner(title):
    line()
    print(title.center(WIDTH))
    line()


def welcome():
    clear_screen()
    banner(f"Welcome to {APP_NAME}")
    print("Learn languages, take quizzes, track your progress.".center(WIDTH))
    print()


def pause():
    input("\nPress Enter to return to the menu...")


def ask(prompt):
    """Read a line of input; treat Ctrl+D / Ctrl+C as 'back out' safely."""
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return ""


def choose(prompt, valid):
    """Keep asking until the user types one of `valid` (list of strings)."""
    while True:
        value = ask(prompt)
        if value in valid:
            return value
        print(f"  Invalid choice '{value}'. Please enter one of: {', '.join(valid)}")


def show_menu(title, options):
    """options: list of labels. Numbered from 1; '0' is always Back/Exit."""
    banner(title)
    for i, label in enumerate(options, start=1):
        print(f"  [{i}] {label}")
    print("  [0] Back / Exit")
    line("-")
