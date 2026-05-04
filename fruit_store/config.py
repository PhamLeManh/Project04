import os

class Config:
    # Secret key cho session
    SECRET_KEY = 'your-secret-key-here-change-in-production'
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:07022005@localhost/fruit_store'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload folder configuration
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'app/static/uploads')
    
    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    # Các cấu hình khác (nếu cần)
    DEBUG = True
    TESTING = False