# Test code sampled from https://flask.palletsprojects.com/en/2.2.x/tutorial/tests/

import pytest
from flaskr.db import get_db
from furl import furl


def test_index(client, auth):
    response = client.get('/')
    assert response.location == "/login"

    auth.login()
    response = client.get('/')
    assert b'Kanban Board' in response.data
    assert b'Log Out' in response.data
    assert b'test' in response.data
    assert b'test&#39;s Personal Board' in response.data

@pytest.mark.parametrize('path', (
    '/',
    '/rename-board',
    '/add-user',
    '/remove-user',
))
def test_access_required(app, client, auth, path):
    # change the board member to another user
    with app.app_context():
        db = get_db()
        db.execute('UPDATE user_board SET user_id = 3 WHERE board_id = 1 AND user_id = 1')
        db.execute('UPDATE board SET admin_id = 3 WHERE id = 1 AND admin_id = 1')
        db.commit()

    auth.login()
    
    if path == '/':
        response = client.get(path + '?board_id=1')
        assert furl(response.location).args["error"] == "403"
        
        response = client.get(path + '?board_id=2')
        assert furl(response.location).args["error"] == "403"
    else:
        # current user can't modify or leave another user's board
        data = {'board_name': 'test #2', "username": "three", "remove_user_id": 2}
        response = client.post(path + '?board_id=1', data=data)
        assert furl(response.location).args["error"] == "403"

        with app.app_context():
            db = get_db()
            board = db.execute('SELECT * FROM board WHERE id = 1').fetchone()
            assert board['name'] == "test's Personal Board"
            board_users = db.execute('SELECT * FROM user_board WHERE board_id = 1 ORDER BY user_id').fetchall()
            assert len(board_users) == 2
            assert board_users[0]['user_id'] == 2
            assert board_users[1]['user_id'] == 3


@pytest.mark.parametrize('path', (
    '/rename-board',
    '/leave-board',
))
def test_exists_required(client, auth, path):
    auth.login()
    response = client.post(path, query_string={"board_id": "10"}, data={"board_name": "test #2"})
    assert furl(response.location).args["error"] == "404"

def test_create(client, auth, app):
    auth.login()
    response = client.post('/create-board?group=to%sdo', data={'name': 'created'})
    assert response.location == "/?board_id=6"
    assert "error" not in furl(response.location).args

    with app.app_context():
        db = get_db()
        count = db.execute('SELECT COUNT(id) FROM board').fetchone()[0]
        assert count == 6

def test_create_invalid(client, auth, app):
    auth.login()
    response = client.post("/create-board", data={'name': ''})
    assert furl(response.location).args["error"] == "400"

    with app.app_context():
        db = get_db()
        count = db.execute('SELECT COUNT(id) FROM board').fetchone()[0]
        assert count == 5

def test_rename(client, auth, app):
    auth.login()
    response = client.post('/rename-board?board_id=1', data={'board_name': 'updated'})
    assert response.location == "/?board_id=1"
    assert "error" not in furl(response.location).args

    with app.app_context():
        db = get_db()
        board = db.execute('SELECT * FROM board WHERE id = 1').fetchone()
        assert board['name'] == 'updated'

def test_rename_invalid(client, auth, app):
    auth.login()
    response = client.post('/rename-board', data={'board_name': 'updated'})
    assert furl(response.location).args["error"] == "400"

    response = client.post('/rename-board?board_id=1', data={'board_name': ''})
    assert furl(response.location).args["board_id"] == "1"
    assert furl(response.location).args["error"] == "400"

    with app.app_context():
        db = get_db()
        board = db.execute('SELECT * FROM board WHERE id = 1').fetchone()
        assert board['name'] == "test's Personal Board"

def test_leave(client, auth, app):
    auth.login()
    response = client.post('/leave-board', query_string={"board_id": "4"})
    assert response.location == "/"
    assert "error" not in furl(response.location).args

    with app.app_context():
        db = get_db()
        board = db.execute('SELECT * FROM user_board WHERE board_id = 4 AND user_id = 1').fetchone()
        assert board is None

