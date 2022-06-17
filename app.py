import json
import datetime
from waitress import serve
from flask import Flask, render_template, redirect, request
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from forms.login import LoginForm
from forms.register import RegisterForm
from forms.add_project import AddProjectForm
from forms.add_task import AddTaskForm
from data import db_session
from data.users import User
from data.projects import Project
from data.tasks import Task
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

app = Flask(__name__)
app.config['SECRET_KEY'] = 'top_secret_keyt'
login_manager = LoginManager()
login_manager.init_app(app)
admin = Admin(app)


class MyModelView(ModelView):
    def is_accessible(self):
        try:
            if current_user.id == 1:
                return True
        except AttributeError:
            return False


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


# function to login user
@app.route('/', methods=['GET', 'POST'])
def login():
    db_sess = db_session.create_session()
    form = LoginForm()
    if form.validate_on_submit():
        user = db_sess.query(User).filter(User.login == form.login.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect('/main')
        return render_template('login.html', form=form, message="Incorrect data!", start=True)
    return render_template('login.html', form=form, start=True)


@app.route('/register', methods=['GET', 'POST'])
def register():
    db_sess = db_session.create_session()
    form = RegisterForm()
    if form.validate_on_submit():
        check_already_exists = db_sess.query(User).filter(
            User.login == form.login.data).first()
        if check_already_exists:
            return render_template('register.html', form=form,
                                   message="Account with this login is already exists!", start=True)
        if form.password.data != form.password_again.data:
            return render_template('register.html', form=form,
                                   message="Passwords don't match!", start=True)
        user = User(login=form.login.data)
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
        project = Project(title=form.title.data, github_link=form.github_link.data, user_id=current_user.id)
        db_sess.add(project)
        db_sess.commit()
    projects = db_sess.query(Project).filter(Project.user == current_user).all()
    result = []
    for project in projects:
        days = 0
        hours = 0
        minutes = 0
        is_use = False
        for task in project.tasks:
            day = divmod(task.duration, 86400)[0]
            hour = divmod(task.duration - day * 86400, 3600)[0]
            minute = divmod(task.duration - hour * 3600 - day * 86400, 60)[0]
            days += day
            hours += hour
            minutes += minute
            if task.start_time:
                is_use = True
        result.append([int(days), int(hours), int(minutes), is_use])
    return render_template('index.html', form=form, projects=projects, user_id=current_user.id, result=result)


@app.route('/projects/<int:user_id>/<int:project_id>', methods=['GET', 'POST'])
@login_required
def projects_func(user_id, project_id):
    if current_user.id == user_id:
        db_sess = db_session.create_session()
        form = AddTaskForm()
        project = db_sess.query(Project).get(project_id)
        if 'title_project' in request.values:
            project.title = request.values['title_project']
            project.github_link = request.values['github_link']
            db_sess.commit()
        if form.validate_on_submit():
            task = Task(title=form.title.data, project_id=project.id)
            project.tasks.append(task)
            db_sess.commit()
        result = []
        for task in project.tasks:
            days = divmod(task.duration, 86400)[0]
            hours = divmod(task.duration - days * 86400, 3600)[0]
            minutes = divmod(task.duration - hours * 3600 - days * 86400, 60)[0]
            result.append([int(days), int(hours), int(minutes)])
        return render_template('project.html', project=project, form=form, back='/main', result=result)
    else:
        return redirect('/main')


@app.route('/tasks/<int:user_id>/<int:project_id>/<int:task_id>', methods=['GET', 'POST'])
@login_required
def tasks_func(user_id, project_id, task_id):
    if current_user.id == user_id:
        db_sess = db_session.create_session()
        form = AddTaskForm()
        project = db_sess.query(Project).get(project_id)
        task = db_sess.query(Task).get(task_id)
        if form.validate_on_submit():
            task.title = form.title.data
            db_sess.commit()
        else:
            form.title.data = task.title
        return render_template('task.html', project=project, task=task, form=form, back=f"/projects/{user_id}/{project_id}")
    else:
        return redirect('/main')


@app.route('/api/delete-project', methods=['GET', 'POST'])
@login_required
def delete_project():
    if current_user.id == request.json['user_id']:
        db_sess = db_session.create_session()
        project = db_sess.query(Project).get(request.json['project_id'])
        db_sess.delete(project)
        db_sess.commit()
        return 'success'
    return 'access deny'


@app.route('/api/delete-task', methods=['GET', 'POST'])
@login_required
def delete_task():
    if current_user.id == request.json['user_id']:
        db_sess = db_session.create_session()
        project = db_sess.query(Project).get(request.json['project_id'])
        task = db_sess.query(Task).get(request.json['task_id'])
        project.tasks.remove(task)
        db_sess.commit()
        return 'success'
    return 'access deny'


@app.route('/api/start-stopwatch', methods=['GET', 'POST'])
@login_required
def start_stopwatch():
    if current_user.id == request.json['user_id']:
        db_sess = db_session.create_session()
        project = db_sess.query(Project).get(request.json['project_id'])
        task = db_sess.query(Task).get(request.json['task_id'])
        task.start_time = datetime.datetime.now()
        db_sess.commit()
        return 'success'
    return 'access deny'


@app.route('/api/stop-stopwatch', methods=['GET', 'POST'])
@login_required
def stop_stopwatch():
    if current_user.id == request.json['user_id']:
        db_sess = db_session.create_session()
        project = db_sess.query(Project).get(request.json['project_id'])
        task = db_sess.query(Task).get(request.json['task_id'])
        duration = datetime.datetime.now() - task.start_time
        seconds = duration.total_seconds()
        task.duration += seconds
        task.start_time = None
        db_sess.commit()
        days = divmod(task.duration, 86400)[0]
        hours = divmod(task.duration - days * 86400, 3600)[0]
        minutes = divmod(task.duration - hours * 3600 - days * 86400, 60)[0]
        return json.dumps({'days': days, 'hours': hours, 'minutes': minutes})
    return 'access deny'


@app.route('/api/reset-stopwatch', methods=['GET', 'POST'])
@login_required
def reset_stopwatch():
    if current_user.id == request.json['user_id']:
        db_sess = db_session.create_session()
        project = db_sess.query(Project).get(request.json['project_id'])
        task = db_sess.query(Task).get(request.json['task_id'])
        task.duration = 0
        task.start_time = None
        db_sess.commit()
        return 'success'
    return 'access deny'


def main():
    db_session.global_init('db/manage_time.db')
    db_sess = db_session.create_session()
    admin.add_view(MyModelView(User, db_sess))
    admin.add_view(MyModelView(Project, db_sess))
    admin.add_view(MyModelView(Task, db_sess))
    serve(app, host="0.0.0.0", port=5001)


if __name__ == '__main__':
    main()
