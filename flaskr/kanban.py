from audioop import add
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)

from flaskr.auth import login_required
from werkzeug.exceptions import abort


from flaskr.db import get_db

bp = Blueprint('kanban', __name__)

@bp.route("/script_js")
def script_js():
    return render_template("/js/script.js")

@bp.route('/')
@login_required
def index():
    user_id = session.get('user_id')
    db = get_db()
    personal_board = db.execute(
        'SELECT u.personal_board FROM user u WHERE u.id = ?', (user_id,)
    ).fetchone()[0]

    board_id = request.args.get('board_id', personal_board)

    board_name = db.execute(
        'SELECT b.name FROM board b WHERE b.id = ?', (board_id,)
    ).fetchone()[0]

    tasks = db.execute(
        'SELECT t.id, t.priority_group, t.task, t.assignees'
        ' FROM board_task bt'
        ' LEFT JOIN task t'
        ' ON bt.task_id = t.id'
        ' WHERE bt.board_id = ?', (board_id,)
    ).fetchall()
    boards = db.execute(
        'SELECT ub.board_id as id, b.name'
        ' FROM user_board ub'
        ' LEFT JOIN board as b'
        ' ON ub.board_id = b.id' 
        ' WHERE ub.user_id = ?', (user_id,)
    ).fetchall()
    return render_template('kanban/index.html', tasks=tasks, boards=boards, board_id=board_id, board_name=board_name)

@bp.route('/create-board', methods=('GET', 'POST'))
@login_required
def create_board():
    if request.method == 'POST':
        user_id = session.get('user_id')
        name = request.form['name']
        error = None

        if not name:
            error = 'Board name is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO board (name)'
                ' VALUES (?)', (name,))
            board_id = db.execute(
                'SELECT b.id FROM board b WHERE b.id = LAST_INSERT_ROWID()'
            ).fetchone()
            db.execute(
                'INSERT INTO user_board (user_id, board_id)'
                ' VALUES (?, LAST_INSERT_ROWID())', (user_id,))
            db.commit()
            print(board_id[0])
        return redirect(url_for('kanban.index', board_id=board_id[0]))

    return render_template('kanban/index.html')

@bp.route('/leave-board', methods=('GET', 'POST'))
@login_required
def leave_board():
    if request.method == 'POST':
        user_id = session.get('user_id')
        board_id = request.args.get('board_id')
        error = None
        if not board_id:
            error = 'Board information is required.'

        if error is None:
            try:
                db = get_db()
                personal_board = db.execute(
                    'SELECT u.personal_board FROM user u WHERE u.id = ?', (user_id,)
                ).fetchone()[0]
                if str(personal_board) == board_id:
                    raise Exception(f"You cannot delete your Personal Board")
                
                db.execute(
                    'DELETE FROM user_board'
                    ' WHERE user_id = ? AND board_id = ?',
                    (user_id, board_id)
                )
                db.commit()
            except Exception as e:
                error = e
            else:
                return redirect(url_for('kanban.index'))
        if error:
            flash(error)

    return render_template('kanban/index.html')

@bp.route('/add-user', methods=('GET', 'POST'))
@login_required
def add_user():
    if request.method == 'POST':
        user_id = session.get('user_id')
        board_id = request.args.get('board_id')
        username = request.form['username']
        error = None
        if not board_id:
            error = 'Board information is required.'

        elif not username:
            error = '\nUsername is required'

        if error is None:
            try:
                db = get_db()
                print(username)
                add_user_id = db.execute(
                    'SELECT u.id FROM user u WHERE u.username = ?', (username,)
                ).fetchone()
                if add_user_id == None:
                    raise Exception(f"User {username} not found.")

                add_user_id = add_user_id[0]
                if add_user_id == user_id:
                    raise Exception(f"Requested user is the same as current user.")
                
                db.execute(
                    'INSERT INTO user_board (user_id, board_id)'
                    ' VALUES (?, ?)',
                    (add_user_id, board_id)
                )
                db.commit()
            except Exception as e:
                error = e
            else:
                return redirect(url_for('kanban.index', board_id=board_id))
        flash(error)

    return render_template('kanban/index.html', board_id=board_id)
    
@bp.route('/create-task', methods=('GET', 'POST'))
@login_required
def create_task():
    if request.method == 'POST':
        user_id = session.get('user_id')
        board_id = request.args.get('board_id')
        task = request.form['task']
        group = "TO DO"
        assignees = request.form['assignees']
        error = None

        if not task:
            error = 'Task information is required.'

        if not board_id:
            error = 'Board information is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO task (priority_group, task, assignees)'
                ' VALUES (?, ?, ?)',
                (group, task, assignees)
            )
            db.execute(
                'INSERT INTO board_task (board_id, task_id)'
                ' VALUES (?, LAST_INSERT_ROWID())',
                (board_id)
            )
            db.commit()
        return redirect(url_for('kanban.index', board_id=board_id))

    return render_template('kanban/index.html')

def get_task(id):
    task = get_db().execute(
        'SELECT t.id, priority_group, task, assignees'
        ' FROM task t'
        ' WHERE t.id = ?',
        (id,)
    ).fetchone()

    if task is None:
        abort(404, f"Task id {id} doesn't exist.")

    return task

@bp.route('/update-task', methods=('GET', 'POST'))
@login_required
def update_task():
    if request.method == 'POST':
        id = request.args.get('id')
        board_id = request.args.get('board_id')
        task = get_task(id)
        group = request.form['group'].upper()
        error = None

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE task SET priority_group = ?'
                ' WHERE id = ?',
                (group, id)
            )
            db.commit()
            return redirect(url_for('kanban.index', board_id=board_id))

    return render_template('kanban/index.html')

@bp.route('/delete-task', methods=('POST',))
@login_required
def delete_task():
    id = request.args.get('id')
    board_id = request.args.get('board_id')
    get_task(id)
    db = get_db()
    db.execute('DELETE FROM task WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('kanban.index', board_id=board_id ))