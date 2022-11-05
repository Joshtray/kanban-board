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

    (board_name, board_admin) = db.execute(
        'SELECT b.name, b.admin_id FROM board b WHERE b.id = ?', (board_id,)
    ).fetchone()

    print(board_name, board_admin, user_id, type(board_admin), type(user_id))
    tasks = db.execute(
        'SELECT t.id, t.priority_group, t.task, t.assignees'
        ' FROM board_task bt'
        ' LEFT JOIN task t'
        ' ON bt.task_id = t.id'
        ' WHERE bt.board_id = ?', (board_id,)
    ).fetchall()
    boards = db.execute(
        'SELECT ub.board_id as id, b.name, b.admin_id'
        ' FROM user_board ub'
        ' LEFT JOIN board as b'
        ' ON ub.board_id = b.id' 
        ' WHERE ub.user_id = ?', (user_id,)
    ).fetchall()
    board_users = db.execute(
        'SELECT u.id, u.username'
        ' FROM user_board ub'
        ' LEFT JOIN user u'
        ' ON ub.user_id = u.id'
        ' WHERE ub.board_id = ?', (board_id,)
    ).fetchall()
    return render_template('kanban/index.html', tasks=tasks, boards=boards, board_id=board_id, board_name=board_name, board_users=board_users, board_admin=board_admin)

@bp.route('/create-board', methods=('POST',))
@login_required
def create_board():
    user_id = session.get('user_id')
    name = request.form['name']
    error = None

    if not name:
        error = 'Board name is required.'

    if error is not None:
        flash("Error: " + error)
    else:
        db = get_db()
        db.execute(
            'INSERT INTO board (name, admin_id)'
            ' VALUES (?, ?)', (name, user_id))
        board_id = db.execute(
            'SELECT b.id FROM board b WHERE b.id = LAST_INSERT_ROWID()'
        ).fetchone()
        db.execute(
            'INSERT INTO user_board (user_id, board_id)'
            ' VALUES (?, LAST_INSERT_ROWID())', (user_id,))
        db.commit()
        flash(f"\"{name}\" created successfully!")

    return redirect(url_for('kanban.index', board_id=board_id[0]))

@bp.route('/rename-board', methods=['POST'])
@login_required
def rename_board():
    board_id = request.args.get('board_id')
    board_name = request.form['board_name']
    
    error = None
    if not board_id:
        error = 'Board id is required.'
    elif not board_name:
        error = 'Board name is required.'

    if error is not None:
        flash("Error: " + error)
    else:
        db = get_db()
        db.execute(
            'UPDATE board'
            ' SET name = ?'
            ' WHERE id = ?', (board_name, board_id))
        db.commit()
    return redirect(url_for('kanban.index', board_id=board_id))


@bp.route('/leave-board', methods=['POST'])
@login_required
def leave_board():
    user_id = session.get('user_id')
    board_id = request.args.get('board_id')
    board_name = request.args.get('board_name')
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
                raise Exception(f"You cannot leave your Personal Board")
            
            db.execute(
                'DELETE FROM user_board'
                ' WHERE user_id = ? AND board_id = ?',
                (user_id, board_id)
            )
            remaining_users = db.execute(
                'SELECT COUNT(*) FROM user_board WHERE board_id = ?', (board_id,)
            ).fetchone()[0]
            if remaining_users == 0:
                db.execute(
                    'DELETE FROM board_task WHERE board_id = ?', (board_id,)
                )
                db.execute(
                    'DELETE FROM board WHERE id = ?', (board_id,)
                )
            db.commit()
        except Exception as e:
            error = str(e)
    if error is not None:
        flash("Error: " + error)
    else:
        flash(f"Successfully left \"{board_name}\"")
    return redirect(url_for('kanban.index'))

@bp.route('/add-user', methods=['POST'])
@login_required
def add_user():
    user_id = session.get('user_id')
    board_id = request.args.get('board_id')
    username = request.form['username']
    error = None
    if not board_id:
        error = 'Board information is required.'

    elif not username:
        error = 'Username is required'

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
            exist_user = db.execute(
                'SELECT COUNT(*) FROM user_board ub'
                ' WHERE ub.user_id = ? AND ub.board_id = ?', (add_user_id, board_id)).fetchone()[0]
            
            if exist_user > 0:
                raise Exception(f"User {username} already in board.")
            
            db.execute(
                'INSERT INTO user_board (user_id, board_id)'
                ' VALUES (?, ?)',
                (add_user_id, board_id)
            )
            db.commit()
        except Exception as e:
            error = str(e)
    if error is not None:
        flash("Error: " + error)
    else:
        flash(f"User {username} added to board")
    return redirect(url_for('kanban.index', board_id=board_id))

@bp.route('/remove-user', methods=['POST'])
@login_required
def remove_user():
    user_id = session.get('user_id')
    remove_user_id = request.form['remove_user_id']
    board_id = request.form['board_id']
    error = None
    if not board_id:
        error = 'Board information is required.'

    elif not remove_user_id:
        error = 'No user to remove'

    if error is None:
        try:
            db = get_db()
            admin_id = db.execute(
                'SELECT admin_id FROM board b WHERE b.id = ?', (board_id,)
            ).fetchone()[0]
            print(admin_id)
            if admin_id != user_id:
                raise Exception(f"Only admins can remove users from the board")
            if remove_user_id == user_id:
                raise Exception(f"You cannot remove yourself from the board.")
            if remove_user_id == admin_id:
                raise Exception(f"You cannot remove the admin from the board.")
            db.execute(
                'DELETE FROM user_board'
                ' WHERE user_id = ? AND board_id = ?',
                (remove_user_id, board_id)
            )
            db.commit()
        except Exception as e:
            error = str(e)
        
    if error is not None:
        flash("Error: " + error)
    else:
        flash(f"User removed from board")
    return redirect(url_for('kanban.index', board_id=board_id))

    
    
@bp.route('/create-task', methods=['POST'])
@login_required
def create_task():
    board_id = request.args.get('board_id')
    group = request.args.get('group').upper()
    task = request.form['task']
    assignees = request.form['assignees']
    error = None

    if not task:
        error = 'Task information is required.'

    if not group:
        error = 'Task priority group is required.'

    if not board_id:
        error = 'Board information is required.'

    if error is not None:
        flash("Error: " + error)
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
            (board_id,)
        )
        db.commit()
    return redirect(url_for('kanban.index', board_id=board_id))

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

@bp.route('/update-task', methods=['POST'])
@login_required
def update_task():
    id = request.args.get('id')
    board_id = request.args.get('board_id')
    task = get_task(id)
    group = request.form['group'].upper()
    error = None

    if error is not None:
        flash("Error: " + error)
    else:
        db = get_db()
        db.execute(
            'UPDATE task SET priority_group = ?'
            ' WHERE id = ?',
            (group, id)
        )
        db.commit()
    return redirect(url_for('kanban.index', board_id=board_id))

@bp.route('/delete-task', methods=['POST'])
@login_required
def delete_task():
    id = request.args.get('id')
    board_id = request.args.get('board_id')
    get_task(id)
    db = get_db()
    db.execute('DELETE FROM task WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('kanban.index', board_id=board_id ))

