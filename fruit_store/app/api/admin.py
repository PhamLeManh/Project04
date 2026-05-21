# app/api/admin.py
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.api import api_bp
from app.models import User, Product, Order, Category
from app.extensions import db
from sqlalchemy import func

@api_bp.route('/admin/stats', methods=['GET'])
@jwt_required()
def admin_stats():
    """Admin: Thống kê tổng quan"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or not user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        total_users = User.query.count()
        total_products = Product.query.count()
        total_orders = Order.query.count()
        
        total_revenue = db.session.query(func.sum(Order.total_price))\
            .filter(Order.status == 'completed').scalar() or 0
        
        pending_orders = Order.query.filter_by(status='pending').count()
        
        return jsonify({
            'total_users': total_users,
            'total_products': total_products,
            'total_orders': total_orders,
            'total_revenue': float(total_revenue),
            'pending_orders': pending_orders
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/admin/users', methods=['GET'])
@jwt_required()
def admin_get_users():
    """Admin: Lấy danh sách users"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or not user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        users = User.query.order_by(User.created_at.desc()).all()
        
        return jsonify([{
            'user_id': u.user_id,
            'username': u.username,
            'email': u.email,
            'full_name': u.full_name,
            'phone': u.phone,
            'role': u.role,
            'is_active': u.is_active,
            'created_at': u.created_at.isoformat() if u.created_at else None
        } for u in users]), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/admin/orders', methods=['GET'])
@jwt_required()
def admin_get_orders():
    """Admin: Lấy danh sách đơn hàng"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or not user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        orders = Order.query.order_by(Order.created_at.desc()).all()
        
        return jsonify([{
            'order_id': o.order_id,
            'user_name': o.user.full_name if o.user else 'N/A',
            'user_email': o.user.email if o.user else 'N/A',
            'total_price': float(o.total_price),
            'status': o.status,
            'status_text': get_status_text(o.status),
            'created_at': o.created_at.isoformat() if o.created_at else None
        } for o in orders]), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/admin/orders/<int:order_id>/status', methods=['PUT'])
@jwt_required()
def admin_update_order_status(order_id):
    """Admin: Cập nhật trạng thái đơn hàng"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or not user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        data = request.get_json()
        new_status = data.get('status')
        
        valid_statuses = ['pending', 'confirmed', 'shipping', 'completed', 'cancelled']
        if new_status not in valid_statuses:
            return jsonify({'error': 'Trạng thái không hợp lệ'}), 400
        
        order = Order.query.get(order_id)
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        
        order.status = new_status
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Đã cập nhật trạng thái thành {get_status_text(new_status)}'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/admin/users/<int:target_user_id>/status', methods=['PATCH'])
@jwt_required()
def admin_toggle_user_status(target_user_id):
    """Admin: Khóa/Mở khóa tài khoản user"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or not user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        target_user = User.query.get(target_user_id)
        if not target_user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        is_active = data.get('is_active')
        
        if is_active is None:
            return jsonify({'error': 'Thiếu is_active'}), 400
        
        target_user.is_active = is_active
        db.session.commit()
        
        status_text = "mở khóa" if is_active else "khóa"
        return jsonify({
            'success': True,
            'message': f'Đã {status_text} tài khoản {target_user.username}'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

def get_status_text(status):
    """Helper: Chuyển status code thành text"""
    status_map = {
        'pending': 'Chờ xử lý',
        'confirmed': 'Đã xác nhận',
        'shipping': 'Đang giao hàng',
        'completed': 'Hoàn thành',
        'cancelled': 'Đã hủy'
    }
    return status_map.get(status, status)