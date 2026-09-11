import ast
import datetime
import os
import re
import secrets
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse

import xlsxwriter
from flask import Flask, abort, jsonify, redirect, render_template, request, send_file
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from flask_wtf.csrf import CSRFProtect
from waitress import serve
from werkzeug.utils import secure_filename

from data import db_session
from data.projects import Project
from data.tasks import Task
from data.users import User
from forms.add_project import AddProjectForm
from forms.add_task import AddTaskForm
from forms.login import LoginForm
from forms.register import RegisterForm

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = Path(os.getenv('MANAGETIME_DATABASE', BASE_DIR / 'db' / 'manage_time.db'))
ADMIN_LOGIN = os.getenv('MANAGETIME_ADMIN_LOGIN', '').strip().casefold()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('MANAGETIME_SECRET_KEY', secrets.token_hex(32))
app.config['JSON_AS_ASCII'] = False
CSRFProtect(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'


def is_admin_user():
    return (
        current_user.is_authenticated
        and bool(ADMIN_LOGIN)
        and current_user.login.casefold() == ADMIN_LOGIN
    )


class MyModelView(ModelView):
    def is_accessible(self):
        return is_admin_user()

    def inaccessible_callback(self, name, **kwargs):
        abort(403)


class SecureAdminIndexView(AdminIndexView):
    def is_accessible(self):
        return is_admin_user()

    def inaccessible_callback(self, name, **kwargs):
        abort(403)


DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
db_session.global_init(str(DATABASE_PATH))
admin = Admin(app, name='ManageTime', index_view=SecureAdminIndexView())
admin_session = db_session.create_session()
admin.add_view(MyModelView(User, admin_session))
admin.add_view(MyModelView(Project, admin_session))
admin.add_view(MyModelView(Task, admin_session))


def get_owned_project(db_sess, project_id):
    project = db_sess.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id,
    ).first()
    if not project:
        abort(404)
    return project


def get_owned_task(db_sess, project_id, task_id):
    project = get_owned_project(db_sess, project_id)
    task = db_sess.query(Task).filter(
        Task.id == task_id,
        Task.project_id == project.id,
    ).first()
    if not task:
        abort(404)
    return project, task


def parse_durations(value):
    try:
        durations = ast.literal_eval(value or '{}')
    except (SyntaxError, ValueError):
        return {}
    if not isinstance(durations, dict):
        return {}
    return {
        str(date): max(float(seconds), 0)
        for date, seconds in durations.items()
        if isinstance(seconds, (int, float))
    }


def format_duration(seconds):
    seconds = max(int(seconds or 0), 0)
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes = remainder // 60
    return [days, hours, minutes]


def normalize_github_link(value):
    value = (value or '').strip()
    if not value:
        return ''
    parsed = urlparse(value)
    if parsed.scheme not in {'http', 'https'} or parsed.hostname not in {
        'github.com', 'www.github.com'
    }:
        abort(400, description='Укажите ссылку на GitHub.')
    return value


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return redirect('/')


