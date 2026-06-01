# ui/shell/main_shell.py
import sys
from typing import Optional, Dict, Any
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *

# استيراد صحيح مع معالجة الأخطاء
try:
    from core.managers.theme_manager import ThemeManager
    from core.database.connection import DatabaseManager
    from core.managers.currency_manager import CurrencyManager
except ImportError as e:
    print(f"خطأ في الاستيراد: {e}")
    sys.exit(1)

# استيراد الوحدات مع معالجة الأخطاء
try:
    from modules.dashboard.ui.dashboard_widget import DashboardWidget
    from modules.pos.ui.pos_window import POSWindow
    from modules.inventory.ui.inventory_widget import InventoryWidget
    from modules.customers.ui.customers_widget import CustomersWidget
    from modules.treasury.ui.treasury_widget import TreasuryWidget
    from modules.manufacturing.ui.manufacturing_widget import ManufacturingWidget
    from modules.reports.ui.reports_widget import ReportsWidget
except ImportError as e:
    print(f"تحذير: بعض الوحدات غير متوفرة - {e}")
    # إنشاء وحدات وهمية للتجربة
    DashboardWidget = lambda: QLabel("Dashboard - قيد التطوير")
    POSWindow = lambda: QLabel("POS - قيد التطوير")
    InventoryWidget = lambda: QLabel("Inventory - قيد التطوير")
    CustomersWidget = lambda: QLabel("Customers - قيد التطوير")
    TreasuryWidget = lambda: QLabel("Treasury - قيد التطوير")
    ManufacturingWidget = lambda: QLabel("Manufacturing - قيد التطوير")
    ReportsWidget = lambda: QLabel("Reports - قيد التطوير")

