import os
import subprocess
import threading
from datetime import datetime


from flask import (
    Blueprint, render_template, flash, url_for, request, redirect,
    send_file, session, current_app
)
from flask_login import login_required
from werkzeug.utils import secure_filename

from app.forms import BackupForm

backup = Blueprint('backup', __name__, url_prefix='/admin')

def execute_command(command):
    try:
        result = subprocess.run(
            command, shell=True, check=True, capture_output=True, text=True, timeout=60
        )
        print(f"Command output: {result.stdout}")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e.stderr}")
        raise
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise

@backup.route('/backup', methods=['GET'])
@login_required
def backup_page():
    form = BackupForm()  # Создаем форму
    return render_template('admin/backup.html', form=form)  # Передаем форму в шаблон

@backup.route('/create', methods=['GET'])
@login_required
def backup_database():
    backup_dir = os.path.join(os.getcwd(), "backups")
    os.makedirs(backup_dir, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f"backup_{timestamp}.sql"
    backup_path = os.path.join(backup_dir, backup_filename)

    try:
        db_url = current_app.config['SQLALCHEMY_DATABASE_URI']
        with open(backup_path, 'w') as f:
            f.write("DROP SCHEMA public CASCADE;\nCREATE SCHEMA public;\n")

        subprocess.run(
            ['pg_dump', f'--dbname={db_url}'],
            stdout=open(backup_path, 'a'),
            stderr=subprocess.PIPE,
            check=True,
            text=True
        )
        session['backup_file'] = backup_filename
        flash('Бэкап успешно создан. Вы можете его скачать.', 'success')
    except subprocess.CalledProcessError as e:
        flash(f'Ошибка при создании бэкапа: {e.stderr}', 'danger')
    except Exception as e:
        flash(f'Ошибка: {str(e)}', 'danger')

    return redirect(url_for('backup.backup_page'))


@backup.route('/upload', methods=['POST', 'GET'])
@login_required
def upload_backup():
    form = BackupForm()

    if form.validate_on_submit():
        if 'file' not in request.files:
            flash('Нет файла в запросе', 'danger')
            return redirect(url_for('backup.backup_page'))

        file = request.files['file']
        if file.filename == '':
            flash('Файл не выбран', 'danger')
            return redirect(url_for('backup.backup_page'))

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            backup_path = os.path.join(os.getcwd(), "backups", filename)
            file.save(backup_path)

            db_url = current_app.config['SQLALCHEMY_DATABASE_URI']

            thread = threading.Thread(target=reset_schema_and_restore, args=(backup_path, db_url))
            thread.start()

            flash('Восстановление запущено. Пожалуйста, подождите.', 'success')
            return redirect(url_for('backup.backup_page'))

    return render_template('admin/backup.html', form=form)

@backup.route('/download', methods=['GET'])
@login_required
def download_backup():
    backup_filename = session.pop('backup_file', None)
    if not backup_filename:
        flash('Файл бэкапа не найден', 'danger')
        return redirect(url_for('backup.backup_page'))

    backup_path = os.path.join(os.getcwd(), "backups", backup_filename)
    return send_file(backup_path, as_attachment=True)

def reset_schema_and_restore(backup_path, db_url):
    try:
        print("Starting schema reset...")
        clear_schema_cmd = f'psql --dbname={db_url} -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"'
        execute_command(clear_schema_cmd)
        print("Schema reset complete.")

        print("Restoring from backup...")
        restore_cmd = f'psql --dbname={db_url} --file={backup_path}'
        execute_command(restore_cmd)
        print("Restore completed successfully.")
    except Exception as e:
        print(f"Error during restore: {e}")

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'sql'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
