from audioop import add
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)

from flaskr.auth import login_required
import werkzeug.exceptions as exceptions
from werkzeug.exceptions import abort


from flaskr.db import get_db

bp = Blueprint('kanban', __name__)

@bp.route("/script_js")
def script_js():
    return render_template("/js/script.js")

@bp.route('/')
@login_required
def index():
    try:
        user_id = session.get('user_id')
        error = request.args.get('error')
        db = get_db()

        boards = db.execute(
            'SELECT ub.board_id as id, b.name, b.admin_id'
            ' FROM user_board ub'
            ' LEFT JOIN board as b'
            ' ON ub.board_id = b.id' 
            ' WHERE ub.user_id = ?', (user_id,)
        ).fetchall()

        personal_board = db.execute(
            'SELECT u.personal_board FROM user u WHERE u.id = ?', (user_id,)
        ).fetchone()[0]

        board_id = int(request.args.get('board_id', personal_board))

        if board_id not in [b['id'] for b in boards]:
            abort(403, f"User {user_id} doesn't have access to board {board_id}")

        board_users = db.execute(
            'SELECT u.id, u.username'
            ' FROM user_board ub'
            ' LEFT JOIN user u'
            ' ON ub.user_id = u.id'
            ' WHERE ub.board_id = ?', (board_id,)
        ).fetchall()


        (board_name, board_admin) = db.execute(
            'SELECT b.name, b.admin_id FROM board b WHERE b.id = ?', (board_id,)
        ).fetchone()

        tasks = db.execute(
            'SELECT t.id, t.priority_group, t.task, t.assignees'
            ' FROM task t'
            ' WHERE t.board_id = ?', (board_id,)

        ).fetchall()
        return render_template('kanban/index.html', tasks=tasks, boards=boards, board_id=board_id, board_name=board_name, board_users=board_users, board_admin=board_admin, error=error)
    except Exception as e:
        if isinstance(e, exceptions.HTTPException):
            flash("Error: " + e.description)
            return redirect(url_for('kanban.index', error=e.code))
        raise e

@bp.route('/create-board', methods=('POST',))
@login_required
def create_board():
    user_id = session.get('user_id')
    name = request.form['name']
    try:
        if not name:
            abort(400, "Board name is required.")
        else:
            db = get_db()
            db.execute(
                'INSERT INTO board (name, admin_id)'
                ' VALUES (?, ?)', (name, user_id))
            board_id = db.execute(
                'SELECT b.id FROM board b WHERE b.ROWID = LAST_INSERT_ROWID()'
            ).fetchone()[0]
            db.execute(
                'INSERT INTO user_board (user_id, board_id)'
                ' VALUES (?, ?)', (user_id, board_id))
            db.commit()
            flash(f"\"{name}\" created successfully!")

            return redirect(url_for('kanban.index', board_id=board_id))
    except Exception as e:
        if isinstance(e, exceptions.HTTPException):
            flash("Error: " + e.description)
            return redirect(url_for('kanban.index', error=e.code))
        else:
            raise e

@bp.route('/rename-board', methods=('POST',))
@login_required
def rename_board():
    user_id = session.get('user_id')
    board_id = request.args.get('board_id')
    board_name = request.form['board_name']

    try:
        if not board_id:
            abort(400, "Board id is required.")
        elif not board_name:
            abort(400, "Board name is required.")

        else:
            db = get_db()

            board = db.execute(
                'SELECT b.admin_id FROM board b WHERE b.id = ?', (board_id,)
            ).fetchone()

            if board is None:
                abort(404, f"Board id {board_id} doesn't exist.")

            if board['admin_id'] != user_id:
                abort(403, "You are not the admin of this board.")

            db.execute(
                'UPDATE board SET name = ? WHERE id = ?', (board_name, board_id))
            db.commit()
            flash(f"\"{board_name}\" renamed successfully!")

            return redirect(url_for('kanban.index', board_id=board_id))
    except Exception as e:
        if isinstance(e, exceptions.HTTPException):
            flash("Error: " + e.description)
            return redirect(url_for('kanban.index', board_id=board_id, error=e.code))
        else:
            raise e


