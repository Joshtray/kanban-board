# Test code sampled from https://flask.palletsprojects.com/en/2.2.x/tutorial/tests/

import pytest
from flaskr.db import get_db


def test_index(client, auth):
    response = client.get('/')
    assert b"Log In" in response.data
    assert b"Register" in response.data

    auth.login()
    response = client.get('/')
    assert b'Kanban Board' in response.data
    assert b'Log Out' in response.data
    assert b'test\'s Board' in response.data 
    # assert b'test title' in response.data
    # assert b'by test on 2018-01-01' in response.data
    # assert b'test\nbody' in response.data
    # assert b'href="/1/update"' in response.data

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
    assert response.headers["Location"] == "/login"


def test_access_required(app, client, auth):
    # change the board member to another user
    with app.app_context():
        db = get_db()
        db.execute('UPDATE board SET admin_id = 2 WHERE id = 1')
        db.execute('UPDATE user_board SET user_id = 2 WHERE board_id = 1')
        db.commit()

    auth.login()
    # current user can't modify or leave another user's board
    assert client.post('/rename-board?board_id=1').status_code == 403
    assert client.post('/leave-board?board_id=1?board_name=').status_code == 403
    # current user doesn't see edit link
    assert b'"/update-task?id=1&board_id=1"' not in client.get('/').data
    assert b'"update-task?id=1&board_id=1"' not in client.get('/').data
    assert b'"/delete-task?id=1&board_id=1"' not in client.get('/').data


@pytest.mark.parametrize('path', (
    '/update-task?id=2&board_id=1',
    '/delete-task?id=2&board_id=1',
))
def test_exists_required(client, auth, path):
    auth.login()
    assert client.post(path).status_code == 404

def test_create(client, auth, app):
    auth.login()
    client.post('/create-task', data={'title': 'created', 'body': ''})

    with app.app_context():
        db = get_db()
        count = db.execute('SELECT COUNT(id) FROM post').fetchone()[0]
        assert count == 2


def test_update(client, auth, app):
    auth.login()
    assert client.get('/1/update').status_code == 200
    client.post('/1/update', data={'title': 'updated', 'body': ''})

    with app.app_context():
        db = get_db()
        post = db.execute('SELECT * FROM post WHERE id = 1').fetchone()
        assert post['title'] == 'updated'


@pytest.mark.parametrize('path', (
    '/create',
    '/1/update',
))
def test_create_update_validate(client, auth, path):
    auth.login()
    response = client.post(path, data={'title': '', 'body': ''})
    assert b'Title is required.' in response.data