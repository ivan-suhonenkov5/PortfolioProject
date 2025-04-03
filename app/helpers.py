import os
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import current_app
from wtforms.validators import ValidationError


def save_image(file, folder='avatars'):
    """Сохраняет изображения (аватарки)"""
    try:
        if not file or not file.filename:
            return None

        # Генерация имени
        ext = secure_filename(file.filename).split('.')[-1].lower()
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"img_{timestamp}.{ext}"

        # Путь сохранения
        save_path = os.path.join(
            current_app.config['UPLOAD_FOLDER'],
            folder,
            filename
        )
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        file.save(save_path)
        return filename
    except Exception as e:
        print(f"[ERROR][IMAGE] {str(e)}")
        return None


def save_pdf(file):
    """Сохраняет PDF-документы"""
    try:
        if not file or not file.filename:
            return None

        # Генерация имени
        ext = secure_filename(file.filename).split('.')[-1].lower()
        if ext != 'pdf':
            raise ValueError("Неверный формат файла")

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"doc_{timestamp}.pdf"

        # Путь сохранения
        save_path = os.path.join(
            current_app.config['UPLOAD_FOLDER'],
            'pdf',
            filename
        )
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        file.save(save_path)
        return filename
    except Exception as e:
        print(f"[ERROR][PDF] {str(e)}")
        return None


def delete_image(filename, folder):
    """Удаляет файлы по типу папки (avatars, pdf, images)"""
    if not filename:
        return False
    try:
        path = os.path.join(
            current_app.config['UPLOAD_FOLDER'],
            folder,
            filename
        )
        if os.path.exists(path):
            os.remove(path)
            return True
    except Exception as e:
        print(f"[ERROR][DELETE] {str(e)}")
    return False


class FileSize:
    """Валидатор размера файла"""

    def __init__(self, max_size, message=None):
        self.max_size = max_size
        self.message = message or f'Макс. размер: {max_size // 1024 // 1024}MB'

    def __call__(self, form, field):
        if field.data:
            file = field.data
            file.seek(0, 2)  # Переход в конец файла
            size = file.tell()
            file.seek(0)
            if size > self.max_size:
                raise ValidationError(self.message)


def save_video(file):
    try:
        print(f"Попытка сохранить видео: {file.filename}")

        if not file or file.filename == '':
            print("Файл не выбран или имя файла пустое")
            return None

        if not allowed_file(file.filename, {'mp4', 'mov', 'avi'}):
            print("Недопустимое расширение файла")
            return None

        upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'videos')
        print(f"Папка для сохранения: {upload_folder}")

        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder, exist_ok=True)
            print("Создана папка для видео")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"video_{timestamp}_{secure_filename(file.filename)}"
        file_path = os.path.join(upload_folder, filename)

        file.save(file_path)
        print(f"Файл сохранен: {file_path}")

        return filename

    except Exception as e:
        print(f"Ошибка при сохранении видео: {str(e)}")
        return None


def allowed_file(filename, allowed_extensions):
    """Проверка расширения файла"""
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in allowed_extensions

class OptionalIfExisting:
    """
    Кастомный валидатор для файловых полей,
    делает поле обязательным только если не существует текущего файла
    """
    def __init__(self, existing_field_name, message=None):
        self.existing_field_name = existing_field_name
        self.message = message or 'Поле обязательно для заполнения'

    def __call__(self, form, field):
        existing_value = getattr(form, self.existing_field_name).data
        if not field.data and not existing_value:
            raise ValidationError(self.message)

