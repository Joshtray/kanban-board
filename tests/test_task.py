# Test code sampled from https://flask.palletsprojects.com/en/2.2.x/tutorial/tests/
import pytest
from flaskr.db import get_db
from furl import furl

@pytest.mark.parametrize(('path'), 
    ('/create-task',
    '/update-task',
    '/delete-task'),
)
def test_exists_required(client, auth, path):
    auth.login()
    response = client.post(path, query_string={'board_id': 10, 'id': 1, 'group': 'to do'}, data={'task': 'test task', 'assignees': 'test, other, three', 'group': 'to do'})
    assert furl(response.location).args["error"]  == "404"

    if path != '/create-task':
        response = client.post(path, query_string={'board_id': 1, 'id': 1, 'group': 'to do'}, data={'task': 'test task', 'assignees': 'test, other, three', 'group': 'to do'})
        assert furl(response.location).args["error"]  == "404"

@pytest.mark.parametrize(('path'), 
    ('/create-task',
    '/update-task',
    '/delete-task'),
)
def test_access_required(client, auth, app, path):
    auth.login()
    
    with app.app_context():
        get_db().execute('INSERT INTO task (priority_group, task, assignees, board_id) VALUES ("TO DO", "test task", "test, other, three", 2)')
        get_db().commit()


    response = client.post( path, query_string={'board_id': 2, 'id': 1, 'group':"doing"}, data={'task': 'test task', 'assignees': 'test, other, three', 'group': 'doing'})
    assert furl(response.location).args["error"]  == "403"

def test_create_task(client, auth, app):
    auth.login()
    with app.app_context():
        db = get_db()
        count = db.execute('SELECT COUNT(id) FROM task WHERE board_id = 1').fetchone()[0]
        assert count == 0

    response = client.post('/create-task', query_string={'board_id': 1, 'group': 'to do'}, data={'task': 'test task', 'assignees': 'test, other, three'})
    assert response.location == "/?board_id=1"

    with app.app_context():
        db = get_db()
        count = db.execute('SELECT COUNT(id) FROM task WHERE board_id = 1').fetchone()[0]
        assert count == 1

    response = client.post('/create-task', query_string={"board_id": 1, "group": "done"}, 
        data={'task': 'test task #2', 'assignees': 'test, other, three'})
    assert response.location == "/?board_id=1"

    with app.app_context():
        db = get_db()
        tasks = db.execute('SELECT * FROM task WHERE board_id = 1 ORDER BY id').fetchall()
        assert len(tasks) == 2
        assert tasks[0]['task'] == 'test task'
        assert tasks[0]['priority_group'].lower() == 'to do'
        assert tasks[1]['task'] == 'test task #2'
        assert tasks[1]['priority_group'].lower() == 'done'

def test_create_task_invalid(client, auth, app):
    auth.login()
    with app.app_context():
        db = get_db()
        count = db.execute('SELECT COUNT(id) FROM task WHERE board_id = 1').fetchone()[0]
        assert count == 0

    response = client.post('/create-task', query_string={"group": "to do"}, data={'task': 'test task', 'assignees': 'test, other, three'})
    assert furl(response.location).args["error"]  == "400"

    response = client.post('/create-task', query_string={"board_id": 1, "group": "to do"}, data={'task': '', 'assignees': 'test, other, three', 'group': 'to do'})
    assert furl(response.location).args["board_id"] == "1"
    assert furl(response.location).args["error"]  == "400"

    response = client.post('/create-task', query_string={"board_id": 1, "group": "invalid"}, data={'task': 'test task', 'assignees': 'test, other, three', 'group': 'invalid'})
    assert furl(response.location).args["board_id"] == "1"
    assert furl(response.location).args["error"]  == "400"

    response = client.post('/create-task', query_string={"board_id": 1, "group": ""}, data={'task': 'test task', 'assignees': 'test, other, three'})
    assert furl(response.location).args["board_id"] == "1"
    assert furl(response.location).args["error"]  == "400"


    with app.app_context():
        db = get_db()
        count = db.execute('SELECT COUNT(id) FROM task WHERE board_id = 1').fetchone()[0]
        assert count == 0

