import json
import pytest
from flask import session

from quizzer.db import get_db


def test_index(client, auth):
    response = client.get("/")
    assert b'action="/auth/login"' in response.data, "'Log in' form is missing in default index without user"
    assert b'action="/auth/register"' in response.data, "'Register' form is missing in default index without user"
    assert b"Test Index Quiz" not in client.get("/").data, "Default index without user should not see Test Index Quiz"
    assert b'action="/create"' not in response.data, "Default index without user should not see 'Create' button'"
    assert b'action="/history"' not in response.data, "Default index without user should not see 'History' button'"
    assert b'action="/1/edit"' not in response.data, "Default index without user should not see 'Edit' button'"
    assert b'action="/1/delete"' not in response.data, "Default index without user should not see 'Delete' button'"
    assert b'action="/1/solve"' not in response.data, "Default index without user should not see 'Solve' button'"

    auth.login()
    response = client.get("/")
    assert b'action="/auth/login"' not in response.data, "Index for ADMIN user should not see 'Log In' button"
    assert b'action="/auth/register"' not in response.data, "Index for ADMIN user should not see 'Register' button"
    assert b'action="/auth/logout"' in response.data, "'Log Out' form is missing in index for ADMIN user"
    assert b"Test Index Quiz" in response.data, "Test Index Quiz information is missing in index for ADMIN user"
    assert b'action="/create"' in response.data, "'Create' button is missing in index for ADMIN user"
    assert b'action="/history"' in response.data, "'History' button is missing in index for ADMIN user"
    assert b'action="/1/edit"' in response.data, "'Edit' button is missing in index for ADMIN user"
    assert b'action="/1/delete"' in response.data, "'Delete' button is missing in index for ADMIN user"
    assert b'action="/1/solve"' not in response.data, "Index for ADMIN user should not see 'Solve' button"

    auth.logout()
    auth.login_as_user()
    response = client.get("/")
    assert b'action="/auth/login"' not in response.data, "Index for USUAL user should not see 'Log In' button"
    assert b'action="/auth/register"' not in response.data, "Index for USUAL user should not see 'Register' button"
    assert b'action="/auth/logout"' in response.data, "'Log Out' form is missing in index for USUAL user"
    assert b"Test Index Quiz" in response.data, "Test Index Quiz information is missing in index for USUAL user"
    assert b'action="/create"' not in response.data, "Index for USUAL user should not see 'Create' button"
    assert b'action="/history"' in response.data, "'History' button is missing in index for USUAL user"
    assert b'action="/1/edit"' not in response.data, "Index for USUAL user should not see 'Edit' button"
    assert b'action="/1/delete"' not in response.data, "Index for USUAL user should not see 'Delete' button"
    assert b'action="/1/solve"' in response.data, "'Solve' button is missing in index for USUAL user"


@pytest.mark.parametrize("path", ("/create", "/1/edit", "/1/delete", "/1/solve"))
def test_login_required(client, path):
    response = client.post(path)
    assert response.headers["Location"] == "http://localhost/auth/login", f"Unauthorized user should not have access to URL {path}"


def test_author_required(app, client, auth):
    # change the post author to another user
    with app.app_context():
        db = get_db()
        db.execute("UPDATE quizzes SET author_id = 2 WHERE id = 1")
        db.commit()

    auth.login()
    assert client.post("/1/edit").status_code == 403, "ADMIN user should not edit quizzes from another authors"
    assert client.post("/1/delete").status_code == 403, "ADMIN user should not delete quizzes from another authors"
    assert b"Test Index Quiz" not in client.get("/").data, "ADMIN user should not see quizzes from another authors"
    assert b'action="/1/edit"' not in client.get("/").data, "ADMIN user should not see 'Edit' button for quizzes from another authors"
    assert b'action="/1/delete"' not in client.get("/").data, "ADMIN user should not see 'Delete' button for quizzes from another authors"


@pytest.mark.parametrize("path", ("/2/edit", "/2/delete", "/2/solve"))
def test_exists_required(client, auth, path):
    auth.login()
    assert client.post(path).status_code == 404


