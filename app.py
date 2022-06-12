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

app = Flask(__name__)
app.config['SECRET_KEY'] = 'top_secret_keyt'
login_manager = LoginManager()
login_manager.init_app(app)


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
        return render_template('login.html', form=form, message="Incorrect data!")
    return render_template('login.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    db_sess = db_session.create_session()
    form = RegisterForm()
    if form.validate_on_submit():
        check_already_exists = db_sess.query(User).filter(
            User.login == form.login.data).first()
        if check_already_exists:
            return render_template('register.html', form=form,
                                   message="Account with this login is already exists!")
        if form.password.data != form.password_again.data:
            return render_template('register.html', form=form,
                                   message="Passwords don't match!")
        user = User(login=form.login.data)
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        login_user(user)
        return redirect('/main')
    return render_template('register.html', form=form)


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
    return render_template('index.html', form=form, projects=projects, user_id=current_user.id)


@app.route('/projects/<int:user_id>/<int:project_id>', methods=['GET', 'POST'])
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
        return render_template('project.html', project=project, form=form)
    else:
        return redirect('/main')


@app.route('/tasks/<int:user_id>/<int:project_id>/<int:task_id>', methods=['GET', 'POST'])
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
        return render_template('task.html', project=project, task=task, form=form)
    else:
        return redirect('/main')


def main():
    db_session.global_init('db/manage_time.db')
    app.run()


if __name__ == '__main__':
    main()
