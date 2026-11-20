
CREATE TABLE IF NOT EXISTS users (
    user_id       INT UNSIGNED NOT NULL AUTO_INCREMENT,
    username      VARCHAR(30) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role          ENUM('student', 'teacher') NOT NULL DEFAULT 'student',
    created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id),
    UNIQUE KEY uq_users_username (username),
    CONSTRAINT chk_users_username_length
        CHECK (CHAR_LENGTH(TRIM(username)) BETWEEN 3 AND 30)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS languages (
    language_id   INT UNSIGNED NOT NULL AUTO_INCREMENT,
    language_code VARCHAR(10) NOT NULL,
    language_name VARCHAR(80) NOT NULL,
    is_active     TINYINT(1) NOT NULL DEFAULT 1,
    PRIMARY KEY (language_id),
    UNIQUE KEY uq_languages_code (language_code),
    UNIQUE KEY uq_languages_name (language_name),
    CONSTRAINT chk_languages_active CHECK (is_active IN (0, 1)),
    CONSTRAINT chk_languages_code_length
        CHECK (CHAR_LENGTH(TRIM(language_code)) BETWEEN 2 AND 10),
    CONSTRAINT chk_languages_name_length
        CHECK (CHAR_LENGTH(TRIM(language_name)) > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS lessons (
    lesson_id          INT UNSIGNED NOT NULL AUTO_INCREMENT,
    language_id        INT UNSIGNED NOT NULL COMMENT 'Language being learned',
    support_language_id INT UNSIGNED NOT NULL COMMENT 'Language used for translations',
    title              VARCHAR(120) NOT NULL,
    description        TEXT NULL,
    level              ENUM('beginner', 'intermediate', 'advanced') NOT NULL DEFAULT 'beginner',
    lesson_number      SMALLINT UNSIGNED NOT NULL DEFAULT 1,
    created_by         INT UNSIGNED NULL,
    is_active          TINYINT(1) NOT NULL DEFAULT 1,
    created_at         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (lesson_id),
    UNIQUE KEY uq_lessons_language_number (language_id, lesson_number),
    UNIQUE KEY uq_lessons_language_title (language_id, title),
    KEY idx_lessons_language_active (language_id, is_active, lesson_number),
    CONSTRAINT chk_lessons_active CHECK (is_active IN (0, 1)),
    CONSTRAINT chk_lessons_number CHECK (lesson_number > 0),
    CONSTRAINT fk_lessons_language FOREIGN KEY (language_id)
        REFERENCES languages(language_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_lessons_support_language FOREIGN KEY (support_language_id)
        REFERENCES languages(language_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_lessons_creator FOREIGN KEY (created_by)
        REFERENCES users(user_id)
        ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS lesson_items (
    item_id              INT UNSIGNED NOT NULL AUTO_INCREMENT,
    lesson_id            INT UNSIGNED NOT NULL,
    item_number          SMALLINT UNSIGNED NOT NULL,
    term_text            VARCHAR(255) NOT NULL,
    translation_text     VARCHAR(255) NOT NULL,
    pronunciation        VARCHAR(255) NULL,
    example_sentence     TEXT NULL,
    example_translation TEXT NULL,
    PRIMARY KEY (item_id),
    UNIQUE KEY uq_lesson_items_order (lesson_id, item_number),
    KEY idx_lesson_items_lesson (lesson_id, item_number),
    CONSTRAINT chk_lesson_items_number CHECK (item_number > 0),
    CONSTRAINT chk_lesson_items_term CHECK (CHAR_LENGTH(TRIM(term_text)) > 0),
    CONSTRAINT chk_lesson_items_translation CHECK (CHAR_LENGTH(TRIM(translation_text)) > 0),
    CONSTRAINT fk_lesson_items_lesson FOREIGN KEY (lesson_id)
        REFERENCES lessons(lesson_id)
        ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS questions (
    question_id     INT UNSIGNED NOT NULL AUTO_INCREMENT,
    lesson_id       INT UNSIGNED NOT NULL,
    question_text   TEXT NOT NULL,
    choice_a        VARCHAR(255) NOT NULL,
    choice_b        VARCHAR(255) NOT NULL,
    choice_c        VARCHAR(255) NOT NULL,
    choice_d        VARCHAR(255) NOT NULL,
    correct_option  ENUM('A', 'B', 'C', 'D') NOT NULL,
    explanation     TEXT NULL,
    created_by      INT UNSIGNED NULL,
    is_active       TINYINT(1) NOT NULL DEFAULT 1,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (question_id),
    UNIQUE KEY uq_questions_id_lesson (question_id, lesson_id),
    KEY idx_questions_lesson_active (lesson_id, is_active),
    CONSTRAINT chk_questions_active CHECK (is_active IN (0, 1)),
    CONSTRAINT chk_questions_text CHECK (CHAR_LENGTH(TRIM(question_text)) > 0),
    CONSTRAINT fk_questions_lesson FOREIGN KEY (lesson_id)
        REFERENCES lessons(lesson_id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_questions_creator FOREIGN KEY (created_by)
        REFERENCES users(user_id)
        ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS lesson_progress (
    progress_id       INT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id           INT UNSIGNED NOT NULL,
    lesson_id         INT UNSIGNED NOT NULL,
    status            ENUM('in_progress', 'completed') NOT NULL DEFAULT 'in_progress',
    started_at        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_accessed_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at      TIMESTAMP NULL DEFAULT NULL,
    PRIMARY KEY (progress_id),
    UNIQUE KEY uq_lesson_progress_user_lesson (user_id, lesson_id),
    KEY idx_lesson_progress_user_status (user_id, status),
    CONSTRAINT fk_lesson_progress_user FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_lesson_progress_lesson FOREIGN KEY (lesson_id)
        REFERENCES lessons(lesson_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS attempts (
    attempt_id      INT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id         INT UNSIGNED NOT NULL,
    lesson_id       INT UNSIGNED NOT NULL,
    score           INT UNSIGNED NOT NULL DEFAULT 0,
    total_questions INT UNSIGNED NOT NULL,
    status          ENUM('in_progress', 'completed', 'abandoned') NOT NULL DEFAULT 'in_progress',
    started_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at    TIMESTAMP NULL DEFAULT NULL,
    PRIMARY KEY (attempt_id),
    UNIQUE KEY uq_attempts_id_lesson (attempt_id, lesson_id),
    KEY idx_attempts_user_completed (user_id, completed_at),
    KEY idx_attempts_lesson_completed (lesson_id, completed_at),
    CONSTRAINT chk_attempts_score CHECK (score <= total_questions),
    CONSTRAINT chk_attempts_total CHECK (total_questions > 0),
    CONSTRAINT fk_attempts_user FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_attempts_lesson FOREIGN KEY (lesson_id)
        REFERENCES lessons(lesson_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS attempt_answers (
    answer_id       INT UNSIGNED NOT NULL AUTO_INCREMENT,
    attempt_id      INT UNSIGNED NOT NULL,
    lesson_id       INT UNSIGNED NOT NULL,
    question_id     INT UNSIGNED NOT NULL,
    selected_option ENUM('A', 'B', 'C', 'D') NULL,
    is_correct      TINYINT(1) NOT NULL DEFAULT 0,
    answered_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (answer_id),
    UNIQUE KEY uq_attempt_answers_attempt_question (attempt_id, question_id),
    CONSTRAINT chk_attempt_answers_correct CHECK (is_correct IN (0, 1)),
    CONSTRAINT chk_attempt_answers_unanswered CHECK (selected_option IS NOT NULL OR is_correct = 0),
    CONSTRAINT fk_attempt_answers_attempt_lesson FOREIGN KEY (attempt_id, lesson_id)
        REFERENCES attempts(attempt_id, lesson_id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_attempt_answers_question_lesson FOREIGN KEY (question_id, lesson_id)
        REFERENCES questions(question_id, lesson_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