def test_create_valid(client, auth, app):
    auth.login()
    response = client.get("/create")
    assert response.status_code == 200
    assert b'id="quiz-name"' in response.data, "Quiz Create should contain input for quiz name"
    assert b'onclick="saveQuiz()"' in response.data, "Quiz Create should contain button for saving quiz"
    assert b'onclick="addQuestion()"' in response.data, "Quiz Create should contain button for adding new questions"
    data = {
        "Test Quiz": {
            "Test Question": {"1": True, "2": False, "3": False, "4": False},
            "Other Question": {"1": False, "2": False, "3": False, "4": True}
        }
    }

    client.post("/create", data=json.dumps(data), content_type='application/json')

    with app.app_context():
        db = get_db()
        count = db.execute("SELECT COUNT(id) FROM answer_options").fetchone()[0]
        assert count == 8 + 4
        count = db.execute("SELECT COUNT(id) FROM questions").fetchone()[0]
        assert count == 2 + 1
        count = db.execute("SELECT COUNT(question_id) FROM question_answer_rel").fetchone()[0]
        assert count == 8 + 4
        count = db.execute("SELECT COUNT(id) FROM quizzes WHERE name = 'Test Quiz'").fetchone()[0]
        assert count == 1
        count = db.execute("SELECT COUNT(quiz_id) FROM quiz_question_rel").fetchone()[0]
        assert count == 2 + 1


def test_edit_valid(client, auth, app):
    auth.login()
    response = client.get("/1/edit")
    assert response.status_code == 200
    assert b'id="quiz-name"' in response.data, "Quiz Create should contain input for quiz name"
    assert b'onclick="saveQuiz(1)"' in response.data, "Quiz Create should contain button for saving quiz"
    assert b'onclick="addQuestion()"' in response.data, "Quiz Create should contain button for adding new questions"
    data = {
        "Test Quiz (edited)": {
            "Test Question": {"1": True, "2": False, "3": False, "4": False}
        }
    }
    client.post("/1/edit", data=json.dumps(data), content_type='application/json')

    with app.app_context():
        db = get_db()
        count = db.execute("SELECT COUNT(id) FROM answer_options").fetchone()[0]
        assert count == 4
        count = db.execute("SELECT COUNT(id) FROM questions").fetchone()[0]
        assert count == 1
        count = db.execute("SELECT COUNT(question_id) FROM question_answer_rel").fetchone()[0]
        assert count == 4
        count = db.execute("SELECT COUNT(id) FROM quizzes WHERE name = 'Test Quiz (edited)'").fetchone()[0]
        assert count == 1
        count = db.execute("SELECT COUNT(quiz_id) FROM quiz_question_rel").fetchone()[0]
        assert count == 1


@pytest.mark.parametrize("path", ("/create", "/1/edit"))
def test_create_edit_invalid(client, auth, path):
    auth.login()
    data = [
        {"Some invalid data": [1, 2, 3]}
    ]

    response = client.post(path, data=json.dumps(data), content_type='application/json')
    assert b"error" in response.data
    assert b"Got wrong data, should be dict" in response.data


@pytest.mark.parametrize("path", ("/create", "/1/edit"))
def test_create_edit_validate(client, auth, path):
    auth.login()
    data = {
        "": {
            "Test Valid Question": {"1": True, "2": False, "3": False, "4": False},
            "": {"1": False, "2": False, "3": False, "4": True},
            "Question Not Enough Answers": {"1": True},
            "Question Multiple Answers": {"1": True, "2": True},
            "Question No Answers": {"1": False, "2": False, "3": False, "4": False},
            "Question With Empty Answer": {"1": True, "2": False, "": False}
        }
    }

    response = client.post(path, data=json.dumps(data), content_type='application/json')
    assert b"error" in response.data
    assert b"Quiz name is required" in response.data
    assert b"Question text is required" in response.data
    assert b"Question should contain at lease 2 options to answer" in response.data
    assert b"Question shouldn't contain more than one answer" in response.data
    assert b"Question should contain at least one answer" in response.data
    assert b"Answer text is required" in response.data

    data = {"Empty Quiz": {}}
    response = client.post(path, data=json.dumps(data), content_type='application/json')

    assert b"error" in response.data
    assert b"Quiz should contain at least one question" in response.data


