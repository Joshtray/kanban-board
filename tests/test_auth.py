# Test code sampled from https://flask.palletsprojects.com/en/2.2.x/tutorial/tests/
import pytest
from flask import g, get_flashed_messages, session
from flaskr.db import get_db


def test_register(client, app):
    assert client.get('/register').status_code == 200

    response = client.post(
        '/register', data={'username': 'a', 'password': 'a'}
    )
    assert response.headers["Location"] == "/login"

    with app.app_context():
        assert get_db().execute(
            "SELECT * FROM user WHERE username = 'a'",
        ).fetchone() is not None


@pytest.mark.parametrize(('username', 'password', 'message'), (
    ('', '', b'Username is required.'),
    ('a', '', b'Password is required.'),
    ('test', 'test', b'is already taken.'),
))
def test_register_validate_input(client, username, password, message):
    response = client.post(
        '/register',
        data={'username': username, 'password': password}
    )
    assert message in response.data

def test_login(client, auth):
    assert client.get('/login').status_code == 200

    response = auth.login()
    assert response.headers["Location"] == "/"

    with client:
        client.get('/')
        assert session['user_id'] == 1
        assert g.user['username'] == 'test'


@pytest.mark.parametrize(('username', 'password', 'message'), (
    ('a', 'test', b'Incorrect username.'),
    ('test', 'a', b'Incorrect password.'),
))
def test_login_validate_input(auth, username, password, message):
    response = auth.login(username, password)
    assert message in response.data

@pytest.mark.parametrize('path', (
    '/create-board',
    '/rename-board',
    '/leave-board',
    '/add-user',
    '/remove-user',
    '/create-task',
    '/update-task',
    '/delete-task',
))
def test_login_required(client, path):
    response = client.post(path)
    assert response.location == "/login"

def test_logout(client, auth):
    auth.login()

    with client:
        auth.logout()
        assert 'user_id' not in session