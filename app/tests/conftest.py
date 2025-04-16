# import pytest
# from app import create_app, db
# from ..models.models import User
#
#
# @pytest.fixture(scope='module')
# def test_client():
#     app = create_app()
#     app.config['TESTING'] = True
#     app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
#     app.config['WTF_CSRF_ENABLED'] = False
#     app.config['LOGIN_DISABLED'] = True  # если login_user используется — отключаем login_required
#
#     with app.test_client() as testing_client:
#         with app.app_context():
#             db.create_all()
#             yield testing_client
#             db.session.remove()
#             db.drop_all()
#
#
# @pytest.fixture
# def init_database():
#     """Создание пользователя для проверки дубликатов"""
#     # Удалим пользователя, если он уже есть
#     existing = User.query.filter_by(username='existing_user').first()
#     if existing:
#         db.session.delete(existing)
#         db.session.commit()
#
#     user = User(
#         username='existing_user',
#         email='existing@test.com',
#         password_hash='hashed_password',
#         role_id=2
#     )
#     db.session.add(user)
#     db.session.commit()
#
#     yield
#
#     db.session.remove()
#
# @pytest.fixture(scope='function', autouse=True)
# def clean_database():
#     yield
#     db.session.rollback()
#     for table in reversed(db.metadata.sorted_tables):
#         db.session.execute(table.delete())
#     db.session.commit()
