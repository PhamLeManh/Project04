# app/extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_jwt_extended import JWTManager
from flask_cors import CORS

# Khởi tạo các extension
db = SQLAlchemy()
login_manager = LoginManager()
jwt = JWTManager()
cors = CORS()