class MainShell(QMainWindow):
    """النافذة الرئيسية للنظام"""
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None, 
                 currency_manager: Optional[CurrencyManager] = None,
                 theme_manager: Optional[ThemeManager] = None):
        super().__init__()
        
        # استخدام المديرين من الخارج أو إنشاء نسخ جديدة
        self.db_manager = db_manager
        self.currency_manager = currency_manager
        self.theme_manager = theme_manager or ThemeManager()
        
        # إعدادات النافذة
        self.setWindowTitle("PerfumeLab Pro ERP")
        self.setLayoutDirection(Qt.RightToLeft)
        
        # استعادة حجم النافذة من الإعدادات
        self._load_window_settings()
        
        # إعداد واجهة المستخدم
        self.setup_ui()
        
        # إعداد المؤقتات والاتصالات
        self.setup_timers()
        
        # تطبيق السمة الحالية
        self.apply_current_theme()
        
        # ربط إشارة الإغلاق
        self.closeEvent = self.on_close_event
    
    def _load_window_settings(self):
        """استعادة إعدادات النافذة من قاعدة البيانات"""
        try:
            # محاولة قراءة الإعدادات من قاعدة البيانات
            if self.db_manager and self.db_manager.table_exists('settings'):
                result = self.db_manager.execute_one(
                    "SELECT setting_value FROM settings WHERE setting_key = ?",
                    ('window_geometry',)
                )
                if result:
                    geometry = result['setting_value']
                    if geometry:
                        self.restoreGeometry(QByteArray.fromHex(geometry.encode()))
                
                result = self.db_manager.execute_one(
                    "SELECT setting_value FROM settings WHERE setting_key = ?",
                    ('window_state',)
                )
                if result:
                    state = result['setting_value']
                    if state:
                        self.restoreState(QByteArray.fromHex(state.encode()))
        except Exception as e:
            print(f"خطأ في استعادة إعدادات النافذة: {e}")
        
        # إذا لم تكن هناك إعدادات، استخدم الحجم الافتراضي
        if not self.geometry().isEmpty():
            return
        
        # الحصول على حجم الشاشة
        screen = QApplication.primaryScreen().availableGeometry()
        self.resize(int(screen.width() * 0.9), int(screen.height() * 0.9))
        self.move((screen.width() - self.width()) // 2, 
                  (screen.height() - self.height()) // 2)
    
    def _save_window_settings(self):
        """حفظ إعدادات النافذة"""
        try:
            if self.db_manager and self.db_manager.table_exists('settings'):
                self.db_manager.execute_update(
                    """INSERT OR REPLACE INTO settings (setting_key, setting_value, setting_group) 
                       VALUES (?, ?, ?)""",
                    ('window_geometry', self.saveGeometry().toHex().decode(), 'window')
                )
                self.db_manager.execute_update(
                    """INSERT OR REPLACE INTO settings (setting_key, setting_value, setting_group) 
                       VALUES (?, ?, ?)""",
                    ('window_state', self.saveState().toHex().decode(), 'window')
                )
        except Exception as e:
            print(f"خطأ في حفظ إعدادات النافذة: {e}")
    
    def setup_ui(self):
        """إعداد واجهة المستخدم الرئيسية"""
        # العنصر المركزي
        central = QWidget()
        self.setCentralWidget(central)
        
        # التخطيط الرئيسي
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # إنشاء شريط التنقل
        nav = self._create_navigation()
        main_layout.addWidget(nav)
        
        # منطقة المحتوى
        self.content_stack = QStackedWidget()
        self.content_stack.setStyleSheet("""
            QStackedWidget {
                background-color: #F5F5F5;
            }
        """)
        main_layout.addWidget(self.content_stack, 1)
        
        # تهيئة الوحدات
        self._initialize_modules()
        
        # عرض لوحة المعلومات الافتراضية
        self.show_module('dashboard')
    
    def _initialize_modules(self):
        """تهيئة جميع وحدات النظام"""
        self.modules: Dict[str, QWidget] = {}
        
        # تمرير المديرين إلى الوحدات إذا كانت تدعمها
        modules_config = {
            'dashboard': DashboardWidget,
            'pos': POSWindow,
            'inventory': InventoryWidget,
            'customers': CustomersWidget,
            'treasury': TreasuryWidget,
            'manufacturing': ManufacturingWidget,
            'reports': ReportsWidget,
        }
        
        for key, widget_class in modules_config.items():
            try:
                # محاولة تمرير المعاملات إذا كانت الوحدة تدعمها
                widget = self._create_module_instance(widget_class)
                if widget:
                    self.modules[key] = widget
                    self.content_stack.addWidget(widget)
                    print(f"تم تحميل الوحدة: {key}")
                else:
                    print(f"فشل تحميل الوحدة: {key}")
            except Exception as e:
                print(f"خطأ في تحميل الوحدة {key}: {e}")
                # إنشاء وحدة وهمية
                placeholder = QLabel(f"⚠️ الوحدة {key} غير متوفرة\n{str(e)}")
                placeholder.setAlignment(Qt.AlignCenter)
                placeholder.setStyleSheet("font-size: 16px; color: red;")
                self.modules[key] = placeholder
                self.content_stack.addWidget(placeholder)
    
    def _create_module_instance(self, widget_class):
        """إنشاء نسخة من الوحدة مع تمرير المعاملات المناسبة"""
        try:
            # محاولة تمرير db_manager و currency_manager
            if hasattr(widget_class, '__init__'):
                import inspect
                sig = inspect.signature(widget_class.__init__)
                params = list(sig.parameters.keys())
                
                kwargs = {}
                if 'db_manager' in params and self.db_manager:
                    kwargs['db_manager'] = self.db_manager
                if 'currency_manager' in params and self.currency_manager:
                    kwargs['currency_manager'] = self.currency_manager
                if 'theme_manager' in params and self.theme_manager:
                    kwargs['theme_manager'] = self.theme_manager
                
                return widget_class(**kwargs) if kwargs else widget_class()
            return widget_class()
        except Exception as e:
            print(f"خطأ في إنشاء الوحدة: {e}")
            return None
    
    def _create_navigation(self) -> QWidget:
        """إنشاء شريط التنقل الجانبي"""
        nav = QWidget()
        nav.setFixedWidth(250)
        nav.setStyleSheet("""
            QWidget {
                background-color: #1B5E20;
            }
        """)
        
        layout = QVBoxLayout(nav)
        layout.setSpacing(8)
        layout.setContentsMargins(10, 20, 10, 20)
        
        # الشعار
        logo = QLabel("PerfumeLab Pro")
        logo.setStyleSheet("""
            font-size: 22px; 
            font-weight: bold; 
            color: white; 
            padding: 15px 0px;
        """)
        logo.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo)
        
        # الإصدار
        version = QLabel("v2.0 Enterprise")
        version.setStyleSheet("""
            font-size: 11px; 
            color: #81C784; 
            padding-bottom: 20px;
        """)
        version.setAlignment(Qt.AlignCenter)
        layout.addWidget(version)
        
        # فاصل
        layout.addWidget(self._create_separator())
        
        # أزرار التنقل
        nav_items = [
            ('dashboard', '📊 لوحة المعلومات', '#4CAF50'),
            ('pos', '💰 نقطة البيع', '#FF6F00'),
            ('inventory', '📦 المخزون', '#1565C0'),
            ('customers', '👥 العملاء', '#6C5CE7'),
            ('treasury', '🏦 الخزينة', '#00CEC9'),
            ('manufacturing', '🏭 التصنيع', '#FD79A8'),
            ('reports', '📈 التقارير', '#2D3436'),
        ]
        
        self.nav_buttons = {}
        for key, label, color in nav_items:
            btn = QPushButton(label)
            btn.setFixedHeight(55)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: white;
                    border: none;
                    border-radius: 10px;
                    font-size: 14px;
                    font-weight: bold;
                    text-align: right;
                    padding-right: 15px;
                }}
                QPushButton:hover {{
                    background-color: {color};
                }}
                QPushButton:checked {{
                    background-color: {color};
                    border-left: 3px solid white;
                }}
            """)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, k=key: self.show_module(k))
            self.nav_buttons[key] = btn
            layout.addWidget(btn)
        
        layout.addStretch()
        
        # فاصل
        layout.addWidget(self._create_separator())
        
        # معلومات المستخدم
        self.user_label = QLabel("👤 المستخدم: Admin")
        self.user_label.setStyleSheet("""
            font-size: 12px; 
            color: #81C784; 
            padding: 10px 5px;
        """)
        self.user_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.user_label)
        
        # زر تبديل السمة
        theme_btn = QPushButton("🎨 تبديل السمة")
        theme_btn.setCursor(Qt.PointingHandCursor)
        theme_btn.setStyleSheet("""
            QPushButton {
                background-color: #2E7D32;
                color: white;
                border-radius: 8px;
                padding: 10px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
        """)
        theme_btn.clicked.connect(self.toggle_theme)
        layout.addWidget(theme_btn)
        
        # زر تسجيل الخروج
        logout_btn = QPushButton("🚪 تسجيل الخروج")
        logout_btn.setCursor(Qt.PointingHandCursor)
        logout_btn.setStyleSheet("""
            QPushButton {
                background-color: #D32F2F;
                color: white;
                border-radius: 8px;
                padding: 10px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #F44336;
            }
        """)
        logout_btn.clicked.connect(self.on_logout)
        layout.addWidget(logout_btn)
        
        return nav
    
    def _create_separator(self) -> QFrame:
        """إنشاء خط فاصل"""
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("color: #2E7D32;")
        return line
    
    def setup_timers(self):
        """إعداد المؤقتات"""
        # مؤقت لتحديث الوقت/الإشعارات
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_status)
        self.timer.start(60000)  # كل دقيقة
    
    def _update_status(self):
        """تحديث شريط الحالة"""
        # تحديث الوقت أو الإشعارات
        current_time = QTime.currentTime().toString("hh:mm:ss")
        self.statusBar().showMessage(f"آخر تحديث: {current_time}", 5000)
    
    def show_module(self, key: str):
        """عرض وحدة معينة"""
        if key not in self.modules:
            print(f"تحذير: الوحدة {key} غير موجودة")
            return
        
        # تحديث حالة الأزرار
        for btn_key, btn in self.nav_buttons.items():
            btn.setChecked(btn_key == key)
        
        # عرض الوحدة
        widget = self.modules[key]
        self.content_stack.setCurrentWidget(widget)
        
        # تحديث عنوان النافذة
        module_names = {
            'dashboard': 'لوحة المعلومات',
            'pos': 'نقطة البيع',
            'inventory': 'إدارة المخزون',
            'customers': 'إدارة العملاء',
            'treasury': 'الخزينة والحسابات',
            'manufacturing': 'التصنيع',
            'reports': 'التقارير'
        }
        title = module_names.get(key, key)
        self.setWindowTitle(f"{title} - PerfumeLab Pro ERP")
        
        # تشغيل أي تحديث عند عرض الوحدة
        if hasattr(widget, 'on_show'):
            try:
                widget.on_show()
            except Exception as e:
                print(f"خطأ في تشغيل on_show للوحدة {key}: {e}")
    
    def apply_current_theme(self):
        """تطبيق السمة الحالية"""
        try:
            self.theme_manager.apply_theme(self.theme_manager.current_theme)
        except Exception as e:
            print(f"خطأ في تطبيق السمة: {e}")
    
    def toggle_theme(self):
        """تبديل السمة (فاتح/داكن/عصري)"""
        current = self.theme_manager.current_theme
        theme_order = {'light': 'dark', 'dark': 'modern', 'modern': 'light'}
        next_theme = theme_order.get(current, 'light')
        
        try:
            self.theme_manager.apply_theme(next_theme)
            
            # تحديث نص الزر
            theme_names = {'light': 'فاتح', 'dark': 'داكن', 'modern': 'عصري'}
            QMessageBox.information(
                self, 
                "تم تغيير السمة", 
                f"تم تغيير السمة إلى الوضع {theme_names.get(next_theme, next_theme)}"
            )
        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"فشل تغيير السمة:\n{str(e)}")
    
    def on_logout(self):
        """تسجيل الخروج"""
        reply = QMessageBox.question(
            self, 
            "تأكيد تسجيل الخروج", 
            "هل أنت متأكد من تسجيل الخروج؟\nسيتم حفظ جميع البيانات.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self._save_window_settings()
            self.close()
    
    def on_close_event(self, event):
        """معالج إغلاق النافذة"""
        # حفظ الإعدادات
        self._save_window_settings()
        
        # إغلاق جميع الاتصالات
        if hasattr(self, 'timer'):
            self.timer.stop()
        
        # إغلاق الوحدات إذا كانت تدعم الإغلاق
        for key, widget in self.modules.items():
            if hasattr(widget, 'on_close'):
                try:
                    widget.on_close()
                except Exception as e:
                    print(f"خطأ في إغلاق الوحدة {key}: {e}")
        
        # قبول الحدث
        event.accept()
    
    def set_user_info(self, username: str, role: str = None):
        """تحديث معلومات المستخدم المعروض"""
        role_text = f" - {role}" if role else ""
        self.user_label.setText(f"👤 {username}{role_text}")
    
    def get_module(self, module_name: str) -> Optional[QWidget]:
        """الحصول على نسخة من وحدة معينة"""
        return self.modules.get(module_name)

# دالة مساعدة لإنشاء النافذة الرئيسية
def create_main_shell(db_manager=None, currency_manager=None, theme_manager=None) -> MainShell:
    """إنشاء النافذة الرئيسية مع تمرير المديرين"""
    return MainShell(db_manager, currency_manager, theme_manager)


if __name__ == "__main__":
    # اختبار مستقل
    app = QApplication(sys.argv)
    
    # إنشاء مدير قاعدة بيانات تجريبي
    from core.database.connection import DatabaseManager
    db = DatabaseManager(":memory:")  # قاعدة بيانات مؤقتة
    
    shell = MainShell(db_manager=db)
    shell.show()
    
    sys.exit(app.exec())
