import sys
import os
import traceback

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from core.database.connection import DatabaseManager
from core.managers.theme_manager import ThemeManager
from core.managers.currency_manager import CurrencyManager
from ui.shell.main_shell import MainShell

class MainApplication(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        
        # إعداد معالج استثناءات عام
        sys.excepthook = self.handle_exception
        
        try:
            # Database - مع التحقق من الخطأ
            self.db_manager = DatabaseManager("perfumelab.db")
            if not self.db_manager.initialize_database():
                QMessageBox.critical(None, "خطأ", "فشل في تهيئة قاعدة البيانات!")
                sys.exit(1)
            
            self.theme_manager = ThemeManager()
            self.theme_manager.apply_theme('light')  # تصحيح الخطأ
            
            # تهيئة مدير العملات مع معالجة الأخطاء
            try:
                self.currency_manager = CurrencyManager(self.db_manager)
            except Exception as e:
                print(f"تحذير: فشل تهيئة مدير العملات - {e}")
                self.currency_manager = None
            
            self.setApplicationName("PerfumeLab Pro")
            self.setApplicationVersion("2.0.0")
            self.setOrganizationName("PerfumeLab")
            self.setLayoutDirection(Qt.RightToLeft)
            
        except Exception as e:
            QMessageBox.critical(None, "خطأ فادح", f"فشل تهيئة التطبيق:\n{e}\n{traceback.format_exc()}")
            sys.exit(1)
    
    def handle_exception(self, exc_type, exc_value, exc_traceback):
        """معالج استثناءات عام لتسجيل الأخطاء"""
        error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        print(f"خطأ غير متوقع:\n{error_msg}")
        QMessageBox.critical(None, "خطأ غير متوقع", f"حدث خطأ غير متوقع:\n{exc_value}")
    
    def run(self):
        try:
            self.main_window = MainShell()
            # تمرير مدير العملات إذا كان MainShell يدعمه
            if hasattr(self.main_window, 'set_currency_manager'):
                self.main_window.set_currency_manager(self.currency_manager)
            
            self.main_window.showMaximized()
            return self.exec()
        except Exception as e:
            print(f"خطأ في تشغيل التطبيق: {e}")
            return 1

if __name__ == "__main__":
    app = MainApplication(sys.argv)
    sys.exit(app.run())
