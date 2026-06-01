# ui/widgets/arabic_widgets.py
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from core.managers.currency_manager import CurrencyManager

class ArabicLineEdit(QLineEdit):
    def __init__(self, parent=None, placeholder: str = ""):
        super().__init__(parent)
        self.setAlignment(Qt.AlignRight)
        if placeholder:
            self.setPlaceholderText(placeholder)
        self.setStyleSheet("padding: 8px; border-radius: 4px; font-size: 14px;")

class ArabicComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setStyleSheet("padding: 6px; border-radius: 4px; font-size: 14px;")

class ArabicTableWidget(QTableWidget):
    def __init__(self, parent=None, columns: list = None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setTextElideMode(Qt.ElideRight)
        if columns:
            self.setColumnCount(len(columns))
            self.setHorizontalHeaderLabels(columns)
        header = self.horizontalHeader()
        header.setDefaultAlignment(Qt.AlignRight | Qt.AlignVCenter)
        header.setSectionResizeMode(QHeaderView.Stretch)
        self.setStyleSheet("QTableWidget { border: 1px solid #E0E0E0; gridline-color: #E0E0E0; } QTableWidget::item { padding: 8px; text-align: right; } QHeaderView::section { background-color: #2E7D32; color: white; padding: 10px; font-weight: bold; font-size: 13px; }")

    def add_arabic_row(self, data: list):
        row = self.rowCount()
        self.insertRow(row)
        for col, value in enumerate(data):
            item = QTableWidgetItem(str(value))
            item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.setItem(row, col, item)

class CurrencySpinBox(QDoubleSpinBox):
    def __init__(self, parent=None, currency_code: str = 'USD'):
        super().__init__(parent)
        self.currency_manager = CurrencyManager()
        self.currency_code = currency_code
        self.setDecimals(2)
        self.setMaximum(999999999.99)
        self.setAlignment(Qt.AlignRight)
        self.setStyleSheet("padding: 6px; font-size: 14px; font-weight: bold; color: #2E7D32;")

    def set_currency(self, code: str):
        self.currency_code = code

    def textFromValue(self, value: float) -> str:
        return self.currency_manager.format_amount(value, self.currency_code, True)

class ProductCard(QFrame):
    clicked = Signal(int)

    def __init__(self, product_data: dict, parent=None):
        super().__init__(parent)
        self.product_id = product_data.get('id')
        self.setup_ui(product_data)
        self.setCursor(Qt.PointingHandCursor)

    def setup_ui(self, data: dict):
        self.setFixedSize(220, 160)
        self.setStyleSheet("ProductCard { background-color: white; border: 1px solid #E0E0E0; border-radius: 8px; } ProductCard:hover { border: 2px solid #2E7D32; background-color: #F1F8E9; }")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        name = QLabel(data.get('name_ar', 'منتج'))
        name.setAlignment(Qt.AlignRight)
        name.setStyleSheet("font-size: 13px; font-weight: bold; color: #212121;")
        name.setWordWrap(True)
        layout.addWidget(name)
        sku = QLabel(data.get('sku', '') or data.get('barcode', ''))
        sku.setAlignment(Qt.AlignRight)
        sku.setStyleSheet("font-size: 10px; color: #757575;")
        layout.addWidget(sku)
        h_layout = QHBoxLayout()
        stock_label = QLabel("مخزون: %s" % data.get('current_stock', 0))
        stock_color = '#4CAF50' if data.get('current_stock', 0) > 0 else '#F44336'
        stock_label.setStyleSheet("font-size: 11px; color: %s;" % stock_color)
        h_layout.addWidget(stock_label)
        price = CurrencySpinBox(currency_code=data.get('currency_code', 'USD'))
        price.setValue(data.get('sale_price', 0))
        price.setEnabled(False)
        price.setButtonSymbols(QDoubleSpinBox.NoButtons)
        price.setStyleSheet("border: none; background: transparent; font-size: 14px; font-weight: bold; color: #2E7D32;")
        h_layout.addWidget(price)
        layout.addLayout(h_layout)
        add_btn = QPushButton("+ إضافة")
        add_btn.setStyleSheet("background-color: #2E7D32; color: white; border-radius: 4px; padding: 4px;")
        add_btn.clicked.connect(lambda: self.clicked.emit(self.product_id))
        layout.addWidget(add_btn)

    def mousePressEvent(self, event):
        self.clicked.emit(self.product_id)

class SearchBar(QWidget):
    search_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.search_input = ArabicLineEdit(placeholder="بحث بالباركود أو الاسم أو SKU...")
        self.search_input.textChanged.connect(self.search_changed.emit)
        self.search_input.setMinimumHeight(40)
        layout.addWidget(self.search_input)
        barcode_btn = QPushButton("Scan")
        barcode_btn.setFixedSize(40, 40)
        barcode_btn.setStyleSheet("font-size: 14px; background-color: #1565C0; color: white; border-radius: 4px;")
        layout.addWidget(barcode_btn)
        voice_btn = QPushButton("Mic")
        voice_btn.setFixedSize(40, 40)
        voice_btn.setStyleSheet("font-size: 14px; background-color: #FF6F00; color: white; border-radius: 4px;")
        layout.addWidget(voice_btn)

class TotalsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.currency_manager = CurrencyManager()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        self.labels = {}
        fields = [
            ('subtotal', 'المجموع', '#212121'),
            ('discount', 'الخصم', '#F44336'),
            ('tax', 'الضريبة', '#757575'),
            ('total', 'الإجمالي', '#2E7D32'),
        ]
        for key, label, color in fields:
            row = QHBoxLayout()
            lbl = QLabel(label)
            lbl.setStyleSheet("font-size: 14px; font-weight: bold;")
            row.addWidget(lbl)
            val = QLabel("0.00")
            val.setStyleSheet("font-size: 16px; font-weight: bold; color: %s;" % color)
            val.setAlignment(Qt.AlignLeft)
            row.addWidget(val)
            self.labels[key] = val
            layout.addLayout(row)
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("color: #E0E0E0;")
        layout.addWidget(line)
        profit_row = QHBoxLayout()
        profit_lbl = QLabel("الربح")
        profit_lbl.setStyleSheet("font-size: 12px; color: #757575;")
        profit_row.addWidget(profit_lbl)
        self.profit_label = QLabel("0.00")
        self.profit_label.setStyleSheet("font-size: 12px; color: #757575;")
        self.profit_label.setAlignment(Qt.AlignLeft)
        profit_row.addWidget(self.profit_label)
        layout.addLayout(profit_row)

    def update_totals(self, subtotal: float, discount: float, tax: float, total: float, profit: float = 0, currency_code: str = 'USD'):
        self.labels['subtotal'].setText(self.currency_manager.format_amount(subtotal, currency_code))
        self.labels['discount'].setText(self.currency_manager.format_amount(discount, currency_code))
        self.labels['tax'].setText(self.currency_manager.format_amount(tax, currency_code))
        self.labels['total'].setText(self.currency_manager.format_amount(total, currency_code))
        self.profit_label.setText(self.currency_manager.format_amount(profit, currency_code))
