from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload
from sqlalchemy import func
from datetime import datetime

from ..models import User, Order, Product, OrderItem, Category, Cart
from ..extensions import db

admin_bp = Blueprint('admin', __name__)


# ======================
# HELPER: CHECK ADMIN
# ======================
def check_admin():
    if not current_user.is_authenticated or not current_user.is_admin:
        return False
    return True


# ======================
# USERS
# ======================
@admin_bp.route('/admin/users', methods=['GET'])
@login_required
def get_users():
    if not check_admin():
        return jsonify({"error": "Không có quyền"}), 403

    users = User.query.order_by(User.created_at.desc()).all()

    return jsonify([{
        "id": u.user_id,
        "username": u.username,
        "full_name": u.full_name or u.username,
        "email": u.email,
        "phone": u.phone or 'Chưa cập nhật',
        "role": u.role,
        "is_active": getattr(u, 'is_active', True),  # 🔥 THÊM DÒNG NÀY
        "created_at": u.created_at.strftime('%d/%m/%Y %H:%M') if u.created_at else None
    } for u in users])  # 🔥 SỬA DÒNG NÀY (thêm is_active)


# ======================
# PRODUCTS
# ======================

# GET ALL PRODUCTS
@admin_bp.route('/admin/products', methods=['GET'])
@login_required
def get_products():
    if not check_admin():
        return jsonify({"error": "Không có quyền"}), 403

    products = Product.query.all()

    return jsonify([{
        "id": p.product_id,
        "name": p.name,
        "price": float(p.price or 0),
        "stock": p.stock,
        "image": p.image or '',
        "description": p.description or '',
        "category_id": p.category_id,
        "created_at": p.created_at.strftime('%d/%m/%Y') if p.created_at else None
    } for p in products])


