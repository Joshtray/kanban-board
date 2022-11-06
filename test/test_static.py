from flaskr.db import get_db

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

    def test_load_jsscript(self):
        self._open()
        auth = self.auth
        client = self.client

        auth.login()
        response = client.get('/script_js')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'var mouseDownPos = null', response.data)
        self.assertIn(b'window.addEventListener(\'load\', function () {', response.data)
        self.assertIn(b'const add_board = (element) => {', response.data)
        self.assertIn(b'const close_add_task = (element) => {', response.data)