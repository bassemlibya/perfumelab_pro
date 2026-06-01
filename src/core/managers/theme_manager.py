from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from typing import List, Callable, Optional, Dict, Any
import traceback

class ThemeManager:
    """مدير السمات والألوان للتطبيق"""
    
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
        """تهيئة مدير السمات"""
        self.current_theme = 'light'
        self._observers: List[Callable] = []
        self._cached_stylesheet: Optional[str] = None
        self._current_theme_hash = None
    
    def apply_theme(self, theme_name: str) -> bool:
        """
        تطبيق السمة على التطبيق
        
        Args:
            theme_name: اسم السمة ('light', 'dark', 'modern')
        
        Returns:
            True إذا تم التطبيق بنجاح، False إذا فشل
        """
        if theme_name not in self.THEMES:
            print(f"⚠️ تحذير: السمة '{theme_name}' غير موجودة")
            return False
        
        try:
            self.current_theme = theme_name
            theme = self.THEMES[theme_name]
            
            # الحصول على مثيل التطبيق (بدون تمرير كمعامل)
            app = QApplication.instance()
            if not app:
                print("⚠️ تحذير: لم يتم العثور على مثيل QApplication")
                return False
            
            # تطبيق الخط على مستوى التطبيق
            try:
                font = QFont(theme.get('font_primary', 'Cairo'), theme.get('font_size_base', 14))
                app.setFont(font)
            except Exception as e:
                print(f"⚠️ تحذير: فشل تطبيق الخط: {e}")
            
            # توليد وتطبيق الـ stylesheet
            try:
                stylesheet = self._generate_stylesheet(theme)
                app.setStyleSheet(stylesheet)
                self._cached_stylesheet = stylesheet
            except Exception as e:
                print(f"⚠️ تحذير: فشل توليد stylesheet: {e}")
                traceback.print_exc()
            
            # تطبيق اتجاه النصوص (RTL أو LTR)
            try:
                if theme.get('rtl', False):
                    app.setLayoutDirection(Qt.RightToLeft)
                else:
                    app.setLayoutDirection(Qt.LeftToRight)
            except Exception as e:
                print(f"⚠️ تحذير: فشل تطبيق اتجاه النصوص: {e}")
            
            # إشعار المراقبين
            self._notify_observers()
            print(f"✅ تم تطبيق السمة: {theme_name}")
            return True
            
        except Exception as e:
            print(f"❌ خطأ في تطبيق السمة: {e}")
            traceback.print_exc()
            return False
    
    def _generate_stylesheet(self, theme: Dict[str, Any]) -> str:
        """
        توليد stylesheet شامل للسمة
        
        Args:
            theme: قاموس السمة يحتوي على الألوان والخطوط
        
        Returns:
            نص CSS يحتوي على تنسيقات التطبيق
        """
        try:
            parts = []
            
            # ===== عام =====
            parts.append(f"""
                QMainWindow {{
                    background-color: {theme.get('background', '#FFFFFF')};
                }}
                QWidget {{
                    font-family: '{theme.get('font_primary', 'Cairo')}', '{theme.get('font_secondary', 'Tajawal')}', sans-serif;
                    color: {theme.get('text_primary', '#212121')};
                    font-size: {theme.get('font_size_base', 14)}px;
                }}
                QDialog {{
                    background-color: {theme.get('surface', '#F5F5F5')};
                }}
            """)
            
            # ===== أزرار =====
            parts.append(f"""
                QPushButton {{
                    background-color: {theme.get('primary', '#2E7D32')};
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {theme.get('secondary', '#1565C0')};
                }}
                QPushButton:pressed {{
                    background-color: {theme.get('primary', '#2E7D32')};
                    opacity: 0.8;
                }}
                QPushButton:disabled {{
                    background-color: {theme.get('border', '#E0E0E0')};
                    color: {theme.get('text_secondary', '#757575')};
                }}
            """)
            
            # ===== جداول وأشجار =====
            parts.append(f"""
                QTableWidget, QTreeWidget {{
                    background-color: {theme.get('surface', '#F5F5F5')};
                    border: 1px solid {theme.get('border', '#E0E0E0')};
                    gridline-color: {theme.get('border', '#E0E0E0')};
                    selection-background-color: {theme.get('primary', '#2E7D32')}40;
                    alternate-background-color: {theme.get('background', '#FFFFFF')};
                }}
                QTableWidget::item, QTreeWidget::item {{
                    padding: 8px;
                }}
                QHeaderView::section {{
                    background-color: {theme.get('primary', '#2E7D32')};
                    color: white;
                    padding: 8px;
                    font-weight: bold;
                    border: none;
                }}
            """)
            
            # ===== حقول الإدخال =====
            parts.append(f"""
                QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
                    background-color: {theme.get('surface', '#F5F5F5')};
                    border: 1px solid {theme.get('border', '#E0E0E0')};
                    padding: 6px;
                    border-radius: 4px;
                    color: {theme.get('text_primary', '#212121')};
                }}
                QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
                    border: 2px solid {theme.get('primary', '#2E7D32')};
                    background-color: {theme.get('background', '#FFFFFF')};
                }}
            """)
            
            # ===== أشرطة التمرير =====
            parts.append(f"""
                QScrollBar:vertical {{
                    background: {theme.get('surface', '#F5F5F5')};
                    width: 12px;
                    border-radius: 6px;
                }}
                QScrollBar::handle:vertical {{
                    background: {theme.get('scrollbar', '#C0C0C0')};
                    border-radius: 6px;
                    min-height: 20px;
                }}
                QScrollBar::handle:vertical:hover {{
                    background: {theme.get('secondary', '#1565C0')};
                }}
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                    border: none;
                    background: none;
                }}
                
                QScrollBar:horizontal {{
                    background: {theme.get('surface', '#F5F5F5')};
                    height: 12px;
                    border-radius: 6px;
                }}
                QScrollBar::handle:horizontal {{
                    background: {theme.get('scrollbar', '#C0C0C0')};
                    border-radius: 6px;
                    min-width: 20px;
                }}
                QScrollBar::handle:horizontal:hover {{
                    background: {theme.get('secondary', '#1565C0')};
                }}
            """)
            
            # ===== علامات تبويب =====
            parts.append(f"""
                QTabWidget::pane {{
                    border: 1px solid {theme.get('border', '#E0E0E0')};
                    background: {theme.get('surface', '#F5F5F5')};
                }}
                QTabBar::tab {{
                    background: {theme.get('background', '#FFFFFF')};
                    padding: 8px 16px;
                    margin-right: 2px;
                    border: 1px solid {theme.get('border', '#E0E0E0')};
                }}
                QTabBar::tab:selected {{
                    background: {theme.get('primary', '#2E7D32')};
                    color: white;
                    border: none;
                }}
                QTabBar::tab:hover {{
                    background: {theme.get('secondary', '#1565C0')};
                    color: white;
                }}
            """)
            
            # ===== مربعات القوائم والحوار =====
            parts.append(f"""
                QMessageBox, QDialog {{
                    background-color: {theme.get('surface', '#F5F5F5')};
                }}
                QComboBox::drop-down {{
                    border: none;
                    width: 20px;
                }}
                QComboBox::down-arrow {{
                    image: none;
                    background: {theme.get('primary', '#2E7D32')};
                    color: white;
                }}
            """)
            
            # ===== شريط القوائم =====
            parts.append(f"""
                QMenuBar {{
                    background-color: {theme.get('primary', '#2E7D32')};
                    color: white;
                }}
                QMenuBar::item:selected {{
                    background-color: {theme.get('secondary', '#1565C0')};
                }}
                QMenu {{
                    background-color: {theme.get('surface', '#F5F5F5')};
                    border: 1px solid {theme.get('border', '#E0E0E0')};
                }}
                QMenu::item:selected {{
                    background-color: {theme.get('primary', '#2E7D32')};
                    color: white;
                }}
            """)
            
            # ===== عناصر إضافية =====
            parts.append(f"""
                QLabel#currency_label {{
                    color: {theme.get('accent', '#FF6F00')};
                    font-weight: bold;
                }}
                QCheckBox, QRadioButton {{
                    spacing: 8px;
                    color: {theme.get('text_primary', '#212121')};
                }}
                QCheckBox::indicator, QRadioButton::indicator {{
                    width: 18px;
                    height: 18px;
                }}
                QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
                    background-color: {theme.get('primary', '#2E7D32')};
                    border: 2px solid {theme.get('primary', '#2E7D32')};
                }}
                QGroupBox {{
                    border: 1px solid {theme.get('border', '#E0E0E0')};
                    border-radius: 4px;
                    margin-top: 8px;
                    padding-top: 8px;
                    color: {theme.get('text_primary', '#212121')};
                    font-weight: bold;
                }}
                QGroupBox::title {{
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 3px;
                }}
            """)
            
            return "\n".join(parts)
        except Exception as e:
            print(f"❌ خطأ في توليد stylesheet: {e}")
            traceback.print_exc()
            return ""
    
    def get_color(self, key: str, default: str = '#000000') -> str:
        """
        الحصول على لون من السمة الحالية
        
        Args:
            key: مفتاح اللون (مثل 'primary', 'accent')
            default: القيمة الافتراضية إذا لم يوجد المفتاح
        
        Returns:
            قيمة اللون كسلسلة نصية
        """
        try:
            theme = self.THEMES.get(self.current_theme, {})
            return theme.get(key, default)
        except Exception as e:
            print(f"⚠️ خطأ في الحصول على اللون: {e}")
            return default
    
    def get_current_theme_name(self) -> str:
        """الحصول على اسم السمة الحالية"""
        return self.current_theme
    
    def get_available_themes(self) -> List[str]:
        """الحصول على قائمة السمات المتاحة"""
        return list(self.THEMES.keys())
    
    def get_theme_colors(self, theme_name: Optional[str] = None) -> Dict[str, Any]:
        """
        الحصول على جميع ألوان السمة
        
        Args:
            theme_name: اسم السمة (إن لم تحدد، ستُرجع السمة الحالية)
        
        Returns:
            قاموس يحتوي على جميع ألوان السمة
        """
        theme_to_get = theme_name or self.current_theme
        return self.THEMES.get(theme_to_get, {})
    
    def register_observer(self, callback: Callable) -> None:
        """
        تسجيل دالة لاستدعائها عند تغيير السمة
        
        Args:
            callback: دالة سيتم استدعاؤها عند تغيير السمة
        """
        if not callable(callback):
            print("⚠️ تحذير: callback يجب أن تكون دالة")
            return
        
        if callback not in self._observers:
            self._observers.append(callback)
            print(f"✅ تم تسجيل المراقب")
    
    def unregister_observer(self, callback: Callable) -> None:
        """
        إلغاء تسجيل دالة
        
        Args:
            callback: الدالة المراد إلغاء تسجيلها
        """
        if callback in self._observers:
            self._observers.remove(callback)
            print(f"✅ تم إلغاء تسجيل المراقب")
    
    def _notify_observers(self) -> None:
        """إشعار جميع المراقبين بتغيير السمة"""
        for callback in self._observers:
            try:
                callback(self.current_theme)
            except Exception as e:
                print(f"❌ خطأ في استدعاء المراقب: {e}")
                traceback.print_exc()