@app.route('/', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect('/main')
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        login_value = form.login.data.strip()
        user = db_sess.query(User).filter(User.login == login_value).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect('/main')
        return render_template(
            'login.html', form=form, message='Неверный логин или пароль.', start=True
        )
    return render_template('login.html', form=form, start=True)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect('/main')
    form = RegisterForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        login_value = form.login.data.strip()
        if db_sess.query(User).filter(User.login == login_value).first():
            return render_template(
                'register.html', form=form,
                message='Пользователь с таким логином уже существует.', start=True
            )
        user = User(login=login_value)
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        login_user(user)
        return redirect('/main')
    return render_template('register.html', form=form, start=True)


@app.route('/main', methods=['GET', 'POST'])
@login_required
def index():
    db_sess = db_session.create_session()
    form = AddProjectForm()
    if form.validate_on_submit():
        project = Project(
            title=form.title.data.strip(),
            github_link=normalize_github_link(form.github_link.data),
            user_id=current_user.id,
        )
        db_sess.add(project)
        db_sess.commit()
        return redirect('/main')

    projects = db_sess.query(Project).filter(Project.user_id == current_user.id).all()
    result = []
    for project in projects:
        seconds = sum(task.duration or 0 for task in project.tasks)
        result.append(format_duration(seconds) + [any(task.start_time for task in project.tasks)])
    return render_template(
        'index.html', form=form, projects=projects,
        user_id=current_user.id, result=result
    )


@app.route('/projects/<int:user_id>/<int:project_id>', methods=['GET', 'POST'])
@login_required
def projects_func(user_id, project_id):
    if current_user.id != user_id:
        abort(404)
    db_sess = db_session.create_session()
    project = get_owned_project(db_sess, project_id)
    form = AddTaskForm()

    if request.method == 'POST' and 'title_project' in request.form:
        title = request.form.get('title_project', '').strip()
        if not title:
            abort(400)
        project.title = title
        project.github_link = normalize_github_link(request.form.get('github_link'))
        db_sess.commit()
        return redirect(f'/projects/{user_id}/{project_id}')

    if form.validate_on_submit():
        project.tasks.append(Task(title=form.title.data.strip()))
        db_sess.commit()
        return redirect(f'/projects/{user_id}/{project_id}')

    result = [format_duration(task.duration) for task in project.tasks]
    return render_template(
        'project.html', project=project, form=form, back='/main', result=result
    )


@app.route('/tasks/<int:user_id>/<int:project_id>/<int:task_id>', methods=['GET', 'POST'])
@login_required
def tasks_func(user_id, project_id, task_id):
    if current_user.id != user_id:
        abort(404)
    db_sess = db_session.create_session()
    project, task = get_owned_task(db_sess, project_id, task_id)
    form = AddTaskForm()
    if form.validate_on_submit():
        task.title = form.title.data.strip()
        db_sess.commit()
        return redirect(f'/tasks/{user_id}/{project_id}/{task_id}')
    form.title.data = task.title
    return render_template(
        'task.html', project=project, task=task, form=form,
        back=f'/projects/{user_id}/{project_id}'
    )


@app.route('/unload-project/<int:user_id>/<int:project_id>')
@login_required
def unload_project(user_id, project_id):
    if current_user.id != user_id:
        abort(404)
    db_sess = db_session.create_session()
    project = get_owned_project(db_sess, project_id)
    durations = {}
    for task in project.tasks:
        for date, seconds in parse_durations(task.duration_per_dates).items():
            durations[date] = durations.get(date, 0) + seconds
    return send_export(durations, project.title)


@app.route('/unload-task/<int:user_id>/<int:project_id>/<int:task_id>')
@login_required
def unload_task(user_id, project_id, task_id):
    if current_user.id != user_id:
        abort(404)
    db_sess = db_session.create_session()
    _, task = get_owned_task(db_sess, project_id, task_id)
    return send_export(parse_durations(task.duration_per_dates), task.title)


@app.route('/api/delete-project', methods=['POST'])
@login_required
def delete_project():
    payload = request.get_json(silent=True) or {}
    db_sess = db_session.create_session()
    project = get_owned_project(db_sess, payload.get('project_id'))
    db_sess.delete(project)
    db_sess.commit()
    return jsonify(status='success')


@app.route('/api/delete-task', methods=['POST'])
@login_required
def delete_task():
    payload = request.get_json(silent=True) or {}
    db_sess = db_session.create_session()
    _, task = get_owned_task(db_sess, payload.get('project_id'), payload.get('task_id'))
    db_sess.delete(task)
    db_sess.commit()
    return jsonify(status='success')


@app.route('/api/start-stopwatch', methods=['POST'])
@login_required
def start_stopwatch():
    payload = request.get_json(silent=True) or {}
    db_sess = db_session.create_session()
    _, task = get_owned_task(db_sess, payload.get('project_id'), payload.get('task_id'))
    if not task.start_time:
        task.start_time = datetime.datetime.now()
        db_sess.commit()
    return jsonify(status='success')


@app.route('/api/stop-stopwatch', methods=['POST'])
@login_required
def stop_stopwatch():
    payload = request.get_json(silent=True) or {}
    db_sess = db_session.create_session()
    _, task = get_owned_task(db_sess, payload.get('project_id'), payload.get('task_id'))
    if not task.start_time:
        return jsonify(error='Секундомер не запущен.'), 409

    seconds = max(int((datetime.datetime.now() - task.start_time).total_seconds()), 0)
    durations = parse_durations(task.duration_per_dates)
    today = str(datetime.date.today())
    durations[today] = durations.get(today, 0) + seconds
    task.duration = int(task.duration or 0) + seconds
    task.duration_per_dates = repr(durations)
    task.start_time = None
    db_sess.commit()
    days, hours, minutes = format_duration(task.duration)
    return jsonify(days=days, hours=hours, minutes=minutes)


@app.route('/api/reset-stopwatch', methods=['POST'])
@login_required
def reset_stopwatch():
    payload = request.get_json(silent=True) or {}
    db_sess = db_session.create_session()
    _, task = get_owned_task(db_sess, payload.get('project_id'), payload.get('task_id'))
    task.duration = 0
    task.duration_per_dates = '{}'
    task.start_time = None
    db_sess.commit()
    return jsonify(status='success')


def create_unload_file(durations, title):
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    sheet_name = re.sub(r'[\[\]:*?/\\]', '_', title).strip().strip("'")[:31]
    sheet_name = sheet_name or 'ManageTime'
    worksheet = workbook.add_worksheet(sheet_name)
    worksheet.write_string(0, 0, 'Date')
    worksheet.write_string(1, 0, 'Time, min')
    result = 0
    for column, date in enumerate(sorted(durations), start=1):
        minutes = int(durations[date] // 60)
        result += minutes
        worksheet.write_string(0, column, date)
        worksheet.write_number(1, column, minutes)
    worksheet.write_string(3, 0, 'Result, min:')
    worksheet.write_number(3, 1, result)
    workbook.close()
    output.seek(0)
    return output


def send_export(durations, title):
    filename = secure_filename(title) or 'manage-time'
    return send_file(
        create_unload_file(durations, title),
        as_attachment=True,
        download_name=f'{filename}.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )


if __name__ == '__main__':
    host = os.getenv('MANAGETIME_HOST', '127.0.0.1')
    port = int(os.getenv('MANAGETIME_PORT', '5001'))
    serve(app, host=host, port=port)
