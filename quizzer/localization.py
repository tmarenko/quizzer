class Localization:
    _current_lang = None

    @property
    def current_lang(self):
        if self._current_lang is None:
            from flask import request
            best_lang = request.accept_languages.best_match(['ru', 'en'])
            self._current_lang = best_lang if best_lang in _localization else 'en'
        return self._current_lang

    def __getattr__(self, attr):
        return _localization[self.current_lang][attr]

    def dict(self):
        import json
        return json.dumps(_localization[self.current_lang])


locale = Localization()

_localization = {
    "ru": {
        "username": "Имя",
        "password": "Пароль",
        "create_account": "Создать аккаунт",
        "log_in_form": "Вход",
        "register_form": "Зарегистрироваться",
        "log_in": "Войти",
        "register": "Регистрация",
        "log_out": "Выйти",
        "create_new": "Создать",
        "edit": "Изменить",
        "delete": "Удалить",
        "solve": "Начать",
        "new_quiz": "Новый опрос",
        "close": "Закрыть",
        "save": "Сохранить",
        "submit": "Завершить",
        "remove": "Удалить",
        "question_text": "Текст вопроса",
        "answer_option": "Ответ №",
        "add_question": "Добавить вопрос",
        "search": "Поиск...",
        "history": "История",
        "name": "Название",
        "quiz_name": "Название Опроса",
        "author_name": "Автор",
        "student_name": "Имя Студента",
        "quiz_result": "Результат",
        "solving": "Проходится",
        "correct_answers": "Правильных ответов",
        "result_for": "Результаты для",
        "of": "из",
        "out_of": "из",
        "by": "от",
        "error_no_questions": "Опросник должен сождержать как минимум один вопрос",
        "error_no_quiz_name": "Необходимо ввести название опросника",
        "error_no_question_text": "Текст вопроса не может быть пуст",
        "error_not_enough_answers": "Вопрос должен иметь как минимум 2 варианта ответа",
        "error_question_too_many_answers": "Вопрос не может иметь несколько вариантов ответов",
        "error_question_no_answers": "Вопрос должен иметь выбранный ответ",
        "error_no_answer_text": "Ответ не может быть пустым",
        "error_wrong_data": "Получен неверный формат данных, должен быть словарь вопросов",
        "error_no_username": "Имя не может быть пустым",
        "error_no_password": "Пароль не может быть пустым",
        "error_username_is_taken": "Пользователь '{username}' уже зарегистрирован",
        "error_incorrect_username": "Неверное имя пользователя",
        "error_incorrect_password": "Неверный пароль",
        "error_no_answer_id": "Вариант ответа с id={answer_id} не существует",
        "error_no_question_id": "Вопроса с id={question_id} не существует",
        "error_no_quiz_id": "Опроса с id={quiz_id} не существует"
    },
    "en": {
        "username": "Username",
        "password": "Password",
        "create_account": "Create an Account",
        "log_in_form": "Log In",
        "register_form": "Register",
        "log_in": "Log In",
        "create_new": "Create new",
        "edit": "Edit",
        "delete": "Delete",
        "solve": "Solve",
        "new_quiz": "Новый опрос",
        "register": "Register",
        "log_out": "Log Out",
        "close": "Close",
        "save": "Save",
        "submit": "Сохранить",
        "remove": "Remove",
        "question_text": "Question",
        "answer_option": "Answer option #",
        "add_question": "Add question",
        "search": "Search....",
        "history": "History",
        "name": "Name",
        "quiz_name": "Quiz Name",
        "author_name": "Author Name",
        "student_name": "Student Name",
        "quiz_result": "Result",
        "solving": "Solving",
        "correct_answers": "Correct answers",
        "result_for": "Result for",
        "of": "of",
        "out_of": "out of",
        "by": "by",
        "error_no_questions": "Quiz should contain at least one question",
        "error_no_quiz_name": "Quiz name is required",
        "error_no_question_text": "Question text is required",
        "error_not_enough_answers": "Question should contain at lease 2 options to answer",
        "error_question_too_many_answers": "Question shouldn't contain more than one answer",
        "error_question_no_answers": "Question should contain at least one answer",
        "error_no_answer_text": "Answer text is required",
        "error_wrong_data": "Got wrong data, should be dict of questions",
        "error_no_username": "Username is required",
        "error_no_password": "Password is required",
        "error_username_is_taken": "User '{username}' is already registered",
        "error_incorrect_username": "Incorrect username",
        "error_incorrect_password": "Incorrect password",
        "error_no_answer_id": "Answer with id={answer_id} does not exist",
        "error_no_question_id": "Question with id={question_id} does not exist",
        "error_no_quiz_id": "Quiz with id={quiz_id} does not exist"
    }
}
