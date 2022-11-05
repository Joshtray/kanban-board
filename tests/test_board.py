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
    assert client.post('/leave-board?board_id=1').status_code == 403
    assert client.post('/add-user?board_id=1').status_code == 403
    assert client.post('/remove-user?board_id=1').status_code == 403


@pytest.mark.parametrize('path', (
    '/rename-board?board_id=2',
    '/leave-board?board_id=2',
))
def test_exists_required(client, auth, path):
    auth.login()
    assert client.post(path).status_code == 404

def test_create(client, auth, app):
    auth.login()
    client.post('/create-board', data={'name': 'created'})

    with app.app_context():
        db = get_db()
        count = db.execute('SELECT COUNT(id) FROM board').fetchone()[0]
        assert count == 2


def test_update(client, auth, app):
    auth.login()
    client.post('/rename-board?board_id=1', data={'board_name': 'updated'})

    with app.app_context():
        db = get_db()
        board = db.execute('SELECT * FROM board WHERE id = 1').fetchone()
        assert board['title'] == 'updated'


@pytest.mark.parametrize('path', (
    '/create-board',
    '/rename-board?board_id=1',
))
def test_create_update_validate(client, auth, path):
    auth.login()
    response = client.post(path, data={'name': '', 'board_name': ''})
    assert b'Board name is required.' in response.data

def test_delete(client, auth, app):
    auth.login()
    response = client.post('/leave-board?board_id=1', data={'board_name': 'task\'s Personal Board'})
    assert response.headers["Location"] == "/"
    assert b'Successfully left task\'s Personal Board' in response.data

    with app.app_context():
        db = get_db()
        board = db.execute('SELECT * FROM board WHERE id = 1').fetchone()
        assert board is None