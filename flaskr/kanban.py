from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)

from flaskr.auth import login_required
from werkzeug.exceptions import abort


from flaskr.db import get_db

bp = Blueprint('kanban', __name__)

@bp.route('/')
@login_required
def index():
    user_id = session.get('user_id')
    db = get_db()
    tasks = db.execute(
        'SELECT t.id, priority_group, task, assignees'
        ' FROM task t WHERE t.user_id = ?', (user_id,)
    ).fetchall()
    return render_template('kanban/index.html', tasks=tasks)

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        user_id = session.get('user_id')
        task = request.form['task']
        group = "TODO"
        assignees = request.form['assignees']
        error = None

        if not task:
            error = 'Task information is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO task (user_id, priority_group, task, assignees)'
                ' VALUES (?, ?, ?, ?)',
                (user_id, group, task, assignees)
            )
            db.commit()
        return redirect(url_for('kanban.index'))

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

@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    task = get_task(id)

    if request.method == 'POST':
        group = request.form['group']
        error = None

        print("PRINGING", id, group)
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
            return redirect(url_for('kanban.index'))

    return render_template('kanban/index.html')

@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_task(id)
    db = get_db()
    db.execute('DELETE FROM task WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('kanban.index'))