from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from ..models import Cart, Product
from ..extensions import db
from datetime import datetime
import traceback

cart = Blueprint('cart', __name__)

@cart.route('/cart/add', methods=['POST'])
@login_required
def add_cart():
    try:
        data = request.json
        if not data or not data.get('product_id'):
            return jsonify({"message": "Thiếu thông tin sản phẩm"}), 400
        
        product = Product.query.get(data['product_id'])
        if not product:
            return jsonify({"message": "Sản phẩm không tồn tại"}), 404

        if product.stock <= 0:
            return jsonify({"message": "Sản phẩm đã hết hàng"}), 400

        item = Cart.query.filter_by(
            user_id=current_user.user_id,
            product_id=data['product_id']
        ).first()

        if item:
            if item.quantity + 1 > product.stock:
                return jsonify({"message": f"Sản phẩm chỉ còn {product.stock} trong kho"}), 400
            item.quantity += 1
            item.updated_at = datetime.utcnow()
            message = "Đã cập nhật số lượng"
        else:
            new_item = Cart(
                user_id=current_user.user_id,
                product_id=data['product_id'],
                quantity=1,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.session.add(new_item)
            message = "Đã thêm vào giỏ hàng"

        db.session.commit()
        cart_count = Cart.query.filter_by(user_id=current_user.user_id).count()
        
        return jsonify({
            "message": message,
            "cart_count": cart_count
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Lỗi: {str(e)}")
        return jsonify({"message": f"Có lỗi xảy ra: {str(e)}"}), 500


@cart.route('/cart', methods=['GET'])
@login_required
def view_cart():
    try:
        items = Cart.query.filter_by(user_id=current_user.user_id).all()
        result = []
        total = 0

        for item in items:
            product = item.product  # DÙNG backref CŨ
            if not product:
                db.session.delete(item)
                continue
                
            subtotal = float(product.price) * item.quantity
            total += subtotal

            result.append({
                "id": product.product_id,
                "name": product.name,
                "price": float(product.price),
                "quantity": item.quantity,
                "subtotal": float(subtotal),
                "image": product.image or '',
                "stock": product.stock
            })

        db.session.commit()
        return jsonify({
            "items": result,
            "total": float(total),
            "count": len(result)
        })
        
    except Exception as e:
        print(f"Lỗi: {str(e)}")
        return jsonify({"message": f"Có lỗi xảy ra: {str(e)}"}), 500


@cart.route('/cart/update', methods=['POST'])
@login_required
def update_cart():
    try:
        data = request.json
        item = Cart.query.filter_by(
            user_id=current_user.user_id,
            product_id=data['product_id']
        ).first()
        
        if not item:
            return jsonify({"message": "Sản phẩm không có trong giỏ"}), 404
        
        quantity = int(data.get('quantity', 1))
        
        if quantity > item.product.stock:  # DÙNG backref CŨ
            return jsonify({"message": f"Sản phẩm chỉ còn {item.product.stock} trong kho"}), 400
        
        if quantity <= 0:
            db.session.delete(item)
            message = "Đã xóa khỏi giỏ hàng"
        else:
            item.quantity = quantity
            item.updated_at = datetime.utcnow()
            message = "Đã cập nhật số lượng"
        
        db.session.commit()
        
        items = Cart.query.filter_by(user_id=current_user.user_id).all()
        new_total = sum(float(i.product.price) * i.quantity for i in items)  # DÙNG backref CŨ
        
        return jsonify({
            "message": message,
            "cart_count": len(items),
            "total": float(new_total)
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Có lỗi xảy ra: {str(e)}"}), 500


@cart.route('/cart/remove/<int:product_id>', methods=['DELETE'])
@login_required
def remove_from_cart(product_id):
    try:
        item = Cart.query.filter_by(
            user_id=current_user.user_id,
            product_id=product_id
        ).first()
        
        if item:
            db.session.delete(item)
            db.session.commit()
            cart_count = Cart.query.filter_by(user_id=current_user.user_id).count()
            return jsonify({
                "message": "Đã xóa khỏi giỏ hàng",
                "cart_count": cart_count
            })
            
        return jsonify({"message": "Không tìm thấy sản phẩm"}), 404
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Có lỗi xảy ra: {str(e)}"}), 500


@cart.route('/cart/count', methods=['GET'])
@login_required
def get_cart_count():
    try:
        count = Cart.query.filter_by(user_id=current_user.user_id).count()
        return jsonify({"count": count})
    except Exception as e:
        return jsonify({"count": 0})


@cart.route('/cart-ui')
@login_required
def cart_ui():
    return render_template('cart.html')