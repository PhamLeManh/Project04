from flask import Flask, render_template, redirect, url_for
from flask_login import login_required, current_user

from .extensions import db, login_manager, jwt, cors

# import routes
from .routes.auth import auth
from .routes.product import product
from .routes.cart import cart
from .routes.order import order
from .routes.admin import admin_bp

from config import Config
import os
from datetime import datetime


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Tạo thư mục uploads
    if 'UPLOAD_FOLDER' in app.config:
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # INIT EXTENSIONS
    db.init_app(app)
    login_manager.init_app(app)
    jwt.init_app(app)  # THÊM JWT
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})  # THÊM CORS

    # Cấu hình login
    login_manager.login_view = 'auth.login_page'
    login_manager.login_message = 'Vui lòng đăng nhập để tiếp tục'

    # User loader
    @login_manager.user_loader
    def load_user(user_id):
        from .models import User
        return User.query.get(int(user_id))

    # REGISTER BLUEPRINTS
    app.register_blueprint(auth, url_prefix='/auth')
    app.register_blueprint(product, url_prefix='/')
    app.register_blueprint(cart, url_prefix='/api')
    app.register_blueprint(order, url_prefix='/api')
    app.register_blueprint(admin_bp, url_prefix='/api')  

    # =========================
    # REGISTER API BLUEPRINT (THÊM MỚI)
    # =========================
    from .api import api_bp
    app.register_blueprint(api_bp)

    # =========================
    # UI ROUTES
    # =========================
    
    @app.route('/')
    def home():
        return render_template('index.html')

    @app.route('/products-ui')
    def products_ui():
        return render_template('product/list.html')

    @app.route('/cart-ui')
    @login_required
    def cart_ui():
        return render_template('cart.html')

    
    # ADMIN UI ROUTES
    
    
    @app.route('/admin')
    @login_required
    def admin_page():
        if not current_user.is_admin:
            return render_template('403.html'), 403
        return render_template('admin/dashboard.html')

    @app.route('/admin/products')
    @login_required
    def admin_products():
        if not current_user.is_admin:
            return render_template('403.html'), 403
        return render_template('admin/product_manage.html')

    @app.route('/admin/users')
    @login_required
    def admin_users():
        if not current_user.is_admin:
            return render_template('403.html'), 403
        return render_template('admin/users.html')

    
    # ERROR HANDLERS
    
    
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('403.html'), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('500.html', error=str(e)), 500

    
    # DEBUG ROUTES
    
    
    @app.route('/debug-routes')
    def debug_routes():
        import urllib
        output = ['<h2>📋 DANH SÁCH ROUTES</h2>']
        output.append('<table border="1" cellpadding="8" style="border-collapse: collapse;">')
        output.append('<tr><th>Endpoint</th><th>URL</th><th>Methods</th></tr>')
        
        for rule in sorted(app.url_map.iter_rules(), key=lambda x: str(x)):
            if not str(rule).startswith('/static'):
                methods = ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
                output.append(f"<tr><td>{rule.endpoint}</td><td>{rule.rule}</td><td>{methods}</td>{lands}")
        
        output.append('</table>')
        return '<div style="font-family: monospace; padding:20px;">' + '\n'.join(output) + '</div>'

    
    # CONTEXT PROCESSOR
    
    
    @app.context_processor
    def utility_processor():
        def format_currency(amount):
            try:
                return f"{amount:,.0f} VNĐ"
            except:
                return f"{amount} VNĐ"
        
        return dict(
            format_currency=format_currency,
            app_name="Fruit Store",
            current_year=datetime.now().year
        )

    print("="*50)
    print("✅ FRUIT STORE APP STARTED SUCCESSFULLY!")
    print(f"   Web app: http://localhost:5000/")
    print(f"   API: http://localhost:5000/api/")
    print("="*50)
    
    return app