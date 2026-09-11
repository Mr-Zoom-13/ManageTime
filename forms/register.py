from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, EqualTo, Length


class RegisterForm(FlaskForm):
    login = StringField(
        'Логин', validators=[DataRequired(), Length(min=3, max=64)]
    )
    password = PasswordField(
        'Пароль', validators=[DataRequired(), Length(min=8, message='Минимум 8 символов.')]
    )
    password_again = PasswordField(
        'Повторите пароль',
        validators=[DataRequired(), EqualTo('password', message='Пароли должны совпадать.')]
    )
    submit = SubmitField('Зарегистрироваться')