@bp.route('/leave-board', methods=('POST',))
@login_required
def leave_board():
    user_id = session.get('user_id')
    board_id = request.args.get('board_id')

    try: 
        if not board_id:
            abort(400, "Board id is required.")
        else:
            db = get_db()
            personal_board = db.execute(
                'SELECT u.personal_board FROM user u WHERE u.id = ?', (user_id,)
            ).fetchone()[0]

            if str(personal_board) == board_id:
                abort(403, "You can't leave your personal board.")
            
            board = db.execute(
                'SELECT b.name FROM board b WHERE b.id = ?', (board_id,)
            ).fetchone()

            if board is None:
                abort(404, f"Board id {board_id} doesn't exist.")
            
            board_name = board['name']

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
                    'DELETE FROM task WHERE board_id = ?', (board_id,)
                )
                db.execute(
                    'DELETE FROM board WHERE id = ?', (board_id,)
                )
            db.commit()
            flash(f"Successfully left \"{board_name}\"")
            return redirect(url_for('kanban.index'))
    except Exception as e:
        if isinstance(e, exceptions.HTTPException):
            flash("Error: " + e.description)
            return redirect(url_for('kanban.index', board_id=board_id, error=e.code))
        else:
            raise e
        

@bp.route('/add-user', methods=['POST'])
@login_required
def add_user():
    user_id = session.get('user_id')
    board_id = request.args.get('board_id')
    username = request.form['username']
    try: 
        if not board_id:
            abort(400, 'Board information is required.')

        elif not username:
            abort(400, 'Username is required')

        else:
            db = get_db()

            board_users = db.execute(
                'SELECT ub.user_id FROM user_board ub'
                ' WHERE ub.board_id = ?', (board_id,)
            ).fetchall()
            board_users = [user['user_id'] for user in board_users]
            if user_id not in board_users:
                abort(403, "You are not a member of this board")

            add_user_id = db.execute(
                'SELECT u.id FROM user u WHERE u.username = ?', (username,)
            ).fetchone()
            if add_user_id == None:
                abort(404, f"User \"{username}\" not found.")

            add_user_id = add_user_id[0]
            if add_user_id == user_id:
                abort(400, "You are already a member of this board")
            
            if add_user_id in board_users:
                abort(400, f"User \"{username}\" is already a member of this board")
            
            db.execute(
                'INSERT INTO user_board (user_id, board_id)'
                ' VALUES (?, ?)',
                (add_user_id, board_id)
            )
            db.commit()
            flash(f"User {username} added to board")
            return redirect(url_for('kanban.index', board_id=board_id))
    except Exception as e:
        if isinstance(e, exceptions.HTTPException):
            flash("Error: " + e.description)
            return redirect(url_for('kanban.index', board_id=board_id, error=e.code))
        else:
            raise e

@bp.route('/remove-user', methods=['POST'])
@login_required
def remove_user():
    user_id = session.get('user_id')
    remove_user_id = request.form['remove_user_id']
    board_id = request.args.get('board_id')
    
    try:
        if not board_id:
            abort(400, 'Board information is required.')

        elif not remove_user_id:
            abort(400, 'The requested user\'s id is required.')

        else:
            db = get_db()
            board = db.execute(
                'SELECT b.admin_id FROM board b WHERE b.id = ?', (board_id,)
            ).fetchone()
            if board is None:
                abort(404, f"Board id {board_id} doesn't exist.")

            if board['admin_id'] != user_id:
                abort(403, "You are not the admin of this board.")

            if remove_user_id == str(user_id):
                abort(400, "You can't remove yourself from the board.")

            db.execute(
                'DELETE FROM user_board'
                ' WHERE user_id = ? AND board_id = ?',
                (remove_user_id, board_id)
            )
            db.commit()
            flash(f"User removed from board")
            return redirect(url_for('kanban.index', board_id=board_id))
    except Exception as e:
        if isinstance(e, exceptions.HTTPException):
            flash("Error: " + e.description)
            return redirect(url_for('kanban.index', board_id=board_id, error=e.code))
        else:
            raise e

