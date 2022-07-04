import json
import datetime
from waitress import serve
import xlsxwriter
from flask import Flask, render_template, redirect, request, send_file, after_this_request
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
        if hasattr(current_user, 'id'):
            if current_user.id == 1:
                return True
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


@app.errorhandler(401)
def unauthorized(error):
    return redirect('/')


# function to login user
@app.route('/', methods=['GET', 'POST'])
def login():
    if hasattr(current_user, 'id'):
        return redirect('/main')
    db_sess = db_session.create_session()
    form = LoginForm()
    if form.validate_on_submit():
        user = db_sess.query(User).filter(User.login == form.login.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect("/main")
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
                                   message="Account with this login is already exists!",
                                   start=True)
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
        project = Project(title=form.title.data, github_link=form.github_link.data,
                          user_id=current_user.id)
        db_sess.add(project)
        db_sess.commit()
    projects = db_sess.query(Project).filter(Project.user == current_user).all()
    result = []
    for project in projects:
        seconds = 0
        is_use = False
        for task in project.tasks:
            seconds += task.duration
            if task.start_time:
                is_use = True
        day = divmod(seconds, 86400)[0]
        hour = divmod(seconds - day * 86400, 3600)[0]
        minute = divmod(seconds - hour * 3600 - day * 86400, 60)[0]
        result.append([int(day), int(hour), int(minute), is_use])
    return render_template('index.html', form=form, projects=projects, user_id=current_user.id,
                           result=result)


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
        return render_template('project.html', project=project, form=form, back='/main',
                               result=result)
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
        return render_template('task.html', project=project, task=task, form=form,
                               back=f"/projects/{user_id}/{project_id}")
    else:
        return redirect('/main')


@app.route('/unload-project/<int:user_id>/<int:project_id>', methods=['GET', 'POST'])
@login_required
def unload_project(user_id, project_id):
    if current_user.id == user_id:
        db_sess = db_session.create_session()
        project = db_sess.query(Project).get(project_id)
        tmp_durations_project = {}
        for task in project.tasks:
            tmp_durations_task = eval(task.duration_per_dates)
            for i in tmp_durations_task.keys():
                if i in tmp_durations_project.keys():
                    tmp_durations_project[i] += tmp_durations_task[i]
                else:
                    tmp_durations_project[i] = tmp_durations_task[i]
        create_unload_file(tmp_durations_project, project.title)
        return send_file('unload.xlsx', download_name=project.title + '.xlsx')
    else:
        return redirect('/main')


@app.route('/unload-task/<int:user_id>/<int:project_id>/<int:task_id>',
           methods=['GET', 'POST'])
@login_required
def unload_task(user_id, project_id, task_id):
    if current_user.id == user_id:
        db_sess = db_session.create_session()
        task = db_sess.query(Task).get(task_id)
        create_unload_file(eval(task.duration_per_dates), task.title)
        return send_file('unload.xlsx', download_name=task.title + '.xlsx')
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
        now = str(datetime.date.today())
        task = db_sess.query(Task).get(request.json['task_id'])
        tmp_durations_task = eval(task.duration_per_dates)
        duration = datetime.datetime.now() - task.start_time
        seconds = duration.total_seconds()
        task.duration += seconds
        if now not in tmp_durations_task.keys():
            tmp_durations_task[now] = seconds
        else:
            tmp_durations_task[now] += seconds
        task.duration_per_dates = str(tmp_durations_task)
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
        task.duration_per_dates = '{}'
        task.start_time = None
        db_sess.commit()
        return 'success'
    return 'access deny'


def create_unload_file(tmp_durations, title):
    tmp_durations_keys = list(tmp_durations.keys())
    workbook = xlsxwriter.Workbook('unload.xlsx')
    worksheet = workbook.add_worksheet(name=title)
    worksheet.write(0, 0, "Date")
    worksheet.write(1, 0, "Time, min")
    result = 0
    for i in range(len(tmp_durations_keys)):
        result += int(divmod(tmp_durations[tmp_durations_keys[i]], 60)[0])
        worksheet.write(0, i + 1, tmp_durations_keys[i])
        worksheet.write(1, i + 1, int(divmod(tmp_durations[tmp_durations_keys[i]], 60)[0]))
    worksheet.write(3, 0, "Result, min: ")
    worksheet.write(3, 1, result)
    workbook.close()


def main():
    db_session.global_init('db/manage_time.db')
    db_sess = db_session.create_session()
    admin.add_view(MyModelView(User, db_sess))
    admin.add_view(MyModelView(Project, db_sess))
    admin.add_view(MyModelView(Task, db_sess))
    serve(app, host="0.0.0.0", port=5001)


if __name__ == '__main__':
    main()
