from flask import Blueprint, redirect, render_template, flash, url_for, request
from flask_login import login_user, logout_user, current_user
from urllib.parse import urlparse, urljoin

from ..forms import RegistrationForm, LoginForm
from ..extensions import db, bcrypt
from ..models.models import User

user = Blueprint("user", __name__)


def redirect_based_on_role():
    """Перенаправление в зависимости от роли пользователя"""
    if current_user.role.name == 'admin':
        return redirect(url_for('admin.dashboard'))
    else:
        return redirect(url_for('student.profile'))


def is_safe_url(target):
    """Проверка безопасности URL для перенаправления"""
    host_url = urlparse(request.host_url)
    redirect_url = urlparse(urljoin(request.host_url, target))
    return redirect_url.scheme in ('http', 'https') and \
        host_url.netloc == redirect_url.netloc


@user.route('/')
def home():
    logout_user()  # Разлогиниваем пользователя
    return redirect(url_for('user.login'))


@user.route('/user/register', methods=['POST', 'GET'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            flash("Пользователь с таким логином уже существует!", "danger")
            return render_template('user/register.html', form=form)

        user = User.query.filter_by(email=form.email.data).first()
        if user:
            flash("Пользователь с таким email уже существует!", "danger")
            return render_template('user/register.html', form=form)

        if form.password.data != form.confirm_password.data:
            flash("Пароли не совпадают!", "danger")
            return render_template('user/register.html', form=form)

        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')

        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            password_hash=hashed_password,
            role_id=2
        )

        try:
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash(f"Поздравляем, {form.username.data}! Вы успешно зарегистрированы", "success")
            return redirect_based_on_role()
        except Exception as e:
            db.session.rollback()
            flash(f"При регистрации произошла ошибка: {str(e)}", "danger")

    return render_template('user/register.html', form=form)



@user.route("/user/login", methods=["POST", "GET"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if user.is_blocked:
                flash("Ваша учётная запись заблокирована. Обратитесь к администратору. ivansuhonenkov80@gmail.com", "warning")
                return redirect(url_for("user.login"))

            if bcrypt.check_password_hash(user.password_hash, form.password.data):
                login_user(user, remember=form.remember.data)
                next_page = request.args.get('next')

                if next_page and is_safe_url(next_page):
                    return redirect(next_page)

                return redirect_based_on_role()

        flash("Ошибка входа. Проверьте логин и пароль!", "danger")
    return render_template("user/login.html", form=form)


@user.route("/user/logout")
def logout():
    logout_user()
    flash("Вы успешно вышли из системы", "success")
    return redirect(url_for("user.login"))