def test_delete(client, auth, app):
    auth.login()
    response = client.post("/1/delete")
    assert response.headers["Location"] == "http://localhost/"

    with app.app_context():
        db = get_db()
        quiz = db.execute("SELECT * FROM quizzes WHERE id = 1").fetchone()
        assert quiz is None


def test_solve_index(client, auth):
    response = client.get("/1/solve")
    assert response.headers["Location"] == "http://localhost/auth/login", f"Unauthorized user should not have access to URL {'/1/solve'}"

    auth.login()
    assert client.get("/1/solve").status_code == 403, "ADMIN user should not be able to solve quizzes"
    assert client.post("/1/solve").status_code == 403, "ADMIN user should not be able to solve quizzes"
    auth.logout()

    auth.login_as_user()
    response = client.get("/1/solve")
    assert response.status_code == 200
    assert b'Solving' in response.data, "Missing 'Solving' quiz label for USUAL user"
    assert b'type="submit"' in response.data, "Missing 'Submit' button for USUAL user"
    assert b'id="question1"' in response.data, "Missing question's elements for USUAL user"


def test_solve_valid(client, auth, app):
    auth.login_as_user()
    with client as client_with_session:
        response = client_with_session.get("/1/solve")
        assert response.status_code == 200
        assert session['quiz_session_id'] == 2, "User should have quiz session ID when trying to solve"

    data = {1: 1}
    response = client.post("/1/solve", data=data)
    assert b'Result for' in response.data
    assert b'Correct answers: 1 out of 1' in response.data

    with app.app_context():
        db = get_db()
        count = db.execute("SELECT COUNT(id) FROM quiz_result").fetchone()[0]
        assert count == 2


def test_solve_multiple_valid(client, auth, app):
    auth.login_as_user()
    for question_index in range(1, 5):
        new_session_id = question_index + 1
        with client as client_with_session:
            with client_with_session.session_transaction() as sess:
                sess['quiz_session_id'] = new_session_id
            data = {1: question_index}
            response = client_with_session.post("/1/solve", data=data)

        assert b'Result for' in response.data
        assert b'Correct answers' in response.data

        with app.app_context():
            db = get_db()
            count = db.execute("SELECT COUNT(id) FROM quiz_result").fetchone()[0]
            assert count == new_session_id
            count = db.execute(f"SELECT COUNT(id) FROM quiz_result "
                               f"WHERE quiz_session_id = {question_index}").fetchone()[0]
            assert count == 1


def test_solve_invalid(client, auth, app):
    auth.login_as_user()
    with client as client_with_session:
        response = client_with_session.get("/1/solve")
        assert response.status_code == 200
        assert session['quiz_session_id'] == 2, "User should have quiz session ID when trying to solve"

    data = {1: 2, 3: 4, 5: 6, "Invalid data": "Still invalid"}
    response = client.post("/1/solve", data=data)
    assert b'Question with id=3 does not exist' in response.data
    assert b'Question with id=5 does not exist' in response.data
    assert b'Answer with id=6 does not exist' in response.data
    assert b'Question with id=Invalid data does not exist' in response.data
    assert b'Answer with id=Still invalid does not exist' in response.data

    with app.app_context():
        db = get_db()
        count = db.execute("SELECT COUNT(id) FROM quiz_result").fetchone()[0]
        assert count == 1


def test_history_author(client, auth):
    auth.login()
    response = client.get("/history")
    assert response.status_code == 200
    assert b'Test Index Quiz' in response.data, "History should show quiz name 'Test Index Quiz'"
    assert b'test' in response.data, "History should show author's name 'test'"
    assert b'user' in response.data, "History should show student's name 'user'"
    assert b'0 of 1' in response.data, "History should show quiz result '0 correct answers out of 1 total'"

    auth.logout()
    auth.login_as_user()
    response = client.get("/history")
    assert response.status_code == 200
    assert b'Test Index Quiz' in response.data, "History should show quiz name 'Test Index Quiz'"
    assert b'test' in response.data, "History should show author's name 'test'"
    assert b'user' in response.data, "History should show student's name 'user'"
    assert b'0 of 1' in response.data, "History should show quiz result '0 correct answers out of 1 total'"
