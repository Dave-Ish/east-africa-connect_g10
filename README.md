# East Africa Connect

A Python terminal application for learning Kinyarwanda, Swahili, French, and English. Students study a lesson before taking its quiz; teachers create and manage the learning content and review quiz results. MySQL is the only application data store.

## Application flow

- **Student:** register or log in → choose a language → open an active lesson → study words, translations → save progress → take that lesson's quiz → receive feedback and a saved score → review progress and quiz history.

- **Teacher:** log in → create a lesson for a target and support language → add lesson items and quiz questions → review student quiz scores; update or archive content when needed.

Public registration creates **student** accounts only. Teacher accounts are provisioned by an authorized setup person. Active lessons are shared and browseable by all students; this version does not implement private course enrollment or teacher-to-student assignment.

## Requirements

- Python 3.10 or later

- WSL/Linux/macOS terminal (the commands below are for WSL)

- Aiven MySQL database and its CA certificate

## Install and configure

Open the project folder in WSL and activate its virtual environment:

```bash
cd "/mnt/c/Users/<WindowsUser>/east-africa-connect_g10"
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Copy the Aiven CA certificate into the project root as `aiven-ca.pem`. The `.gitignore` excludes PEM/CRT files; never commit the certificate or database password.

Set Aiven's host, port, service username, database, and password in the same terminal. Use the values from Aiven's connection information; the password prompt does not echo what you type.

```bash
export MYSQL_HOST='<Aiven host>'
export MYSQL_PORT='<Aiven port>'
export MYSQL_USER='<Aiven service username>'
read -rsp 'Aiven MySQL password: ' MYSQL_PASSWORD; echo
export MYSQL_PASSWORD
export MYSQL_DATABASE='east_africa_connect'
export MYSQL_SSL_CA="$PWD/aiven-ca.pem"
```

These variables last for the current terminal session. Re-enter them when opening a new terminal. Do not use the Aiven service username/password at the East Africa Connect login prompt.

## Prepare the database

Create/select the database in Aiven Console first. Then, from the project root, apply the schema:

```bash
python -c "from db.connection import init_db; print('Database ready:', init_db())"
```

`init_db()` creates tables in the selected database; it does not create the database or migrate existing tables. Seed the supported languages:

```bash
python -m scripts.seed_data
```

The seed operation is safe to rerun and only inserts missing language rows or reactivates exact matching rows. It stops rather than silently changing conflicting language names/codes.

Check the connection before launching the app:

```bash
python -c "from db.connection import get_connection; c=get_connection(); q=c.cursor(); q.execute('SELECT DATABASE()'); print('Connected to:', q.fetchone()[0]); q.close(); c.close()"
```

## Create the first teacher account

Run this once from the active virtual environment as the person authorized to provision teachers. Choose a unique app username and an app password of at least eight characters; this is not the Aiven password.

```bash
python -c 'from getpass import getpass; from models.user_service import create_teacher_account; name=input("Teacher username: ").strip(); password=getpass("Teacher app password (8+ characters): "); print("Teacher user ID:", create_teacher_account(name, password))'
```

## Run and use the app

```bash
python main.py
```

**To prepare lessons:** log in as the teacher. In the teacher admin menu, create a lesson, choosing the target language and support (translation) language. Add lesson items and at least one active quiz question. Keep the lesson active so students can find it.

**To learn:** choose student registration if needed, then log in. Select **Learn a lesson**, choose an active language and lesson, study the displayed material, and choose whether to mark the lesson complete. You can then take the quiz for that same lesson. Use **Progress/quiz history** to review saved records.

**To review scores:** log in as a teacher and choose **View All Student Quiz Scores**. Quiz rows may show `in_progress` as well as `completed`; only completed attempts are final scores.

## Verify the shared data

These read-only queries can be run in a MySQL client connected to the same Aiven database:

```sql
SELECT language_id, language_name, language_code, is_active FROM languages;
SELECT lesson_id, language_id, title, is_active FROM lessons;
SELECT user_id, username, role FROM users;
SELECT attempt_id, user_id, lesson_id, score, total_questions, status FROM attempts;
```

Each team member's app connects to the same shared database. Do not drop, truncate, or reset shared tables for testing. Use uniquely named test content and archive lessons/questions that are referenced by learner progress or attempts.

## Common problems

- **`No module named mysql`**: activate `.venv`, then run `python -m pip install -r requirements.txt`.

- **`Set MYSQL_USER`**: set the Aiven environment variables in this terminal before starting the app.

- **No languages appear**: run `python -m scripts.seed_data`, then check that language rows have `is_active = 1`.

- **No lessons appear**: a teacher must create an active lesson for the selected language and add lesson items.

- **`KeyError: 'id'`**** while listing lessons**: lesson rows use `lesson_id`; the learning menu should display `lesson['lesson_id']` (or handle both keys).

- **Student menu appears for a teacher**: check that the signed-in account has `role = 'teacher'` in `users` and that `main_menu.py` routes using that role.

- **Aiven connection fails**: check host, port, service username, database name, CA path, and Aiven's IP allowlist. Never paste credentials into chat or commit them.

