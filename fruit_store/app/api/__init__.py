# app/api/__init__.py
from flask import Blueprint, jsonify
from flask_jwt_extended import JWTManager
from flask_cors import CORS

# Tạo blueprint cho API
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Import tất cả các routes
from . import auth, products, cart, orders, admin

# Test endpoint
@api_bp.route('/test', methods=['GET'])
def test():
    return jsonify({
        'status': 'success',
        'message': 'API is working!',
        'version': '1.0'
    }), 200

# Error handlers
@api_bp.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request', 'message': str(error)}), 400

@api_bp.errorhandler(401)
def unauthorized(error):
    return jsonify({'error': 'Unauthorized', 'message': 'Authentication required'}), 401

@api_bp.errorhandler(403)
def forbidden(error):
    return jsonify({'error': 'Forbidden', 'message': 'Access denied'}), 403

@api_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found', 'message': 'Resource not found'}), 404

@api_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500