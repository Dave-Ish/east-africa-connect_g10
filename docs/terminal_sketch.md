# Section 2.1 - Terminal screen sketch

Start the app with `python3 main.py`.

## Welcome + main menu
```
==================================================
                Welcome to LinguaLearn
==================================================
    Learn languages, take quizzes, track your progress.

==================================================
                     MAIN MENU
==================================================
  [1] I am a Student
  [2] I am a Teacher
  [0] Back / Exit
--------------------------------------------------
Select an option: _
```

## What happens on each choice
| Input | Result |
|-------|--------|
| 1 | Opens the Student Menu |
| 2 | Opens the Teacher Menu |
| 0 | Prints "Goodbye" and exits |
| anything else | "Invalid choice" message, asks again (no crash) |

## Student menu
```
==================================================
                   STUDENT MENU
==================================================
  [1] Learn
  [2] Take a quiz
  [3] View my history
  [0] Back / Exit
--------------------------------------------------
```

## Teacher menu
```
==================================================
                   TEACHER MENU
==================================================
  [1] Manage content (add / edit / delete)
  [0] Back / Exit
--------------------------------------------------
```

## Returning to the main menu
- After any action finishes, the user presses **Enter** to go back to their role menu.
- Typing **0** in the Student or Teacher menu returns to the main menu.
- Typing **0** in the main menu exits the app.
