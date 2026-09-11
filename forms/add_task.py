from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField
from wtforms.validators import DataRequired


class AddTaskForm(FlaskForm):
    title = StringField('Название', validators=[DataRequired()])
    submit = SubmitField('Добавить')