# CREATE PRODUCT
@admin_bp.route('/admin/products', methods=['POST'])
@login_required
def create_product():
    if not check_admin():
        return jsonify({"error": "Không có quyền"}), 403

    try:
        data = request.get_json()

        name = data.get('name')
        price = data.get('price')
        stock = data.get('stock', 0)
        description = data.get('description', '')
        image = data.get('image', '')
        category_id = data.get('category_id')

        if not name or price is None:
            return jsonify({"error": "Thiếu dữ liệu"}), 400

        product = Product(
            name=name,
            price=float(price),
            stock=int(stock),
            description=description,
            image=image,
            category_id=category_id,
            created_at=datetime.utcnow()
        )

        db.session.add(product)
        db.session.commit()

        return jsonify({
            "success": True, 
            "id": product.product_id,
            "message": "Đã thêm sản phẩm thành công"
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# GET PRODUCT DETAIL
@admin_bp.route('/admin/products/<int:product_id>', methods=['GET'])
@login_required
def get_product_detail(product_id):
    if not check_admin():
        return jsonify({"error": "Không có quyền"}), 403

    product = Product.query.get(product_id)

    if not product:
        return jsonify({"error": "Không tìm thấy sản phẩm"}), 404

    return jsonify({
        "id": product.product_id,
        "name": product.name,
        "price": float(product.price or 0),
        "stock": product.stock,
        "image": product.image or '',
        "description": product.description or '',
        "category_id": product.category_id
    })


# UPDATE PRODUCT
@admin_bp.route('/admin/products/<int:product_id>', methods=['PUT'])
@login_required
def update_product(product_id):
    if not check_admin():
        return jsonify({"error": "Không có quyền"}), 403

    try:
        product = Product.query.get(product_id)

        if not product:
            return jsonify({"error": "Không tìm thấy sản phẩm"}), 404

        data = request.get_json()

        product.name = data.get('name', product.name)
        product.price = float(data.get('price', product.price))
        product.stock = int(data.get('stock', product.stock))
        product.description = data.get('description', product.description)
        product.image = data.get('image', product.image)
        product.category_id = data.get('category_id', product.category_id)

        db.session.commit()

        return jsonify({
            "success": True, 
            "message": "Đã cập nhật sản phẩm"
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# DELETE PRODUCT (HARD DELETE - XÓA VĨNH VIỄN)
@admin_bp.route('/admin/products/<int:product_id>', methods=['DELETE'])
@login_required
def delete_product(product_id):
    if not check_admin():
        return jsonify({"error": "Không có quyền"}), 403

    try:
        print(f"🗑️ Đang xóa sản phẩm ID: {product_id}")
        
        product = Product.query.get(product_id)

        if not product:
            return jsonify({"error": "Không tìm thấy sản phẩm"}), 404

        # Xóa các cart items liên quan trước
        Cart.query.filter_by(product_id=product_id).delete()
        
        # Xóa các order items liên quan
        OrderItem.query.filter_by(product_id=product_id).delete()
        
        # Xóa sản phẩm
        db.session.delete(product)
        db.session.commit()
        
        print(f"✅ Đã xóa sản phẩm: {product.name}")

        return jsonify({
            "success": True,
            "message": f"Đã xóa sản phẩm '{product.name}'"
        })

    except Exception as e:
        db.session.rollback()
        print(f"❌ Lỗi khi xóa: {str(e)}")
        return jsonify({"error": str(e)}), 500


# ======================
# ORDERS
# ======================

# GET ALL ORDERS
@admin_bp.route('/admin/orders', methods=['GET'])
@login_required
def get_orders():
    if not check_admin():
        return jsonify({"error": "Không có quyền"}), 403

    orders = Order.query.options(
        joinedload(Order.user)
    ).order_by(Order.created_at.desc()).all()

    return jsonify([{
        "order_id": o.order_id,
        "user_name": o.user.username if o.user else "N/A",
        "total": float(o.total_price or 0),
        "status": o.status,
        "status_text": get_status_text(o.status),
        "created_at": o.created_at.strftime('%d/%m/%Y %H:%M') if o.created_at else None
    } for o in orders])


# GET ORDER DETAIL
@admin_bp.route('/admin/orders/<int:order_id>', methods=['GET'])
@login_required
def get_order_detail(order_id):
    if not check_admin():
        return jsonify({"error": "Không có quyền"}), 403

    o = Order.query.options(
        joinedload(Order.items).joinedload(OrderItem.product)
    ).get(order_id)

    if not o:
        return jsonify({"error": "Không tìm thấy đơn hàng"}), 404

    items = []
    for item in o.items:
        items.append({
            "product_name": item.product.name if item.product else "N/A",
            "quantity": item.quantity,
            "price": float(item.price or 0),
            "subtotal": float(item.subtotal or item.price * item.quantity)
        })

    return jsonify({
        "order_id": o.order_id,
        "total": float(o.total_price),
        "status": o.status,
        "status_text": get_status_text(o.status),
        "receiver_name": o.receiver_name,
        "receiver_phone": o.receiver_phone,
        "shipping_address": o.shipping_address,
        "order_note": o.order_note,
        "payment_method": o.payment_method,
        "created_at": o.created_at.strftime('%d/%m/%Y %H:%M') if o.created_at else None,
        "items": items
    })


# UPDATE ORDER STATUS
@admin_bp.route('/admin/orders/<int:order_id>/status', methods=['PUT'])
@login_required
def update_order_status(order_id):
    if not check_admin():
        return jsonify({"error": "Không có quyền"}), 403

    try:
        o = Order.query.get(order_id)

        if not o:
            return jsonify({"error": "Không tìm thấy đơn hàng"}), 404

        data = request.get_json()
        new_status = data.get('status')

        valid = ['pending', 'confirmed', 'shipping', 'completed', 'cancelled']
        if new_status not in valid:
            return jsonify({"error": "Trạng thái không hợp lệ"}), 400

        o.status = new_status
        db.session.commit()

        return jsonify({
            "success": True,
            "message": f"Đã cập nhật trạng thái thành {get_status_text(new_status)}"
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# ======================
# USER MANAGEMENT (THÊM MỚI)
# ======================

@admin_bp.route('/admin/users/<int:user_id>', methods=['PUT'])
@login_required
def update_user(user_id):
    if not check_admin():
        return jsonify({"error": "Không có quyền"}), 403

    try:
        user = User.query.get(user_id)

        if not user:
            return jsonify({"error": "Không tìm thấy người dùng"}), 404

        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Không nhận được dữ liệu"}), 400

        # Cập nhật các trường
        if 'full_name' in data:
            user.full_name = data['full_name']
        if 'phone' in data:
            user.phone = data['phone']
        if 'role' in data:
            role_value = data['role']
            if role_value == 'customer':
                role_value = 'user'
            if role_value in ['user', 'admin']:
                user.role = role_value
        if 'is_active' in data:
            user.is_active = data['is_active']

        db.session.commit()

        return jsonify({
            "success": True,
            "message": f"Đã cập nhật người dùng {user.username}"
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@admin_bp.route('/admin/users/<int:user_id>/status', methods=['PATCH'])
@login_required
def update_user_status(user_id):
    if not check_admin():
        return jsonify({"error": "Không có quyền"}), 403

    try:
        user = User.query.get(user_id)

        if not user:
            return jsonify({"error": "Không tìm thấy người dùng"}), 404

        data = request.get_json()
        is_active = data.get('is_active')

        if is_active is None:
            return jsonify({"error": "Thiếu trạng thái is_active"}), 400

        user.is_active = is_active
        db.session.commit()

        status_text = "mở khóa" if is_active else "khóa"
        return jsonify({
            "success": True,
            "message": f"Đã {status_text} tài khoản {user.username}"
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# ======================
# STATS
# ======================
@admin_bp.route('/admin/stats', methods=['GET'])
@login_required
def get_stats():
    if not check_admin():
        return jsonify({"error": "Không có quyền"}), 403

    total_users = User.query.count()
    total_products = Product.query.count()
    total_orders = Order.query.count()
    
    total_revenue = db.session.query(func.sum(Order.total_price))\
        .filter(Order.status == 'completed').scalar() or 0
    
    pending_orders = Order.query.filter_by(status='pending').count()
    admin_count = User.query.filter_by(role='admin').count()

    return jsonify({
        "total_users": total_users,
        "total_products": total_products,
        "total_orders": total_orders,
        "total_revenue": float(total_revenue),
        "pending_orders": pending_orders,
        "admin_count": admin_count
    })


# ======================
# HELPER FUNCTIONS
# ======================

def get_status_text(status):
    """Chuyển đổi status code thành text hiển thị"""
    status_map = {
        'pending': '⏳ Chờ xử lý',
        'confirmed': '✅ Đã xác nhận',
        'shipping': '🚚 Đang giao hàng',
        'completed': '🎉 Hoàn thành',
        'cancelled': '❌ Đã hủy'
    }
    return status_map.get(status, status)