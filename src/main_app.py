# main_app.py
import sys
import os

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

        # Database - المسار النسبي تلقائياً
        self.db_manager = DatabaseManager("perfumelab.db")
        self.db_manager.initialize_database()  # لا حاجة لتمرير المسار!

        self.theme_manager = ThemeManager()
        self.theme_manager.apply_theme('light', self)

        self.currency_manager = CurrencyManager(self.db_manager)

        self.setApplicationName("PerfumeLab Pro")
        self.setApplicationVersion("2.0.0")
        self.setOrganizationName("PerfumeLab")
        self.setLayoutDirection(Qt.RightToLeft)

    def run(self):
        self.main_window = MainShell()
        self.main_window.showMaximized()
        return self.exec()

if __name__ == "__main__":
    app = MainApplication(sys.argv)
    sys.exit(app.run())
