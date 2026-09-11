from flask_wtf import FlaskForm
from wtforms import SubmitField, URLField, StringField
from wtforms.validators import DataRequired, Optional, URL


class AddProjectForm(FlaskForm):
    title = StringField('Название', validators=[DataRequired()])
    github_link = URLField(
        'Ссылка на GitHub (необязательно)',
        validators=[Optional(), URL(require_tld=True, message='Введите корректную ссылку.')]
    )
    submit = SubmitField('Добавить')
