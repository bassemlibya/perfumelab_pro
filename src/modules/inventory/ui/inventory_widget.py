# modules/inventory/ui/inventory_widget.py
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from core.services.inventory_service import InventoryService
from core.managers.currency_manager import CurrencyManager
from ui.widgets.arabic_widgets import ArabicTableWidget, ArabicLineEdit, ArabicComboBox

class InventoryWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.inventory_service = InventoryService()
        self.currency_manager = CurrencyManager()
        self.setLayoutDirection(Qt.RightToLeft)
        self.setup_ui()
        self.load_products()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        header = QHBoxLayout()
        title = QLabel("إدارة المخزون")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #2E7D32;")
        header.addWidget(title)
        header.addStretch()
        self.search_input = ArabicLineEdit(placeholder="بحث بالاسم أو الباركود أو SKU...")
        self.search_input.setMinimumWidth(300)
        self.search_input.textChanged.connect(self.on_search)
        header.addWidget(self.search_input)
        self.category_combo = ArabicComboBox()
        self.category_combo.addItem("جميع الفئات", None)
        categories = self.inventory_service.db.execute("SELECT id, name_ar FROM product_categories WHERE is_active = 1")
        for cat in categories:
            self.category_combo.addItem(cat['name_ar'], cat['id'])
        self.category_combo.currentIndexChanged.connect(self.on_category_changed)
        header.addWidget(self.category_combo)
        self.warehouse_combo = ArabicComboBox()
        self.warehouse_combo.addItem("جميع المستودعات", None)
        warehouses = self.inventory_service.db.execute("SELECT id, name_ar FROM warehouses WHERE is_active = 1")
        for wh in warehouses:
            self.warehouse_combo.addItem(wh['name_ar'], wh['id'])
        self.warehouse_combo.currentIndexChanged.connect(self.on_warehouse_changed)
        header.addWidget(self.warehouse_combo)
        add_btn = QPushButton("+ إضافة منتج")
        add_btn.setStyleSheet("background-color: #2E7D32; color: white; padding: 8px 16px; border-radius: 4px; font-weight: bold;")
        add_btn.clicked.connect(self.on_add_product)
        header.addWidget(add_btn)
        layout.addLayout(header)
        self.products_table = ArabicTableWidget(columns=["الكود", "الاسم", "الفئة", "الماركة", "SKU", "الباركود", "سعر التكلفة", "سعر البيع", "المخزون", "الحد الأدنى", "الحالة", ""])
        layout.addWidget(self.products_table)
        movements_group = QGroupBox("حركات المخزون")
        movements_layout = QVBoxLayout(movements_group)
        self.movements_table = ArabicTableWidget(columns=["التاريخ", "النوع", "المنتج", "المستودع", "الكمية", "التكلفة", "المرجع", ""])
        movements_layout.addWidget(self.movements_table)
        layout.addWidget(movements_group)

    def load_products(self, category_id=None, warehouse_id=None, search=None):
        self.products_table.setRowCount(0)
        query = "SELECT p.*, c.name_ar as category_name, b.name_ar as brand_name, COALESCE(ws.quantity, 0) as warehouse_stock FROM products p LEFT JOIN product_categories c ON p.category_id = c.id LEFT JOIN product_brands b ON p.brand_id = b.id LEFT JOIN warehouse_stock ws ON p.id = ws.product_id"
        params = []
        conditions = ["p.is_active = 1"]
        if warehouse_id:
            query += " AND ws.warehouse_id = ?"
            params.append(warehouse_id)
        if category_id:
            conditions.append("p.category_id = ?")
            params.append(category_id)
        if search:
            conditions.append("(p.name_ar LIKE ? OR p.barcode LIKE ? OR p.sku LIKE ?)")
            params.extend(["%%%s%%" % search, "%%%s%%" % search, "%%%s%%" % search])
        query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY p.name_ar"
        products = self.inventory_service.db.execute(query, tuple(params))
        for p in products:
            status = "نشط" if p['is_active'] else "معطل"
            self.products_table.add_arabic_row([
                str(p['id']), p['name_ar'], p['category_name'] or "", p['brand_name'] or "",
                p['sku'] or "", p['barcode'] or "",
                self.currency_manager.format_amount(p['cost_price'] or 0, 'USD'),
                self.currency_manager.format_amount(p['sale_price'] or 0, 'USD'),
                str(p['current_stock'] or 0), str(p['minimum_stock'] or 0), status, "تعديل"
            ])

    def on_search(self, text):
        self.load_products(search=text)
    def on_category_changed(self, index):
        self.load_products(category_id=self.category_combo.currentData())
    def on_warehouse_changed(self, index):
        self.load_products(warehouse_id=self.warehouse_combo.currentData())
    def on_add_product(self):
        QMessageBox.information(self, "إضافة منتج", "فتح شاشة إضافة منتج جديد")
