# LinguaLearn (terminal app)

A terminal language-learning app. Students learn, take quizzes and view
history; teachers manage content. Everything runs in the terminal.

## Setup (fresh machine)
```bash
git clone https://github.com/Dave-Ish/east-africa-connect_g10.git
cd east-africa-connect_g10
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
python3 scripts/seed_data.py     # loads sample data from db/seed.sql
python3 main.py
```

## Using the app
1. Choose **1** (Student) or **2** (Teacher) from the main menu.
2. Student: Learn, Quiz, History. Teacher: Manage content.
3. Press **Enter** after an action to return to your menu; **0** goes back.
4. Invalid input never crashes the app; you are simply asked again.

## Tests
```bash
pip install pytest
python3 -m pytest tests/
```

## Project structure
| Path | Purpose |
|------|---------|
| `main.py` | Entry point |
| `ui/terminal.py` | Shared text and input helpers |
| `ui/main_menu.py` | Main menu and role-based routing |
| `scripts/seed_data.py` | Sample-data loader |
| `tests/test_app_flow.py` | End-to-end menu-flow tests |
| `docs/terminal_sketch.md` | Section 2.1 screen sketch |
