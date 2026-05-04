from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from sqlalchemy.orm import joinedload
from sqlalchemy import func

from ..models import Cart, Product, Order, OrderItem
from ..extensions import db

order = Blueprint('order', __name__)

# =========================
# USER: CHECKOUT
# =========================
@order.route('/checkout', methods=['POST'])
@login_required
def checkout():
    try:
        if not request.is_json:
            return jsonify({"success": False, "message": "Invalid request"}), 400

        data = request.get_json()

        receiver_name = data.get('receiver_name')
        receiver_phone = data.get('receiver_phone')
        shipping_address = data.get('shipping_address')
        order_note = data.get('order_note')
        payment_method = data.get('payment_method', 'cod')

        if not receiver_name or not receiver_phone or not shipping_address:
            return jsonify({"success": False, "message": "Thiếu thông tin"}), 400

        # Lấy giỏ hàng từ DB (KHÔNG tin frontend)
        cart_items = Cart.query.filter_by(user_id=current_user.user_id).all()

        if not cart_items:
            return jsonify({"success": False, "message": "Giỏ hàng trống"}), 400

        total = 0

        # Tạo đơn hàng
        new_order = Order(
            user_id=current_user.user_id,
            receiver_name=receiver_name,
            receiver_phone=receiver_phone,
            shipping_address=shipping_address,
            order_note=order_note,
            payment_method=payment_method,
            status='pending',
            created_at=datetime.now()
        )

        db.session.add(new_order)
        db.session.flush()  # lấy order_id

        # Thêm sản phẩm
        for item in cart_items:
            product = db.session.get(Product, item.product_id)

            if not product:
                continue

            price = float(product.price or 0)
            subtotal = price * item.quantity
            total += subtotal

            order_item = OrderItem(
                order_id=new_order.order_id,
                product_id=product.product_id,
                quantity=item.quantity,
                price=price,
                subtotal=subtotal
            )
            db.session.add(order_item)

        new_order.total_price = total

        # Xóa giỏ hàng
        Cart.query.filter_by(user_id=current_user.user_id).delete()

        db.session.commit()

        return jsonify({
            "success": True,
            "order_id": new_order.order_id
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500


# =========================
# USER: LẤY ĐƠN HÀNG CỦA MÌNH
# =========================
@order.route('/orders', methods=['GET'])
@login_required
def get_orders():
    try:
        orders = Order.query.filter_by(user_id=current_user.user_id)\
            .order_by(Order.created_at.desc()).all()

        result = []
        for o in orders:
            result.append({
                "order_id": o.order_id,
                "total": float(o.total_price),
                "status": o.status,
                "status_text": get_status_text(o.status),
                "created_at": o.created_at.strftime('%d/%m/%Y %H:%M') if o.created_at else None
            })

        return jsonify(result)

    except Exception as e:
        return jsonify({"message": str(e)}), 500


# =========================
# ADMIN: LẤY DANH SÁCH ĐƠN
# =========================
@order.route('/admin/orders', methods=['GET'])
@login_required
def admin_get_orders():
    if not current_user.is_admin:
        return jsonify({"message": "Không có quyền"}), 403

    try:
        orders = Order.query.options(
            joinedload(Order.user),
            joinedload(Order.items).joinedload(OrderItem.product)
        ).order_by(Order.created_at.desc()).all()

        result = []
        for o in orders:
            items_count = sum(item.quantity for item in o.items)

            result.append({
                "order_id": o.order_id,
                "user_name": o.user.full_name if o.user else "N/A",
                "user_email": o.user.email if o.user else "N/A",
                "total": float(o.total_price),
                "status": o.status,
                "status_text": get_status_text(o.status),
                "items_count": items_count,
                "created_at": o.created_at.strftime('%d/%m/%Y %H:%M') if o.created_at else None
            })

        return jsonify(result)

    except Exception as e:
        return jsonify({"message": str(e)}), 500


# =========================
# ADMIN: CHI TIẾT ĐƠN
# =========================
@order.route('/admin/orders/<int:order_id>', methods=['GET'])
@login_required
def admin_get_order_detail(order_id):
    if not current_user.is_admin:
        return jsonify({"message": "Không có quyền"}), 403

    try:
        o = db.session.get(Order, order_id)

        if not o:
            return jsonify({"message": "Không tìm thấy"}), 404

        items = []
        for item in o.items:
            price = float(item.price or 0)
            subtotal = float(item.subtotal) if item.subtotal else price * item.quantity

            items.append({
                "product_name": item.product.name if item.product else "N/A",
                "quantity": item.quantity,
                "price": price,
                "subtotal": subtotal
            })

        return jsonify({
            "order_id": o.order_id,
            "total": float(o.total_price),
            "status": o.status,
            "status_text": get_status_text(o.status),
            "receiver_name": o.receiver_name,
            "receiver_phone": o.receiver_phone,
            "shipping_address": o.shipping_address,
            "payment_method": get_payment_method_text(o.payment_method),
            "created_at": o.created_at.strftime('%d/%m/%Y %H:%M') if o.created_at else None,
            "items": items
        })

    except Exception as e:
        return jsonify({"message": str(e)}), 500


# =========================
# ADMIN: UPDATE STATUS
# =========================
@order.route('/admin/orders/<int:order_id>/status', methods=['PUT'])
@login_required
def update_order_status(order_id):
    if not current_user.is_admin:
        return jsonify({"message": "Không có quyền"}), 403

    try:
        data = request.get_json()
        new_status = data.get('status')

        valid_transitions = {
            'pending': ['confirmed', 'cancelled'],
            'confirmed': ['shipping', 'cancelled'],
            'shipping': ['completed'],
            'completed': [],
            'cancelled': []
        }

        o = db.session.get(Order, order_id)
        if not o:
            return jsonify({"message": "Không tìm thấy"}), 404

        if new_status not in valid_transitions.get(o.status, []):
            return jsonify({"message": "Không thể chuyển trạng thái"}), 400

        o.status = new_status
        db.session.commit()

        return jsonify({"success": True})

    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 500


# =========================
# ADMIN: THỐNG KÊ
# =========================
@order.route('/admin/orders/stats', methods=['GET'])
@login_required
def get_order_stats():
    if not current_user.is_admin:
        return jsonify({"message": "Không có quyền"}), 403

    try:
        total_orders = Order.query.count()

        stats = db.session.query(
            func.sum(func.case((Order.status == 'pending', 1), else_=0)),
            func.sum(func.case((Order.status == 'completed', 1), else_=0))
        ).one()

        total_revenue = db.session.query(func.sum(Order.total_price))\
            .filter(Order.status == 'completed').scalar() or 0

        return jsonify({
            "total_orders": total_orders,
            "pending_orders": int(stats[0] or 0),
            "completed_orders": int(stats[1] or 0),
            "total_revenue": float(total_revenue)
        })

    except Exception as e:
        return jsonify({"message": str(e)}), 500


# =========================
# HELPER
# =========================
def get_status_text(status):
    return {
        'pending': '⏳ Chờ xử lý',
        'confirmed': '✅ Đã xác nhận',
        'shipping': '🚚 Đang giao',
        'completed': '🎉 Hoàn thành',
        'cancelled': '❌ Đã hủy'
    }.get(status, status)


def get_payment_method_text(method):
    return {
        'cod': '💵 COD',
        'bank': '🏦 Bank',
        'momo': '📱 MoMo',
        'vnpay': '💳 VNPay'
    }.get(method, method)