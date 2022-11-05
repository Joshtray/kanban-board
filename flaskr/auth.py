import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from flaskr.db import get_db

bp = Blueprint('auth', __name__)

@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None

        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'

        if error is None:
            try:
                db.execute(
                    'INSERT INTO board (name)'
                    f'VALUES ("{username}\'s Personal Board")',
                )
                personal_board_id = db.execute(
                    'SELECT id FROM board b WHERE b.ROWID = LAST_INSERT_ROWID()'
                ).fetchone()[0]
                print("PB", personal_board_id)

                db.execute(
                    "INSERT INTO user (username, password, personal_board) VALUES (?, ?, ?)",
                    (username, generate_password_hash(password), personal_board_id)
                )
                user_id = db.execute(
                    'SELECT id FROM user u WHERE u.ROWID = LAST_INSERT_ROWID()'
                ).fetchone()[0]
                print(user_id)
                db.execute(
                    'UPDATE board SET admin_id = ? WHERE id = ?', (user_id, personal_board_id)
                )
                db.execute(
                    'INSERT INTO user_board (user_id, board_id)'
                    ' VALUES (?, ?)',
                    (user_id, personal_board_id)
                )
                db.commit()
            except db.IntegrityError as e:
                print("Ex", e)
                error = f"User {username} is already taken."
            else:
                flash("Registration successful! Please log in.")
                return redirect(url_for("auth.login"))

        flash("Error: " + error)

    return render_template('auth/register.html')

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None
        user = db.execute(
            'SELECT * FROM user WHERE username = ?', (username,)
        ).fetchone()

        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for('index'))

        flash("Error: " + error)

    return render_template('auth/login.html')

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM user WHERE id = ?', (user_id,)
        ).fetchone()

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view