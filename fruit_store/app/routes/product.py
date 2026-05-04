from flask import Blueprint, jsonify, request, render_template
from ..models import Product, Category
from ..extensions import db
import traceback

product = Blueprint('product', __name__)

# ==================== API ENDPOINTS ====================

@product.route('/api/products', methods=['GET'])
def get_products_api():
    """Lấy danh sách sản phẩm (API)"""
    try:
        print("📦 API /api/products được gọi")
        products = Product.query.all()
        print(f"✅ Tìm thấy {len(products)} sản phẩm")
        
        result = []
        for p in products:
            # Sử dụng placeholder nếu không có ảnh
            image_url = p.image if p.image else 'https://images.unsplash.com/photo-1619566636858-adf3ef46400b?w=200&h=200&fit=crop'
            
            result.append({
                "id": p.product_id,
                "name": p.name,
                "price": float(p.price) if p.price else 0,
                "stock": p.stock if p.stock else 0,
                "image": image_url,
                "description": p.description or '',
                "category_id": p.category_id,
                "category_name": p.category.name if p.category else None
            })
        
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Lỗi trong /api/products: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e), "message": "Lỗi server"}), 500


@product.route('/api/categories', methods=['GET'])
def get_categories_api():
    """Lấy danh sách danh mục (API)"""
    try:
        print("📦 API /api/categories được gọi")
        categories = Category.query.all()
        
        result = [{
            "id": c.category_id,
            "name": c.name,
            "description": c.description or ''
        } for c in categories]
        
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Lỗi trong /api/categories: {str(e)}")
        return jsonify({"error": str(e)}), 500


@product.route('/products', methods=['GET'])
def get_products():
    """Lấy danh sách sản phẩm (Legacy - redirect to API)"""
    return get_products_api()


@product.route('/categories', methods=['GET'])
def get_categories():
    """Lấy danh sách danh mục (Legacy - redirect to API)"""
    return get_categories_api()


# ==================== UI ROUTES ====================

@product.route('/')
def home():
    """Trang chủ"""
    return render_template('index.html')


@product.route('/products-ui')
def products_ui():
    """Trang danh sách sản phẩm"""
    return render_template('product/list.html')


# ==================== DEBUG ROUTES ====================

@product.route('/debug-products')
def debug_products():
    """Debug: Hiển thị sản phẩm dạng HTML"""
    products = Product.query.all()
    categories = Category.query.all()
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Debug Products</title>
        <style>
            body { font-family: Arial; padding: 20px; }
            table { border-collapse: collapse; width: 100%; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #28a745; color: white; }
            tr:nth-child(even) { background-color: #f2f2f2; }
            .success { color: green; }
            .error { color: red; }
        </style>
    </head>
    <body>
        <h1>📋 DANH SÁCH SẢN PHẨM</h1>
        <p>Tổng số sản phẩm: <strong class="success">""" + str(len(products)) + """</strong></p>
        
        <h2>Sản phẩm:</h2>
        <table>
            <tr>
                <th>ID</th>
                <th>Tên</th>
                <th>Giá</th>
                <th>Stock</th>
                <th>Hình ảnh</th>
                <th>Danh mục ID</th>
                <th>Danh mục tên</th>
            </tr>
    """
    
    for p in products:
        category_name = p.category.name if p.category else 'N/A'
        html += f"""
            <tr>
                <td>{p.product_id}</td>
                <td><strong>{p.name}</strong></td>
                <td>{p.price:,.0f} VNĐ</td>
                <td>{p.stock}</td>
                <td><img src="{p.image if p.image else 'https://images.unsplash.com/photo-1619566636858-adf3ef46400b?w=50&h=50&fit=crop'}" width="50" height="50" style="object-fit: cover;"></td>
                <td>{p.category_id}</td>
                <td>{category_name}</td>
            </tr>
        """
    
    html += """
        </table>
        
        <h2>Danh mục:</h2>
        <table>
            <tr>
                <th>ID</th>
                <th>Tên danh mục</th>
                <th>Mô tả</th>
            </tr>
    """
    
    for c in categories:
        html += f"""
            <tr>
                <td>{c.category_id}</td>
                <td><strong>{c.name}</strong></td>
                <td>{c.description or ''}</td>
            </tr>
        """
    
    html += """
        </table>
        
        <div style="margin-top: 20px;">
            <a href="/admin/products" style="background: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Quản lý sản phẩm</a>
            <a href="/products-ui" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-left: 10px;">Xem giao diện</a>
        </div>
    </body>
    </html>
    """
    
    return html