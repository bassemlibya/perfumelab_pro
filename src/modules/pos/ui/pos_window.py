# modules/pos/ui/pos_window.py
import sys
import traceback
from typing import List, Dict, Any, Optional
from decimal import Decimal, InvalidOperation
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *

# استيراد صحيح مع معالجة الأخطاء
try:
    from core.services.pos_service import POSService
    from core.managers.currency_manager import CurrencyManager
    from core.managers.theme_manager import ThemeManager
    from core.database.connection import DatabaseManager
    from ui.widgets.arabic_widgets import (
        ArabicLineEdit, ArabicComboBox, ArabicTableWidget, 
        ProductCard, SearchBar, TotalsPanel
    )
except ImportError as e:
    print(f"خطأ في الاستيراد: {e}")
    # إنشاء واجهات وهمية للتجربة
    ArabicLineEdit = QLineEdit
    ArabicComboBox = QComboBox
    ArabicTableWidget = QTableWidget
    ProductCard = QPushButton
    SearchBar = QLineEdit
    TotalsPanel = QWidget

class POSWindow(QMainWindow):
    """نافذة نقطة البيع الرئيسية"""
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None, 
                 currency_manager: Optional[CurrencyManager] = None,
                 theme_manager: Optional[ThemeManager] = None):
        super().__init__()
        
        # استخدام المديرين من الخارج أو إنشاء نسخ جديدة
        self.db_manager = db_manager
        self.currency_manager = currency_manager or CurrencyManager(db_manager)
        self.theme_manager = theme_manager or ThemeManager()
        
        # تهيئة POS Service مع تمرير db_manager و currency_manager
        try:
            self.pos_service = POSService(self.db_manager, self.currency_manager)
        except Exception as e:
            print(f"⚠️ خطأ في تهيئة POS Service: {e}")
            traceback.print_exc()
            self.pos_service = None
        
        # متغيرات الحالة
        self.cart_items: List[Dict[str, Any]] = []
        self.current_customer: Optional[int] = None
        self.current_customer_data: Optional[Dict] = None
        
        # الحصول على العملة الافتراضية بأمان
        try:
            default_currency = self.currency_manager.get_default_currency() if self.currency_manager else None
            self.current_currency = default_currency['code'] if default_currency else 'USD'
        except:
            self.current_currency = 'USD'
        
        self.discount_percent: float = 0.0
        self.discount_amount: float = 0.0
        self.hold_id: Optional[int] = None
        
        # إعدادات النافذة
        self.setWindowTitle("🏪 نقطة البيع - PerfumeLab Pro ERP")
        self.setLayoutDirection(Qt.RightToLeft)
        
        # جعل النافذة بحجم افتراضي
        screen = QApplication.primaryScreen().availableGeometry()
        self.resize(int(screen.width() * 0.95), int(screen.height() * 0.95))
        self.move(int(screen.width() * 0.025), int(screen.height() * 0.025))
        
        # إعداد واجهة المستخدم
        self.setup_ui()
        self.setup_shortcuts()
        
        # تحميل البيانات بأمان
        try:
            self.load_products()
            self.load_currencies()
            self.update_datetime()
            self.generate_invoice_number()
        except Exception as e:
            print(f"⚠️ خطأ في تحميل البيانات الأولية: {e}")
        
        # مؤقت لتحديث الوقت
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_datetime)
        self.timer.start(1000)
    
    def setup_ui(self):
        """إعداد واجهة المستخدم الرئيسية"""
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # الشريط الجانبي
        self.sidebar = self.create_sidebar()
        main_layout.addWidget(self.sidebar)
        
        # المنطقة الوسطى (المنتجات والسلة)
        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.setContentsMargins(10, 10, 10, 10)
        center_layout.setSpacing(10)
        
        # الرأس
        self.header = self.create_header()
        center_layout.addWidget(self.header)
        
        # شريط البحث
        self.search_bar = SearchBar()
        self.search_bar.setPlaceholderText("🔍 ابحث عن منتج...")
        self.search_bar.setMaximumHeight(45)
        # معالجة الإشارات بشكل آمن
        if hasattr(self.search_bar, 'search_changed'):
            self.search_bar.search_changed.connect(self.on_search)
        else:
            self.search_bar.textChanged.connect(self.on_search)
        center_layout.addWidget(self.search_bar)
        
        # تقسيم المنتجات والسلة
        splitter = QSplitter(Qt.Vertical)
        
        # شبكة المنتجات
        self.product_grid = self.create_product_grid()
        splitter.addWidget(self.product_grid)
        
        # جدول السلة
        self.cart_table = self.create_cart_table()
        splitter.addWidget(self.cart_table)
        
        splitter.setSizes([500, 300])
        center_layout.addWidget(splitter, 1)
        
        main_layout.addWidget(center_widget, 1)
        
        # لوحة الدفع
        self.payment_panel = self.create_payment_panel()
        main_layout.addWidget(self.payment_panel)
    
    def setup_shortcuts(self):
        """إعداد اختصارات لوحة المفاتيح"""
        # F1 - عرض المساعدة
        QShortcut(QKeySequence("F1"), self, self.show_help)
        # F2 - البحث
        QShortcut(QKeySequence("F2"), self, lambda: self.search_bar.setFocus())
        # F3 - خصم
        QShortcut(QKeySequence("F3"), self, self.on_apply_discount)
        # F4 - عميل
        QShortcut(QKeySequence("F4"), self, self.on_select_customer)
        # F5 - إتمام البيع
        QShortcut(QKeySequence("F5"), self, self.on_complete_sale)
        # Ctrl+N - فاتورة جديدة
        QShortcut(QKeySequence("Ctrl+N"), self, self.clear_cart)
        # Ctrl+H - تعليق
        QShortcut(QKeySequence("Ctrl+H"), self, self.on_hold_invoice)
        # Delete - حذف
        QShortcut(QKeySequence.Delete, self, self.delete_selected_item)
    
    def create_header(self) -> QWidget:
        """إنشاء رأس النافذة"""
        header = QWidget()
        header.setFixedHeight(70)
        header.setStyleSheet("""
            QWidget {
                background-color: #2E7D32;
                color: white;
                border-radius: 10px;
            }
        """)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 5, 20, 5)
        layout.setSpacing(15)
        
        # الشعار
        logo = QLabel("🏪 PerfumeLab POS")
        logo.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(logo)
        
        # رقم الفاتورة
        self.invoice_label = QLabel("📄 فاتورة: تحميل...")
        self.invoice_label.setStyleSheet("font-size: 14px; font-family: 'Courier New';")
        layout.addWidget(self.invoice_label)
        
        layout.addStretch()
        
        # المستخدم
        self.user_label = QLabel("👤 المدير")
        self.user_label.setStyleSheet("font-size: 13px;")
        layout.addWidget(self.user_label)
        
        # العملة
        self.currency_combo = ArabicComboBox()
        self.currency_combo.setMinimumWidth(150)
        self.currency_combo.setMaximumHeight(40)
        self.currency_combo.setStyleSheet("""
            QComboBox {
                background-color: white;
                color: black;
                border-radius: 5px;
                padding: 5px;
                font-weight: bold;
            }
        """)
        self.currency_combo.currentIndexChanged.connect(self.on_currency_changed)
        layout.addWidget(self.currency_combo)
        
        # التاريخ والوقت
        self.datetime_label = QLabel()
        self.datetime_label.setStyleSheet("font-size: 13px; font-family: 'Courier New'; color: white;")
        self.datetime_label.setMinimumWidth(170)
        layout.addWidget(self.datetime_label)
        
        return header
    
    def create_sidebar(self) -> QWidget:
        """إنشاء الشريط الجانبي للأزرار السريعة"""
        sidebar = QWidget()
        sidebar.setFixedWidth(90)
        sidebar.setStyleSheet("""
            QWidget {
                background-color: #1B5E20;
            }
            QPushButton {
                background-color: #2E7D32;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 10px;
                font-weight: bold;
                padding: 8px 4px;
            }
            QPushButton:hover {
                background-color: #4CAF50;
            }
            QPushButton:pressed {
                background-color: #1B5E20;
            }
        """)
        
        layout = QVBoxLayout(sidebar)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 20, 8, 20)
        
        buttons = [
            ("💰\nنقدي", self.on_cash_payment),
            ("🏦\nبنك", self.on_bank_payment),
            ("📝\nآجل", self.on_debt_payment),
            ("⏸️\nتعليق", self.on_hold_invoice),
            ("▶️\nاستئناف", self.on_resume_invoice),
            ("🔄\nمرتجع", self.on_return),
            ("👤\nعميل", self.on_select_customer),
            ("🏷️\nخصم", self.on_apply_discount),
            ("🧮\nحاسبة", self.on_calculator),
            ("🖨️\nطباعة", self.on_print),
            ("⚙️\nإعدادات", self.on_settings),
        ]
        
        for label, callback in buttons:
            btn = QPushButton(label)
            btn.setFixedSize(74, 70)
            btn.clicked.connect(callback)
            layout.addWidget(btn)
        
        layout.addStretch()
        
        # زر إلغاء الفاتورة
        cancel_btn = QPushButton("❌\nإلغاء")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #D32F2F;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F44336;
            }
        """)
        cancel_btn.clicked.connect(self.on_cancel_sale)
        layout.addWidget(cancel_btn)
        
        return sidebar
    
    def create_product_grid(self) -> QScrollArea:
        """إنشاء شبكة عرض المنتجات"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #FAFAFA;
            }
            QScrollBar:vertical {
                width: 12px;
            }
        """)
        
        container = QWidget()
        self.product_layout = QGridLayout(container)
        self.product_layout.setSpacing(12)
        self.product_layout.setContentsMargins(10, 10, 10, 10)
        
        scroll.setWidget(container)
        return scroll
    
    def create_cart_table(self) -> QWidget:
        """إنشاء جدول سلة المشتريات"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # عنوان الجدول
        title = QLabel("🛒 سلة المشتريات")
        title.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            padding: 10px;
            background-color: #E8F5E9;
            border-radius: 5px;
            color: #1B5E20;
        """)
        layout.addWidget(title)
        
        # الجدول
        self.cart_widget = ArabicTableWidget(
            columns=["#", "الصنف", "الكمية", "السعر", "الخصم", "الضريبة", "الإجمالي", ""]
        )
        self.cart_widget.setMinimumHeight(200)
        self.cart_widget.setAlternatingRowColors(True)
        layout.addWidget(self.cart_widget)
        
        return widget
    
    def create_payment_panel(self) -> QWidget:
        """إنشاء لوحة الدفع"""
        panel = QWidget()
        panel.setFixedWidth(380)
        panel.setStyleSheet("""
            QWidget {
                background-color: #F5F5F5;
                border-left: 2px solid #E0E0E0;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # بطاقة العميل
        self.customer_card = self.create_customer_card()
        layout.addWidget(self.customer_card)
        
        # لوحة الإجماليات
        self.totals_panel = TotalsPanel()
        layout.addWidget(self.totals_panel)
        
        # مجموعة الدفع
        payment_group = QGroupBox("💳 طريقة الدفع")
        payment_layout = QVBoxLayout(payment_group)
        
        self.payment_method = ArabicComboBox()
        self.payment_method.addItem("💵 نقدي", "cash")
        self.payment_method.addItem("💳 بطاقة ائتمان", "card")
        self.payment_method.addItem("🏦 تحويل بنكي", "bank")
        self.payment_method.addItem("📱 محفظة رقمية", "wallet")
        self.payment_method.addItem("📝 آجل", "debt")
        payment_layout.addWidget(self.payment_method)
        
        self.payment_amount = ArabicLineEdit()
        self.payment_amount.setPlaceholderText("المبلغ المدفوع")
        self.payment_amount.setMinimumHeight(45)
        self.payment_amount.setStyleSheet("font-size: 16px; padding: 8px;")
        payment_layout.addWidget(self.payment_amount)
        
        layout.addWidget(payment_group)
        
        # تغيير الباقي
        self.change_label = QLabel("💰 الإجمالي: 0.00")
        self.change_label.setStyleSheet("""
            font-size: 14px;
            color: #2E7D32;
            font-weight: bold;
            padding: 8px;
        """)
        self.payment_amount.textChanged.connect(self.calculate_change)
        layout.addWidget(self.change_label)
        
        # أزرار الإجراءات
        btn_layout = QHBoxLayout()
        
        self.pay_btn = QPushButton("✅ إتمام البيع")
        self.pay_btn.setMinimumHeight(55)
        self.pay_btn.setStyleSheet("""
            QPushButton {
                background-color: #2E7D32;
                color: white;
                font-size: 15px;
                font-weight: bold;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #1B5E20;
            }
            QPushButton:disabled {
                background-color: #CCCCCC;
            }
        """)
        self.pay_btn.clicked.connect(self.on_complete_sale)
        btn_layout.addWidget(self.pay_btn)
        
        layout.addLayout(btn_layout)
        layout.addStretch()
        
        return panel
    
    def create_customer_card(self) -> QFrame:
        """إنشاء بطاقة معلومات العميل"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                padding: 12px;
                border: 1px solid #E0E0E0;
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(8)
        
        title = QLabel("👤 معلومات العميل")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #2E7D32;")
        layout.addWidget(title)
        
        self.customer_name = QLabel("عميل نقدي")
        self.customer_name.setStyleSheet("font-size: 15px; font-weight: bold; color: #212121;")
        layout.addWidget(self.customer_name)
        
        self.customer_balance = QLabel("الرصيد: 0.00")
        self.customer_balance.setStyleSheet("font-size: 12px; color: #757575;")
        layout.addWidget(self.customer_balance)
        
        self.customer_points = QLabel("🌟 النقاط: 0")
        self.customer_points.setStyleSheet("font-size: 12px; color: #FF6F00;")
        layout.addWidget(self.customer_points)
        
        return card
    
    def load_currencies(self):
        """تحميل قائمة العملات بأمان"""
        try:
            if self.currency_manager:
                currencies = self.currency_manager.get_active_currencies()
                if currencies:
                    self.currency_combo.clear()
                    for c in currencies:
                        symbol = c.get('symbol', c.get('code', ''))
                        name = c.get('name_ar', c.get('name_en', ''))
                        self.currency_combo.addItem(f"{symbol} {name}", c['code'])
                    
                    # تعيين العملة الافتراضية
                    default = self.currency_manager.get_default_currency()
                    if default:
                        self.current_currency = default['code']
                        index = self.currency_combo.findData(default['code'])
                        if index >= 0:
                            self.currency_combo.setCurrentIndex(index)
        except Exception as e:
            print(f"⚠️ خطأ في تحميل العملات: {e}")
    
    def generate_invoice_number(self):
        """توليد رقم فاتورة جديد بأمان"""
        try:
            if self.pos_service and hasattr(self.pos_service, 'generate_invoice_number'):
                invoice_num = self.pos_service.generate_invoice_number()
                self.invoice_label.setText(f"📄 فاتورة: {invoice_num}")
            else:
                import datetime
                invoice_num = datetime.datetime.now().strftime("INV-%Y%m%d%H%M%S")
                self.invoice_label.setText(f"📄 فاتورة: {invoice_num}")
        except Exception as e:
            print(f"⚠️ خطأ في توليد رقم الفاتورة: {e}")
            self.invoice_label.setText("📄 فاتورة: INV-000001")
    
    def load_products(self, category_id: Optional[int] = None, search: Optional[str] = None):
        """تحميل وعرض المنتجات بأمان"""
        # تنظيف شبكة المنتجات
        while self.product_layout.count():
            item = self.product_layout.takeAt(0)
            if item and item.widget():
                try:
                    item.widget().deleteLater()
                except:
                    pass
        
        try:
            if not self.pos_service:
                # عرض رسالة خطأ في الشبكة
                label = QLabel("⚠️ خدمة POS غير متوفرة")
                label.setAlignment(Qt.AlignCenter)
                label.setStyleSheet("color: red; font-size: 14px;")
                self.product_layout.addWidget(label, 0, 0)
                return
            
            products = self.pos_service.get_products_for_pos(category_id, search)
            
            if not products:
                label = QLabel("لا توجد منتجات للعرض")
                label.setAlignment(Qt.AlignCenter)
                label.setStyleSheet("color: #999; font-size: 14px;")
                self.product_layout.addWidget(label, 0, 0)
                return
            
            cols = 5
            for i, product in enumerate(products):
                try:
                    card = ProductCard(product)
                    # معالجة الإشارات بشكل آمن
                    if hasattr(card, 'clicked'):
                        card.clicked.connect(lambda product_id=product.get('id'): self.on_product_clicked(product_id))
                    else:
                        card.clicked.connect(lambda checked=False, product_id=product.get('id'): self.on_product_clicked(product_id))
                    self.product_layout.addWidget(card, i // cols, i % cols)
                except Exception as e:
                    print(f"⚠️ خطأ في إنشاء بطاقة منتج: {e}")
                    
        except Exception as e:
            print(f"❌ خطأ في تحميل المنتجات: {e}")
            traceback.print_exc()
            label = QLabel(f"❌ خطأ في تحميل المنتجات:\n{str(e)[:50]}")
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("color: red; font-size: 12px;")
            self.product_layout.addWidget(label, 0, 0)
    
    def on_product_clicked(self, product_id: Optional[int]):
        """معالج النقر على منتج بأمان"""
        if not product_id:
            return
        
        try:
            if not self.pos_service or not self.pos_service.db:
                QMessageBox.warning(self, "تنبيه", "خدمة قاعدة البيانات غير متوفرة")
                return
            
            product = self.pos_service.db.execute_one(
                "SELECT * FROM products WHERE id = ? AND is_active = 1", 
                (product_id,)
            )
            if not product:
                QMessageBox.warning(self, "تنبيه", "المنتج غير متوفر أو تم حذفه")
                return
            
            # التحقق من المخزون
            current_stock = float(product.get('current_stock', 0))
            if current_stock <= 0:
                reply = QMessageBox.question(
                    self, 
                    "⚠️ مخزون منخفض", 
                    f"المنتج '{product.get('name_ar', 'N/A')}' غير متوفر حالياً.\nهل تريد إضافته مع تنبيه؟",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return
            
            # البحث عن المنتج في السلة
            for item in self.cart_items:
                if item['product_id'] == product_id:
                    # التحقق من الكمية المتاحة
                    if item['quantity'] + 1 > current_stock and current_stock > 0:
                        QMessageBox.warning(self, "⚠️ تنبيه", f"الكمية المتاحة: {current_stock}")
                        return
                    item['quantity'] += 1
                    self.update_cart()
                    return
            
            # إضافة منتج جديد إلى السلة
            self.cart_items.append({
                'product_id': product_id,
                'name': product.get('name_ar', product.get('name_en', 'N/A')),
                'quantity': 1,
                'unit_price': float(product.get('sale_price', 0)),
                'unit_cost': float(product.get('cost_price', 0)),
                'discount_percent': 0.0,
                'tax_percent': float(product.get('tax_percent', 0)),
                'stock': current_stock
            })
            self.update_cart()
            
        except Exception as e:
            print(f"❌ خطأ في إضافة المنتج: {e}")
            traceback.print_exc()
            QMessageBox.critical(self, "❌ خطأ", f"فشل إضافة المنتج:\n{str(e)[:100]}")
    
    def update_cart(self):
        """تحديث عرض سلة المشتريات بدقة عالية"""
        try:
            self.cart_widget.setRowCount(0)
            
            subtotal = Decimal('0')
            total_discount = Decimal('0')
            total_tax = Decimal('0')
            total_profit = Decimal('0')
            
            for i, item in enumerate(self.cart_items):
                try:
                    quantity = Decimal(str(item.get('quantity', 1)))
                    unit_price = Decimal(str(item.get('unit_price', 0)))
                    discount_percent = Decimal(str(item.get('discount_percent', 0)))
                    tax_percent = Decimal(str(item.get('tax_percent', 0)))
                    unit_cost = Decimal(str(item.get('unit_cost', 0)))
                    
                    item_subtotal = quantity * unit_price
                    item_discount = item_subtotal * discount_percent / Decimal('100')
                    item_tax = (item_subtotal - item_discount) * tax_percent / Decimal('100')
                    item_total = item_subtotal - item_discount + item_tax
                    item_profit = (unit_price - unit_cost) * quantity - item_discount
                    
                    subtotal += item_subtotal
                    total_discount += item_discount
                    total_tax += item_tax
                    total_profit += item_profit
                    
                    # إضافة الصف إلى الجدول
                    self.cart_widget.add_arabic_row([
                        str(i + 1),
                        item.get('name', 'N/A'),
                        str(int(item.get('quantity', 1))),
                        self.format_amount(unit_price),
                        self.format_amount(item_discount),
                        self.format_amount(item_tax),
                        self.format_amount(item_total),
                        "🗑️"
                    ])
                except Exception as e:
                    print(f"⚠️ خطأ في حساب صف من السلة: {e}")
                    continue
            
            # تطبيق الخصم العام
            final_total = subtotal - total_discount + total_tax
            if self.discount_percent > 0:
                discount_amount = final_total * Decimal(str(self.discount_percent)) / Decimal('100')
                final_total = final_total - discount_amount
                total_discount += discount_amount
            elif self.discount_amount > 0:
                final_total = final_total - Decimal(str(self.discount_amount))
                total_discount += Decimal(str(self.discount_amount))
            
            # تحديث لوحة الإجماليات
            if hasattr(self.totals_panel, 'update_totals'):
                try:
                    self.totals_panel.update_totals(
                        float(subtotal), 
                        float(total_discount), 
                        float(total_tax), 
                        float(final_total), 
                        float(total_profit), 
                        self.current_currency
                    )
                except Exception as e:
                    print(f"⚠️ خطأ في تحديث لوحة الإجماليات: {e}")
            
            self.calculate_change()
        except Exception as e:
            print(f"❌ خطأ في تحديث السلة: {e}")
            traceback.print_exc()
    
    def format_amount(self, amount: Decimal) -> str:
        """تنسيق المبلغ حسب العملة الحالية"""
        try:
            if self.currency_manager:
                formatted = self.currency_manager.format_amount(float(amount), self.current_currency)
                return formatted if formatted else f"{amount:.2f}"
            return f"{amount:.2f}"
        except Exception as e:
            print(f"⚠️ خطأ في تنسيق المبلغ: {e}")
            return f"{amount:.2f}"
    
    def calculate_change(self):
        """حساب الباقي بأمان"""
        try:
            # الحصول على الإجمالي
            total = Decimal('0')
            if hasattr(self.totals_panel, 'get_total'):
                try:
                    total = Decimal(str(self.totals_panel.get_total()))
                except:
                    total = Decimal('0')
            
            # الحصول على المبلغ المدفوع
            paid_text = self.payment_amount.text().strip()
            if paid_text:
                try:
                    paid = Decimal(paid_text)
                    change = paid - total
                    if change >= 0:
                        self.change_label.setText(f"✅ الباقي: {self.format_amount(change)}")
                        self.change_label.setStyleSheet("color: #2E7D32; font-weight: bold;")
                        self.pay_btn.setEnabled(True)
                    else:
                        self.change_label.setText(f"⚠️ المتبقي: {self.format_amount(abs(change))}")
                        self.change_label.setStyleSheet("color: #F44336; font-weight: bold;")
                        self.pay_btn.setEnabled(False)
                except InvalidOperation:
                    self.change_label.setText("❌ مبلغ غير صحيح")
                    self.change_label.setStyleSheet("color: #F44336;")
                    self.pay_btn.setEnabled(False)
            else:
                self.change_label.setText(f"💰 الإجمالي: {self.format_amount(total)}")
                self.change_label.setStyleSheet("color: #2E7D32; font-weight: bold;")
                self.pay_btn.setEnabled(len(self.cart_items) > 0)
        except Exception as e:
            print(f"⚠️ خطأ في حساب الباقي: {e}")
    
    def delete_selected_item(self):
        """حذف العنصر المحدد من السلة"""
        try:
            current_row = self.cart_widget.currentRow()
            if 0 <= current_row < len(self.cart_items):
                self.cart_items.pop(current_row)
                self.update_cart()
        except Exception as e:
            print(f"⚠️ خطأ في حذف العنصر: {e}")
    
    def on_search(self, text: str):
        """معالج البحث"""
        self.load_products(search=text if text.strip() else None)
    
    def on_currency_changed(self, index: int):
        """معالج تغيير العملة"""
        try:
            if index >= 0:
                self.current_currency = self.currency_combo.currentData()
                self.update_cart()
        except Exception as e:
            print(f"⚠️ خطأ في تغيير العملة: {e}")
    
    def update_datetime(self):
        """تحديث عرض التاريخ والوقت"""
        try:
            now = QDateTime.currentDateTime()
            self.datetime_label.setText(now.toString("yyyy-MM-dd\nhh:mm:ss"))
        except:
            pass
    
    def on_complete_sale(self):
        """إتمام عملية البيع بأمان"""
        if not self.cart_items:
            QMessageBox.warning(self, "⚠️ تنبيه", "السلة فارغة! أضف منتجات أولاً.")
            return
        
        try:
            # حساب الإجمالي
            total = Decimal('0')
            if hasattr(self.totals_panel, 'get_total'):
                total = Decimal(str(self.totals_panel.get_total()))
            
            # التحقق من المبلغ المدفوع
            paid_text = self.payment_amount.text().strip()
            paid = Decimal('0')
            
            if paid_text:
                try:
                    paid = Decimal(paid_text)
                except InvalidOperation:
                    QMessageBox.warning(self, "❌ خطأ", "المبلغ المدفوع غير صحيح")
                    return
                
                if paid < total:
                    reply = QMessageBox.question(
                        self,
                        "⚠️ مبلغ غير مكتمل",
                        f"المبلغ المدفوع ({self.format_amount(paid)}) أقل من الإجمالي ({self.format_amount(total)}).\nهل تريد إكمال البيع كدفعة جزئية؟",
                        QMessageBox.Yes | QMessageBox.No
                    )
                    if reply == QMessageBox.No:
                        return
            
            # تجهيز بيانات الدفع
            payments = []
            if paid > 0:
                payments.append({
                    'method': self.payment_method.currentData(),
                    'amount': float(paid),
                    'currency': self.current_currency
                })
            
            # إنشاء الفاتورة
            if self.pos_service:
                result = self.pos_service.create_invoice(
                    items=self.cart_items,
                    customer_id=self.current_customer,
                    currency_code=self.current_currency,
                    payments=payments,
                    discount_percent=self.discount_percent
                )
                
                QMessageBox.information(
                    self,
                    "✅ تم البيع بنجاح",
                    f"تم إتمام البيع بنجاح!\n\n"
                    f"🧾 رقم الفاتورة: {result.get('invoice_number', 'N/A')}\n"
                    f"💰 الإجمالي: {self.format_amount(total)}\n"
                    f"💵 المدفوع: {self.format_amount(paid)}\n"
                    f"🔄 الباقي: {self.format_amount(paid - total)}"
                )
                
                # طباعة الإيصال تلقائياً
                self.on_print()
                
                # تحضير فاتورة جديدة
                self.clear_cart()
                self.generate_invoice_number()
            else:
                QMessageBox.warning(self, "❌ خطأ", "خدمة POS غير متوفرة")
                
        except Exception as e:
            print(f"❌ خطأ في إتمام البيع: {e}")
            traceback.print_exc()
            QMessageBox.critical(self, "❌ خطأ", f"فشل إتمام البيع:\n{str(e)[:100]}")
    
    def clear_cart(self):
        """مسح السلة بالكامل"""
        self.cart_items = []
        self.current_customer = None
        self.current_customer_data = None
        self.discount_percent = 0.0
        self.discount_amount = 0.0
        self.payment_amount.clear()
        self.payment_method.setCurrentIndex(0)
        
        self.customer_name.setText("عميل نقدي")
        self.customer_balance.setText("الرصيد: 0.00")
        self.customer_points.setText("🌟 النقاط: 0")
        
        self.update_cart()
        self.load_products()
    
    def on_cancel_sale(self):
        """إلغاء البيع الحالي"""
        if self.cart_items:
            reply = QMessageBox.question(
                self,
                "⚠️ تأكيد الإلغاء",
                "هل أنت متأكد من إلغاء الفاتورة الحالية؟\nسيتم فقدان جميع البيانات.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.clear_cart()
    
    def on_cash_payment(self):
        """تعيين طريقة الدفع نقدي"""
        try:
            index = self.payment_method.findData("cash")
            if index >= 0:
                self.payment_method.setCurrentIndex(index)
            self.payment_amount.setFocus()
        except:
            pass
    
    def on_bank_payment(self):
        """تعيين طريقة الدفع بنكي"""
        try:
            index = self.payment_method.findData("bank")
            if index >= 0:
                self.payment_method.setCurrentIndex(index)
            self.payment_amount.setFocus()
        except:
            pass
    
    def on_debt_payment(self):
        """تعيين طريقة الدفع آجل"""
        try:
            index = self.payment_method.findData("debt")
            if index >= 0:
                self.payment_method.setCurrentIndex(index)
            self.payment_amount.clear()
            self.payment_amount.setPlaceholderText("آجل - سيتم تسجيل الدين")
        except:
            pass
    
    def on_hold_invoice(self):
        """تعليق الفاتورة الحالية"""
        if not self.cart_items:
            QMessageBox.warning(self, "⚠️ تنبيه", "لا توجد منتجات لتعليقها")
            return
        
        try:
            if self.pos_service and hasattr(self.pos_service, 'hold_invoice'):
                hold_num = self.pos_service.hold_invoice(self.cart_items, self.current_customer)
                QMessageBox.information(self, "✅ تم التعليق", f"تم تعليق الفاتورة بنجاح\n🔖 الرمز: {hold_num}")
                self.clear_cart()
            else:
                QMessageBox.warning(self, "⚠️ خطأ", "خدمة التعليق غير متوفرة")
        except Exception as e:
            print(f"❌ خطأ في تعليق الفاتورة: {e}")
            QMessageBox.critical(self, "❌ خطأ", f"فشل تعليق الفاتورة:\n{str(e)[:100]}")
    
    def on_resume_invoice(self):
        """استئناف فاتورة معلقة"""
        try:
            if not self.pos_service or not hasattr(self.pos_service, 'get_held_invoices'):
                QMessageBox.warning(self, "⚠️ خطأ", "خدمة الاستئناف غير متوفرة")
                return
            
            held_invoices = self.pos_service.get_held_invoices()
            if not held_invoices:
                QMessageBox.information(self, "ℹ️ معلقات", "لا توجد فواتير معلقة")
                return
            
            # فتح نافذة اختيار الفاتورة
            dialog = QDialog(self)
            dialog.setWindowTitle("استئناف فاتورة معلقة")
            dialog.setMinimumWidth(400)
            dialog.setLayoutDirection(Qt.RightToLeft)
            dialog.setLayout(QVBoxLayout())
            
            list_widget = QListWidget()
            for inv in held_invoices:
                list_widget.addItem(f"🔖 {inv.get('hold_number', 'N/A')} - {inv.get('created_at', 'N/A')}")
            
            buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            
            dialog.layout().addWidget(QLabel("اختر الفاتورة المراد استئناؤها:"))
            dialog.layout().addWidget(list_widget)
            dialog.layout().addWidget(buttons)
            
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            
            if dialog.exec() == QDialog.Accepted and list_widget.currentRow() >= 0:
                selected = held_invoices[list_widget.currentRow()]
                # استعادة البيانات
                import json
                items_json = selected.get('items_json', '[]')
                self.cart_items = json.loads(items_json) if items_json else []
                self.current_customer = selected.get('customer_id')
                self.update_cart()
                QMessageBox.information(self, "✅ تم", "تم استئناف الفاتورة بنجاح")
                
        except Exception as e:
            print(f"❌ خطأ في استئناف الفاتورة: {e}")
            traceback.print_exc()
            QMessageBox.critical(self, "❌ خطأ", f"فشل استئناف الفاتورة:\n{str(e)[:100]}")
    
    def on_return(self):
        """معالج المرتجعات"""
        QMessageBox.information(self, "🔄 المرتجعات", "فتح شاشة إدارة المرتجعات - قيد التطوير")
    
    def on_select_customer(self):
        """معالج اختيار العميل"""
        QMessageBox.information(self, "👤 اختيار عميل", "فتح شاشة البحث عن العملاء - قيد التطوير")
    
    def on_apply_discount(self):
        """تطبيق خصم على الفاتورة"""
        if not self.cart_items:
            QMessageBox.warning(self, "⚠️ تنبيه", "لا توجد منتجات لتطبيق الخصم")
            return
        
        try:
            dialog = QDialog(self)
            dialog.setWindowTitle("تطبيق خصم")
            dialog.setMinimumWidth(300)
            dialog.setLayoutDirection(Qt.RightToLeft)
            dialog.setLayout(QVBoxLayout())
            
            form = QFormLayout()
            discount_type = QComboBox()
            discount_type.addItems(["نسبة مئوية (%)", "قيمة ثابتة"])
            discount_value = QDoubleSpinBox()
            discount_value.setRange(0, 10000)
            discount_value.setSuffix(" %")
            
            form.addRow("نوع الخصم:", discount_type)
            form.addRow("القيمة:", discount_value)
            
            buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            
            dialog.layout().addLayout(form)
            dialog.layout().addWidget(buttons)
            
            def apply_discount_dialog():
                if discount_type.currentIndex() == 0:  # نسبة
                    self.discount_percent = discount_value.value()
                    self.discount_amount = 0
                else:  # قيمة
                    self.discount_amount = discount_value.value()
                    self.discount_percent = 0
                self.update_cart()
                dialog.accept()
            
            buttons.accepted.connect(apply_discount_dialog)
            buttons.rejected.connect(dialog.reject)
            
            dialog.exec()
        except Exception as e:
            print(f"⚠️ خطأ في تطبيق الخصم: {e}")
    
    def on_calculator(self):
        """فتح الحاسبة"""
        QMessageBox.information(self, "🧮 حاسبة", "فتح الحاسبة - قيد التطوير")
    
    def on_print(self):
        """طباعة الإيصال"""
        QMessageBox.information(self, "🖨️ طباعة", "جاري طباعة الإيصال - قيد التطوير")
    
    def on_settings(self):
        """فتح الإعدادات"""
        QMessageBox.information(self, "⚙️ إعدادات", "فتح إعدادات نقطة البيع - قيد التطوير")
    
    def show_help(self):
        """عرض المساعدة"""
        QMessageBox.information(
            self,
            "📖 مساعدة - نقطة البيع",
            "اختصارات لوحة المفاتيح:\n\n"
            "🔹 F1 - عرض هذه المساعدة\n"
            "🔹 F2 - التركيز على شريط البحث\n"
            "🔹 F3 - تطبيق خصم\n"
            "🔹 F4 - اختيار عميل\n"
            "🔹 F5 - إتمام البيع\n"
            "🔹 Ctrl+N - فاتورة جديدة\n"
            "🔹 Ctrl+H - تعليق فاتورة\n"
            "🔹 Delete - حذف العنصر المحدد"
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # للاختبار المستقل
    try:
        from core.database.connection import DatabaseManager
        db = DatabaseManager(":memory:")
        
        window = POSWindow(db_manager=db)
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        print(f"❌ خطأ في تشغيل التطبيق: {e}")
        traceback.print_exc()
        sys.exit(1)
