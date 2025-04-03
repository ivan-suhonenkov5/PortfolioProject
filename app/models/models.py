from ..extensions import db, login_manager
from flask_login import UserMixin
from datetime import datetime, timezone


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Промежуточная таблица для связи Work ↔ SearchMarker
work_markers = db.Table(
    'work_markers',
    db.Column('work_id', db.Integer, db.ForeignKey('works.id', ondelete="CASCADE"), primary_key=True),
    db.Column('marker_id', db.Integer, db.ForeignKey('search_markers.id', ondelete="CASCADE"), primary_key=True)
)


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), default=2)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))

    profile = db.relationship('Profile', backref='user', uselist=False, cascade='all, delete-orphan', lazy='joined')
    role = db.relationship('Role', backref=db.backref('users', lazy='dynamic'))

    def is_admin(self):
        return self.role.name == 'admin' if self.role else False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.profile:
            self.profile = Profile()


class Profile(db.Model):
    __tablename__ = 'profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    bio = db.Column(db.Text, nullable=True)
    avatar_url = db.Column(db.String(255), nullable=True)
    skills = db.Column(db.Text, nullable=True)
    education = db.Column(db.Text, nullable=True)
    experience = db.Column(db.Text, nullable=True)


class Work(db.Model):
    __tablename__ = 'works'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    title = db.Column(db.String(100), nullable=True)
    description = db.Column(db.Text, nullable=True)
    video_url = db.Column(db.String(255), nullable=True)

    # Поля для разных типов контента
    url = db.Column(db.String(500), nullable=True)  # Для ссылок
    file_url = db.Column(db.String(255), nullable=True)  # Для файлов (PDF, изображения)
    content_category = db.Column(db.String(50), nullable=False)  # Стандартные категории
    category = db.Column(db.String(50), nullable=True)  # Пользовательская категория
    order = db.Column(db.Integer, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    is_published = db.Column(db.Boolean, default=True)

    user = db.relationship('User', backref=db.backref('works', lazy='dynamic'))

    # Связь с маркерами
    markers = db.relationship('SearchMarker', secondary=work_markers, back_populates='works', lazy='dynamic')

    def get_category(self):
        """Возвращает либо стандартную, либо пользовательскую категорию"""
        return self.category if self.category else self.content_category


class SearchMarker(db.Model):
    __tablename__ = 'search_markers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    # Связь с Work
    works = db.relationship('Work', secondary=work_markers, back_populates='markers')


# class Certificate(db.Model):
#     __tablename__ = 'certificates'
#     id = db.Column(db.Integer, primary_key=True)
#     profile_id = db.Column(db.Integer, db.ForeignKey('profiles.id'), nullable=False)
#     title = db.Column(db.String(100), nullable=False)
#     description = db.Column(db.Text)
#     file_url = db.Column(db.String(255), nullable=False)
#     issued_at = db.Column(db.Date)
#
#     profile = db.relationship('Profile', backref='certificates')