def apply_theme_to_widget(widget: QWidget, theme_manager: ThemeManager, style_type: str = 'card') -> None:
    """
    تطبيق سمة على عنصر واجهة محدد
    
    Args:
        widget: العنصر المراد تطبيق السمة عليه
        theme_manager: مدير السمات
        style_type: نوع النمط ('card', 'button', 'panel')
    """
    try:
        if not isinstance(theme_manager, ThemeManager):
            print("⚠️ تحذير: theme_manager يجب أن يكون من نوع ThemeManager")
            return
        
        styles = {
            'card': f"""
                QWidget {{
                    background-color: {theme_manager.get_color('surface')};
                    border: 1px solid {theme_manager.get_color('border')};
                    border-radius: 8px;
                    padding: 12px;
                }}
            """,
            'button': f"""
                QPushButton {{
                    background-color: {theme_manager.get_color('primary')};
                    color: white;
                    border-radius: 4px;
                    padding: 8px 16px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {theme_manager.get_color('secondary')};
                }}
            """,
            'panel': f"""
                QWidget {{
                    background-color: {theme_manager.get_color('background')};
                    border: 1px solid {theme_manager.get_color('border')};
                    border-radius: 8px;
                    padding: 10px;
                }}
            """,
            'header': f"""
                QWidget {{
                    background-color: {theme_manager.get_color('primary')};
                    color: white;
                    font-weight: bold;
                    padding: 10px;
                    border-radius: 8px;
                }}
            """
        }
        
        stylesheet = styles.get(style_type, '')
        if stylesheet:
            widget.setStyleSheet(stylesheet)
            print(f"✅ تم تطبيق النمط '{style_type}' على العنصر")
        else:
            print(f"⚠️ تحذير: نوع النمط '{style_type}' غير معروف")
    except Exception as e:
        print(f"❌ خطأ في تطبيق السمة على العنصر: {e}")
        traceback.print_exc()
