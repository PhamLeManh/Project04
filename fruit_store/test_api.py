import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:5000/api"

class APITester:
    def __init__(self):
        self.token = None
        self.headers = {}
        self.test_results = []
    
    def print_response(self, title, response):
        """In response đẹp mắt"""
        print(f"\n{'='*60}")
        print(f"📌 {title}")
        print(f"Status: {response.status_code} {'✅' if response.status_code < 400 else '❌'}")
        print(f"{'='*60}")
        try:
            response_json = response.json()
            print(json.dumps(response_json, indent=2, ensure_ascii=False))
            
            # Lưu kết quả
            self.test_results.append({
                'test': title,
                'status': response.status_code,
                'success': response.status_code < 400,
                'response': response_json
            })
        except:
            print(response.text)
            self.test_results.append({
                'test': title,
                'status': response.status_code,
                'success': response.status_code < 400,
                'response': response.text
            })
    
    def test_register(self, username, email, password):
        """Test 1: Đăng ký tài khoản mới"""
        print("\n🔐 TEST 1: ĐĂNG KÝ TÀI KHOẢN")
        data = {
            "username": username,
            "email": email,
            "password": password
        }
        response = requests.post(f"{BASE_URL}/auth/register", json=data)
        self.print_response("Đăng ký", response)
        return response
    
    def test_login(self, email, password):
        """Test 2: Đăng nhập và lấy token"""
        print("\n🔑 TEST 2: ĐĂNG NHẬP")
        data = {
            "email": email,
            "password": password
        }
        response = requests.post(f"{BASE_URL}/auth/login", json=data)
        self.print_response("Đăng nhập", response)
        
        if response.status_code == 200:
            self.token = response.json().get('access_token')
            self.headers = {"Authorization": f"Bearer {self.token}"}
            print(f"\n✅ Token đã lấy thành công!")
            print(f"Token: {self.token[:50]}...")
        return response
    
    def test_get_profile(self):
        """Test 3: Lấy thông tin profile"""
        print("\n👤 TEST 3: LẤY THÔNG TIN PROFILE")
        if not self.token:
            print("❌ Chưa đăng nhập! Bỏ qua test này.")
            return None
        
        response = requests.get(f"{BASE_URL}/auth/profile", headers=self.headers)
        self.print_response("Get Profile", response)
        return response
    
    def test_update_profile(self, new_username=None):
        """Test 4: Cập nhật profile"""
        print("\n✏️ TEST 4: CẬP NHẬT PROFILE")
        if not self.token:
            print("❌ Chưa đăng nhập! Bỏ qua test này.")
            return None
        
        data = {}
        if new_username:
            data['username'] = new_username
        
        if not data:
            data = {"username": "updated_user"}
        
        response = requests.put(f"{BASE_URL}/auth/profile", json=data, headers=self.headers)
        self.print_response("Update Profile", response)
        return response
    
    def test_get_products(self, page=1, per_page=10):
        """Test 5: Lấy danh sách sản phẩm"""
        print("\n📦 TEST 5: LẤY DANH SÁCH SẢN PHẨM")
        params = {"page": page, "per_page": per_page}
        response = requests.get(f"{BASE_URL}/products", params=params)
        self.print_response("Get Products", response)
        
        # Trả về danh sách sản phẩm để dùng cho test sau
        if response.status_code == 200:
            products = response.json().get('products', [])
            return products
        return []
    
    def test_get_product_detail(self, product_id):
        """Test 6: Lấy chi tiết sản phẩm"""
        print(f"\n🔍 TEST 6: LẤY CHI TIẾT SẢN PHẨM ID={product_id}")
        response = requests.get(f"{BASE_URL}/products/{product_id}")
        self.print_response("Get Product Detail", response)
        return response
    
    def test_get_categories(self):
        """Test 7: Lấy danh sách danh mục"""
        print("\n📂 TEST 7: LẤY DANH SÁCH DANH MỤC")
        response = requests.get(f"{BASE_URL}/products/categories")
        self.print_response("Get Categories", response)
        return response
    
    def test_add_to_cart(self, product_id, quantity=1):
        """Test 8: Thêm sản phẩm vào giỏ hàng"""
        print(f"\n🛒 TEST 8: THÊM VÀO GIỎ HÀNG (Product ID={product_id}, Số lượng={quantity})")
        if not self.token:
            print("❌ Chưa đăng nhập! Bỏ qua test này.")
            return None
        
        data = {"product_id": product_id, "quantity": quantity}
        response = requests.post(f"{BASE_URL}/cart", json=data, headers=self.headers)
        self.print_response("Add to Cart", response)
        return response
    
    def test_get_cart(self):
        """Test 9: Xem giỏ hàng"""
        print("\n🛍️ TEST 9: XEM GIỎ HÀNG")
        if not self.token:
            print("❌ Chưa đăng nhập! Bỏ qua test này.")
            return None
        
        response = requests.get(f"{BASE_URL}/cart", headers=self.headers)
        self.print_response("Get Cart", response)
        
        # Trả về danh sách items trong giỏ
        if response.status_code == 200:
            items = response.json().get('items', [])
            return items
        return []
    
    def test_update_cart_item(self, item_id, quantity):
        """Test 10: Cập nhật số lượng trong giỏ"""
        print(f"\n🔄 TEST 10: CẬP NHẬT GIỎ HÀNG (Item ID={item_id}, Số lượng={quantity})")
        if not self.token:
            print("❌ Chưa đăng nhập! Bỏ qua test này.")
            return None
        
        data = {"quantity": quantity}
        response = requests.put(f"{BASE_URL}/cart/{item_id}", json=data, headers=self.headers)
        self.print_response("Update Cart Item", response)
        return response
    
    def test_remove_from_cart(self, item_id):
        """Test 11: Xóa sản phẩm khỏi giỏ"""
        print(f"\n🗑️ TEST 11: XÓA KHỎI GIỎ HÀNG (Item ID={item_id})")
        if not self.token:
            print("❌ Chưa đăng nhập! Bỏ qua test này.")
            return None
        
        response = requests.delete(f"{BASE_URL}/cart/{item_id}", headers=self.headers)
        self.print_response("Remove from Cart", response)
        return response
    
    def test_clear_cart(self):
        """Test 12: Xóa toàn bộ giỏ hàng"""
        print("\n🧹 TEST 12: XÓA TOÀN BỘ GIỎ HÀNG")
        if not self.token:
            print("❌ Chưa đăng nhập! Bỏ qua test này.")
            return None
        
        response = requests.delete(f"{BASE_URL}/cart/clear", headers=self.headers)
        self.print_response("Clear Cart", response)
        return response
    
    def test_create_order(self, shipping_address, phone_number, note=""):
        """Test 13: Tạo đơn hàng"""
        print("\n📝 TEST 13: TẠO ĐƠN HÀNG")
        if not self.token:
            print("❌ Chưa đăng nhập! Bỏ qua test này.")
            return None
        
        data = {
            "shipping_address": shipping_address,
            "phone_number": phone_number,
            "note": note
        }
        response = requests.post(f"{BASE_URL}/orders", json=data, headers=self.headers)
        self.print_response("Create Order", response)
        
        # Trả về order_id nếu thành công
        if response.status_code == 201:
            order = response.json().get('order', {})
            return order.get('id')
        return None
    
    def test_get_orders(self):
        """Test 14: Lấy danh sách đơn hàng"""
        print("\n📋 TEST 14: LẤY DANH SÁCH ĐƠN HÀNG")
        if not self.token:
            print("❌ Chưa đăng nhập! Bỏ qua test này.")
            return None
        
        response = requests.get(f"{BASE_URL}/orders", headers=self.headers)
        self.print_response("Get Orders", response)
        return response
    
    def test_get_order_detail(self, order_id):
        """Test 15: Lấy chi tiết đơn hàng"""
        print(f"\n📄 TEST 15: LẤY CHI TIẾT ĐƠN HÀNG ID={order_id}")
        if not self.token:
            print("❌ Chưa đăng nhập! Bỏ qua test này.")
            return None
        
        response = requests.get(f"{BASE_URL}/orders/{order_id}", headers=self.headers)
        self.print_response("Get Order Detail", response)
        return response
    
    def test_cancel_order(self, order_id):
        """Test 16: Hủy đơn hàng"""
        print(f"\n❌ TEST 16: HỦY ĐƠN HÀNG ID={order_id}")
        if not self.token:
            print("❌ Chưa đăng nhập! Bỏ qua test này.")
            return None
        
        response = requests.post(f"{BASE_URL}/orders/{order_id}/cancel", headers=self.headers)
        self.print_response("Cancel Order", response)
        return response
    
    def print_summary(self):
        """In tổng kết kết quả test"""
        print("\n" + "="*60)
        print("📊 TỔNG KẾT KẾT QUẢ TEST")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"\nTổng số test: {total_tests}")
        print(f"✅ Thành công: {passed_tests}")
        print(f"❌ Thất bại: {failed_tests}")
        print(f"📈 Tỷ lệ thành công: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ Các test thất bại:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']} (Status: {result['status']})")
    
    def run_full_test(self):
        """Chạy toàn bộ các test"""
        print("\n" + "🎯"*30)
        print("BẮT ĐẦU TEST API FRUIT STORE")
        print("🎯"*30)
        
        # 1. Đăng ký
        test_email = f"test_{datetime.now().strftime('%Y%m%d%H%M%S')}@example.com"
        self.test_register("testuser", test_email, "123456")
        
        # 2. Đăng nhập
        self.test_login(test_email, "123456")
        
        if not self.token:
            print("\n❌ Không thể đăng nhập, dừng test!")
            return
        
        # 3. Lấy profile
        self.test_get_profile()
        
        # 4. Cập nhật profile
        self.test_update_profile("testuser_updated")
        
        # 5. Lấy danh sách sản phẩm
        products = self.test_get_products()
        
        # 6. Lấy chi tiết sản phẩm đầu tiên (nếu có)
        if products:
            first_product = products[0]
            self.test_get_product_detail(first_product['id'])
        
        # 7. Lấy danh mục
        self.test_get_categories()
        
        # 8. Thêm vào giỏ hàng (nếu có sản phẩm)
        if products:
            self.test_add_to_cart(products[0]['id'], 2)
        
        # 9. Xem giỏ hàng
        cart_items = self.test_get_cart()
        
        # 10. Cập nhật số lượng trong giỏ (nếu có)
        if cart_items:
            self.test_update_cart_item(cart_items[0]['id'], 5)
        
        # 11. Tạo đơn hàng
        order_id = self.test_create_order(
            "123 Đường Láng, Đống Đa, Hà Nội",
            "0987654321",
            "Giao hàng trong giờ hành chính"
        )
        
        # 12. Lấy danh sách đơn hàng
        self.test_get_orders()
        
        # 13. Lấy chi tiết đơn hàng (nếu có)
        if order_id:
            self.test_get_order_detail(order_id)
        
        # 14. Xóa item khỏi giỏ
        if cart_items:
            self.test_remove_from_cart(cart_items[0]['id'])
        
        # 15. In tổng kết
        self.print_summary()
        
        print("\n✨ TEST HOÀN TẤT! ✨")

def run_quick_test():
    """Chạy test nhanh (chỉ test các chức năng chính)"""
    print("\n⚡ CHẠY TEST NHANH ⚡")
    tester = APITester()
    
    # Đăng ký và đăng nhập
    tester.test_register("quickuser", "quick@test.com", "123456")
    tester.test_login("quick@test.com", "123456")
    
    if tester.token:
        # Test chính
        tester.test_get_products()
        tester.test_add_to_cart(1, 1)
        tester.test_get_cart()
        tester.test_create_order(
            "456 Nguyễn Trãi, Hà Nội",
            "0123456789"
        )
        tester.test_get_orders()
    
    tester.print_summary()

if __name__ == "__main__":
    print("\n🔧 CHỌN CHẾ ĐỘ TEST:")
    print("1. Test đầy đủ (Full Test)")
    print("2. Test nhanh (Quick Test)")
    
    choice = input("\nNhập lựa chọn (1 hoặc 2): ").strip()
    
    tester = APITester()
    
    if choice == "1":
        tester.run_full_test()
    elif choice == "2":
        run_quick_test()
    else:
        print("Lựa chọn không hợp lệ! Mặc định chạy test nhanh.")
        run_quick_test()