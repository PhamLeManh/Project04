# app/api/orders.py
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.api import api_bp
from app.models import Order, OrderItem, Cart, Product, User
from app.extensions import db
from datetime import datetime

@api_bp.route('/orders', methods=['GET'])
@jwt_required()
def get_orders():
    """Lấy danh sách đơn hàng của user"""
    try:
        user_id = get_jwt_identity()
        orders = Order.query.filter_by(user_id=user_id).order_by(Order.created_at.desc()).all()
        
        return jsonify([{
            'order_id': o.order_id,
            'total_price': float(o.total_price),
            'status': o.status,
            'status_text': get_status_text(o.status),
            'receiver_name': o.receiver_name,
            'receiver_phone': o.receiver_phone,
            'shipping_address': o.shipping_address,
            'payment_method': o.payment_method,
            'created_at': o.created_at.isoformat() if o.created_at else None
        } for o in orders]), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/orders/<int:order_id>', methods=['GET'])
@jwt_required()
def get_order_detail(order_id):
    """Lấy chi tiết một đơn hàng"""
    try:
        user_id = get_jwt_identity()
        order = Order.query.filter_by(order_id=order_id, user_id=user_id).first()
        
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        
        items = []
        for item in order.items:
            items.append({
                'product_id': item.product_id,
                'product_name': item.product.name if item.product else 'N/A',
                'quantity': item.quantity,
                'price': float(item.price),
                'subtotal': float(item.subtotal or item.price * item.quantity)
            })
        
        return jsonify({
            'order_id': order.order_id,
            'total_price': float(order.total_price),
            'status': order.status,
            'status_text': get_status_text(order.status),
            'receiver_name': order.receiver_name,
            'receiver_phone': order.receiver_phone,
            'shipping_address': order.shipping_address,
            'order_note': order.order_note,
            'payment_method': order.payment_method,
            'created_at': order.created_at.isoformat() if order.created_at else None,
            'items': items
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/orders', methods=['POST'])
@jwt_required()
def create_order():
    """Tạo đơn hàng mới từ giỏ hàng"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        required = ['receiver_name', 'receiver_phone', 'shipping_address']
        for field in required:
            if not data.get(field):
                return jsonify({'error': f'Thiếu {field}'}), 400
        
        # Get cart items
        cart_items = Cart.query.filter_by(user_id=user_id).all()
        
        if not cart_items:
            return jsonify({'error': 'Giỏ hàng trống'}), 400
        
        # Create order
        new_order = Order(
            user_id=user_id,
            receiver_name=data['receiver_name'],
            receiver_phone=data['receiver_phone'],
            shipping_address=data['shipping_address'],
            order_note=data.get('order_note', ''),
            payment_method=data.get('payment_method', 'cod'),
            status='pending',
            created_at=datetime.utcnow(),
            total_price=0
        )
        
        db.session.add(new_order)
        db.session.flush()  # Get order_id
        
        total = 0
        
        # Create order items and update stock
        for cart_item in cart_items:
            product = cart_item.product
            if not product:
                continue
            
            # Check stock again
            if product.stock < cart_item.quantity:
                db.session.rollback()
                return jsonify({'error': f'Sản phẩm {product.name} chỉ còn {product.stock} trong kho'}), 400
            
            price = float(product.price)
            subtotal = price * cart_item.quantity
            total += subtotal
            
            order_item = OrderItem(
                order_id=new_order.order_id,
                product_id=product.product_id,
                quantity=cart_item.quantity,
                price=price,
                subtotal=subtotal
            )
            db.session.add(order_item)
            
            # Update stock
            product.stock -= cart_item.quantity
        
        new_order.total_price = total
        
        # Clear cart
        Cart.query.filter_by(user_id=user_id).delete()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Đặt hàng thành công',
            'order_id': new_order.order_id,
            'total_price': float(total)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/orders/<int:order_id>/cancel', methods=['POST'])
@jwt_required()
def cancel_order(order_id):
    """Hủy đơn hàng (chỉ khi đang pending)"""
    try:
        user_id = get_jwt_identity()
        order = Order.query.filter_by(order_id=order_id, user_id=user_id).first()
        
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        
        if order.status != 'pending':
            return jsonify({'error': f'Không thể hủy đơn hàng đang {order.status}'}), 400
        
        # Restore stock
        for item in order.items:
            product = item.product
            if product:
                product.stock += item.quantity
        
        order.status = 'cancelled'
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Đã hủy đơn hàng'
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