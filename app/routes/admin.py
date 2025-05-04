import os

from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from ..models.models import User, Role
from ..extensions import db, bcrypt
from ..forms import EditUserForm, CreateUserForm, BackupForm
from flask_mail import Message
from ..extensions import mail

admin = Blueprint('admin', __name__)


def is_admin():
    """Проверка что текущий пользователь админ"""
    return current_user.is_authenticated and \
        current_user.role and \
        current_user.role.name == 'admin'


# Главная страница админки
@admin.route('/admin/dashboard')
@login_required
def dashboard():
    if not is_admin():
        flash('Доступ запрещен', 'danger')
        return redirect('/')
    return render_template('admin/dashboard.html')


# Список пользователей
@admin.route('/admin/users')
@login_required
def users():
    if not is_admin():
        flash('Доступ запрещен', 'danger')
        return redirect('/')

    users = User.query.all()
    return render_template('admin/users.html', users=users)


# Создание пользователя
@admin.route('/admin/users/create', methods=['GET', 'POST'])
@login_required
def create_user():
    if not is_admin():
        flash('Доступ запрещен', 'danger')
        return redirect('/')

    form = CreateUserForm()  # Больше не нужно заполнять choices!

    if form.validate_on_submit():
        try:
            # Проверка уникальности email
            if User.query.filter_by(email=form.email.data).first():
                flash('Этот email уже зарегистрирован', 'danger')
                return redirect(url_for('admin.create_user'))

            # Проверка совпадения паролей
            if form.password.data != form.confirm_password.data:
                flash('Пароли не совпадают', 'danger')
                return redirect(url_for('admin.create_user'))

            user = User(
                username=form.username.data,
                email=form.email.data,
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                password_hash=bcrypt.generate_password_hash(form.password.data).decode('utf-8'),
                role_id=form.role_id.data  # Берем значение из hidden-поля
            )

            db.session.add(user)
            db.session.commit()
            flash('Пользователь успешно создан', 'success')
            return redirect(url_for('admin.users'))

        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при создании пользователя: {str(e)}', 'danger')

    return render_template('admin/create_user.html', form=form)




# Редактирование пользователя
@admin.route('/admin/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if not is_admin():
        flash('Доступ запрещен', 'danger')
        return redirect('/')

    user = User.query.get_or_404(user_id)
    form = EditUserForm(obj=user)
    form.role_id.choices = [(r.id, r.name) for r in Role.query.all()]

    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        user.role_id = form.role_id.data

        db.session.commit()
        flash('Данные пользователя обновлены', 'success')
        return redirect(url_for('admin.users'))

    return render_template('admin/edit_user.html', form=form, user=user)



@admin.route('/admin/users/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if not is_admin():
        flash('Доступ запрещен', 'danger')
        return redirect('/')

    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('Пользователь успешно удален', 'success')
    return redirect(url_for('admin.users'))

# Бэкап
@admin.route('/admin/backup')
@login_required
def backup():
    if not is_admin():
        flash('Доступ запрещен', 'danger')
        return redirect('/')

    form = BackupForm()  # Создаем форму
    return render_template('admin/backup.html', form=form)  # Передаем форму в шаблон

# Страницы пользователей
@admin.route('/admin/pages')
@login_required
def pages():
    if not is_admin():
        flash('Доступ запрещен', 'danger')
        return redirect('/')
    return render_template('admin/pages.html')


@admin.route("/logs")
@login_required
def show_logs():
    if current_user.role.name != "admin":
        return redirect(url_for("user.login"))

    log_file_path = 'app.log'
    logs = []
    try:
        if os.path.exists(log_file_path):
            with open(log_file_path, 'r', encoding='utf-8') as log_file:
                logs = log_file.readlines()
        else:
            logs = ["No logs available."]
    except UnicodeDecodeError:
        logs = ["Error reading log file due to encoding issues."]

    return render_template("admin/logs.html", logs=logs)

@admin.route('/admin/users/block/<int:user_id>', methods=['POST'])
@login_required
def toggle_block_user(user_id):
    if not is_admin():
        flash('Доступ запрещен', 'danger')
        return redirect('/')

    user = User.query.get_or_404(user_id)
    user.is_blocked = not user.is_blocked  # Переключаем статус блокировки

    # Отправляем письмо пользователю, если его заблокировали
    if user.is_blocked:
        send_block_notification(user)

    db.session.commit()
    return redirect(url_for('admin.users'))

def send_block_notification(user):
    """Отправка уведомления на почту о блокировке"""
    msg = Message(
        subject="Вы были заблокированы",
        recipients=[user.email],
        body=f"Здравствуйте, {user.username}. Ваш аккаунт был заблокирован администратором. Если это ошибка, обратитесь к поддержке по этому адресу ivansuhonenkov80@gmail.com"
    )
    try:
        mail.send(msg)
    except Exception as e:
        flash(f"Ошибка при отправке уведомления: {str(e)}", 'danger')
