# ui/shell/main_shell.py
import sys
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from core.managers.theme_manager import ThemeManager
from modules.dashboard.ui.dashboard_widget import DashboardWidget
from modules.pos.ui.pos_window import POSWindow
from modules.inventory.ui.inventory_widget import InventoryWidget
from modules.customers.ui.customers_widget import CustomersWidget
from modules.treasury.ui.treasury_widget import TreasuryWidget
from modules.manufacturing.ui.manufacturing_widget import ManufacturingWidget
from modules.reports.ui.reports_widget import ReportsWidget

class MainShell(QMainWindow):
    def __init__(self):
        super().__init__()
        self.theme_manager = ThemeManager()
        self.setWindowTitle("PerfumeLab Pro ERP")
        self.setLayoutDirection(Qt.RightToLeft)
        self.resize(1920, 1080)
        self.setup_ui()

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        nav = self.create_navigation()
        main_layout.addWidget(nav)
        self.content_stack = QStackedWidget()
        self.content_stack.setStyleSheet("background-color: #FAFAFA;")
        main_layout.addWidget(self.content_stack, 1)
        self.modules = {
            'dashboard': DashboardWidget(),
            'pos': POSWindow(),
            'inventory': InventoryWidget(),
            'customers': CustomersWidget(),
            'treasury': TreasuryWidget(),
            'manufacturing': ManufacturingWidget(),
            'reports': ReportsWidget(),
        }
        for key, widget in self.modules.items():
            self.content_stack.addWidget(widget)
        self.show_module('dashboard')

    def create_navigation(self):
        nav = QWidget()
        nav.setFixedWidth(220)
        nav.setStyleSheet("background-color: #1B5E20;")
        layout = QVBoxLayout(nav)
        layout.setSpacing(4)
        layout.setContentsMargins(10, 20, 10, 20)
        logo = QLabel("PerfumeLab Pro")
        logo.setStyleSheet("font-size: 20px; font-weight: bold; color: white; padding: 10px;")
        logo.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo)
        version = QLabel("v2.0 Enterprise")
        version.setStyleSheet("font-size: 11px; color: #81C784; padding-bottom: 20px;")
        version.setAlignment(Qt.AlignCenter)
        layout.addWidget(version)
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("color: #2E7D32;")
        layout.addWidget(line)
        nav_items = [
            ('dashboard', 'لوحة المعلومات', '#4CAF50'),
            ('pos', 'نقطة البيع', '#FF6F00'),
            ('inventory', 'المخزون', '#1565C0'),
            ('customers', 'العملاء', '#6C5CE7'),
            ('treasury', 'الخزينة', '#00CEC9'),
            ('manufacturing', 'التصنيع', '#FD79A8'),
            ('reports', 'التقارير', '#2D3436'),
        ]
        self.nav_buttons = {}
        for key, label, color in nav_items:
            btn = QPushButton(label)
            btn.setFixedHeight(50)
            btn.setStyleSheet("QPushButton { background-color: transparent; color: white; border: none; border-radius: 8px; font-size: 14px; font-weight: bold; text-align: right; padding-right: 15px; } QPushButton:hover { background-color: %s; } QPushButton:checked { background-color: %s; }" % (color, color))
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, k=key: self.show_module(k))
            self.nav_buttons[key] = btn
            layout.addWidget(btn)
        layout.addStretch()
        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setStyleSheet("color: #2E7D32;")
        layout.addWidget(line2)
        self.user_label = QLabel("المستخدم: Admin")
        self.user_label.setStyleSheet("font-size: 12px; color: #81C784; padding: 5px;")
        self.user_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.user_label)
        theme_btn = QPushButton("تبديل السمة")
        theme_btn.setStyleSheet("background-color: #2E7D32; color: white; border-radius: 6px; padding: 8px; font-size: 12px;")
        theme_btn.clicked.connect(self.toggle_theme)
        layout.addWidget(theme_btn)
        logout_btn = QPushButton("تسجيل الخروج")
        logout_btn.setStyleSheet("background-color: #F44336; color: white; border-radius: 6px; padding: 8px; font-size: 12px;")
        logout_btn.clicked.connect(self.on_logout)
        layout.addWidget(logout_btn)
        return nav

    def show_module(self, key):
        for btn in self.nav_buttons.values():
            btn.setChecked(False)
        if key in self.nav_buttons:
            self.nav_buttons[key].setChecked(True)
        widget = self.modules.get(key)
        if widget:
            self.content_stack.setCurrentWidget(widget)
            if key in self.nav_buttons:
                self.setWindowTitle("%s - PerfumeLab Pro" % self.nav_buttons[key].text())

    def toggle_theme(self):
        current = self.theme_manager.current_theme
        next_theme = {'light': 'dark', 'dark': 'modern', 'modern': 'light'}[current]
        app = QApplication.instance()
        self.theme_manager.apply_theme(next_theme, app)

    def on_logout(self):
        reply = QMessageBox.question(self, "تسجيل الخروج", "هل أنت متأكد من تسجيل الخروج؟")
        if reply == QMessageBox.Yes:
            self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    shell = MainShell()
    shell.showMaximized()
    sys.exit(app.exec())
