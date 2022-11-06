# Test code sampled from https://flask.palletsprojects.com/en/2.2.x/tutorial/tests/
import os
import tempfile

from flaskr.db import get_db
from flask import session, g
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

    def test_register(self):
        self._open()
        client = self.client
        auth = self.auth
        app = self.app

        self.assertEqual(client.get('/register').status_code, 200)

        response = client.post(
            '/register', data={'username': 'a', 'password': 'a'}
        )
        self.assertEqual(response.location, "/login")

        with app.app_context():
            self.assertIsNotNone(get_db().execute(
                "SELECT * FROM user WHERE username = 'a'",
            ).fetchone())
        
        self._close()

    def test_register_validate_input(self):
        for (username, password, message) in (
        ('', '', b'Username is required.'),
        ('a', '', b'Password is required.'),
        ('test', 'test', b'is already taken.'),
    ):
            self._open()
            client = self.client
            auth = self.auth
            app = self.app

            response = client.post(
                '/register',
                data={'username': username, 'password': password}
            )
            self.assertIn(message, response.data)
            self._close()

    def test_login(self):
        self._open()
        client = self.client
        auth = self.auth

        self.assertEqual(client.get('/login').status_code, 200)

        response = auth.login()
        self.assertEqual(response.location, "/")

        with client:
            client.get('/')
            self.assertEqual(session['user_id'], 1)
            self.assertEqual(g.user['username'], 'test')

        self._close()

    def test_login_validate_input(self):
        for (username, password, message) in (
        ('a', 'test', b'Incorrect username.'),
        ('test', 'a', b'Incorrect password.'),
    ):
            self._open()
            client = self.client
            auth = self.auth
            app = self.app

            response = auth.login(username, password)
            self.assertIn(message, response.data)
            self._close()

    def test_login_required(self):
        for path in (
        '/create-board',
        '/rename-board',
        '/leave-board',
        '/add-user',
        '/remove-user',
        '/create-task',
        '/update-task',
        '/delete-task',
    ):
            self._open()
            client = self.client
            response = client.post(path)
            self.assertEqual(response.location, "/login")
            self._close()

    def test_logout(self):
        self._open()
        client = self.client
        auth = self.auth

        auth.login()

        with client:
            auth.logout()
            self.assertNotIn('user_id', session)