from flask import Flask, render_template

from .bundles import register_bundles, bundles
from .extensions import db, migrate, login_manager, assets
from .config import Config

from .routes.user import user
from .routes.admin import admin
from .routes.student import student
import pdfkit
from flask_wtf.csrf import CSRFProtect
import os

pdfkit_path = os.getenv("WKHTMLTOPDF_PATH", "PythonProject/wkhtmltopdf/wkhtmltopdf.exe")
pdfkit_config = pdfkit.configuration(wkhtmltopdf=pdfkit_path)

def create_app(config_class=Config):
    app = Flask("__name__", template_folder='app/templates', static_folder='app/static')
    app.config.from_object(config_class)
    csrf = CSRFProtect(app)
    app.config['PDFKIT_CONFIG'] = pdfkit_config

    app.register_blueprint(user)
    app.register_blueprint(admin)
    app.register_blueprint(student)


    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    assets.init_app(app)
    app.run(debug=True, host='0.0.0.0', port=5000)

    # LOGIN MANAGER
    login_manager.login_view = "user.login"
    login_manager.login_message = "Необходимо авторизоваться!"
    login_manager.login_message_category = "info"

    # ASSETS
    register_bundles(assets, bundles)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cookies = {}

    with app.app_context():
        db.create_all()
        from pathlib import Path
        # Полный путь до папки uploads
        upload_dir = Path(app.config['UPLOAD_FOLDER'])
        # Создаем все недостающие папки (включая avatars/images/pdf)
        upload_dir.mkdir(parents=True, exist_ok=True)
        print(f"Папка загрузок: {upload_dir}")

    return app
