import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'emp-mgmt-secret-key-2026')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'employee.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'img', 'avatars')
    QR_FOLDER = os.path.join(BASE_DIR, 'static', 'qrcodes')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
