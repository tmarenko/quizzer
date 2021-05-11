import os
import sys

from flask import Flask


def create_app(test_config=None):
    """Create and configure an instance of the Flask application.

    :param test_config: configuration for Flask app.
    :return: Flask app.
    """
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="dev",
        DATABASE=os.path.join(app.instance_path, "quizzer.sqlite"),
    )

    if test_config is None:
        app.config.from_pyfile("config.py", silent=True)
    else:
        app.config.update(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from quizzer import db

    db.init_app(app)

    from quizzer import auth, quizzes

    app.register_blueprint(auth.bp)
    app.register_blueprint(quizzes.bp)
    app.add_url_rule("/", endpoint="index")

    from quizzer.localization import locale
    app.jinja_env.globals['get_locale'] = locale

    return app
