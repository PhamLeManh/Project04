# app/api/auth.py
from flask import request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app.api import api_bp
from app.models import User
from app.extensions import db
from datetime import timedelta

@api_bp.route('/auth/register', methods=['POST'])
def register():
    """Đăng ký tài khoản mới"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('username') or not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Thiếu thông tin bắt buộc'}), 400
        
        # Check existing user
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email đã tồn tại'}), 400
        
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Username đã tồn tại'}), 400
        
        # Create new user
        user = User(
            username=data['username'],
            email=data['email'],
            full_name=data.get('full_name', ''),
            phone=data.get('phone', ''),
            address=data.get('address', ''),
            role='user',
            is_active=True
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Đăng ký thành công',
            'user': {
                'user_id': user.user_id,
                'username': user.username,
                'email': user.email,
                'full_name': user.full_name,
                'role': user.role
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/auth/login', methods=['POST'])
def login():
    """Đăng nhập và nhận JWT token"""
    try:
        data = request.get_json()
        
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email và password là bắt buộc'}), 400
        
        # Find user by email
        user = User.query.filter_by(email=data['email']).first()
        
        # Check password and active status
        if not user or not user.check_password(data['password']):
            return jsonify({'error': 'Email hoặc mật khẩu không đúng'}), 401
        
        if not user.is_active:
            return jsonify({'error': 'Tài khoản đã bị khóa'}), 403
        
        # Create access token (sử dụng user_id làm identity)
        access_token = create_access_token(
            identity=user.user_id,
            expires_delta=timedelta(hours=24)
        )
        
        return jsonify({
            'success': True,
            'message': 'Đăng nhập thành công',
            'access_token': access_token,
            'token_type': 'Bearer',
            'user': {
                'user_id': user.user_id,
                'username': user.username,
                'email': user.email,
                'full_name': user.full_name,
                'role': user.role,
                'is_admin': user.is_admin
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/auth/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Lấy thông tin profile của user hiện tại"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'user_id': user.user_id,
            'username': user.username,
            'email': user.email,
            'full_name': user.full_name,
            'phone': user.phone,
            'address': user.address,
            'role': user.role,
            'is_admin': user.is_admin,
            'is_active': user.is_active,
            'created_at': user.created_at.isoformat() if user.created_at else None
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/auth/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Cập nhật thông tin profile"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        # Update allowed fields
        if 'full_name' in data:
            user.full_name = data['full_name']
        if 'phone' in data:
            user.phone = data['phone']
        if 'address' in data:
            user.address = data['address']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Cập nhật profile thành công',
            'user': {
                'user_id': user.user_id,
                'username': user.username,
                'email': user.email,
                'full_name': user.full_name,
                'phone': user.phone,
                'address': user.address
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500