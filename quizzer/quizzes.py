from flask import Blueprint, flash, abort, g, redirect, render_template, request, url_for, jsonify, session

from quizzer.auth import login_required
from quizzer.db import get_db
from quizzer.localization import locale

bp = Blueprint("quizzes", __name__)


@bp.route("/")
def index():
    """Index route for quizzes. Shows available quizzes for students and created quizzes for authors."""
    quizzes = []
    if g.user is not None:
        quizzes = Quiz.select_by_author_id(author_id=g.user['id']) if g.is_admin else Quiz.select_available_to_solve()
    return render_template("quizzes/index.html", quizzes=quizzes)


@bp.route("/create", methods=("GET", "POST"))
@login_required
def create():
    """Creates new quiz and stores information about it in database."""
    if request.method == "GET":
        return render_template("quizzes/create.html")
    error = None
    questions = []
    quiz_name = None
    if isinstance(request.json, dict):
        for quiz in request.json:
            quiz_name = quiz
            for question_text in request.json[quiz_name]:
                question_options = request.json[quiz_name][question_text]
                questions.append(Question(text=question_text, options=question_options))
    else:
        error = locale.error_wrong_data

    new_quiz = Quiz(author_id=g.user["id"], name=quiz_name, questions=questions)
    errors = new_quiz.validate()

    if error or errors:
        error_msg = "\n".join(filter(None, [error, *errors]))
        return jsonify(error=error_msg)
    else:
        db = get_db()
        new_quiz.add_to_db()
        db.commit()
        return jsonify(result="success", url=redirect(url_for("quizzes.index")).headers["Location"])


@bp.route("/<int:quiz_id>/edit", methods=("GET", "POST"))
@login_required
def edit(quiz_id):
    """Edits quiz by it's identifier and stores information about it in database."""
    if request.method == "GET":
        quiz = Quiz.from_quiz_id(quiz_id)
        return render_template("quizzes/edit.html", quiz=quiz)
    original_quiz = Quiz.from_quiz_id(quiz_id)
    original_quiz.validate()
    questions = []
    quiz_name = None
    error = None
    if isinstance(request.json, dict):
        for quiz in request.json:
            quiz_name = quiz
            for question_text in request.json[quiz_name]:
                question_options = request.json[quiz_name][question_text]
                questions.append(Question(text=question_text, options=question_options))
    else:
        error = locale.error_wrong_data

    new_quiz = Quiz(author_id=g.user["id"], name=quiz_name, questions=questions)
    errors = new_quiz.validate()

    if error or errors:
        error_msg = "\n".join(filter(None, [error, *errors]))
        return jsonify(error=error_msg)
    else:
        db = get_db()
        original_quiz.delete_from_db()
        new_quiz.add_to_db()
        db.commit()
        return jsonify(result="success", url=redirect(url_for("quizzes.index")).headers["Location"])


@bp.route("/<int:quiz_id>/delete", methods=("POST",))
@login_required
def delete(quiz_id):
    """Deletes quiz by it's identifier."""
    quiz = Quiz.from_quiz_id(quiz_id)
    quiz.validate()
    quiz.delete_from_db()
    return redirect(url_for("quizzes.index"))


@bp.route("/<int:quiz_id>/solve", methods=("GET", "POST"))
@login_required
def solve(quiz_id):
    """Solves quiz by it's identifier. Stores result information in database."""
    quiz = Quiz.from_quiz_id(quiz_id)
    if g.user['is_admin']:
        abort(403)
    if request.method == "GET":
        if not session.get('quiz_session_id'):
            Quiz.create_session_for_user(g.user['id'])
        return render_template("quizzes/solve.html", quiz=quiz)

    errors = []
    for question_id, answer_id in request.form.items():
        errors.append(Question.validate_id(question_id))
        errors.append(AnswerOption.validate_id(answer_id))

    errors = list(filter(None, errors))
    if errors:
        flash("\n".join(errors))
        return render_template("quizzes/solve.html", quiz=quiz)

    for question_id, answer_id in request.form.items():
        quiz.write_answer_result(user_id=g.user['id'], question_id=question_id, answer_id=answer_id)

    answers_ratio = QuizResult.calculate_answers(quiz_id=quiz.quiz_id, user_id=g.user['id'],
                                                 session_id=session['quiz_session_id'])

    session['quiz_session_id'] = None
    return render_template("quizzes/result.html", quiz=quiz, answers_ratio=answers_ratio)


