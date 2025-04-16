import os
import re
from urllib import request
from flask import current_app
from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, jsonify, Response
from flask_login import login_required, current_user
from ..models.models import Work, SearchMarker, Profile, work_markers, User
from ..forms import WorkForm, ProfileForm, ProfileEditForm, SearchForm
from ..extensions import db, bcrypt
from ..helpers import save_image, delete_image, save_pdf, save_video
from flask import send_from_directory
from werkzeug.utils import safe_join
from flask import abort
import pdfkit

student = Blueprint('student', __name__)


@student.route('/student/dashboard')
@login_required
def dashboard():
    return render_template('student/dashboard.html')


@student.route('/works')
@login_required
def works():
    works = current_user.works.filter_by(is_published=True).all()
    return render_template('student/works.html', works=works)


@student.route('/works/new', methods=['GET', 'POST'])
@login_required
def new_work():
    form = WorkForm()
    selected_type = request.args.get('type', 'category')

    if request.method == 'GET':
        form.content_category.data = selected_type

    if form.validate_on_submit():
        try:
            # Если пользователь ввел свою категорию, используем её, иначе используем выбранную из списка
            category = form.custom_category.data if form.custom_category.data else form.category.data

            # Получение максимального значения order для текущего пользователя
            max_order = db.session.query(db.func.max(Work.order)).filter_by(user_id=current_user.id).scalar()
            next_order = (max_order or 0) + 1  # Если max_order == None, начинаем с 1

            new_work = Work(
                user_id=current_user.id,
                content_category=form.content_category.data,
                category=category,
                is_published=True,
                title=form.title.data if form.content_category.data != 'category' else None,
                description=form.description.data if form.content_category.data != 'category' else None,
                url=form.url.data if form.content_category.data == 'link' else None,
                order=next_order  # Присваиваем значение order
            )

            # Обработка видео
            if form.content_category.data == 'video':
                video_file = form.video_file.data
                if video_file:
                    filename = save_video(video_file)
                    new_work.video_url = filename
                else:
                    flash('Выберите видеофайл', 'danger')
                    return redirect(url_for('student.new_work'))

            # Обработка файлов (PDF/Image)
            elif form.content_category.data in ['pdf', 'image'] and form.file.data:
                if form.content_category.data == 'pdf':
                    filename = save_pdf(form.file.data)
                else:
                    filename = save_image(form.file.data, folder='images')

                if not filename:
                    flash('Не удалось сохранить файл', 'danger')
                    return redirect(url_for('student.new_work'))
                new_work.file_url = filename

            db.session.add(new_work)
            db.session.flush()  # Проверка ошибок перед коммитом

            # Обработка маркеров
            if form.content_category.data in ['video', 'pdf', 'image']:
                marker_list = [m.strip().lower() for m in form.markers.data.split(',') if m.strip()]

                for marker_text in marker_list:
                    marker = SearchMarker.query.filter_by(name=marker_text).first()
                    if not marker:
                        marker = SearchMarker(name=marker_text)
                        db.session.add(marker)

                    if marker not in new_work.markers:
                        new_work.markers.append(marker)

            db.session.commit()
            flash('Работа успешно сохранена!', 'success')
            return redirect(url_for('student.profile'))

        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка: {str(e)}', 'danger')
            current_app.logger.error(f'Error saving work: {str(e)}')

    return render_template('student/new_work.html', form=form)


@student.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    # Гарантируем создание профиля
    if not current_user.profile:
        current_user.profile = Profile()
        db.session.commit()

    # Получаем все работы пользователя, которые опубликованы
    works = current_user.works.filter_by(is_published=True).order_by(Work.order).all()

    # Получаем уникальные категории, привязанные к пользователю
    categories = {work.category for work in works if work.category}

    # Извлекаем категорию из параметров запроса (если есть)
    selected_category = request.args.get('category', None)

    # Фильтрация работ по выбранной категории
    if selected_category:
        works = [work for work in works if work.category == selected_category]

    form = ProfileForm(obj=current_user)
    form.bio.data = current_user.profile.bio  # Предзаполняем bio

    if form.validate_on_submit():
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data

        if form.avatar.data:
            # Удаляем старый аватар перед сохранением нового
            if current_user.profile.avatar_url:
                delete_image(current_user.profile.avatar_url, 'avatars')

            # Сохраняем новый
            filename = save_image(form.avatar.data)
            if filename:
                current_user.profile.avatar_url = filename
                db.session.commit()
        flash('Профиль обновлен!', 'success')
        return redirect(url_for('student.profile'))

    return render_template('student/profile.html',
                           form=form,
                           profile=current_user.profile,
                           works=works,
                           categories=categories)


