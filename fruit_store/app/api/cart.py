# app/api/cart.py
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.api import api_bp
from app.models import Cart, Product, User
from app.extensions import db
from datetime import datetime

@api_bp.route('/cart', methods=['GET'])
@jwt_required()
def get_cart():
    """Lấy giỏ hàng của user"""
    try:
        user_id = get_jwt_identity()
        cart_items = Cart.query.filter_by(user_id=user_id).all()
        
        items = []
        total = 0
        
        for item in cart_items:
            product = item.product
            if product:
                subtotal = float(product.price) * item.quantity
                total += subtotal
                items.append({
                    'cart_id': item.cart_id,
                    'product_id': product.product_id,
                    'name': product.name,
                    'price': float(product.price),
                    'quantity': item.quantity,
                    'subtotal': subtotal,
                    'image': product.image or '',
                    'stock': product.stock
                })
        
        return jsonify({
            'items': items,
            'total': float(total),
            'total_items': sum(item.quantity for item in cart_items)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/cart', methods=['POST'])
@jwt_required()
def add_to_cart():
    """Thêm sản phẩm vào giỏ hàng"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'product_id' not in data:
            return jsonify({'error': 'Thiếu product_id'}), 400
        
        product_id = data['product_id']
        quantity = data.get('quantity', 1)
        
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'error': 'Sản phẩm không tồn tại'}), 404
        
        if product.stock < quantity:
            return jsonify({'error': f'Sản phẩm chỉ còn {product.stock} trong kho'}), 400
        
        # Check if product already in cart
        cart_item = Cart.query.filter_by(user_id=user_id, product_id=product_id).first()
        
        if cart_item:
            new_quantity = cart_item.quantity + quantity
            if product.stock < new_quantity:
                return jsonify({'error': f'Sản phẩm chỉ còn {product.stock} trong kho'}), 400
            cart_item.quantity = new_quantity
            cart_item.updated_at = datetime.utcnow()
            message = 'Đã cập nhật số lượng'
        else:
            cart_item = Cart(
                user_id=user_id,
                product_id=product_id,
                quantity=quantity,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.session.add(cart_item)
            message = 'Đã thêm vào giỏ hàng'
        
        db.session.commit()
        
        # Get updated cart count
        cart_count = Cart.query.filter_by(user_id=user_id).count()
        
        return jsonify({
            'success': True,
            'message': message,
            'cart_count': cart_count,
            'item': {
                'product_id': product_id,
                'quantity': cart_item.quantity
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/cart/<int:product_id>', methods=['PUT'])
@jwt_required()
def update_cart_item(product_id):
    """Cập nhật số lượng sản phẩm trong giỏ"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'quantity' not in data:
            return jsonify({'error': 'Thiếu quantity'}), 400
        
        quantity = data['quantity']
        
        cart_item = Cart.query.filter_by(user_id=user_id, product_id=product_id).first()
        
        if not cart_item:
            return jsonify({'error': 'Sản phẩm không có trong giỏ'}), 404
        
        if quantity <= 0:
            db.session.delete(cart_item)
            message = 'Đã xóa khỏi giỏ hàng'
        else:
            if cart_item.product.stock < quantity:
                return jsonify({'error': f'Sản phẩm chỉ còn {cart_item.product.stock} trong kho'}), 400
            cart_item.quantity = quantity
            cart_item.updated_at = datetime.utcnow()
            message = 'Đã cập nhật số lượng'
        
        db.session.commit()
        
        cart_count = Cart.query.filter_by(user_id=user_id).count()
        
        return jsonify({
            'success': True,
            'message': message,
            'cart_count': cart_count
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/cart/<int:product_id>', methods=['DELETE'])
@jwt_required()
def remove_from_cart(product_id):
    """Xóa sản phẩm khỏi giỏ hàng"""
    try:
        user_id = get_jwt_identity()
        
        cart_item = Cart.query.filter_by(user_id=user_id, product_id=product_id).first()
        
        if not cart_item:
            return jsonify({'error': 'Sản phẩm không có trong giỏ'}), 404
        
        db.session.delete(cart_item)
        db.session.commit()
        
        cart_count = Cart.query.filter_by(user_id=user_id).count()
        
        return jsonify({
            'success': True,
            'message': 'Đã xóa khỏi giỏ hàng',
            'cart_count': cart_count
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/cart/clear', methods=['DELETE'])
@jwt_required()
def clear_cart():
    """Xóa toàn bộ giỏ hàng"""
    try:
        user_id = get_jwt_identity()
        Cart.query.filter_by(user_id=user_id).delete()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Đã xóa toàn bộ giỏ hàng'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500