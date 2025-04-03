from typing import re

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileRequired
from wtforms import StringField, PasswordField, SubmitField, FileField
from wtforms.fields.simple import BooleanField, HiddenField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Optional, Regexp
from wtforms import StringField, TextAreaField, FileField, SelectMultipleField, SelectField
from wtforms.validators import DataRequired, Length
from wtforms.validators import Optional, ValidationError, URL
from flask_login import current_user

from app.extensions import bcrypt
from app.helpers import FileSize, OptionalIfExisting
from app.models.models import User


class RegistrationForm(FlaskForm):
    first_name = StringField("Имя", validators=[DataRequired(), Length(min=2, max=50)])
    last_name = StringField("Фамилия", validators=[DataRequired(), Length(min=2, max=50)])
    username = StringField("Логин", validators=[
        DataRequired(),
        Length(min=2, max=50)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Пароль", validators=[DataRequired()])
    confirm_password = PasswordField(
        "Подтвердите пароль", validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Зарегистрироваться")

    def validate_username(self, username):
        if User.query.filter_by(username=username.data).first():
            raise ValidationError('Данное имя пользователя уже занято!')

    def validate_email(self, email):
        if User.query.filter_by(email=email.data).first():
            raise ValidationError('Данный email уже используется!')


class LoginForm(FlaskForm):
    username = StringField("Логин", validators=[DataRequired(), Length(min=2, max=50)])
    password = PasswordField("Пароль", validators=[DataRequired()])
    remember = BooleanField("Запомнить меня")
    submit = SubmitField("Войти")


class CreateUserForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired(), Length(min=2, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    first_name = StringField('Имя', validators=[DataRequired(), Length(min=2, max=50)])
    last_name = StringField('Фамилия', validators=[DataRequired(), Length(min=2, max=50)])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Подтвердите пароль', validators=[DataRequired(), EqualTo('password')])
    role_id = HiddenField('Роль', default=2)
    submit = SubmitField('Создать пользователя')


class EditUserForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired(), Length(min=2, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    first_name = StringField('Имя', validators=[DataRequired(), Length(min=2, max=50)])
    last_name = StringField('Фамилия', validators=[DataRequired(), Length(min=2, max=50)])
    role_id = SelectField('Роль', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Сохранить изменения')


class WorkForm(FlaskForm):
    CONTENT_TYPES = [
        ('category', 'Категория'),
        ('link', 'Ссылка'),
        ('pdf', 'PDF документ'),
        ('video', 'Видео'),
        ('image', 'Изображение')
    ]

    DEFAULT_CATEGORIES = [
        ('web_dev', 'Веб-разработка'),
        ('mobile_apps', 'Мобильные приложения'),
        ('ui_ux', 'Дизайн UI/UX'),
        ('ai', 'Искусственный интеллект'),
        ('databases', 'Базы данных')
    ]

    content_category = SelectField(
        'Тип контента',
        choices=CONTENT_TYPES,
        validators=[DataRequired()]
    )

    title = StringField('Название', validators=[
        Optional(),
        Length(max=100)
    ])

    description = TextAreaField('Описание', validators=[
        Optional(),
        Length(max=500)
    ])

    url = StringField('URL', validators=[
        Optional(),
        URL(message="Некорректный URL")
    ])

    file = FileField('Файл', validators=[
        Optional(),
        FileAllowed(['pdf', 'png', 'jpg', 'jpeg'], 'Допустимы только PDF, PNG, JPG/JPEG')
    ])

    video_file = FileField('Видеофайл', validators=[
        Optional(),
        FileAllowed(['mp4', 'mov', 'avi'], 'Только видеофайлы!')
    ])

    existing_video = HiddenField()
    existing_file = HiddenField()

    category = SelectField(
        'Категория',
        choices=DEFAULT_CATEGORIES,
        validators=[Optional()]
    )

    custom_category = StringField(
        'Или введите свою категорию',
        validators=[Optional(), Length(max=50)]
    )

    markers = StringField('Маркеры', validators=[Optional()])

    submit = SubmitField('Сохранить')

    def validate(self, extra_validators=None):
        if not super().validate(extra_validators=extra_validators):
            return False

        content_type = self.content_category.data
        is_edit = hasattr(self, 'work') and self.work is not None

        if content_type == 'video':
            if not is_edit and not self.video_file.data:
                self.video_file.errors.append('Загрузите видеофайл')
                return False
            if is_edit and not self.video_file.data and not self.work.video_url:
                self.video_file.errors.append('Загрузите видеофайл или используйте текущий')
                return False

        elif content_type in ['pdf', 'image']:
            if not is_edit and not self.file.data:
                self.file.errors.append('Загрузите файл')
                return False
            if is_edit and not self.file.data and not self.work.file_url:
                self.file.errors.append('Загрузите файл или используйте текущий')
                return False

        if content_type == 'category':
            return True

        if content_type == 'link' and not self.url.data:
            self.url.errors.append('Обязательное поле')
            return False

        if not self.category.data and not self.custom_category.data:
            self.category.errors.append('Выберите категорию или введите свою')
            return False

        return True


class ProfileForm(FlaskForm):
    first_name = StringField('Имя', validators=[DataRequired()])
    last_name = StringField('Фамилия', validators=[DataRequired()])
    avatar = FileField('Аватар', validators=[FileAllowed(['jpg', 'jpeg', 'png'])])
    bio = TextAreaField('О себе')
    submit = SubmitField('Обновить')


class ProfileEditForm(FlaskForm):
    # User fields
    username = StringField('Логин', validators=[
        DataRequired(),
        Length(min=3, max=50),
        Regexp('^[A-Za-z0-9_]+$', message='Только буквы, цифры и подчеркивания')
    ])
    email = StringField('Email', validators=[
        DataRequired(),
        Email(),
        Length(max=100)
    ])
    first_name = StringField('Имя', validators=[
        DataRequired(),
        Length(max=50)
    ])
    last_name = StringField('Фамилия', validators=[
        DataRequired(),
        Length(max=50)
    ])

    # Password change fields
    current_password = PasswordField('Текущий пароль (для изменений)', validators=[Optional()])
    new_password = PasswordField('Новый пароль', validators=[
        Optional(),
        Length(min=6)
    ])
    confirm_password = PasswordField('Подтвердите новый пароль', validators=[
        EqualTo('new_password', message='Пароли должны совпадать')
    ])

    # Profile fields
    bio = TextAreaField('О себе', validators=[Length(max=1000)])
    avatar = FileField('Аватар', validators=[
        FileAllowed(['jpg', 'jpeg', 'png'], 'Только изображения!'),
        FileSize(max_size=5 * 1024 * 1024, message='Макс. размер 5 МБ')  # Используем наш класс
    ])
    skills = StringField('Навыки', validators=[Length(max=255)])
    education = TextAreaField('Образование', validators=[Length(max=500)])
    experience = TextAreaField('Опыт работы', validators=[Length(max=500)])

    submit = SubmitField('Сохранить изменения')

    def validate_username(self, field):
        if field.data != current_user.username:
            user = User.query.filter_by(username=field.data).first()
            if user:
                raise ValidationError('Этот логин уже занят')

    def validate_email(self, field):
        if field.data != current_user.email:
            user = User.query.filter_by(email=field.data).first()
            if user:
                raise ValidationError('Этот email уже используется')

    def validate_current_password(self, field):
        if self.new_password.data:
            if not bcrypt.check_password_hash(current_user.password_hash, field.data):
                raise ValidationError('Неверный текущий пароль')


class SearchForm(FlaskForm):
    query = StringField("Поиск по маркерам", validators=[DataRequired(), Length(max=100)])
    submit = SubmitField("Найти")
