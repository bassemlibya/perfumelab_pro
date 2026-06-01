# modules/manufacturing/ui/manufacturing_widget.py
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from core.database.connection import DatabaseManager
from core.managers.currency_manager import CurrencyManager
from ui.widgets.arabic_widgets import ArabicTableWidget, ArabicLineEdit, ArabicComboBox

class ManufacturingWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = DatabaseManager()
        self.currency_manager = CurrencyManager()
        self.setLayoutDirection(Qt.RightToLeft)
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        header = QHBoxLayout()
        title = QLabel("إدارة التصنيع")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #2E7D32;")
        header.addWidget(title)
        header.addStretch()

        recipe_btn = QPushButton("+ وصفة جديدة")
        recipe_btn.setStyleSheet("background-color: #1565C0; color: white; padding: 8px 16px; border-radius: 4px; font-weight: bold;")
        recipe_btn.clicked.connect(self.on_add_recipe)
        header.addWidget(recipe_btn)

        order_btn = QPushButton("+ أمر إنتاج")
        order_btn.setStyleSheet("background-color: #2E7D32; color: white; padding: 8px 16px; border-radius: 4px; font-weight: bold;")
        order_btn.clicked.connect(self.on_add_order)
        header.addWidget(order_btn)

        layout.addLayout(header)

        # Tabs
        tabs = QTabWidget()
        tabs.setLayoutDirection(Qt.RightToLeft)

        # Recipes tab
        recipes_widget = QWidget()
        recipes_layout = QVBoxLayout(recipes_widget)
        self.recipes_table = ArabicTableWidget(columns=["الكود", "الاسم", "المنتج النهائي", "الحجم", "التركيز", "التكلفة", "الحالة"])
        recipes_layout.addWidget(self.recipes_table)
        tabs.addTab(recipes_widget, "الوصفات")

        # Production orders tab
        orders_widget = QWidget()
        orders_layout = QVBoxLayout(orders_widget)
        self.orders_table = ArabicTableWidget(columns=["رقم الأمر", "الوصفة", "الكمية", "التكلفة", "الحالة", "التاريخ", ""])
        orders_layout.addWidget(self.orders_table)
        tabs.addTab(orders_widget, "أوامر الإنتاج")

        # Raw materials tab
        materials_widget = QWidget()
        materials_layout = QVBoxLayout(materials_widget)
        self.materials_table = ArabicTableWidget(columns=["الكود", "الاسم", "النوع", "المورد", "المخزون", "التكلفة", "الحالة"])
        materials_layout.addWidget(self.materials_table)
        tabs.addTab(materials_widget, "المواد الخام")

        layout.addWidget(tabs)

    def load_data(self):
        # Recipes
        self.recipes_table.setRowCount(0)
        recipes = self.db.execute(
            "SELECT r.*, p.name_ar as product_name FROM recipes r LEFT JOIN products p ON r.product_id = p.id WHERE r.is_active = 1"
        )
        for r in recipes:
            self.recipes_table.add_arabic_row([
                str(r['id']), r['name_ar'], r['product_name'] or "", str(r['volume_ml'] or 0),
                r['concentration'] or "", "-", "نشط"
            ])

        # Production orders
        self.orders_table.setRowCount(0)
        orders = self.db.execute(
            "SELECT po.*, r.name_ar as recipe_name FROM production_orders po JOIN recipes r ON po.recipe_id = r.id ORDER BY po.created_at DESC"
        )
        for o in orders:
            self.orders_table.add_arabic_row([
                o['order_number'], o['recipe_name'], str(o['quantity'] or 0),
                self.currency_manager.format_amount(o['total_cost'] or 0, 'USD'),
                o['status'], str(o['created_at']), "تفاصيل"
            ])

        # Raw materials
        self.materials_table.setRowCount(0)
        materials = self.db.execute(
            "SELECT rm.*, s.name_ar as supplier_name FROM raw_materials rm LEFT JOIN suppliers s ON rm.supplier_id = s.id WHERE rm.is_active = 1"
        )
        for m in materials:
            self.materials_table.add_arabic_row([
                str(m['id']), m['name_ar'], m['material_type'] or "", m['supplier_name'] or "",
                str(m['current_stock'] or 0), self.currency_manager.format_amount(m['cost_per_unit'] or 0, 'USD'), "نشط"
            ])

    def on_add_recipe(self):
        QMessageBox.information(self, "وصفة جديدة", "فتح شاشة إضافة وصفة")

    def on_add_order(self):
        QMessageBox.information(self, "أمر إنتاج", "فتح شاشة أمر إنتاج جديد")
