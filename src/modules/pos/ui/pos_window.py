# modules/pos/ui/pos_window.py
import sys
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from core.services.pos_service import POSService
from core.managers.currency_manager import CurrencyManager
from core.managers.theme_manager import ThemeManager
from ui.widgets.arabic_widgets import (
    ArabicLineEdit, ArabicComboBox, ArabicTableWidget, 
    ProductCard, SearchBar, TotalsPanel
)

class POSWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.pos_service = POSService()
        self.currency_manager = CurrencyManager()
        self.theme_manager = ThemeManager()
        self.cart_items = []
        self.current_customer = None
        self.current_currency = self.currency_manager.get_default_currency()['code']
        self.setWindowTitle("نقطة البيع - PerfumeLab Pro")
        self.setLayoutDirection(Qt.RightToLeft)
        self.resize(1920, 1080)
        self.setup_ui()
        self.load_products()

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.sidebar = self.create_sidebar()
        main_layout.addWidget(self.sidebar)
        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.setContentsMargins(10, 10, 10, 10)
        center_layout.setSpacing(10)
        self.header = self.create_header()
        center_layout.addWidget(self.header)
        self.search_bar = SearchBar()
        self.search_bar.search_changed.connect(self.on_search)
        center_layout.addWidget(self.search_bar)
        splitter = QSplitter(Qt.Vertical)
        self.product_grid = self.create_product_grid()
        splitter.addWidget(self.product_grid)
        self.cart_table = self.create_cart_table()
        splitter.addWidget(self.cart_table)
        splitter.setSizes([500, 400])
        center_layout.addWidget(splitter, 1)
        main_layout.addWidget(center_widget, 1)
        self.payment_panel = self.create_payment_panel()
        main_layout.addWidget(self.payment_panel)

    def create_header(self):
        header = QWidget()
        header.setFixedHeight(60)
        header.setStyleSheet("background-color: #2E7D32; color: white;")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(15, 5, 15, 5)
        logo = QLabel("PerfumeLab Pro")
        logo.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(logo)
        self.invoice_label = QLabel("فاتورة: INV-000000000000")
        self.invoice_label.setStyleSheet("font-size: 14px;")
        layout.addWidget(self.invoice_label)
        self.user_label = QLabel("المستخدم: Admin")
        layout.addWidget(self.user_label)
        self.currency_combo = ArabicComboBox()
        currencies = self.currency_manager.get_active_currencies()
        for c in currencies:
            self.currency_combo.addItem("%s (%s)" % (c['name_ar'], c['symbol']), c['code'])
        self.currency_combo.currentIndexChanged.connect(self.on_currency_changed)
        layout.addWidget(self.currency_combo)
        self.datetime_label = QLabel()
        self.datetime_label.setStyleSheet("font-size: 13px;")
        layout.addWidget(self.datetime_label)
        self.update_datetime()
        timer = QTimer(self)
        timer.timeout.connect(self.update_datetime)
        timer.start(1000)
        layout.addStretch()
        return header

    def create_sidebar(self):
        sidebar = QWidget()
        sidebar.setFixedWidth(80)
        sidebar.setStyleSheet("background-color: #1B5E20;")
        layout = QVBoxLayout(sidebar)
        layout.setSpacing(8)
        layout.setContentsMargins(5, 10, 5, 10)
        buttons = [
            ("نقدي", "cash", self.on_cash_payment),
            ("بنك", "bank", self.on_bank_payment),
            ("آجل", "debt", self.on_debt_payment),
            ("تعليق", "hold", self.on_hold_invoice),
            ("استئناف", "resume", self.on_resume_invoice),
            ("مرتجع", "return", self.on_return),
            ("عميل", "customer", self.on_select_customer),
            ("خصم", "discount", self.on_apply_discount),
            ("حاسبة", "calc", self.on_calculator),
            ("طباعة", "print", self.on_print),
            ("إعدادات", "settings", self.on_settings),
        ]
        for label, icon, callback in buttons:
            btn = QPushButton(label)
            btn.setFixedSize(70, 60)
            btn.setStyleSheet("QPushButton { background-color: #2E7D32; color: white; border: none; border-radius: 6px; font-size: 11px; font-weight: bold; } QPushButton:hover { background-color: #4CAF50; }")
            btn.clicked.connect(callback)
            layout.addWidget(btn)
        layout.addStretch()
        return sidebar

    def create_product_grid(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: #FAFAFA; }")
        container = QWidget()
        self.product_layout = QGridLayout(container)
        self.product_layout.setSpacing(10)
        self.product_layout.setContentsMargins(10, 10, 10, 10)
        scroll.setWidget(container)
        return scroll

    def create_cart_table(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        self.cart_widget = ArabicTableWidget(columns=["#", "الصنف", "الكمية", "السعر", "الخصم", "الضريبة", "الإجمالي", ""])
        self.cart_widget.setMinimumHeight(250)
        layout.addWidget(self.cart_widget)
        return widget

    def create_payment_panel(self):
        panel = QWidget()
        panel.setFixedWidth(350)
        panel.setStyleSheet("background-color: #F5F5F5; border-left: 1px solid #E0E0E0;")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)
        self.customer_card = self.create_customer_card()
        layout.addWidget(self.customer_card)
        self.totals_panel = TotalsPanel()
        layout.addWidget(self.totals_panel)
        payment_group = QGroupBox("طريقة الدفع")
        payment_layout = QVBoxLayout(payment_group)
        self.payment_method = ArabicComboBox()
        self.payment_method.addItem("نقدي", "cash")
        self.payment_method.addItem("بنك", "bank")
        self.payment_method.addItem("بطاقة", "card")
        self.payment_method.addItem("محفظة", "wallet")
        self.payment_method.addItem("آجل", "debt")
        payment_layout.addWidget(self.payment_method)
        self.payment_amount = ArabicLineEdit(placeholder="المبلغ المدفوع")
        self.payment_amount.setMinimumHeight(45)
        payment_layout.addWidget(self.payment_amount)
        layout.addWidget(payment_group)
        btn_layout = QHBoxLayout()
        self.pay_btn = QPushButton("إتمام البيع")
        self.pay_btn.setMinimumHeight(50)
        self.pay_btn.setStyleSheet("QPushButton { background-color: #2E7D32; color: white; font-size: 16px; font-weight: bold; border-radius: 6px; } QPushButton:hover { background-color: #1B5E20; }")
        self.pay_btn.clicked.connect(self.on_complete_sale)
        btn_layout.addWidget(self.pay_btn)
        self.cancel_btn = QPushButton("إلغاء")
        self.cancel_btn.setMinimumHeight(50)
        self.cancel_btn.setStyleSheet("QPushButton { background-color: #F44336; color: white; font-size: 16px; font-weight: bold; border-radius: 6px; } QPushButton:hover { background-color: #D32F2F; }")
        self.cancel_btn.clicked.connect(self.on_cancel_sale)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)
        layout.addStretch()
        return panel

    def create_customer_card(self):
        card = QFrame()
        card.setStyleSheet("background-color: white; border-radius: 8px; padding: 10px; border: 1px solid #E0E0E0;")
        layout = QVBoxLayout(card)
        self.customer_name = QLabel("عميل نقدي")
        self.customer_name.setStyleSheet("font-size: 16px; font-weight: bold; color: #212121;")
        layout.addWidget(self.customer_name)
        self.customer_balance = QLabel("الرصيد: 0.00")
        self.customer_balance.setStyleSheet("font-size: 13px; color: #757575;")
        layout.addWidget(self.customer_balance)
        self.customer_points = QLabel("النقاط: 0")
        self.customer_points.setStyleSheet("font-size: 13px; color: #757575;")
        layout.addWidget(self.customer_points)
        return card

    def load_products(self, category_id=None, search=None):
        while self.product_layout.count():
            item = self.product_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        products = self.pos_service.get_products_for_pos(category_id, search)
        cols = 5
        for i, product in enumerate(products):
            card = ProductCard(product)
            card.clicked.connect(self.on_product_clicked)
            self.product_layout.addWidget(card, i // cols, i % cols)

    def on_product_clicked(self, product_id):
        product = self.pos_service.db.execute_one("SELECT * FROM products WHERE id = ?", (product_id,))
        if not product:
            return
        for item in self.cart_items:
            if item['product_id'] == product_id:
                item['quantity'] += 1
                self.update_cart()
                return
        self.cart_items.append({
            'product_id': product_id,
            'name': product['name_ar'],
            'quantity': 1,
            'unit_price': product['sale_price'],
            'unit_cost': product['cost_price'],
            'discount_percent': 0,
            'tax_percent': product['tax_percent'],
            'stock': product['current_stock']
        })
        self.update_cart()

    def update_cart(self):
        self.cart_widget.setRowCount(0)
        subtotal = 0
        total_discount = 0
        total_tax = 0
        total_profit = 0
        for i, item in enumerate(self.cart_items):
            item_subtotal = item['quantity'] * item['unit_price']
            item_discount = item_subtotal * (item['discount_percent'] / 100)
            item_tax = (item_subtotal - item_discount) * (item['tax_percent'] / 100)
            item_total = item_subtotal - item_discount + item_tax
            item_profit = (item['unit_price'] - item['unit_cost']) * item['quantity'] - item_discount
            subtotal += item_subtotal
            total_discount += item_discount
            total_tax += item_tax
            total_profit += item_profit
            self.cart_widget.add_arabic_row([
                str(i + 1),
                item['name'],
                str(item['quantity']),
                self.currency_manager.format_amount(item['unit_price'], self.current_currency),
                self.currency_manager.format_amount(item_discount, self.current_currency),
                self.currency_manager.format_amount(item_tax, self.current_currency),
                self.currency_manager.format_amount(item_total, self.current_currency),
                "X"
            ])
        total = subtotal - total_discount + total_tax
        self.totals_panel.update_totals(subtotal, total_discount, total_tax, total, total_profit, self.current_currency)

    def on_search(self, text):
        self.load_products(search=text)

    def on_currency_changed(self, index):
        self.current_currency = self.currency_combo.currentData()
        self.update_cart()

    def update_datetime(self):
        self.datetime_label.setText(QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss"))

    def on_complete_sale(self):
        if not self.cart_items:
            QMessageBox.warning(self, "تنبيه", "السلة فارغة!")
            return
        try:
            payments = []
            if self.payment_amount.text():
                payments.append({
                    'method': self.payment_method.currentData(),
                    'amount': float(self.payment_amount.text() or 0),
                    'currency': self.current_currency
                })
            result = self.pos_service.create_invoice(
                items=self.cart_items,
                customer_id=self.current_customer,
                currency_code=self.current_currency,
                payments=payments
            )
            QMessageBox.information(self, "نجاح", "تم إتمام البيع بنجاح!\nرقم الفاتورة: %s" % result['invoice_number'])
            self.clear_cart()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))

    def clear_cart(self):
        self.cart_items = []
        self.current_customer = None
        self.customer_name.setText("عميل نقدي")
        self.customer_balance.setText("الرصيد: 0.00")
        self.customer_points.setText("النقاط: 0")
        self.payment_amount.clear()
        self.update_cart()
        self.load_products()

    def on_cancel_sale(self):
        self.clear_cart()

    def on_cash_payment(self): self.payment_method.setCurrentIndex(0)
    def on_bank_payment(self): self.payment_method.setCurrentIndex(1)
    def on_debt_payment(self): self.payment_method.setCurrentIndex(4)
    def on_hold_invoice(self):
        if not self.cart_items:
            return
        hold_num = self.pos_service.hold_invoice(self.cart_items, self.current_customer)
        QMessageBox.information(self, "تعليق", "تم تعليق الفاتورة: %s" % hold_num)
        self.clear_cart()
    def on_resume_invoice(self):
        held = self.pos_service.get_held_invoices()
        if not held:
            QMessageBox.information(self, "تعليق", "لا توجد فواتير معلقة")
            return
    def on_return(self): QMessageBox.information(self, "مرتجع", "فتح شاشة المرتجعات")
    def on_select_customer(self): QMessageBox.information(self, "عميل", "فتح شاشة اختيار العميل")
    def on_apply_discount(self): QMessageBox.information(self, "خصم", "فتح شاشة الخصم")
    def on_calculator(self): QMessageBox.information(self, "حاسبة", "فتح الحاسبة")
    def on_print(self): QMessageBox.information(self, "طباعة", "جاري الطباعة...")
    def on_settings(self): QMessageBox.information(self, "إعدادات", "فتح الإعدادات")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = POSWindow()
    window.show()
    sys.exit(app.exec())
