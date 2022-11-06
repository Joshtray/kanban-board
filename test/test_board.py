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

class TestBoard(unittest.TestCase):
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


    def test_index(self):
        self._open()
        response = self.client.get('/')
        assert response.location == "/login"

        self.auth.login()
        response = self.client.get('/')
        self.assertIn(b'Kanban Board', response.data)
        self.assertIn(b'Log Out', response.data)
        self.assertIn(b'test', response.data)
        self.assertIn(b'test&#39;s Personal Board', response.data)
        self._close()

    def test_access_required(self):
        for path in ['/', '/rename-board', '/add-user', '/remove-user']:
            self._open()
            app = self.app
            auth = self.auth
            client = self.client
            # change the board member to another user
            with app.app_context():
                db = get_db()
                db.execute('UPDATE user_board SET user_id = 3 WHERE board_id = 1 AND user_id = 1')
                db.execute('UPDATE board SET admin_id = 3 WHERE id = 1 AND admin_id = 1')
                db.commit()

            auth.login()
            
            if path == '/':
                response = client.get(path + '?board_id=1')
                self.assertEqual(furl(response.location).args["error"], "403")
                
                response = client.get(path + '?board_id=2')
                self.assertEqual(furl(response.location).args["error"], "403")
            else:
                # current user can't modify or leave another user's board
                data = {'board_name': 'test #2', "username": "three", "remove_user_id": 2}
                response = client.post(path + '?board_id=1', data=data)
                self.assertEqual(furl(response.location).args["error"], "403")

                with app.app_context():
                    db = get_db()
                    board = db.execute('SELECT * FROM board WHERE id = 1').fetchone()
                    self.assertEqual(board['name'], "test's Personal Board")
                    board_users = db.execute('SELECT * FROM user_board WHERE board_id = 1 ORDER BY user_id').fetchall()
                    self.assertEqual(len(board_users), 2)
                    self.assertEqual(board_users[0]['user_id'], 2)
                    self.assertEqual(board_users[1]['user_id'], 3)
            self._close()

    
    def test_exists_required(self):
        for path in ['/rename-board', '/leave-board']:
            self._open()
            auth = self.auth
            client = self.client
            app = self.app
            auth.login()
            response = client.post(path, query_string={"board_id": "10"}, data={"board_name": "test #2"})
            self.assertEqual(furl(response.location).args["error"], "404")
            self._close()

    def test_create(self):
        self._open()
        auth = self.auth
        client = self.client
        app = self.app
        auth.login()
        response = client.post('/create-board?group=to%sdo', data={'name': 'created'})
        self.assertEqual(response.location, "/?board_id=6")
        self.assertNotIn("error", furl(response.location).args)

        with app.app_context():
            db = get_db()
            count = db.execute('SELECT COUNT(id) FROM board').fetchone()[0]
            self.assertEqual(count, 6)

        self._close()

    def test_create_invalid(self):
        self._open()
        auth = self.auth
        client = self.client
        app = self.app

        auth.login()
        response = client.post("/create-board", data={'name': ''})
        self.assertEqual(furl(response.location).args["error"], "400")

        with app.app_context():
            db = get_db()
            count = db.execute('SELECT COUNT(id) FROM board').fetchone()[0]
            self.assertEqual(count, 5)
        
        self._close()

    def test_rename(self):
        self._open()
        auth = self.auth
        client = self.client
        app = self.app

        auth.login()
        response = client.post('/rename-board?board_id=1', data={'board_name': 'updated'})
        self.assertEqual(response.location, "/?board_id=1")
        self.assertNotIn("error", furl(response.location).args)

        with app.app_context():
            db = get_db()
            board = db.execute('SELECT * FROM board WHERE id = 1').fetchone()
            self.assertEqual(board['name'], 'updated')
        self._close()

    def test_rename_invalid(self):
        self._open()
        auth = self.auth
        client = self.client
        app = self.app

        auth.login()
        response = client.post('/rename-board', data={'board_name': 'updated'})
        self.assertEqual(furl(response.location).args["error"], "400")

        response = client.post('/rename-board?board_id=1', data={'board_name': ''})
        self.assertEqual(furl(response.location).args["board_id"], "1")
        self.assertEqual(furl(response.location).args["error"], "400")

        with app.app_context():
            db = get_db()
            board = db.execute('SELECT * FROM board WHERE id = 1').fetchone()
            self.assertEqual(board['name'], "test's Personal Board")
        self._close()

    def test_leave(self):
        self._open()
        auth = self.auth
        client = self.client
        app = self.app

        auth.login()
        response = client.post('/leave-board', query_string={"board_id": "4"})
        self.assertEqual(response.location, "/")
        self.assertNotIn("error", furl(response.location).args)

        with app.app_context():
            db = get_db()
            board = db.execute('SELECT * FROM user_board WHERE board_id = 4 AND user_id = 1').fetchone()
            self.assertIsNone(board)
        self._close()

    def test_leave_invalid(self):
        self._open()
        auth = self.auth
        client = self.client
        app = self.app
        
        auth.login()
        response = client.post('/leave-board')
        self.assertEqual(furl(response.location).args["error"], "400")

        response = client.post('/leave-board?board_id=1')
        self.assertEqual(furl(response.location).args["board_id"], "1")
        self.assertEqual(furl(response.location).args["error"], "403")

        with app.app_context():
            db = get_db()
            board = db.execute('SELECT * FROM user_board WHERE board_id = 1 AND user_id = 1').fetchone()
            self.assertIsNotNone(board)
        self._close()

    def test_empty_board_invalid(self):
        self._open()
        auth = self.auth
        client = self.client
        app = self.app

        auth.login()

        response = client.post('/leave-board?board_id=5')
        self.assertEqual(response.location, "/")
        self.assertNotIn("error", furl(response.location).args)

        with app.app_context():
            db = get_db()
            board = db.execute('SELECT * FROM board WHERE id = 5').fetchone()
            self.assertIsNone(board)
            tasks = db.execute('SELECT * FROM task WHERE board_id = 5').fetchone()
            self.assertIsNone(tasks)
            board_users = db.execute('SELECT * FROM user_board WHERE board_id = 5').fetchone()
            self.assertIsNone(board_users)
        self._close()

    def test_add_user(self):
        self._open()
        auth = self.auth
        client = self.client
        app = self.app

        auth.login()
        response = client.post('/add-user?board_id=1', data={'username': 'three'})
        self.assertEqual(response.location, "/?board_id=1")
        self.assertNotIn("error", furl(response.location).args)

        with app.app_context():
            db = get_db()
            board_users = db.execute('SELECT * FROM user_board WHERE board_id = 1 ORDER BY user_id').fetchall()
            self.assertEqual(len(board_users), 3)
            self.assertEqual(board_users[0]['user_id'], 1)
            self.assertEqual(board_users[1]['user_id'], 2)
            self.assertEqual(board_users[2]['user_id'], 3)
        self._close()

    def test_add_user_invalid(self):
        self._open()
        auth = self.auth
        client = self.client
        app = self.app

        auth.login()
        response = client.post('/add-user', data={'username': 'three'})
        self.assertEqual(furl(response.location).args["error"], "400")

        response = client.post('/add-user?board_id=1', data={'username': ''})
        self.assertEqual(furl(response.location).args["board_id"], "1")
        self.assertEqual(furl(response.location).args["error"], "400")

        response = client.post('/add-user?board_id=1', data={'username': 'one'})
        self.assertEqual(furl(response.location).args["board_id"], "1")
        self.assertEqual(furl(response.location).args["error"], "404")

        response = client.post('/add-user?board_id=1', data={'username': 'test'})
        self.assertEqual(furl(response.location).args["board_id"], "1")
        self.assertEqual(furl(response.location).args["error"], "400")

        response = client.post('/add-user?board_id=1', data={'username': 'other'})
        self.assertEqual(furl(response.location).args["board_id"], "1")
        self.assertEqual(furl(response.location).args["error"], "400")

        with app.app_context():
            db = get_db()
            board_users = db.execute('SELECT * FROM user_board WHERE board_id = 1 ORDER BY user_id').fetchall()
            self.assertEqual(len(board_users), 2)
            self.assertEqual(board_users[1]['user_id'], 2)
            self.assertEqual(board_users[0]['user_id'], 1)
        
        self._close()

    def test_remove_user(self):
        self._open()
        auth = self.auth
        client = self.client
        app = self.app

        auth.login()
        response = client.post('/remove-user?board_id=1', data={'remove_user_id': 2})
        self.assertEqual(response.location, "/?board_id=1")
        self.assertNotIn("error", furl(response.location).args)

        with app.app_context():
            db = get_db()
            board_users = db.execute('SELECT * FROM user_board WHERE board_id = 1 ORDER BY user_id').fetchall()
            self.assertEqual(len(board_users), 1)
            self.assertEqual(board_users[0]['user_id'], 1)
        
        self._close()

    def test_remove_user_invalid(self):
        self._open()
        auth = self.auth
        client = self.client
        app = self.app

        auth.login()
        response = client.post('/remove-user', data={'remove_user_id': 2})
        self.assertEqual(furl(response.location).args["error"], "400")

        response = client.post('/remove-user?board_id=1', data={'remove_user_id': ''})
        self.assertEqual(furl(response.location).args["board_id"], "1")
        self.assertEqual(furl(response.location).args["error"], "400")

        response = client.post('/remove-user?board_id=10', data={'remove_user_id': 2})
        self.assertEqual(furl(response.location).args["error"], "404")

        response = client.post('/remove-user?board_id=1', data={'remove_user_id': 1})
        self.assertEqual(furl(response.location).args["board_id"], "1")
        self.assertEqual(furl(response.location).args["error"], "400")

        with app.app_context():
            db = get_db()
            board_users = db.execute('SELECT * FROM user_board WHERE board_id = 1 ORDER BY user_id').fetchall()
            self.assertEqual(len(board_users), 2)
            self.assertEqual(board_users[0]['user_id'], 1)
            self.assertEqual(board_users[1]['user_id'], 2)
        
        self._close()