@student.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = ProfileEditForm()

    # Гарантируем существование профиля
    if not current_user.profile:
        current_user.profile = Profile()
        db.session.commit()

    # Заполняем форму данными
    if request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.first_name.data = current_user.first_name
        form.last_name.data = current_user.last_name
        form.bio.data = current_user.profile.bio
        form.skills.data = current_user.profile.skills
        form.education.data = current_user.profile.education
        form.experience.data = current_user.profile.experience

    # Если форма валидна при сабмите
    if form.validate_on_submit():
        try:
            # Обновляем User
            current_user.username = form.username.data
            current_user.email = form.email.data
            current_user.first_name = form.first_name.data
            current_user.last_name = form.last_name.data

            # Обновляем Profile
            current_user.profile.bio = form.bio.data
            current_user.profile.skills = form.skills.data
            current_user.profile.education = form.education.data
            current_user.profile.experience = form.experience.data

            # Явно добавляем профиль в сессию
            db.session.add(current_user.profile)

            # Проверка пароля, если указан новый
            if form.new_password.data:
                if not form.current_password.data:
                    flash('Для изменения пароля нужно указать текущий пароль', 'danger')
                    return redirect(url_for('student.edit_profile'))  # Переходим обратно на страницу редактирования

                # Проверка текущего пароля
                if not bcrypt.check_password_hash(current_user.password_hash, form.current_password.data):
                    flash('Неверный текущий пароль', 'danger')
                    return redirect(url_for('student.edit_profile'))  # Переходим обратно на страницу редактирования

                # Проверка нового пароля на количество символов и наличие строчных букв
                new_password = form.new_password.data
                if len(new_password) < 8:
                    flash('Пароль должен содержать хотя бы 8 символов', 'danger')
                    return redirect(url_for('student.edit_profile'))  # Переходим обратно на страницу редактирования

                if not re.search(r'[a-z]', new_password):
                    flash('Пароль должен содержать хотя бы одну строчную букву', 'danger')
                    return redirect(url_for('student.edit_profile'))  # Переходим обратно на страницу редактирования

                # Генерация нового хэша пароля
                current_user.password_hash = bcrypt.generate_password_hash(
                    new_password
                ).decode('utf-8')

            # Обновляем аватар, если есть
            if form.avatar.data:
                if current_user.profile.avatar_url:
                    delete_image(current_user.profile.avatar_url, 'avatars')
                filename = save_image(form.avatar.data, 'avatars')
                current_user.profile.avatar_url = filename

            # Сохраняем изменения
            db.session.commit()
            flash('Профиль успешно обновлен!', 'success')
            return redirect(url_for('student.profile'))

        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка обновления: {str(e)}', 'danger')
            current_app.logger.error(f'Profile update error: {str(e)}')

    return render_template('student/edit_profile.html', form=form)

@student.route('/download/<path:filename>')
@login_required
def download_file(filename):
    # Убедитесь, что конфигурация UPLOAD_FOLDER существует
    upload_folder = current_app.config['UPLOAD_FOLDER']

    # Безопасное объединение путей
    target_folder = safe_join(upload_folder, os.path.dirname(filename))
    file_name = os.path.basename(filename)

    return send_from_directory(
        directory=target_folder,
        path=file_name,
        as_attachment=False,
        download_name=file_name
    )


@student.route('/pdf/<filename>')
@login_required
def view_pdf(filename):
    pdf_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'pdf')
    file_path = safe_join(pdf_folder, filename)
    if not os.path.isfile(file_path):
        abort(404)
    return send_file(file_path, mimetype='application/pdf')


@student.route('/profile/<int:user_id>/organize', methods=['GET', 'POST'])
@login_required
def organize_works(user_id):
    if user_id != current_user.id:
        # Проверка прав доступа (чтобы нельзя было изменять чужие данные)
        return redirect(url_for('student.profile', user_id=user_id))
    user = User.query.get(user_id)
    if request.method == 'POST':
        data = request.json
        new_order = data.get("order")

        if not new_order:
            return jsonify({"status": "error", "message": "Нет данных для обновления"}), 400

        works = {work.id: work for work in Work.query.filter_by(user_id=user_id).all()}

        for index, work_id in enumerate(new_order):
            if int(work_id) in works:
                works[int(work_id)].order = index

        db.session.commit()
        return jsonify({"status": "success"}), 200

    # GET-запрос - отображение страницы
    works = Work.query.filter_by(user_id=user_id).order_by(Work.order.asc().nulls_last()).all()
    works_data = [
        {"id": w.id, "title": w.title, "content_category": w.content_category or "", "category": w.category or "",
         "order": w.order or 0}
        for w in works
    ]

    return render_template("student/organize_works.html", works=works_data, user_id=user_id)


