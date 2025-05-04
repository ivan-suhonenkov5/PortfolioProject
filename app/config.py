import os
from flask_mail import Mail

class Config(object):
    APPNAME = "app"
    ROOT = os.path.abspath(APPNAME)
    UPLOAD_PATH = "static/uploads/"
    SERVER_PATH = ROOT + UPLOAD_PATH

    USER = os.environ.get("POSTGRES_USER", "postgres")
    PASSWORD = os.environ.get("POSTGRES_PASSWORD", "1234")
    HOST = os.environ.get("POSTGRES_HOST", "127.0.0.1")
    PORT = os.environ.get("POSTGRES_PORT", "5432")
    DB = os.environ.get("POSTGRES_DB", "resumedb")

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              'postgresql://postgres:1234@localhost:5432/resumedb'

    SECRET_KEY = "hfjsdkflsdfkjsdhfsdf3"
    SQLALCHEMY_TRACK_MODIFICATIONS = "True"
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = "hfjsdkflsdfkjsdhfsdf3"

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Путь к папке app/
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')  # Правильный путь
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB


    # Настройки для почты
    MAIL_SERVER = 'smtp.gmail.com'  # Сервер почты (для Gmail)
    MAIL_PORT = 587  # Порт для отправки почты
    MAIL_USE_TLS = True  # Использовать TLS
    MAIL_USE_SSL = False  # Не использовать SSL
    MAIL_USERNAME = 'ivansuhonenkov80@gmail.com'  # Твой email
    MAIL_PASSWORD = 'xpvg dbtm rxxb odjj '  # Пароль от email (или app password, если включена двухфакторная аутентификация)
    MAIL_DEFAULT_SENDER = 'ivansuhonenkov80@gmail.com'  # Адрес, с которого будут отправляться письма

    # Инициализация объекта mail
    mail = Mail()