@bp.route("/history", methods=("GET",))
@login_required
def history():
    """Shows history for solved quizzes with information about students, authors, results, etc."""
    if g.is_admin:
        quiz_results = QuizResult.get_quiz_results_for_author(author_id=g.user['id'])
    else:
        quiz_results = QuizResult.get_quiz_results_for_user(user_id=g.user['id'])
    user_ids = {result['user_id'] for result in quiz_results}

    quiz_info = []
    for user_id in user_ids:
        session_ids = {result['quiz_session_id'] for result in quiz_results}
        for session_id in session_ids:
            quiz_result = QuizResult.get_quiz_results_for_user_by_session(user_id=user_id, session_id=session_id)
            if quiz_result:
                quiz_result = quiz_result[0]
                res = {
                    'author_id': quiz_result['author_id'],
                    'user_id': quiz_result['user_id'],
                    'author_name': quiz_result['author_name'],
                    'user_name': quiz_result['username'],
                    'quiz_id': quiz_result['quiz_id'],
                    'quiz_name': quiz_result['quiz_name']
                }
                answer_ratio = QuizResult.calculate_answers(quiz_id=quiz_result['quiz_id'], user_id=user_id,
                                                            session_id=session_id)
                res['correct_answers'], res['total_answers'] = answer_ratio
                quiz_info.append(res)
    return render_template("quizzes/history.html", quiz_info=quiz_info)


class AnswerOption:
    """Class that represents an answer option."""

    def __init__(self, text, checked=False):
        """Class initialization.

        :param text: text of the answer.
        :param checked: is option checked (is real answer).
        """
        self.text = text
        self.answer_id = -1
        self.checked = checked

    def add_to_db(self):
        """Adds answer to database.

        :return: rowid of added answer.
        """
        cursor = get_db().cursor()
        cursor.execute(
            "INSERT INTO answer_options (text) VALUES (?)",
            (self.text,),
        )
        cursor.connection.commit()
        self.answer_id = cursor.lastrowid
        return self.answer_id

    def delete_from_db(self):
        """Deletes an answer from database."""
        db = get_db()
        db.execute(
            "DELETE FROM answer_options WHERE id = (?)",
            (self.answer_id,),
        )
        db.execute(
            "DELETE FROM question_answer_rel WHERE answer_option_id = (?)",
            (self.answer_id,),
        )
        db.commit()

    def validate(self):
        """Validates that current object has no errors with it's properties.

        :return: list of errors if they were found.
        """
        errors = []
        if not self.text:
            errors.append(locale.error_no_answer_text)

        return errors

    @staticmethod
    def validate_id(answer_id):
        """Validates that answer with given ID is exists.

        :param answer_id: answer ID.
        :return: error if it was found.
        """
        db = get_db()
        answer_db = db.execute(
            "SELECT text FROM answer_options ao WHERE id = ?",
            (answer_id,),
        ).fetchone()
        if not answer_db:
            return locale.error_no_answer_id.format(answer_id=answer_id)

    @staticmethod
    def from_answer_id(answer_id):
        """Creates object from given answer ID.

        :param answer_id: answer ID.
        :return: AnswerOption object.
        """
        db = get_db()
        answer_db = db.execute(
            "SELECT text FROM answer_options ao WHERE id = ?",
            (answer_id,),
        ).fetchone()
        answer = AnswerOption(text=answer_db['text'])
        answer.answer_id = answer_id
        return answer

    @staticmethod
    def from_dict(options_dict):
        """Creates object from given dictionary with options.

        :param options_dict: dictionary with answer options.
        :return: AnswerOption object.
        """
        if isinstance(options_dict, dict):
            options = [AnswerOption(text=option_text, checked=is_checked) for option_text, is_checked in
                       options_dict.items()]
            return options
        return options_dict


