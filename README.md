# Quizzer

Simple web application on Flask that allows you to create, edit and solve quizzes

## Installation
1) Download source code
2) Run `pip install .`

## Usage
From Python:
1) `pip install waitress`
2) `waitress-serve --call 'quizzer:create_app'`

From Docker:
1) `docker build -t quizzer .`
2) `docker run -p 5000:5000 -v "%CD%/instance:/app/instance" quizzer`