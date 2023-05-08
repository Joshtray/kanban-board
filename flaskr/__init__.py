# Test code sampled from https://flask.palletsprojects.com/en/2.2.x/tutorial/tests/
import os

from flask import Flask
from flaskr import db
from flaskr import auth
from flaskr import kanban


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    print(app.instance_path)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.environ.get('DATABASE_URL'),
    )


    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    db.init_app(app)

    app.register_blueprint(auth.bp)
    
    app.register_blueprint(kanban.bp)
    app.add_url_rule('/', endpoint='index')

    return app  