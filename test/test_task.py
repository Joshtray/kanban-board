# Test code sampled from https://flask.palletsprojects.com/en/2.2.x/tutorial/tests/
import os
import tempfile

from flaskr.db import get_db
from furl import furl
from app import create_app
import unittest
from flaskr.db import get_db, init_db

class AuthActions(object):
    def __init__(self, client):
        self._client = client

    def login(self, username='test', password='test'):
        return self._client.post(
            '/login',
            data={'username': username, 'password': password}
        )

    def logout(self):
        return self._client.get('/logout')

class TestTask(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        with open(os.path.join(os.path.dirname(__file__), 'data.sql'), 'rb') as f:
            self._data_sql = f.read().decode('utf8')
        return super().__init__(*args, **kwargs)

    def _open(self):
        self.db_fd, self.db_path = tempfile.mkstemp()

        self.app = create_app({
            'TESTING': True,
            'DATABASE': self.db_path,
        })
        with self.app.app_context():
            init_db()
            get_db().executescript(self._data_sql)

        self.client = self.app.test_client()
        self.auth = AuthActions(self.client)
    
    def _close(self):
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_exists_required(self):
        for path in ['/create-task', '/update-task', '/delete-task']:
            self._open()
            auth = self.auth
            app = self.app
            client = self.client
            auth.login()
            response = client.post(path, query_string={'board_id': 10, 'id': 1, 'group': 'to do'}, data={'task': 'test task', 'assignees': 'test, other, three', 'group': 'to do'})
            self.assertEqual(furl(response.location).args["error"], "404")

            if path != '/create-task':
                response = client.post(path, query_string={'board_id': 1, 'id': 1, 'group': 'to do'}, data={'task': 'test task', 'assignees': 'test, other, three', 'group': 'to do'})
                self.assertEqual(furl(response.location).args["error"], "404")
            self._close()

    def test_access_required(self):
        for path in ['/create-task', '/update-task', '/delete-task']:
            self._open()
            auth = self.auth
            app = self.app
            client = self.client

            auth.login()
            
            with app.app_context():
                get_db().execute('INSERT INTO task (priority_group, task, assignees, board_id) VALUES ("TO DO", "test task", "test, other, three", 2)')
                get_db().commit()


            response = client.post( path, query_string={'board_id': 2, 'id': 1, 'group':"doing"}, data={'task': 'test task', 'assignees': 'test, other, three', 'group': 'doing'})
            self.assertEqual(furl(response.location).args["error"], "403")

    def test_create_task(self):
        self._open()
        auth = self.auth
        app = self.app
        client = self.client

        auth.login()
        with app.app_context():
            db = get_db()
            count = db.execute('SELECT COUNT(id) FROM task WHERE board_id = 1').fetchone()[0]
            self.assertEqual(count, 0)

        response = client.post('/create-task', query_string={'board_id': 1, 'group': 'to do'}, data={'task': 'test task', 'assignees': 'test, other, three'})
        self.assertEqual(response.location, "/?board_id=1")

        with app.app_context():
            db = get_db()
            count = db.execute('SELECT COUNT(id) FROM task WHERE board_id = 1').fetchone()[0]
            self.assertEqual(count, 1)

        response = client.post('/create-task', query_string={"board_id": 1, "group": "done"}, 
            data={'task': 'test task #2', 'assignees': 'test, other, three'})
        self.assertEqual(response.location, "/?board_id=1")

        with app.app_context():
            db = get_db()
            tasks = db.execute('SELECT * FROM task WHERE board_id = 1 ORDER BY id').fetchall()
            self.assertEqual(len(tasks), 2)
            self.assertEqual(tasks[0]['task'], 'test task')
            self.assertEqual(tasks[0]['priority_group'].lower(), 'to do')
            self.assertEqual(tasks[1]['task'], 'test task #2')
            self.assertEqual(tasks[1]['priority_group'].lower(), 'done')
        self._close()

    def test_create_task_invalid(self):
        self._open()
        auth = self.auth
        app = self.app
        client = self.client

        auth.login()
        with app.app_context():
            db = get_db()
            count = db.execute('SELECT COUNT(id) FROM task WHERE board_id = 1').fetchone()[0]
            self.assertEqual(count, 0)

        response = client.post('/create-task', query_string={"group": "to do"}, data={'task': 'test task', 'assignees': 'test, other, three'})
        self.assertEqual(furl(response.location).args["error"], "400")

        response = client.post('/create-task', query_string={"board_id": 1, "group": "to do"}, data={'task': '', 'assignees': 'test, other, three', 'group': 'to do'})
        self.assertEqual(furl(response.location).args["board_id"], "1")
        self.assertEqual(furl(response.location).args["error"], "400")

        response = client.post('/create-task', query_string={"board_id": 1, "group": "invalid"}, data={'task': 'test task', 'assignees': 'test, other, three', 'group': 'invalid'})
        self.assertEqual(furl(response.location).args["board_id"], "1")
        self.assertEqual(furl(response.location).args["error"], "400")

        response = client.post('/create-task', query_string={"board_id": 1, "group": ""}, data={'task': 'test task', 'assignees': 'test, other, three'})
        self.assertEqual(furl(response.location).args["board_id"], "1")
        self.assertEqual(furl(response.location).args["error"], "400")


        with app.app_context():
            db = get_db()
            count = db.execute('SELECT COUNT(id) FROM task WHERE board_id = 1').fetchone()[0]
            self.assertEqual(count, 0)
        
        self._close()

    def test_update_task(self):
        self._open()
        auth = self.auth
        app = self.app
        client = self.client

        auth.login()
        with app.app_context():
            db = get_db()
            db.execute('INSERT INTO task (priority_group, task, assignees, board_id) VALUES ("TO DO", "test task", "test, other, three", 1)')
            db.commit()
            count = db.execute('SELECT COUNT(id) FROM task WHERE board_id = 1').fetchone()[0]
            self.assertEqual(count, 1)

        response = client.post('/update-task', query_string={"board_id": 1, "id": 1}, data={'task': 'test task', 'assignees': 'test, other, three', 'group': 'doing'})
        self.assertEqual(response.location, "/?board_id=1")

        with app.app_context():
            db = get_db()
            tasks = db.execute('SELECT * FROM task WHERE board_id = 1 ORDER BY id').fetchall()
            self.assertEqual(len(tasks), 1)
            self.assertEqual(tasks[0]['task'], 'test task')
            self.assertEqual(tasks[0]['priority_group'].lower(), 'doing')
        
        self._close()
        

    def test_update_task_invalid(self):
        self._open()
        auth = self.auth
        app = self.app
        client = self.client

        auth.login()
        with app.app_context():
            db = get_db()
            db.execute('INSERT INTO task (priority_group, task, assignees, board_id) VALUES ("TO DO", "test task", "test, other, three", 1)')
            db.commit()
            count = db.execute('SELECT COUNT(id) FROM task WHERE board_id = 1').fetchone()[0]
            self.assertEqual(count, 1)

        response = client.post('/update-task', query_string={"id": 1}, data={'group': 'doing'})
        self.assertEqual(furl(response.location).args["error"], "400")

        response = client.post('/update-task', query_string={"board_id": 1}, data={'group': 'doing'})
        self.assertEqual(furl(response.location).args["board_id"], "1")
        self.assertEqual(furl(response.location).args["error"], "400")

        response = client.post('/update-task', query_string={"board_id": 1, "id": 1}, data={'group': 'invalid'})
        self.assertEqual(furl(response.location).args["board_id"], "1")
        self.assertEqual(furl(response.location).args["error"], "400")

        response = client.post('/update-task', query_string={"board_id": 1, "id": 1}, data={'group': ''})
        self.assertEqual(furl(response.location).args["board_id"], "1")
        self.assertEqual(furl(response.location).args["error"], "400")

        with app.app_context():
            db = get_db()
            tasks = db.execute('SELECT * FROM task WHERE board_id = 1 ORDER BY id').fetchall()
            self.assertEqual(len(tasks), 1)
            self.assertEqual(tasks[0]['task'], 'test task')
            self.assertEqual(tasks[0]['priority_group'].lower(), 'to do')
        
        self._close()

    def test_delete_task(self):
        self._open()
        auth = self.auth
        app = self.app
        client = self.client

        auth.login()
        with app.app_context():
            db = get_db()
            db.execute('INSERT INTO task (priority_group, task, assignees, board_id) VALUES ("TO DO", "test task", "test, other, three", 1)')
            db.commit()
            count = db.execute('SELECT COUNT(id) FROM task WHERE board_id = 1').fetchone()[0]
            self.assertEqual(count, 1)

        response = client.post('/delete-task', query_string={"board_id": 1, "id": 1})
        self.assertEqual(response.location, "/?board_id=1")

        with app.app_context():
            db = get_db()
            count = db.execute('SELECT COUNT(id) FROM task WHERE board_id = 1').fetchone()[0]
            self.assertEqual(count, 0)

        self._close()

    def test_delete_task_invalid(self):
        self._open()
        auth = self.auth
        app = self.app
        client = self.client

        auth.login()
        with app.app_context():
            db = get_db()
            db.execute('INSERT INTO task (priority_group, task, assignees, board_id) VALUES ("TO DO", "test task", "test, other, three", 1)')
            db.commit()
            count = db.execute('SELECT COUNT(id) FROM task WHERE board_id = 1').fetchone()[0]
            self.assertEqual(count, 1)

        response = client.post('/delete-task', query_string={"id": 1})
        self.assertEqual(furl(response.location).args["error"], "400")

        response = client.post('/delete-task', query_string={"board_id": 1})
        self.assertEqual(furl(response.location).args["board_id"], "1")
        self.assertEqual(furl(response.location).args["error"], "400")

        with app.app_context():
            db = get_db()
            count = db.execute('SELECT COUNT(id) FROM task WHERE board_id = 1').fetchone()[0]
            self.assertEqual(count, 1)

        self._close()