class Question:
    """Class that represents a question."""

    def __init__(self, text, options):
        """Class initialization.

        :param text: text of the question.
        :param options: dictionary or list of answer options for the question.
        """
        self.text = text
        self.options = AnswerOption.from_dict(options)
        self.answer_id, self.question_id = -1, -1

    def _add_answer_option_to_db(self):
        """Adds answer options to database and updates information of the real answer to the question."""
        cursor = get_db().cursor()
        for option in self.options:
            answer_id = option.add_to_db()
            if option.checked:
                self.answer_id = answer_id
            cursor.execute(
                "INSERT INTO question_answer_rel (question_id, answer_option_id) VALUES (?, ?)",
                (self.question_id, answer_id),
            )
        cursor.connection.commit()
        self._update_answer()

    def _update_answer(self):
        """Updates information of the real answer to the question in database."""
        db = get_db()
        db.execute(
            "UPDATE questions SET answer_id = (?) WHERE id = (?)",
            (self.answer_id, self.question_id),
        )
        db.commit()

    def add_to_db(self):
        """Adds question with options to database.

        :return: rowid of added question.
        """
        cursor = get_db().cursor()
        cursor.execute(
            "INSERT INTO questions (answer_id, text) VALUES (?, ?)",
            (-1, self.text),
        )
        cursor.connection.commit()
        self.question_id = cursor.lastrowid
        self._add_answer_option_to_db()
        return self.question_id

    def delete_from_db(self):
        """Deletes a question with it's options from database."""
        db = get_db()
        db.execute(
            "DELETE FROM questions WHERE id = (?)",
            (self.question_id,),
        )
        db.commit()
        for option in self.options:
            option.delete_from_db()

    def validate(self):
        """Validates that current object has no errors with it's properties.

        :return: list of errors if they were found.
        """
        errors = []
        if not self.text:
            errors.append(locale.error_no_question_text)
        if len([option for option in self.options if option.text is not None]) < 2:
            errors.append(locale.error_not_enough_answers)
        if len([option for option in self.options if option.checked]) > 1:
            errors.append(locale.error_question_too_many_answers)
        if len([option for option in self.options if option.checked]) == 0:
            errors.append(locale.error_question_no_answers)

        option_errors = [options.validate() for options in self.options]
        errors.extend([item for sublist in option_errors for item in sublist])
        return errors

    @staticmethod
    def validate_id(question_id):
        """Validates that question with given ID is exists.

        :param question_id: question ID.
        :return: error if it was found.
        """
        db = get_db()
        question_db = db.execute(
            "SELECT id, answer_id, text FROM questions WHERE id = ?",
            (question_id,),
        ).fetchone()
        if not question_db:
            return locale.error_no_question_id.format(question_id=question_id)

    @staticmethod
    def from_question_id(question_id):
        """Creates object from given question ID.

        :param question_id: question ID.
        :return: Question object.
        """
        db = get_db()
        question_db = db.execute(
            "SELECT id, answer_id, text FROM questions WHERE id = ?",
            (question_id,),
        ).fetchone()
        options_db = db.execute(
            "SELECT question_id, answer_option_id FROM question_answer_rel WHERE question_id = ?",
            (question_id,),
        ).fetchall()
        options = []
        for option in options_db:
            answer = AnswerOption.from_answer_id(option['answer_option_id'])
            if answer.answer_id == question_db['answer_id']:
                answer.checked = True
            options.append(answer)
        question = Question(text=question_db['text'], options=options)
        question.question_id = question_id
        question.answer_id = question_db['answer_id']
        return question


