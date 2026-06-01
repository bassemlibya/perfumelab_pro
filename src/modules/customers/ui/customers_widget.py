# modules/customers/ui/customers_widget.py
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from core.database.connection import DatabaseManager
from core.managers.currency_manager import CurrencyManager
from ui.widgets.arabic_widgets import ArabicTableWidget, ArabicLineEdit, ArabicComboBox

class CustomersWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = DatabaseManager()
        self.currency_manager = CurrencyManager()
        self.setLayoutDirection(Qt.RightToLeft)
        self.setup_ui()
        self.load_customers()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        header = QHBoxLayout()
        title = QLabel("إدارة العملاء")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #2E7D32;")
        header.addWidget(title)
        header.addStretch()

        self.search_input = ArabicLineEdit(placeholder="بحث بالاسم أو الهاتف...")
        self.search_input.setMinimumWidth(300)
        self.search_input.textChanged.connect(self.on_search)
        header.addWidget(self.search_input)

        self.group_combo = ArabicComboBox()
        self.group_combo.addItem("جميع المجموعات", None)
        groups = self.db.execute("SELECT id, name_ar FROM customer_groups WHERE is_active = 1")
        for g in groups:
            self.group_combo.addItem(g['name_ar'], g['id'])
        self.group_combo.currentIndexChanged.connect(self.on_group_changed)
        header.addWidget(self.group_combo)

        add_btn = QPushButton("+ عميل جديد")
        add_btn.setStyleSheet("background-color: #2E7D32; color: white; padding: 8px 16px; border-radius: 4px; font-weight: bold;")
        add_btn.clicked.connect(self.on_add_customer)
        header.addWidget(add_btn)

        layout.addLayout(header)

        # Customers table
        self.customers_table = ArabicTableWidget(columns=[
            "الكود", "الاسم", "الهاتف", "المجموعة", "الرصيد", "النقاط", "حد الائتمان", "الفواتير", "المشتريات", "الحالة", ""
        ])
        layout.addWidget(self.customers_table)

        # Customer details panel
        details_group = QGroupBox("تفاصيل العميل")
        details_layout = QVBoxLayout(details_group)
        self.details_label = QLabel("اختر عميلاً لعرض التفاصيل")
        self.details_label.setStyleSheet("font-size: 14px; color: #757575;")
        details_layout.addWidget(self.details_label)
        layout.addWidget(details_group)

    def load_customers(self, group_id=None, search=None):
        self.customers_table.setRowCount(0)
        query = "SELECT c.*, cg.name_ar as group_name, COUNT(s.id) as invoice_count, SUM(s.total) as total_purchases FROM customers c LEFT JOIN customer_groups cg ON c.group_id = cg.id LEFT JOIN sales s ON c.id = s.customer_id AND s.status = 'completed' WHERE c.is_active = 1"
        params = []

        if group_id:
            query += " AND c.group_id = ?"
            params.append(group_id)

        if search:
            query += " AND (c.name_ar LIKE ? OR c.phone LIKE ?)"
            params.extend(["%%%s%%" % search, "%%%s%%" % search])

        query += " GROUP BY c.id ORDER BY c.name_ar"

        customers = self.db.execute(query, tuple(params))
        for c in customers:
            status = "نشط" if c['is_active'] else "معطل"
            balance_color = "#F44336" if (c['balance'] or 0) > 0 else "#4CAF50"
            self.customers_table.add_arabic_row([
                str(c['id']),
                c['name_ar'],
                c['phone'] or "",
                c['group_name'] or "",
                self.currency_manager.format_amount(c['balance'] or 0, 'USD'),
                str(c['loyalty_points'] or 0),
                self.currency_manager.format_amount(c['credit_limit'] or 0, 'USD'),
                str(c['invoice_count'] or 0),
                self.currency_manager.format_amount(c['total_purchases'] or 0, 'USD'),
                status,
                "تفاصيل"
            ])

    def on_search(self, text):
        self.load_customers(search=text)

    def on_group_changed(self, index):
        self.load_customers(group_id=self.group_combo.currentData())

    def on_add_customer(self):
        QMessageBox.information(self, "عميل جديد", "فتح شاشة إضافة عميل جديد")
