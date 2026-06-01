from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from typing import List, Callable, Optional

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
            'scrollbar': '#C0C0C0',
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
            'scrollbar': '#555555',
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
            'scrollbar': '#B2BEC3',
            'font_primary': 'Cairo',
            'font_secondary': 'Tajawal',
            'font_size_base': 14,
            'rtl': True
        }
    }
    
    def __init__(self):
        self.current_theme = 'light'
        self._observers: List[Callable] = []
        self._cached_stylesheet: Optional[str] = None
        self._current_theme_hash = None
    
    def apply_theme(self, theme_name: str) -> bool:
        """تطبيق السمة مع التحقق من الصحة"""
        if theme_name not in self.THEMES:
            print(f"تحذير: السمة '{theme_name}' غير موجودة")
            return False
        
        self.current_theme = theme_name
        theme = self.THEMES[theme_name]
        
        # تطبيق الخط على مستوى التطبيق
        app = QApplication.instance()
        if app:
            font = QFont(theme['font_primary'], theme['font_size_base'])
            app.setFont(font)
            
            # توليد وتطبيق الـ stylesheet
            stylesheet = self._generate_stylesheet(theme)
            app.setStyleSheet(stylesheet)
            
            # إعادة تطبيق اتجاه RTL إذا لزم الأمر
            if theme.get('rtl', False):
                app.setLayoutDirection(Qt.RightToLeft)
            else:
                app.setLayoutDirection(Qt.LeftToRight)
        
        self._notify_observers()
        return True
    
    def _generate_stylesheet(self, theme: dict) -> str:
        """توليد stylesheet شامل"""
        parts = []
        
        # عام
        parts.append(f"""
            QMainWindow {{ background-color: {theme['background']}; }}
            QWidget {{ 
                font-family: '{theme['font_primary']}', '{theme['font_secondary']}', sans-serif; 
                color: {theme['text_primary']}; 
                font-size: {theme['font_size_base']}px;
            }}
        """)
        
        # أزرار
        parts.append(f"""
            QPushButton {{ 
                background-color: {theme['primary']}; 
                color: white; 
                border: none; 
                padding: 8px 16px; 
                border-radius: 4px; 
            }}
            QPushButton:hover {{ background-color: {theme['secondary']}; }}
            QPushButton:pressed {{ background-color: {theme['primary']}; }}
            QPushButton:disabled {{ background-color: {theme['border']}; color: {theme['text_secondary']}; }}
        """)
        
        # جداول
        parts.append(f"""
            QTableWidget, QTreeWidget {{
                background-color: {theme['surface']}; 
                border: 1px solid {theme['border']}; 
                gridline-color: {theme['border']};
                selection-background-color: {theme['primary']}40;
            }}
            QTableWidget::item, QTreeWidget::item {{ padding: 8px; }}
            QHeaderView::section {{
                background-color: {theme['primary']}; 
                color: white; 
                padding: 8px; 
                font-weight: bold;
                border: none;
            }}
        """)
        
        # حقول الإدخال
        parts.append(f"""
            QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
                background-color: {theme['surface']}; 
                border: 1px solid {theme['border']}; 
                padding: 6px; 
                border-radius: 4px;
            }}
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{
                border: 2px solid {theme['primary']};
            }}
        """)
        
        # أشرطة التمرير
        parts.append(f"""
            QScrollBar:vertical {{
                background: {theme['surface']};
                width: 12px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical {{
                background: {theme['scrollbar']};
                border-radius: 6px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {theme['secondary']};
            }}
        """)
        
        # علامات تبويب
        parts.append(f"""
            QTabWidget::pane {{
                border: 1px solid {theme['border']};
                background: {theme['surface']};
            }}
            QTabBar::tab {{
                background: {theme['background']};
                padding: 8px 16px;
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background: {theme['primary']};
                color: white;
            }}
        """)
        
        # مربعات حوار
        parts.append(f"""
            QMessageBox, QDialog {{
                background-color: {theme['surface']};
            }}
        """)
        
        # شريط القوائم
        parts.append(f"""
            QMenuBar {{
                background-color: {theme['primary']};
                color: white;
            }}
            QMenuBar::item:selected {{
                background-color: {theme['secondary']};
            }}
            QMenu {{
                background-color: {theme['surface']};
                border: 1px solid {theme['border']};
            }}
            QMenu::item:selected {{
                background-color: {theme['primary']};
                color: white;
            }}
        """)
        
        # عناصر إضافية
        parts.append(f"QLabel#currency_label {{ color: {theme['accent']}; font-weight: bold; }}")
        parts.append(f"QCheckBox, QRadioButton {{ spacing: 8px; }}")
        
        return "\n".join(parts)
    
    def get_color(self, key: str, default: str = '#000000') -> str:
        """الحصول على لون من السمة الحالية"""
        theme = self.THEMES.get(self.current_theme, {})
        return theme.get(key, default)
    
    def get_current_theme_name(self) -> str:
        return self.current_theme
    
    def get_available_themes(self) -> List[str]:
        return list(self.THEMES.keys())
    
    def register_observer(self, callback: Callable):
        """تسجيل دالة لاستدعائها عند تغيير السمة"""
        if callback not in self._observers:
            self._observers.append(callback)
    
    def unregister_observer(self, callback: Callable):
        """إلغاء تسجيل دالة"""
        if callback in self._observers:
            self._observers.remove(callback)
    
    def _notify_observers(self):
        """إشعار المراقبين بتغيير السمة"""
        for callback in self._observers:
            try:
                callback(self.current_theme)
            except Exception as e:
                print(f"خطأ في إشعار المراقب: {e}")

# دالة مساعدة لتطبيق السمة بسهولة
def apply_theme_to_widget(widget: QWidget, theme_manager: ThemeManager, style_type: str = 'card'):
    """تطبيق سمة على عنصر محدد"""
    colors = {
        'card': f"""
            QWidget {{
                background-color: {theme_manager.get_color('surface')};
                border: 1px solid {theme_manager.get_color('border')};
                border-radius: 8px;
                padding: 8px;
            }}
        """,
        'button': f"""
            QPushButton {{
                background-color: {theme_manager.get_color('primary')};
                color: white;
                border-radius: 4px;
                padding: 6px 12px;
            }}
        """
    }
    widget.setStyleSheet(colors.get(style_type, ''))