class Quiz:
    """Class that represents a quiz."""

    def __init__(self, author_id, name, questions):
        """Class initialization.

        :param author_id: author ID.
        :param name: name of the quiz.
        :param questions: list of questions for the quiz.
        """
        self.author_id = author_id
        self.name = name
        self.questions = questions
        self.quiz_id = -1

    def add_to_db(self):
        """Adds quiz with questions to database.

        :return: rowid of added quiz.
        """
        cursor = get_db().cursor()
        cursor.execute(
            "INSERT INTO quizzes (name, author_id) VALUES (?, ?)",
            (self.name, self.author_id),
        )
        cursor.connection.commit()
        self.quiz_id = cursor.lastrowid
        self._add_questions_to_quiz()
        return self.quiz_id

    def _add_questions_to_quiz(self):
        """Adds questions for quiz to database."""
        db = get_db()
        for question in self.questions:
            question.add_to_db()
            db.execute(
                "INSERT INTO quiz_question_rel (quiz_id, question_id) VALUES (?, ?)",
                (self.quiz_id, question.question_id),
            )
        db.commit()

    def delete_from_db(self):
        """Deletes a quiz with it's questions from database."""
        db = get_db()
        db.execute(
            "DELETE FROM quizzes WHERE id = (?)",
            (self.quiz_id,),
        )
        db.execute(
            "DELETE FROM quiz_question_rel WHERE quiz_id = (?)",
            (self.quiz_id,),
        )
        db.commit()
        for question in self.questions:
            question.delete_from_db()

    def validate(self):
        """Validates that current object has no errors with it's properties.

        :return: list of errors if they were found.
        """
        if self.author_id != g.user["id"]:
            abort(403)

        errors = []
        if not self.name:
            errors.append(locale.error_no_quiz_name)

        if len(self.questions) == 0:
            errors.append(locale.error_no_questions)

        question_errors = [question.validate() for question in self.questions]
        errors.extend([item for sublist in question_errors for item in sublist])
        return errors

    @staticmethod
    def from_quiz_id(quiz_id):
        """Creates object from given quiz ID.

        :param quiz_id: quiz ID.
        :return: Quiz object.
        """
        db = get_db()
        quiz_db = db.execute(
            "SELECT q.id, q.name, q.author_id FROM quizzes q WHERE q.id = ?",
            (quiz_id,),
        ).fetchone()

        if quiz_db is None:
            abort(404, locale.error_no_quiz_id.format(quiz_id=quiz_id))

        question_rels = db.execute(
            """SELECT qqr.quiz_id, qqr.question_id
            FROM quiz_question_rel qqr
            WHERE qqr.quiz_id = ?
            """,
            (quiz_id,),
        ).fetchall()
        questions = []
        for rel in question_rels:
            question_id = rel['question_id']
            question = Question.from_question_id(question_id)
            questions.append(question)
        quiz = Quiz(author_id=quiz_db['author_id'], name=quiz_db['name'], questions=questions)
        quiz.quiz_id = quiz_id
        return quiz

    @staticmethod
    def select_by_author_id(author_id):
        """Select quizzes by author.

        :param author_id: author ID.
        :return: database query list.
        """
        return get_db().execute(
            """SELECT q.id, q.name, q.author_id, u.username as author_name
            FROM quizzes q
            JOIN user u ON q.author_id = u.id
            WHERE q.author_id = ?
            ORDER BY q.id DESC
            """,
            (author_id,),
        ).fetchall()

    @staticmethod
    def select_available_to_solve():
        """Select all available quizzes.

        :return: database query list.
        """
        return get_db().execute(
            """SELECT q.id, q.name, q.author_id, u.username as author_name
            FROM quizzes q
            JOIN user u ON q.author_id = u.id
            ORDER BY q.id DESC
            """
        ).fetchall()

    def write_answer_result(self, user_id, question_id, answer_id):
        """Writes result of an answer for quiz.

        :param user_id: user ID who is solving the quiz.
        :param question_id: question ID which was answered.
        :param answer_id: answer ID which was selected.
        """
        db = get_db()
        db.execute(
            """INSERT INTO quiz_result (user_id, quiz_id, quiz_session_id, question_id, answer_id)
                VALUES (?, ?, ?, ?, ?)""",
            (user_id, self.quiz_id, session['quiz_session_id'], question_id, answer_id),
        )
        db.commit()

    @staticmethod
    def create_session_for_user(user_id):
        """Creates new quiz session ID for given user and sets it in the session.

        :param user_id: user ID.
        """
        next_session = get_db().execute(
            "SELECT IFNULL(MAX(quiz_session_id) + 1, 1) AS quiz_session_id FROM quiz_result WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        session['quiz_session_id'] = next_session['quiz_session_id']
        print(f"Created new session {session['quiz_session_id']} for user {user_id}")


class QuizResult:
    """Class that represents a result of a quiz."""

    @staticmethod
    def get_quiz_results_for_user_by_session(user_id, session_id):
        """Gets results of quiz for given user and session ID.

        :param user_id: user ID.
        :param session_id: quiz session ID.
        :return: database query list.
        """
        return get_db().execute(
            """SELECT *
                FROM quiz_results
                WHERE user_id = (?) AND quiz_session_id = (?)""",
            (user_id, session_id),
        ).fetchall()

    @staticmethod
    def get_quiz_results_for_user(user_id):
        """Get results for given user.

        :param user_id: user ID.
        :return: database query list.
        """
        return get_db().execute(
            """SELECT *
                FROM quiz_results
                WHERE user_id = (?)""",
            (user_id,),
        ).fetchall()

    @staticmethod
    def get_quiz_results_for_author(author_id):
        """Get result for quizzes with given author.

        :param author_id: author ID.
        :return: database query list.
        """
        return get_db().execute(
            """SELECT *
                FROM quiz_results
                WHERE author_id = (?)""",
            (author_id,),
        ).fetchall()

    @staticmethod
    def calculate_answers(quiz_id, user_id, session_id):
        """Calculates right answer for given quiz result.

        :param quiz_id: quiz ID.
        :param user_id: user ID.
        :param session_id: quiz session ID.
        :return: tuple of (num of correct answers, num of all questions in quiz)
        """
        quiz = Quiz.from_quiz_id(quiz_id=quiz_id)
        num_questions = len(quiz.questions)
        num_correct_answers = 0
        for result in QuizResult.get_quiz_results_for_user_by_session(user_id=user_id, session_id=session_id):
            if result['answer_id'] == result['real_answer_id']:
                num_correct_answers += 1
        return num_correct_answers, num_questions