@bp.route('/create-task', methods=['POST'])
@login_required
def create_task():
    user_id = session.get('user_id')
    board_id = request.args.get('board_id')
    group = request.args.get('group')
    task = request.form['task']
    assignees = request.form['assignees']

    try:
        if not task:
            abort(400, 'Task information is required.')

        if not group:
            abort(400, 'Task priority group is required.')

        group = group.upper()
        if group not in ['TO DO', 'DOING', 'DONE']:
            abort(400, 'Invalid task priority group.')

        if not board_id:
            abort(400, 'Board id is required.')
        
        get_board(board_id)

        board_users = get_db().execute(
            'SELECT ub.user_id FROM user_board ub'
            ' WHERE ub.board_id = ?', (board_id,)
        ).fetchall()
        board_users = [user['user_id'] for user in board_users]
        if user_id not in board_users:
            abort(403, "You are not a member of this board")
        
        else:
            db = get_db()
            db.execute(
                'INSERT INTO task (priority_group, task, assignees, board_id)'
                ' VALUES (?, ?, ?, ?)',
                (group, task, assignees, board_id)
            )
            db.commit()
            return redirect(url_for('kanban.index', board_id=board_id))
    except Exception as e:
        if isinstance(e, exceptions.HTTPException):
            flash("Error: " + e.description)
            return redirect(url_for('kanban.index', board_id=board_id, error=e.code))
        else:
            raise e

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

def get_board(id):
    board = get_db().execute(
        'SELECT b.id, b.name, b.admin_id'
        ' FROM board b'
        ' WHERE b.id = ?',
        (id,)
    ).fetchone()

    if board is None:
        abort(404, f"Board id {id} doesn't exist.")

    return board

@bp.route('/update-task', methods=['POST'])
@login_required
def update_task():
    user_id = session.get('user_id')
    id = request.args.get('id')
    board_id = request.args.get('board_id')
    group = request.form['group'].upper()

    try:
        if not id:
            abort(400, 'Task id is required.')

        if not group:
            abort(400, 'Task priority group is required.')
        
        if not board_id:
            abort(400, 'Board information is required.')
        
        get_board(board_id)
        
        get_task(id)

        board_users = get_db().execute(
            'SELECT ub.user_id FROM user_board ub'
            ' WHERE ub.board_id = ?', (board_id,)
        ).fetchall()
        board_users = [user['user_id'] for user in board_users]
        if user_id not in board_users:
            abort(403, "You are not a member of this board")

        if group not in ['TO DO', 'DOING', 'DONE']:
            abort(400, 'Invalid task priority group.')

        else:
            db = get_db()
            db.execute(
                'UPDATE task SET priority_group = ?'
                ' WHERE id = ?',
                (group, id)
            )
            db.commit()
            return redirect(url_for('kanban.index', board_id=board_id))
    except Exception as e:
        if isinstance(e, exceptions.HTTPException):
            flash("Error: " + e.description)
            return redirect(url_for('kanban.index', board_id=board_id, error=e.code))
        else:
            raise e

@bp.route('/delete-task', methods=['POST'])
@login_required
def delete_task():
    user_id = session.get('user_id')
    id = request.args.get('id')
    board_id = request.args.get('board_id')

    try:
        if not id:
            abort(400, 'Task id is required.')

        get_task(id)

        if not board_id:
            abort(400, 'Board id is required.')

        get_board(board_id)
        
        board_users = get_db().execute(
            'SELECT ub.user_id FROM user_board ub'
            ' WHERE ub.board_id = ?', (board_id,)
        ).fetchall()
        board_users = [user['user_id'] for user in board_users]
        if user_id not in board_users:
            abort(403, "You are not a member of this board")

        else:
            db = get_db()
            db.execute(
                'DELETE FROM task'
                ' WHERE id = ?',
                (id,)
            )
            db.commit()
            return redirect(url_for('kanban.index', board_id=board_id))
    except Exception as e:
        if isinstance(e, exceptions.HTTPException):
            flash("Error: " + e.description)
            return redirect(url_for('kanban.index', board_id=board_id, error=e.code))
        else:
            raise e

