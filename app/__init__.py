import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, request
from .bundles import register_bundles, bundles
from .extensions import db, migrate, login_manager, assets
from .config import Config
from .routes.user import user
from .routes.admin import admin
from .routes.student import student
from .routes.backup import backup
import pdfkit
from flask_wtf.csrf import CSRFProtect
import os
import traceback
import atexit
from pathlib import Path
from flask_mail import Mail
# Настройка pdfkit
pdfkit_config = pdfkit.configuration(wkhtmltopdf=r'wkhtmltopdf.exe')


def create_app(config_class=Config):
    app = Flask("__name__", template_folder='app/templates', static_folder='app/static')
    app.config.from_object(config_class)

    mail = Mail(app)

    # Настройка CSRF защиты
    csrf = CSRFProtect(app)
    app.config['PDFKIT_CONFIG'] = pdfkit_config

    # Настройка логирования
    log_handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=3, encoding='utf-8')
    log_handler.setLevel(logging.INFO)  # Можно настроить на ERROR или INFO
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    log_handler.setFormatter(formatter)
    app.logger.addHandler(log_handler)
    app.logger.setLevel(logging.INFO)

    # Логирование всех запросов
    @app.after_request
    def log_request(response):
        app.logger.info(f"Request: {request.method} {request.path} - Status: {response.status_code}")
        return response

    # Обработка ошибок и логирование traceback
    @app.errorhandler(Exception)
    def handle_exception(e):
        tb = traceback.format_exc()
        app.logger.error(f"Exception occurred: {str(e)}\n{tb}")
        return "Произошла ошибка. Попробуйте снова позже.", 500

    # Очистка логов при остановке приложения
    def cleanup_logs():
        open('app.log', 'w').close()

    atexit.register(cleanup_logs)

    # Регистрация Blueprints
    app.register_blueprint(user)
    app.register_blueprint(admin)
    app.register_blueprint(student)
    app.register_blueprint(backup)

    # Инициализация расширений
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    assets.init_app(app)

    # LOGIN MANAGER
    login_manager.login_view = "user.login"
    login_manager.login_message = "Необходимо авторизоваться!"
    login_manager.login_message_category = "info"

    # ASSETS
    register_bundles(assets, bundles)

    # Создание всех недостающих папок
    with app.app_context():
        db.create_all()

        upload_dir = Path(app.config['UPLOAD_FOLDER'])
        upload_dir.mkdir(parents=True, exist_ok=True)
        print(f"Папка загрузок: {upload_dir}")

    return app