def test_leave_invalid(client, auth, app):
    auth.login()
    response = client.post('/leave-board')
    assert furl(response.location).args["error"] == "400"

    response = client.post('/leave-board?board_id=1')
    assert furl(response.location).args["board_id"] == "1"
    assert furl(response.location).args["error"] == "403"

    with app.app_context():
        db = get_db()
        board = db.execute('SELECT * FROM user_board WHERE board_id = 1 AND user_id = 1').fetchone()
        assert board is not None

def test_empty_board_invalid(client, auth, app):
    auth.login()

    response = client.post('/leave-board?board_id=5')
    assert response.location == "/"
    assert "error" not in furl(response.location).args

    with app.app_context():
        db = get_db()
        board = db.execute('SELECT * FROM board WHERE id = 5').fetchone()
        assert board is None
        tasks = db.execute('SELECT * FROM task WHERE board_id = 5').fetchone()
        assert tasks is None
        board_users = db.execute('SELECT * FROM user_board WHERE board_id = 5').fetchone()
        assert board_users is None

def test_add_user(client, auth, app):
    auth.login()
    response = client.post('/add-user?board_id=1', data={'username': 'three'})
    assert response.location == "/?board_id=1"
    assert "error" not in furl(response.location).args

    with app.app_context():
        db = get_db()
        board_users = db.execute('SELECT * FROM user_board WHERE board_id = 1 ORDER BY user_id').fetchall()
        assert len(board_users) == 3
        assert board_users[0]['user_id'] == 1
        assert board_users[1]['user_id'] == 2
        assert board_users[2]['user_id'] == 3

def test_add_user_invalid(client, auth, app):
    auth.login()
    response = client.post('/add-user', data={'username': 'three'})
    assert furl(response.location).args["error"] == "400"

    response = client.post('/add-user?board_id=1', data={'username': ''})
    assert furl(response.location).args["board_id"] == "1"
    assert furl(response.location).args["error"] == "400"

    response = client.post('/add-user?board_id=1', data={'username': 'one'})
    assert furl(response.location).args["board_id"] == "1"
    assert furl(response.location).args["error"] == "404"

    response = client.post('/add-user?board_id=1', data={'username': 'test'})
    assert furl(response.location).args["board_id"] == "1"
    assert furl(response.location).args["error"] == "400"

    response = client.post('/add-user?board_id=1', data={'username': 'other'})
    assert furl(response.location).args["board_id"] == "1"
    assert furl(response.location).args["error"] == "400"

    with app.app_context():
        db = get_db()
        board_users = db.execute('SELECT * FROM user_board WHERE board_id = 1 ORDER BY user_id').fetchall()
        assert len(board_users) == 2
        assert board_users[0]['user_id'] == 1
        assert board_users[1]['user_id'] == 2

def test_remove_user(client, auth, app):
    auth.login()
    response = client.post('/remove-user?board_id=1', data={'remove_user_id': 2})
    assert response.location == "/?board_id=1"
    assert "error" not in furl(response.location).args

    with app.app_context():
        db = get_db()
        board_users = db.execute('SELECT * FROM user_board WHERE board_id = 1 ORDER BY user_id').fetchall()
        assert len(board_users) == 1
        assert board_users[0]['user_id'] == 1

def test_remove_user_invalid(client, auth, app):
    auth.login()
    response = client.post('/remove-user', data={'remove_user_id': 2})
    assert furl(response.location).args["error"] == "400"

    response = client.post('/remove-user?board_id=1', data={'remove_user_id': ''})
    assert furl(response.location).args["board_id"] == "1"
    assert furl(response.location).args["error"] == "400"

    response = client.post('/remove-user?board_id=10', data={'remove_user_id': 2})
    assert furl(response.location).args["error"] == "404"

    response = client.post('/remove-user?board_id=1', data={'remove_user_id': 1})
    assert furl(response.location).args["board_id"] == "1"
    assert furl(response.location).args["error"] == "400"

    with app.app_context():
        db = get_db()
        board_users = db.execute('SELECT * FROM user_board WHERE board_id = 1 ORDER BY user_id').fetchall()
        assert len(board_users) == 2
        assert board_users[0]['user_id'] == 1
        assert board_users[1]['user_id'] == 2