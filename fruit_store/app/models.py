from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from .extensions import db

# =========================
# 👤 USER
# =========================
class User(db.Model, UserMixin):
    __tablename__ = 'users'

    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    role = db.Column(db.Enum('user', 'admin'), default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 🔗 RELATIONSHIPS - GIỮ NGUYÊN NHƯ CŨ
    carts = db.relationship('Cart', backref='user', lazy=True, cascade='all, delete-orphan')
    orders = db.relationship('Order', backref='user', lazy=True)

    # 🔥 BẮT BUỘC CHO FLASK-LOGIN
    def get_id(self):
        return str(self.user_id)

    @property
    def id(self):
        return self.user_id

    @property
    def is_admin(self):
        return self.role == 'admin'

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def __repr__(self):
        return f"<User {self.email}>"


# =========================
# 🍎 PRODUCT
# =========================
class Product(db.Model):
    __tablename__ = 'products'

    product_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    image = db.Column(db.String(255))
    category_id = db.Column(db.Integer, db.ForeignKey('categories.category_id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 🔗 RELATIONSHIPS - GIỮ NGUYÊN NHƯ CŨ
    cart_items = db.relationship('Cart', backref='product', lazy=True, cascade='all, delete-orphan')
    order_items = db.relationship('OrderItem', backref='product', lazy=True)

    def __repr__(self):
        return f"<Product {self.name}>"


# =========================
# 📁 CATEGORY
# =========================
class Category(db.Model):
    __tablename__ = 'categories'

    category_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)

    # 🔗 RELATIONSHIPS - GIỮ NGUYÊN NHƯ CŨ
    products = db.relationship('Product', backref='category', lazy=True)

    def __repr__(self):
        return f"<Category {self.name}>"


# =========================
# 🛒 CART
# =========================
class Cart(db.Model):
    __tablename__ = 'cart'

    cart_id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.product_id', ondelete='CASCADE'), nullable=False)

    quantity = db.Column(db.Integer, default=1)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('user_id', 'product_id', name='unique_user_product'),)

    def __repr__(self):
        return f"<Cart user={self.user_id} product={self.product_id}>"


# =========================
# 💳 ORDER - GIỮ NGUYÊN
# =========================
class Order(db.Model):
    __tablename__ = 'orders'

    order_id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)

    total_price = db.Column(db.Float, default=0)
    status = db.Column(db.Enum('pending', 'confirmed', 'shipping', 'completed', 'cancelled'), default='pending')
    
    # Thông tin giao hàng
    receiver_name = db.Column(db.String(100))
    receiver_phone = db.Column(db.String(20))
    shipping_address = db.Column(db.Text)
    order_note = db.Column(db.Text)
    payment_method = db.Column(db.String(50), default='cod')

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 🔗 RELATIONSHIPS - GIỮ NGUYÊN
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Order {self.order_id} - User {self.user_id} - {self.status}>"


# =========================
# 📦 ORDER ITEM - GIỮ NGUYÊN
# =========================
class OrderItem(db.Model):
    __tablename__ = 'order_items'

    order_item_id = db.Column(db.Integer, primary_key=True)

    order_id = db.Column(db.Integer, db.ForeignKey('orders.order_id', ondelete='CASCADE'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.product_id'), nullable=False)

    quantity = db.Column(db.Integer, default=1)
    price = db.Column(db.Float, nullable=False)
    subtotal = db.Column(db.Float)

    def __repr__(self):
        return f"<OrderItem order={self.order_id} product={self.product_id}>"