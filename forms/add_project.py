from flask_wtf import FlaskForm
from wtforms import SubmitField, URLField, StringField
from wtforms.validators import DataRequired


class AddProjectForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    github_link = URLField('Github link(optional)')
    submit = SubmitField('Add')
