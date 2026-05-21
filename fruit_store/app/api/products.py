# app/api/products.py
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.api import api_bp
from app.models import Product, Category, User
from app.extensions import db

@api_bp.route('/products', methods=['GET'])
def get_products():
    """Lấy danh sách sản phẩm (public)"""
    try:
        # Query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        category_id = request.args.get('category_id', type=int)
        search = request.args.get('search', '')
        
        query = Product.query
        
        # Apply filters
        if category_id:
            query = query.filter_by(category_id=category_id)
        
        if search:
            query = query.filter(Product.name.ilike(f'%{search}%'))
        
        # Pagination
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Get categories for filter
        categories = Category.query.all()
        
        return jsonify({
            'products': [{
                'product_id': p.product_id,
                'name': p.name,
                'price': float(p.price) if p.price else 0,
                'stock': p.stock,
                'image': p.image or '',
                'description': p.description,
                'category_id': p.category_id,
                'category_name': p.category.name if p.category else None,
                'created_at': p.created_at.isoformat() if p.created_at else None
            } for p in pagination.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_prev': pagination.has_prev,
                'has_next': pagination.has_next
            },
            'categories': [{
                'category_id': c.category_id,
                'name': c.name,
                'description': c.description
            } for c in categories]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Lấy chi tiết một sản phẩm"""
    try:
        product = Product.query.get(product_id)
        
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        return jsonify({
            'product_id': product.product_id,
            'name': product.name,
            'price': float(product.price) if product.price else 0,
            'stock': product.stock,
            'image': product.image or '',
            'description': product.description,
            'category_id': product.category_id,
            'category_name': product.category.name if product.category else None,
            'created_at': product.created_at.isoformat() if product.created_at else None
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/categories', methods=['GET'])
def get_categories():
    """Lấy danh sách danh mục"""
    try:
        categories = Category.query.all()
        
        return jsonify([{
            'category_id': c.category_id,
            'name': c.name,
            'description': c.description,
            'product_count': len(c.products) if c.products else 0
        } for c in categories]), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500