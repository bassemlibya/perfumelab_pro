# modules/treasury/ui/treasury_widget.py
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from core.services.treasury_service import TreasuryService
from core.managers.currency_manager import CurrencyManager
from ui.widgets.arabic_widgets import ArabicTableWidget, ArabicLineEdit, ArabicComboBox

class TreasuryWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.treasury_service = TreasuryService()
        self.currency_manager = CurrencyManager()
        self.setLayoutDirection(Qt.RightToLeft)
        self.setup_ui()
        self.refresh_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        header = QHBoxLayout()
        title = QLabel("إدارة الخزينة")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #2E7D32;")
        header.addWidget(title)
        header.addStretch()

        receipt_btn = QPushButton("+ سند قبض")
        receipt_btn.setStyleSheet("background-color: #1565C0; color: white; padding: 8px 16px; border-radius: 4px; font-weight: bold;")
        receipt_btn.clicked.connect(self.on_create_receipt)
        header.addWidget(receipt_btn)

        payment_btn = QPushButton("+ سند صرف")
        payment_btn.setStyleSheet("background-color: #FF6F00; color: white; padding: 8px 16px; border-radius: 4px; font-weight: bold;")
        payment_btn.clicked.connect(self.on_create_payment)
        header.addWidget(payment_btn)

        transfer_btn = QPushButton("تحويل")
        transfer_btn.setStyleSheet("background-color: #6C5CE7; color: white; padding: 8px 16px; border-radius: 4px; font-weight: bold;")
        transfer_btn.clicked.connect(self.on_transfer)
        header.addWidget(transfer_btn)

        layout.addLayout(header)

        # Cashboxes summary
        cashbox_group = QGroupBox("الخزائن النقدية")
        cashbox_layout = QVBoxLayout(cashbox_group)
        self.cashbox_table = ArabicTableWidget(columns=["الخزينة", "الفرع", "العملة", "الرصيد الحالي", "الرصيد الافتتاحي", "الحالة"])
        cashbox_layout.addWidget(self.cashbox_table)
        layout.addWidget(cashbox_group)

        # Bank accounts
        bank_group = QGroupBox("الحسابات البنكية")
        bank_layout = QVBoxLayout(bank_group)
        self.bank_table = ArabicTableWidget(columns=["البنك", "اسم الحساب", "رقم الحساب", "العملة", "الرصيد", "الحالة"])
        bank_layout.addWidget(self.bank_table)
        layout.addWidget(bank_group)

        # Transactions
        trans_group = QGroupBox("المعاملات الأخيرة")
        trans_layout = QVBoxLayout(trans_group)
        self.trans_table = ArabicTableWidget(columns=["التاريخ", "النوع", "المن", "إلى", "المبلغ", "العملة", "المرجع"])
        trans_layout.addWidget(self.trans_table)
        layout.addWidget(trans_group)

    def refresh_data(self):
        # Cashboxes
        self.cashbox_table.setRowCount(0)
        cashboxes = self.treasury_service.get_cashbox_balance()
        for cb in cashboxes:
            status = "نشط" if cb['is_active'] else "معطل"
            self.cashbox_table.add_arabic_row([
                cb['name_ar'],
                "الفرع الرئيسي",
                cb['symbol_ar'] or cb['symbol'],
                self.currency_manager.format_amount(cb['current_balance'] or 0, cb['currency_code']),
                self.currency_manager.format_amount(cb['opening_balance'] or 0, cb['currency_code']),
                status
            ])

        # Bank accounts
        self.bank_table.setRowCount(0)
        banks = self.treasury_service.db.execute(
            "SELECT ba.*, b.name_ar as bank_name, c.symbol, c.symbol_ar FROM bank_accounts ba JOIN banks b ON ba.bank_id = b.id JOIN currencies c ON ba.currency_code = c.code WHERE ba.is_active = 1"
        )
        for ba in banks:
            self.bank_table.add_arabic_row([
                ba['bank_name'],
                ba['account_name_ar'],
                ba['account_number'] or "",
                ba['symbol_ar'] or ba['symbol'],
                self.currency_manager.format_amount(ba['current_balance'] or 0, ba['currency_code']),
                "نشط"
            ])

        # Transactions
        self.trans_table.setRowCount(0)
        transactions = self.treasury_service.db.execute(
            "SELECT tt.*, c.symbol, c.symbol_ar FROM treasury_transactions tt JOIN currencies c ON tt.currency_code = c.code ORDER BY tt.created_at DESC LIMIT 50"
        )
        for t in transactions:
            self.trans_table.add_arabic_row([
                str(t['created_at']),
                t['transaction_type'],
                "-",
                "-",
                self.currency_manager.format_amount(t['amount'] or 0, t['currency_code']),
                t['symbol_ar'] or t['symbol'],
                t['reference_type'] or ""
            ])

    def on_create_receipt(self):
        QMessageBox.information(self, "سند قبض", "فتح شاشة سند القبض")

    def on_create_payment(self):
        QMessageBox.information(self, "سند صرف", "فتح شاشة سند الصرف")

    def on_transfer(self):
        QMessageBox.information(self, "تحويل", "فتح شاشة التحويل بين الخزائن")
