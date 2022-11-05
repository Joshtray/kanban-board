import pytest
from flaskr.db import get_db

def test_load_jsscript(client, auth):
    auth.login()
    response = client.get('/script_js')
    assert response.status_code == 200
    assert b'var mouseDownPos = null' in response.data
    assert b'window.addEventListener(\'load\', function () {' in response.data
    assert b'const add_board = (element) => {' in response.data
    assert b'const close_add_task = (element) => {' in response.data

    