@student.route('/search', methods=['GET', 'POST'])
def search():
    form = SearchForm()
    works = []

    if form.validate_on_submit():
        query = form.query.data.strip()
        words = query.split()
        works = Work.query.join(work_markers).join(SearchMarker).filter(
            SearchMarker.name.in_(words)
        ).all()
    else:
        query = request.args.get('q', '').strip()  # Для поддержки GET-запросов

    return render_template('student/search.html', form=form, works=works, query=query or "")


@student.route('/profile/<int:user_id>', methods=['GET'])
def view_profile(user_id):
    user = User.query.get_or_404(user_id)

    works_query = user.works.filter_by(is_published=True).order_by(Work.order)

    user_categories = db.session.query(Work.category).filter(Work.user_id == user.id).distinct().all()
    user_categories = [category[0] for category in user_categories]
    category_filter = request.args.get('category')
    if category_filter:
        works_query = works_query.filter_by(category=category_filter)

    works = works_query.all()

    return render_template('student/view_profile.html', user=user, works=works, user_categories=user_categories)


@student.route('/download_resume/<username>')
def download_resume(username):
    # Получаем пользователя по username
    user = User.query.filter_by(username=username).first_or_404()
    profile = user.profile  # Получаем профиль пользователя

    # Генерация PDF из шаблона
    html_content = render_template('student/resume_template.html', user=user, profile=profile)

    # Генерация PDF
    config = current_app.config['PDFKIT_CONFIG']
    pdf = pdfkit.from_string(html_content, False, configuration=config)

    # Отправка PDF файла
    return Response(pdf, mimetype='application/pdf', headers={'Content-Disposition': 'attachment; filename=resume.pdf'})


@student.route('/works/<int:work_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_work(work_id):
    work = Work.query.get_or_404(work_id)
    if work.user_id != current_user.id:
        abort(403)

    form = WorkForm(obj=work)
    form.work = work  # Добавляем объект работы в форму

    # Предзаполнение данных для GET-запроса
    if request.method == 'GET':
        form.markers.data = ', '.join(m.name for m in work.markers)
        form.content_category.data = work.content_category

        # Предзаполнение категории
        if work.content_category != 'category':
            for value, label in form.category.choices:
                if label == work.category:
                    form.category.data = value
                    break
            else:
                form.custom_category.data = work.category

    # Обработка отправки формы
    if form.validate_on_submit():
        try:
            # Обновление базовых полей
            work.content_category = form.content_category.data
            work.category = form.custom_category.data or form.category.data
            work.title = form.title.data if form.content_category.data != 'category' else None
            work.description = form.description.data if form.content_category.data != 'category' else None
            work.url = form.url.data if form.content_category.data == 'link' else None

            # Обработка файлов
            def update_file(field, folder, attr):
                if field.data:
                    if getattr(work, attr):
                        delete_image(getattr(work, attr), folder)
                    filename = save_image(field.data, folder) if attr == 'file_url' else save_video(field.data)
                    setattr(work, attr, filename)

            if form.content_category.data == 'video':
                update_file(form.video_file, 'videos', 'video_url')
            elif form.content_category.data == 'pdf':
                update_file(form.file, 'pdf', 'file_url')
            elif form.content_category.data == 'image':
                update_file(form.file, 'images', 'file_url')

            # Обновление маркеров
            if form.content_category.data in ['video', 'pdf', 'image']:
                markers = [m.strip() for m in form.markers.data.split(',') if m.strip()]
                work.markers = []
                for m in markers:
                    marker = SearchMarker.query.filter_by(name=m).first()
                    if not marker:
                        marker = SearchMarker(name=m)
                        db.session.add(marker)
                        db.session.flush()
                    work.markers.append(marker)

            db.session.commit()
            flash('Изменения успешно сохранены!', 'success')
            return redirect(url_for('student.profile'))

        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при сохранении: {str(e)}', 'danger')

    return render_template('student/edit_work.html', form=form, work=work)


@student.route('/work/delete/<int:work_id>', methods=['POST'])
@login_required
def delete_work(work_id):
    work = Work.query.get_or_404(work_id)

    if work.user_id != current_user.id:
        abort(403)

    db.session.delete(work)
    db.session.commit()
    flash('Работа удалена!', 'success')
    return redirect(url_for('student.profile'))
