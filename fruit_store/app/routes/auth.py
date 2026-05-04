from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from ..models import User
from ..extensions import db

auth = Blueprint('auth', __name__)

# 👉 ĐÃ XÓA @login_manager.user_loader (vì đã có trong extensions.py)

@auth.route('/register', methods=['POST'])
def register():
    data = request.json
    # Kiểm tra user đã tồn tại chưa
    if User.query.filter_by(email=data['email']).first():
        return jsonify({"message": "Email đã tồn tại"}), 400
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({"message": "Username đã tồn tại"}), 400
    
    user = User(
        username=data['username'],
        email=data['email'],
        role='user'  # Mặc định là user
    )
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "Đăng ký thành công"})

@auth.route('/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(email=data['email']).first()

    if user and user.check_password(data['password']):
        login_user(user)
        return jsonify({
            "message": "Đăng nhập thành công",
            "role": user.role,
            "is_admin": user.is_admin
        })

    return jsonify({"message": "Sai email hoặc mật khẩu"}), 401

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Đăng xuất thành công"})

# Route cho UI
@auth.route('/login-page')
def login_page():
    return render_template('auth/login.html')

@auth.route('/register-page')
def register_page():
    return render_template('auth/register.html')