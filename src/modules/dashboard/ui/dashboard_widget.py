# modules/dashboard/ui/dashboard_widget.py
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from core.reports.report_engine import ReportEngine
from core.managers.currency_manager import CurrencyManager
from ui.widgets.arabic_widgets import ArabicTableWidget

class DashboardWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.report_engine = ReportEngine()
        self.currency_manager = CurrencyManager()
        self.setLayoutDirection(Qt.RightToLeft)
        self.setup_ui()
        self.refresh_data()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_data)
        self.timer.start(60000)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        title = QLabel("لوحة المعلومات")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #2E7D32;")
        title.setAlignment(Qt.AlignRight)
        layout.addWidget(title)
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(15)
        self.kpi_cards = {}
        kpi_configs = [
            ('sales', 'المبيعات اليوم', '#2E7D32'),
            ('profit', 'الربح اليوم', '#1565C0'),
            ('invoices', 'عدد الفواتير', '#FF6F00'),
            ('customers', 'عملاء جدد', '#6C5CE7'),
        ]
        for key, title_text, color in kpi_configs:
            card = self.create_kpi_card(title_text, color)
            self.kpi_cards[key] = card
            kpi_layout.addWidget(card)
        layout.addLayout(kpi_layout)
        middle_layout = QHBoxLayout()
        self.low_stock_table = ArabicTableWidget(columns=["المنتج", "المخزون الحالي", "الحد الأدنى", "الحالة"])
        self.low_stock_table.setMaximumHeight(300)
        low_stock_group = QGroupBox("تنبيه المخزون المنخفض")
        low_stock_layout = QVBoxLayout(low_stock_group)
        low_stock_layout.addWidget(self.low_stock_table)
        middle_layout.addWidget(low_stock_group)
        self.treasury_table = ArabicTableWidget(columns=["الخزينة", "العملة", "الرصيد"])
        self.treasury_table.setMaximumHeight(300)
        treasury_group = QGroupBox("ملخص الخزينة")
        treasury_layout = QVBoxLayout(treasury_group)
        treasury_layout.addWidget(self.treasury_table)
        middle_layout.addWidget(treasury_group)
        layout.addLayout(middle_layout)
        self.top_products_table = ArabicTableWidget(columns=["المنتج", "الكمية المباعة", "إجمالي المبيعات"])
        top_group = QGroupBox("أكثر المنتجات مبيعاً اليوم")
        top_layout = QVBoxLayout(top_group)
        top_layout.addWidget(self.top_products_table)
        layout.addWidget(top_group)

    def create_kpi_card(self, title, color):
        card = QFrame()
        card.setStyleSheet("QFrame { background-color: white; border-radius: 12px; border: 1px solid #E0E0E0; padding: 15px; } QFrame:hover { border: 2px solid %s; }" % color)
        card.setMinimumHeight(120)
        card.setMinimumWidth(200)
        layout = QVBoxLayout(card)
        layout.setSpacing(8)
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 14px; color: #757575;")
        title_label.setAlignment(Qt.AlignRight)
        layout.addWidget(title_label)
        value_label = QLabel("0")
        value_label.setStyleSheet("font-size: 28px; font-weight: bold; color: %s;" % color)
        value_label.setAlignment(Qt.AlignRight)
        layout.addWidget(value_label)
        card.value_label = value_label
        return card

    def refresh_data(self):
        kpis = self.report_engine.get_dashboard_kpis()
        currency = self.currency_manager.get_default_currency()['code']
        self.kpi_cards['sales'].value_label.setText(self.currency_manager.format_amount(kpis['today_sales']['total_sales'] or 0, currency))
        self.kpi_cards['profit'].value_label.setText(self.currency_manager.format_amount(kpis['today_sales']['total_profit'] or 0, currency))
        self.kpi_cards['invoices'].value_label.setText(str(kpis['today_sales']['invoice_count'] or 0))
        self.kpi_cards['customers'].value_label.setText(str(kpis['new_customers'] or 0))
        self.low_stock_table.setRowCount(0)
        low_stock = self.report_engine.db.execute("SELECT p.name_ar, p.current_stock, p.minimum_stock, CASE WHEN p.current_stock <= 0 THEN 'نفذ' ELSE 'منخفض' END as status FROM products p WHERE p.current_stock <= p.minimum_stock AND p.is_active = 1 LIMIT 10")
        for item in low_stock:
            self.low_stock_table.add_arabic_row([item['name_ar'], str(item['current_stock']), str(item['minimum_stock']), item['status']])
        self.treasury_table.setRowCount(0)
        for balance in kpis['treasury_balances']:
            self.treasury_table.add_arabic_row([balance['name_ar'], balance['symbol_ar'] or balance['symbol'], self.currency_manager.format_amount(balance['balance'], balance['name_ar'])])
        self.top_products_table.setRowCount(0)
        for product in kpis['top_products']:
            self.top_products_table.add_arabic_row([product['name_ar'], str(product['qty']), self.currency_manager.format_amount(product['total'], currency)])
