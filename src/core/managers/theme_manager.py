# core/managers/theme_manager.py

from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *

class ThemeManager:
    THEMES = {
        'light': {
            'primary': '#2E7D32',
            'secondary': '#1565C0',
            'background': '#FFFFFF',
            'surface': '#F5F5F5',
            'text_primary': '#212121',
            'text_secondary': '#757575',
            'accent': '#FF6F00',
            'success': '#4CAF50',
            'warning': '#FFC107',
            'error': '#F44336',
            'border': '#E0E0E0',
            'font_primary': 'Cairo',
            'font_secondary': 'Tajawal',
            'font_size_base': 14,
            'rtl': True
        },
        'dark': {
            'primary': '#66BB6A',
            'secondary': '#42A5F5',
            'background': '#121212',
            'surface': '#1E1E1E',
            'text_primary': '#FFFFFF',
            'text_secondary': '#B0B0B0',
            'accent': '#FFA726',
            'success': '#81C784',
            'warning': '#FFD54F',
            'error': '#E57373',
            'border': '#333333',
            'font_primary': 'Cairo',
            'font_secondary': 'Tajawal',
            'font_size_base': 14,
            'rtl': True
        },
        'modern': {
            'primary': '#6C5CE7',
            'secondary': '#00CEC9',
            'background': '#FAFAFA',
            'surface': '#FFFFFF',
            'text_primary': '#2D3436',
            'text_secondary': '#636E72',
            'accent': '#FD79A8',
            'success': '#00B894',
            'warning': '#FDCB6E',
            'error': '#D63031',
            'border': '#DFE6E9',
            'font_primary': 'Cairo',
            'font_secondary': 'Tajawal',
            'font_size_base': 14,
            'rtl': True
        }
    }
    
    def __init__(self):
        self.current_theme = 'light'
        self._observers = []
    
    def apply_theme(self, theme_name: str, app: QApplication):
        if theme_name not in self.THEMES:
            return
        self.current_theme = theme_name
        theme = self.THEMES[theme_name]
        font = QFont(theme['font_primary'], theme['font_size_base'])
        app.setFont(font)
        stylesheet = self._generate_stylesheet(theme)
        app.setStyleSheet(stylesheet)
        self._notify_observers()
    
    def _generate_stylesheet(self, theme: dict) -> str:
        parts = []
        parts.append("QMainWindow { background-color: %s; }" % theme['background'])
        parts.append("QWidget { font-family: '%s', '%s', sans-serif; color: %s; }" % (theme['font_primary'], theme['font_secondary'], theme['text_primary']))
        parts.append("QPushButton { background-color: %s; color: white; border: none; padding: 8px 16px; border-radius: 4px; font-size: %spx; }" % (theme['primary'], theme['font_size_base']))
        parts.append("QPushButton:hover { background-color: %s; }" % theme['secondary'])
        parts.append("QTableWidget { background-color: %s; border: 1px solid %s; gridline-color: %s; }" % (theme['surface'], theme['border'], theme['border']))
        parts.append("QTableWidget::item { padding: 8px; }")
        parts.append("QHeaderView::section { background-color: %s; color: white; padding: 8px; font-weight: bold; }" % theme['primary'])
        parts.append("QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox { background-color: %s; border: 1px solid %s; padding: 6px; border-radius: 4px; }" % (theme['surface'], theme['border']))
        parts.append("QLabel#currency_label { color: %s; font-weight: bold; }" % theme['accent'])
        return str.join("\n", parts)

    def get_color(self, key: str) -> str:
        return self.THEMES[self.current_theme].get(key, '#000000')
    
    def register_observer(self, callback):
        self._observers.append(callback)
    
    def _notify_observers(self):
        for callback in self._observers:
            callback(self.current_theme)
