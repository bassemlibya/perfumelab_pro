# modules/reports/ui/reports_widget.py
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from core.reports.report_engine import ReportEngine
from core.managers.currency_manager import CurrencyManager
from ui.widgets.arabic_widgets import ArabicTableWidget

class ReportsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.report_engine = ReportEngine()
        self.currency_manager = CurrencyManager()
        self.setLayoutDirection(Qt.RightToLeft)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        header = QHBoxLayout()
        title = QLabel("التقارير والإحصائيات")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #2E7D32;")
        header.addWidget(title)
        header.addStretch()

        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate().addDays(-30))
        header.addWidget(QLabel("من:"))
        header.addWidget(self.start_date)

        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        header.addWidget(QLabel("إلى:"))
        header.addWidget(self.end_date)

        refresh_btn = QPushButton("تحديث")
        refresh_btn.setStyleSheet("background-color: #2E7D32; color: white; padding: 8px 16px; border-radius: 4px; font-weight: bold;")
        refresh_btn.clicked.connect(self.refresh_reports)
        header.addWidget(refresh_btn)

        export_btn = QPushButton("تصدير Excel")
        export_btn.setStyleSheet("background-color: #1565C0; color: white; padding: 8px 16px; border-radius: 4px; font-weight: bold;")
        export_btn.clicked.connect(self.on_export)
        header.addWidget(export_btn)

        layout.addLayout(header)

        # Report tabs
        tabs = QTabWidget()
        tabs.setLayoutDirection(Qt.RightToLeft)

        # Sales report
        sales_widget = QWidget()
        sales_layout = QVBoxLayout(sales_widget)
        self.sales_report_table = ArabicTableWidget(columns=["الفترة", "عدد الفواتير", "المبيعات", "الربح", "الخصومات", "متوسط الفاتورة"])
        sales_layout.addWidget(self.sales_report_table)
        tabs.addTab(sales_widget, "المبيعات")

        # Profit report
        profit_widget = QWidget()
        profit_layout = QVBoxLayout(profit_widget)
        profit_summary = QHBoxLayout()
        self.profit_revenue = QLabel("الإيرادات: 0.00")
        self.profit_revenue.setStyleSheet("font-size: 18px; font-weight: bold; color: #2E7D32;")
        profit_summary.addWidget(self.profit_revenue)
        self.profit_costs = QLabel("التكاليف: 0.00")
        self.profit_costs.setStyleSheet("font-size: 18px; font-weight: bold; color: #F44336;")
        profit_summary.addWidget(self.profit_costs)
        self.profit_net = QLabel("صافي الربح: 0.00")
        self.profit_net.setStyleSheet("font-size: 18px; font-weight: bold; color: #1565C0;")
        profit_summary.addWidget(self.profit_net)
        profit_layout.addLayout(profit_summary)
        tabs.addTab(profit_widget, "الأرباح")

        # Inventory report
        inventory_widget = QWidget()
        inventory_layout = QVBoxLayout(inventory_widget)
        self.inventory_report_table = ArabicTableWidget(columns=["المنتج", "الفئة", "المخزون", "التكلفة", "القيمة"])
        inventory_layout.addWidget(self.inventory_report_table)
        tabs.addTab(inventory_widget, "المخزون")

        # Customers report
        customers_widget = QWidget()
        customers_layout = QVBoxLayout(customers_widget)
        self.customers_report_table = ArabicTableWidget(columns=["العميل", "المجموعة", "عدد الفواتير", "إجمالي المشتريات", "الرصيد"])
        customers_layout.addWidget(self.customers_report_table)
        tabs.addTab(customers_widget, "العملاء")

        layout.addWidget(tabs)
        self.refresh_reports()

    def refresh_reports(self):
        start = self.start_date.date().toString("yyyy-MM-dd")
        end = self.end_date.date().toString("yyyy-MM-dd")
        currency = self.currency_manager.get_default_currency()['code']

        # Sales report
        self.sales_report_table.setRowCount(0)
        sales_data = self.report_engine.get_sales_report(start, end)
        for row in sales_data:
            self.sales_report_table.add_arabic_row([
                row['period'],
                str(row['invoice_count']),
                self.currency_manager.format_amount(row['total_amount'] or 0, currency),
                self.currency_manager.format_amount(row['total_profit'] or 0, currency),
                self.currency_manager.format_amount(row['total_discounts'] or 0, currency),
                self.currency_manager.format_amount(row['avg_invoice'] or 0, currency)
            ])

        # Profit report
        profit_data = self.report_engine.get_profit_report(start, end)
        self.profit_revenue.setText("الإيرادات: %s" % self.currency_manager.format_amount(profit_data['revenue'], currency))
        self.profit_costs.setText("التكاليف: %s" % self.currency_manager.format_amount(profit_data['costs'] + profit_data['purchases'] + profit_data['expenses'], currency))
        self.profit_net.setText("صافي الربح: %s" % self.currency_manager.format_amount(profit_data['profit'], currency))

        # Inventory report
        self.inventory_report_table.setRowCount(0)
        inventory_data = self.report_engine.get_inventory_report()
        for item in inventory_data:
            value = (item['stock_qty'] or 0) * (item['cost_price'] or 0)
            self.inventory_report_table.add_arabic_row([
                item['name_ar'],
                item['category_name'] or "",
                str(item['stock_qty'] or 0),
                self.currency_manager.format_amount(item['cost_price'] or 0, currency),
                self.currency_manager.format_amount(value, currency)
            ])

        # Customers report
        self.customers_report_table.setRowCount(0)
        customers_data = self.report_engine.get_customer_report()
        for c in customers_data:
            self.customers_report_table.add_arabic_row([
                c['name_ar'],
                c['group_name'] or "",
                str(c['total_invoices'] or 0),
                self.currency_manager.format_amount(c['total_purchases'] or 0, currency),
                self.currency_manager.format_amount(c['balance'] or 0, currency)
            ])

    def on_export(self):
        QMessageBox.information(self, "تصدير", "جاري تصدير التقرير إلى Excel...")
