from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from ..models.models import User, Role
from ..extensions import db, bcrypt
from ..forms import EditUserForm, CreateUserForm

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
    return render_template('admin/backup.html')

# Логи приложения
@admin.route('/admin/logs')
@login_required
def logs():
    if not is_admin():
        flash('Доступ запрещен', 'danger')
        return redirect('/')
    return render_template('admin/logs.html')

# Страницы пользователей
@admin.route('/admin/pages')
@login_required
def pages():
    if not is_admin():
        flash('Доступ запрещен', 'danger')
        return redirect('/')
    return render_template('admin/pages.html')
