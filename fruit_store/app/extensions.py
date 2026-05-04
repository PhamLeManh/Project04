from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# Khởi tạo các extension
db = SQLAlchemy()
login_manager = LoginManager()

# KHÔNG cấu hình ở đây vì sẽ được cấu hình trong create_app
# Các dòng dưới đây sẽ được chuyển vào __init__.py