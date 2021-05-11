-- Initialize the database.
-- Drop any existing data and create empty tables.

DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS answer_options;
DROP TABLE IF EXISTS questions;
DROP TABLE IF EXISTS question_answer_rel;
DROP TABLE IF EXISTS quizzes;
DROP TABLE IF EXISTS quiz_question_rel;
DROP TABLE IF EXISTS quiz_result;
DROP VIEW IF EXISTS quiz_results;

CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL,
  is_admin INTEGER
);

CREATE TABLE answer_options (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  text TEXT NOT NULL
);

CREATE TABLE questions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  answer_id INTEGER NOT NULL,
  text TEXT NOT NULL,
  FOREIGN KEY (answer_id) REFERENCES answer_options (id) ON DELETE CASCADE
);

CREATE TABLE question_answer_rel (
  question_id INTEGER NOT NULL,
  answer_option_id INTEGER NOT NULL,
  FOREIGN KEY (question_id) REFERENCES questions (id),
  FOREIGN KEY (answer_option_id) REFERENCES answer_options (id)
);

CREATE TABLE quizzes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  author_id INTEGER NOT NULL,
  FOREIGN KEY (author_id) REFERENCES user (id) ON DELETE CASCADE
);

CREATE TABLE quiz_question_rel (
  quiz_id INTEGER NOT NULL,
  question_id INTEGER NOT NULL,
  FOREIGN KEY (quiz_id) REFERENCES quizzes (id),
  FOREIGN KEY (question_id) REFERENCES questions (id)
);

CREATE TABLE quiz_result (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  quiz_session_id INTEGER NOT NULL,
  quiz_id INTEGER NOT NULL,
  question_id INTEGER NOT NULL,
  answer_id INTEGER NOT NULL,
  FOREIGN KEY (user_id) REFERENCES user (id),
  FOREIGN KEY (quiz_id) REFERENCES quizzes (id),
  FOREIGN KEY (question_id) REFERENCES questions (id)
  FOREIGN KEY (answer_id) REFERENCES answer_options (id)
);

CREATE VIEW quiz_results AS
    SELECT qr.id, qr.user_id, u.username, qi.author_id, qi.author_name, qr.quiz_session_id, qr.quiz_id, qi.name as quiz_name, qr.question_id, qr.answer_id, qi.real_answer_id
    FROM quiz_result qr
    JOIN
    (SELECT quiz_id, q.name, question_id, author_id, answer_id as real_answer_id, username as author_name
    FROM questions que
    JOIN quiz_question_rel qqrel ON qqrel.question_id = que.id
    JOIN quizzes q ON qqrel.quiz_id = q.id
	JOIN user u ON u.id = q.author_id) qi
	ON qi.quiz_id = qr.quiz_id AND qi.question_id = qr.question_id
	JOIN user u ON u.id = qr.user_id
;

INSERT INTO "user" ("id","username","password","is_admin") VALUES (1,'admin','pbkdf2:sha256:150000$7WONihzf$738e73ec2abc7bb4537b6af33c89aa7e1f0ce5400cee3f3c07fc48e69a990d07',1);