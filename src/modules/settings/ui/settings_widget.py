# modules/settings/ui/settings_widget.py
"""
وحدة الإعدادات - Settings Module
نقطة دخول موحدة لإدارة جميع إعدادات النظام
Unified entry point for all system settings management
"""

from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *

from core.managers.settings_manager import get_settings_manager
from ui.dialogs.settings_dialog import SettingsDialog
from ui.widgets.arabic_widgets import ArabicTableWidget

class SettingsWidget(QWidget):
    """وحدة الإعدادات الرئيسية"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings_mgr = get_settings_manager()
        self.setLayoutDirection(Qt.RightToLeft)
        self.setup_ui()
        self.refresh_display()
    
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("⚙️ إدارة الإعدادات | System Settings")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #2E7D32;")
        header.addWidget(title)
        header.addStretch()
        
        settings_btn = QPushButton("تحرير الإعدادات | Edit Settings")
        settings_btn.setIcon(QIcon(":/icons/settings.png"))
        settings_btn.setStyleSheet("background-color: #2E7D32; color: white; padding: 8px 16px; border-radius: 4px;")
        settings_btn.clicked.connect(self.open_settings_dialog)
        header.addWidget(settings_btn)
        
        main_layout.addLayout(header)
        
        # Quick Settings Cards
        self.create_quick_settings_cards(main_layout)
        
        # Settings Groups Tabs
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #E0E0E0; }
            QTabBar::tab { background: #F5F5F5; padding: 8px 20px; }
            QTabBar::tab:selected { background: #2E7D32; color: white; }
        """)
        
        # Company Info Tab
        tabs.addTab(self.create_company_info_tab(), "🏢 معلومات الشركة")
        
        # System Settings Tab
        tabs.addTab(self.create_system_settings_tab(), "🔧 إعدادات النظام")
        
        # Operations Settings Tab
        tabs.addTab(self.create_operations_tab(), "📊 إعدادات التشغيل")
        
        # Audit Log Tab
        tabs.addTab(self.create_audit_log_tab(), "📋 سجل التغييرات")
        
        main_layout.addWidget(tabs)
    
    def create_quick_settings_cards(self, parent_layout):
        """إنشاء بطاقات الإعدادات السريعة"""
        cards_layout = QHBoxLayout()
        
        # Company Name Card
        company_card = self.create_setting_card(
            "🏢 اسم الشركة",
            self.settings_mgr.get('company.name_ar', 'N/A')
        )
        cards_layout.addWidget(company_card)
        
        # Tax Number Card
        tax_card = self.create_setting_card(
            "💰 الرقم الضريبي",
            self.settings_mgr.get('company.tax_number', 'غير محدد')
        )
        cards_layout.addWidget(tax_card)
        
        # Currency Card
        currency_card = self.create_setting_card(
            "💵 العملة الأساسية",
            self.settings_mgr.get('currency.base_currency', 'SAR')
        )
        cards_layout.addWidget(currency_card)
        
        # Language Card
        language_card = self.create_setting_card(
            "🌐 اللغة",
            "العربية" if self.settings_mgr.get('system.language', 'ar') == 'ar' else "English"
        )
        cards_layout.addWidget(language_card)
        
        parent_layout.addLayout(cards_layout)
    
    def create_setting_card(self, title: str, value: str) -> QGroupBox:
        """إنشاء بطاقة إعداد"""
        card = QGroupBox(title)
        layout = QVBoxLayout(card)
        
        label = QLabel(str(value))
        label.setStyleSheet("font-size: 14px; font-weight: bold; color: #1565C0;")
        label.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(label)
        
        card.setStyleSheet("""
            QGroupBox {
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                padding: 10px;
                background-color: #FAFAFA;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
            }
        """)
        
        return card
    
    def create_company_info_tab(self) -> QWidget:
        """إنشاء تبويب معلومات الشركة"""
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setAlignment(Qt.AlignTop | Qt.AlignRight)
        
        company_info = self.settings_mgr.get_company_info()
        
        fields = [
            ("اسم الشركة (AR):", company_info.get('name_ar')),
            ("Company Name (EN):", company_info.get('name_en')),
            ("الهاتف:", company_info.get('phone')),
            ("البريد الإلكتروني:", company_info.get('email')),
            ("الرقم الضريبي:", company_info.get('tax_number')),
            ("السجل التجاري:", company_info.get('commercial_register')),
            ("العنوان:", company_info.get('address')),
        ]
        
        for label_text, value in fields:
            label = QLabel(str(value or 'غير محدد'))
            label.setStyleSheet("padding: 8px; background-color: #F5F5F5; border-radius: 4px;")
            layout.addRow(label_text, label)
        
        return widget
    
    def create_system_settings_tab(self) -> QWidget:
        """إنشاء تبويب إعدادات النظام"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # General Settings Group
        general_group = QGroupBox("إعدادات عامة | General Settings")
        general_layout = QFormLayout(general_group)
        
        settings_data = [
            ("العملة الأساسية:", self.settings_mgr.get('currency.base_currency', 'SAR')),
            ("اللغة:", "العربية" if self.settings_mgr.get('system.language') == 'ar' else "English"),
            ("المنطقة الزمنية:", self.settings_mgr.get('system.timezone', 'Asia/Riyadh')),
            ("الأرقام العشرية:", str(self.settings_mgr.get('currency.decimal_places', 2))),
            ("اتجاه الواجهة:", "من اليمين لليسار" if self.settings_mgr.get('system.rtl') else "Left to Right"),
        ]
        
        for label_text, value in settings_data:
            value_label = QLabel(str(value))
            value_label.setStyleSheet("padding: 8px; background-color: #F5F5F5; border-radius: 4px;")
            general_layout.addRow(label_text, value_label)
        
        layout.addWidget(general_group)
        
        # Loyalty Settings
        loyalty_group = QGroupBox("برنامج الولاء | Loyalty Program")
        loyalty_layout = QFormLayout(loyalty_group)
        
        loyalty_settings = self.settings_mgr.get_loyalty_settings()
        loyalty_data = [
            ("حالة البرنامج:", "مفعل" if loyalty_settings.get('enabled') else "معطل"),
            ("نقاط لكل وحدة:", str(loyalty_settings.get('points_per_currency'))),
            ("قيمة النقطة:", str(loyalty_settings.get('currency_per_point'))),
            ("أقل نقاط للاستبدال:", str(loyalty_settings.get('min_redeem_points'))),
            ("صلاحية النقاط:", f"{loyalty_settings.get('points_expiry_days')} يوم"),
        ]
        
        for label_text, value in loyalty_data:
            value_label = QLabel(value)
            value_label.setStyleSheet("padding: 8px; background-color: #F5F5F5; border-radius: 4px;")
            loyalty_layout.addRow(label_text, value_label)
        
        layout.addWidget(loyalty_group)
        
        # Tax Settings
        tax_group = QGroupBox("إعدادات الضرائب | Tax Settings")
        tax_layout = QFormLayout(tax_group)
        
        tax_data = [
            ("معدل الضريبة الافتراضي:", f"{self.settings_mgr.get('tax.default_tax_rate', 15)}%"),
            ("الضريبة مضمنة:", "نعم" if self.settings_mgr.get('tax.tax_inclusive') else "لا"),
            ("ضرائب متعددة:", "مسموح" if self.settings_mgr.get('tax.multiple_taxes') else "غير مسموح"),
        ]
        
        for label_text, value in tax_data:
            value_label = QLabel(value)
            value_label.setStyleSheet("padding: 8px; background-color: #F5F5F5; border-radius: 4px;")
            tax_layout.addRow(label_text, value_label)
        
        layout.addWidget(tax_group)
        
        layout.addStretch()
        return widget
    
    def create_operations_tab(self) -> QWidget:
        """إنشاء تبويب إعدادات التشغيل"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # POS Settings
        pos_group = QGroupBox("إعدادات نقطة البيع | POS Settings")
        pos_layout = QFormLayout(pos_group)
        
        pos_settings = self.settings_mgr.get_pos_settings()
        pos_data = [
            ("السماح بالبيع بالدين:", "نعم" if pos_settings.get('allow_debt_sales') else "لا"),
            ("السماح بالمخزون السالب:", "نعم" if pos_settings.get('allow_negative_stock') else "لا"),
            ("طباعة الإيصال تلقائياً:", "نعم" if pos_settings.get('auto_print_receipt') else "لا"),
            ("نسبة الخصم الأقصى:", f"{pos_settings.get('max_discount_percent')}%"),
            ("عدد نسخ الطباعة:", str(pos_settings.get('print_copies'))),
        ]
        
        for label_text, value in pos_data:
            value_label = QLabel(value)
            value_label.setStyleSheet("padding: 8px; background-color: #F5F5F5; border-radius: 4px;")
            pos_layout.addRow(label_text, value_label)
        
        layout.addWidget(pos_group)
        
        # Inventory Settings
        inv_group = QGroupBox("إعدادات المخزون | Inventory Settings")
        inv_layout = QFormLayout(inv_group)
        
        inv_settings = self.settings_mgr.get_inventory_settings()
        inv_data = [
            ("تنبيهات المخزون المنخفض:", "مفعلة" if inv_settings.get('low_stock_alert') else "معطلة"),
            ("نسبة المخزون المنخفض:", f"{inv_settings.get('low_stock_percentage')}%"),
            ("تنبيهات الصلاحية (أيام):", str(inv_settings.get('expiry_alert_days'))),
            ("طريقة تحديد التكلفة:", inv_settings.get('costing_method', 'FIFO').upper()),
            ("تتبع الدفعات:", "نعم" if inv_settings.get('track_by_batch') else "لا"),
        ]
        
        for label_text, value in inv_data:
            value_label = QLabel(value)
            value_label.setStyleSheet("padding: 8px; background-color: #F5F5F5; border-radius: 4px;")
            inv_layout.addRow(label_text, value_label)
        
        layout.addWidget(inv_group)
        
        # Manufacturing Settings
        mfg_group = QGroupBox("إعدادات التصنيع | Manufacturing Settings")
        mfg_layout = QFormLayout(mfg_group)
        
        mfg_data = [
            ("تحديث التكلفة تلقائياً:", "نعم" if self.settings_mgr.get('manufacturing.auto_update_cost') else "لا"),
            ("تحديث السعر تلقائياً:", "نعم" if self.settings_mgr.get('manufacturing.auto_update_price') else "لا"),
            ("نسبة الهدر الافتراضية:", f"{self.settings_mgr.get('manufacturing.default_wastage', 5)}%"),
            ("طلب فحص الجودة:", "نعم" if self.settings_mgr.get('manufacturing.require_quality_check') else "لا"),
        ]
        
        for label_text, value in mfg_data:
            value_label = QLabel(value)
            value_label.setStyleSheet("padding: 8px; background-color: #F5F5F5; border-radius: 4px;")
            mfg_layout.addRow(label_text, value_label)
        
        layout.addWidget(mfg_group)
        
        layout.addStretch()
        return widget
    
    def create_audit_log_tab(self) -> QWidget:
        """إنشاء تبويب سجل التغييرات"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Audit log table
        self.audit_table = ArabicTableWidget(
            columns=["التاريخ | Date", "الإعداد | Setting", "القيمة القديمة | Old Value", "القيمة الجديدة | New Value"]
        )
        
        # Add some sample audit entries
        sample_logs = [
            ("2026-06-01 15:30:00", "pos.max_discount_percent", "50", "60"),
            ("2026-06-01 14:20:00", "loyalty.enabled", "False", "True"),
            ("2026-06-01 13:10:00", "currency.base_currency", "USD", "SAR"),
            ("2026-06-01 12:00:00", "tax.default_tax_rate", "10", "15"),
        ]
        
        for date, setting, old_value, new_value in sample_logs:
            self.audit_table.add_arabic_row([date, setting, old_value, new_value])
        
        layout.addWidget(self.audit_table)
        
        return widget
    
    def refresh_display(self):
        """تحديث عرض الإعدادات"""
        pass
    
    def open_settings_dialog(self):
        """فتح نافذة الإعدادات الشاملة"""
        dialog = SettingsDialog(self)
        if dialog.exec():
            self.refresh_display()


# Export for easy import
__all__ = ['SettingsWidget']