def test_update_task(client, auth, app):
    auth.login()
    with app.app_context():
        db = get_db()
        db.execute('INSERT INTO task (priority_group, task, assignees, board_id) VALUES ("TO DO", "test task", "test, other, three", 1)')
        db.commit()
        count = db.execute('SELECT COUNT(id) FROM task WHERE board_id = 1').fetchone()[0]
        assert count == 1

    response = client.post('/update-task', query_string={"board_id": 1, "id": 1}, data={'task': 'test task', 'assignees': 'test, other, three', 'group': 'doing'})
    assert response.location == "/?board_id=1"

    with app.app_context():
        db = get_db()
        tasks = db.execute('SELECT * FROM task WHERE board_id = 1 ORDER BY id').fetchall()
        assert len(tasks) == 1
        assert tasks[0]['task'] == 'test task'
        assert tasks[0]['priority_group'].lower() == 'doing'
    

def test_update_task_invalid(client, auth, app):
    auth.login()
    with app.app_context():
        db = get_db()
        db.execute('INSERT INTO task (priority_group, task, assignees, board_id) VALUES ("TO DO", "test task", "test, other, three", 1)')
        db.commit()
        count = db.execute('SELECT COUNT(id) FROM task WHERE board_id = 1').fetchone()[0]
        assert count == 1

    response = client.post('/update-task', query_string={"id": 1}, data={'group': 'doing'})
    assert furl(response.location).args["error"]  == "400"

    response = client.post('/update-task', query_string={"board_id": 1}, data={'group': 'doing'})
    assert furl(response.location).args["board_id"] == "1"
    assert furl(response.location).args["error"]  == "400"

    response = client.post('/update-task', query_string={"board_id": 1, "id": 1}, data={'group': 'invalid'})
    assert furl(response.location).args["board_id"] == "1"
    assert furl(response.location).args["error"]  == "400"

    response = client.post('/update-task', query_string={"board_id": 1, "id": 1}, data={'group': ''})
    assert furl(response.location).args["board_id"] == "1"
    assert furl(response.location).args["error"]  == "400"

    with app.app_context():
        db = get_db()
        tasks = db.execute('SELECT * FROM task WHERE board_id = 1 ORDER BY id').fetchall()
        assert len(tasks) == 1
        assert tasks[0]['task'] == 'test task'
        assert tasks[0]['priority_group'].lower() == 'to do'

def test_delete_task(client, auth, app):
    auth.login()
    with app.app_context():
        db = get_db()
        db.execute('INSERT INTO task (priority_group, task, assignees, board_id) VALUES ("TO DO", "test task", "test, other, three", 1)')
        db.commit()
        count = db.execute('SELECT COUNT(id) FROM task WHERE board_id = 1').fetchone()[0]
        assert count == 1

    response = client.post('/delete-task', query_string={"board_id": 1, "id": 1})
    assert response.location == "/?board_id=1"

    with app.app_context():
        db = get_db()
        count = db.execute('SELECT COUNT(id) FROM task WHERE board_id = 1').fetchone()[0]
        assert count == 0

def test_delete_task_invalid(client, auth, app):
    auth.login()
    with app.app_context():
        db = get_db()
        db.execute('INSERT INTO task (priority_group, task, assignees, board_id) VALUES ("TO DO", "test task", "test, other, three", 1)')
        db.commit()
        count = db.execute('SELECT COUNT(id) FROM task WHERE board_id = 1').fetchone()[0]
        assert count == 1

    response = client.post('/delete-task', query_string={"id": 1})
    assert furl(response.location).args["error"]  == "400"

    response = client.post('/delete-task', query_string={"board_id": 1})
    assert furl(response.location).args["board_id"] == "1"
    assert furl(response.location).args["error"]  == "400"

    with app.app_context():
        db = get_db()
        count = db.execute('SELECT COUNT(id) FROM task WHERE board_id = 1').fetchone()[0]
        assert count == 1