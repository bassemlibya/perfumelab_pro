# core/managers/settings_manager.py
"""
نظام إدارة الإعدادات الشامل
Comprehensive Settings Management System
Supports: Company, User, Branch, POS, Inventory, Tax, Loyalty, Manufacturing settings
"""

import json
import os
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from decimal import Decimal
import logging

from core.database.connection import DatabaseManager

logger = logging.getLogger(__name__)

class SettingsManager:
    """مدير الإعدادات المركزي - Central settings manager for database and file configurations"""
    
    # تعريف جميع مجموعات الإعدادات
    SETTING_GROUPS = {
        'company': 'company_settings',
        'pos': 'pos_settings',
        'inventory': 'inventory_settings',
        'tax': 'tax_settings',
        'loyalty': 'loyalty_settings',
        'manufacturing': 'manufacturing_settings',
        'currency': 'currency_settings',
        'backup': 'backup_settings',
        'email': 'email_settings',
        'printer': 'printer_settings',
        'ui': 'ui_settings'
    }
    
    # الإعدادات الافتراضية
    DEFAULTS = {
        'system': {
            'language': 'ar',
            'rtl': True,
            'date_format': 'YYYY-MM-DD',
            'time_format': 'HH:MM:SS',
            'timezone': 'Asia/Riyadh',
            'decimal_places': 2,
            'thousands_separator': ',',
            'decimal_separator': '.'
        },
        'company': {
            'name_ar': 'بروفيوم لاب',
            'name_en': 'PerfumeLab',
            'tax_number': '',
            'commercial_register': '',
            'phone': '',
            'email': '',
            'address': '',
            'logo_path': ''
        },
        'pos': {
            'allow_negative_stock': False,
            'allow_debt_sales': True,
            'max_discount_percent': 50.0,
            'auto_print_receipt': True,
            'print_copies': 1,
            'receipt_header': 'شكراً لتسوقكم معنا',
            'receipt_footer': 'مع خالص الشكر والتقدير',
            'require_customer_for_debt': True,
            'barcode_scanner_enabled': True
        },
        'inventory': {
            'low_stock_alert': True,
            'low_stock_percentage': 20.0,
            'expiry_alert_days': 30,
            'costing_method': 'fifo',  # fifo, lifo, weighted_average
            'track_by_batch': True,
            'allow_negative_stock': False
        },
        'loyalty': {
            'enabled': True,
            'points_per_currency': 1.0,
            'currency_per_point': 0.01,
            'points_expiry_days': 365,
            'min_redeem_points': 100,
            'max_redeem_percent': 50.0
        },
        'tax': {
            'default_tax_rate': 15.0,
            'tax_inclusive': False,
            'multiple_taxes': True
        },
        'manufacturing': {
            'auto_update_cost': True,
            'auto_update_price': False,
            'default_wastage': 5.0,
            'require_quality_check': True
        }
    }
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        """
        Initialize Settings Manager
        
        Args:
            db_manager: Database manager instance
        """
        self.db = db_manager
        self._cache: Dict[str, Any] = {}  # Cache for settings
        self._observers: List[Callable] = []  # Observers for settings changes
        
        # Load settings from database if available
        if self.db:
            self._load_all_settings()
            logger.info("✅ SettingsManager initialized with database")
        else:
            logger.warning("⚠️ SettingsManager initialized without database")
    
    def _load_all_settings(self):
        """تحميل جميع الإعدادات من قاعدة البيانات"""
        try:
            # Load company settings
            company_settings = self.db.execute(
                "SELECT setting_key, setting_value, data_type FROM company_settings"
            )
            for setting in company_settings:
                key = f"company.{setting['setting_key']}"
                self._cache[key] = self._deserialize(setting['setting_value'], setting['data_type'])
            
            # Load POS settings
            pos_settings = self.db.execute_one("SELECT * FROM pos_settings WHERE id = 1")
            if pos_settings:
                for key, value in pos_settings.items():
                    if key not in ['id', 'branch_id', 'updated_at']:
                        self._cache[f"pos.{key}"] = value
            
            # Load inventory settings
            inv_settings = self.db.execute_one("SELECT * FROM inventory_settings WHERE id = 1")
            if inv_settings:
                for key, value in inv_settings.items():
                    if key not in ['id', 'updated_at']:
                        self._cache[f"inventory.{key}"] = value
            
            # Load loyalty settings
            loyalty_settings = self.db.execute_one("SELECT * FROM loyalty_settings WHERE id = 1")
            if loyalty_settings:
                for key, value in loyalty_settings.items():
                    if key not in ['id', 'updated_at']:
                        self._cache[f"loyalty.{key}"] = value
            
            # Load manufacturing settings
            mfg_settings = self.db.execute_one("SELECT * FROM manufacturing_settings WHERE id = 1")
            if mfg_settings:
                for key, value in mfg_settings.items():
                    if key not in ['id', 'updated_at']:
                        self._cache[f"manufacturing.{key}"] = value
            
            logger.info(f"✅ Loaded {len(self._cache)} settings from database")
            
        except Exception as e:
            logger.error(f"❌ Failed to load settings: {e}")
    
    def _serialize(self, value: Any, data_type: Optional[str] = None) -> tuple:
        """تحويل القيمة إلى نص للتخزين"""
        if data_type == 'bool' or isinstance(value, bool):
            return ('1' if value else '0', 'bool')
        elif data_type == 'int' or isinstance(value, int):
            return (str(value), 'int')
        elif data_type == 'float' or isinstance(value, (float, Decimal)):
            return (str(value), 'float')
        elif data_type == 'json' or isinstance(value, (dict, list)):
            return (json.dumps(value, ensure_ascii=False, default=str), 'json')
        else:
            return (str(value), 'string')
    
    def _deserialize(self, value: Optional[str], data_type: str) -> Any:
        """تحويل النص المخزن إلى قيمة"""
        if value is None or value == '':
            return None
        
        try:
            if data_type == 'bool':
                return value in ('1', 'true', 'True', 'yes', 'on')
            elif data_type == 'int':
                return int(value)
            elif data_type == 'float':
                return float(value)
            elif data_type == 'json':
                return json.loads(value)
            else:
                return value
        except Exception as e:
            logger.warning(f"⚠️ Deserialization error: {e}")
            return value
    
    def get(self, key: str, default: Any = None, user_id: Optional[int] = None, 
            branch_id: Optional[int] = None) -> Any:
        """
        الحصول على قيمة إعداد
        
        Args:
            key: مفتاح الإعداد (مثل 'pos.allow_debt_sales')
            default: القيمة الافتراضية إذا لم يوجد
            user_id: معرف المستخدم (للإعدادات الخاصة)
            branch_id: معرف الفرع (للإعدادات الخاصة بالفرع)
        
        Returns:
            قيمة الإعداد أو القيمة الافتراضية
        """
        # Check user settings first
        if user_id:
            user_key = f"user_{user_id}.{key}"
            if user_key in self._cache:
                return self._cache[user_key]
        
        # Check branch settings
        if branch_id:
            branch_key = f"branch_{branch_id}.{key}"
            if branch_key in self._cache:
                return self._cache[branch_key]
        
        # Check global settings
        if key in self._cache:
            return self._cache[key]
        
        # Check defaults
        parts = key.split('.')
        if len(parts) == 2:
            group, setting = parts
            if group in self.DEFAULTS and setting in self.DEFAULTS[group]:
                return self.DEFAULTS[group][setting]
        
        return default
    
    def set(self, key: str, value: Any, user_id: Optional[int] = None, 
            branch_id: Optional[int] = None) -> bool:
        """
        تعيين قيمة إعداد
        
        Args:
            key: مفتاح الإعداد
            value: القيمة الجديدة
            user_id: معرف المستخدم (للإعدادات الخاصة)
            branch_id: معرف الفرع (للإعدادات الخاصة بالفرع)
        
        Returns:
            True if successful
        """
        try:
            if not self.db:
                logger.warning("⚠️ Database not available for settings")
                return False
            
            serialized, data_type = self._serialize(value)
            
            if user_id:
                # User setting
                self.db.execute_update(
                    """INSERT OR REPLACE INTO user_settings (user_id, setting_key, setting_value, data_type, updated_at)
                       VALUES (?, ?, ?, ?, ?)""",
                    (user_id, key, serialized, data_type, datetime.now().isoformat())
                )
                cache_key = f"user_{user_id}.{key}"
                
            elif branch_id:
                # Branch setting
                self.db.execute_update(
                    """INSERT OR REPLACE INTO branch_settings (branch_id, setting_key, setting_value, data_type, updated_at)
                       VALUES (?, ?, ?, ?, ?)""",
                    (branch_id, key, serialized, data_type, datetime.now().isoformat())
                )
                cache_key = f"branch_{branch_id}.{key}"
                
            else:
                # Global setting
                parts = key.split('.')
                group = parts[0] if len(parts) > 0 else 'company'
                setting_name = parts[1] if len(parts) > 1 else key
                
                if group == 'pos':
                    self.db.execute_update(
                        f"UPDATE pos_settings SET {setting_name} = ?, updated_at = ? WHERE id = 1",
                        (value, datetime.now().isoformat())
                    )
                elif group == 'inventory':
                    self.db.execute_update(
                        f"UPDATE inventory_settings SET {setting_name} = ?, updated_at = ? WHERE id = 1",
                        (value, datetime.now().isoformat())
                    )
                elif group == 'loyalty':
                    self.db.execute_update(
                        f"UPDATE loyalty_settings SET {setting_name} = ?, updated_at = ? WHERE id = 1",
                        (value, datetime.now().isoformat())
                    )
                elif group == 'manufacturing':
                    self.db.execute_update(
                        f"UPDATE manufacturing_settings SET {setting_name} = ?, updated_at = ? WHERE id = 1",
                        (value, datetime.now().isoformat())
                    )
                elif group == 'currency':
                    self.db.execute_update(
                        f"UPDATE currency_settings SET {setting_name} = ?, updated_at = ? WHERE id = 1",
                        (value, datetime.now().isoformat())
                    )
                else:
                    self.db.execute_update(
                        """INSERT OR REPLACE INTO company_settings (setting_key, setting_value, data_type, setting_group, updated_at)
                           VALUES (?, ?, ?, ?, ?)""",
                        (key, serialized, data_type, group, datetime.now().isoformat())
                    )
                cache_key = key
            
            # Update cache
            self._cache[cache_key] = value
            
            # Notify observers
            self._notify_observers(key, value)
            
            logger.info(f"✅ Setting updated: {key} = {value}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to set setting {key}: {e}")
            return False
    
    def get_all(self, group: Optional[str] = None) -> Dict[str, Any]:
        """الحصول على جميع الإعدادات لمجموعة معينة"""
        if group:
            prefix = f"{group}."
            return {k.replace(prefix, ''): v for k, v in self._cache.items() if k.startswith(prefix)}
        return self._cache.copy()
    
    def get_company_info(self) -> Dict[str, str]:
        """الحصول على معلومات الشركة"""
        return {
            'name_ar': self.get('company.name_ar'),
            'name_en': self.get('company.name_en'),
            'tax_number': self.get('company.tax_number'),
            'commercial_register': self.get('company.commercial_register'),
            'phone': self.get('company.phone'),
            'email': self.get('company.email'),
            'address': self.get('company.address'),
            'logo_path': self.get('company.logo_path')
        }
    
    def get_pos_settings(self) -> Dict[str, Any]:
        """الحصول على إعدادات نقطة البيع"""
        return {
            'allow_negative_stock': self.get('pos.allow_negative_stock', False),
            'allow_debt_sales': self.get('pos.allow_debt_sales', True),
            'max_discount_percent': self.get('pos.max_discount_percent', 50),
            'auto_print_receipt': self.get('pos.auto_print_receipt', True),
            'print_copies': self.get('pos.print_copies', 1),
            'receipt_header': self.get('pos.receipt_header', ''),
            'receipt_footer': self.get('pos.receipt_footer', '')
        }
    
    def get_inventory_settings(self) -> Dict[str, Any]:
        """الحصول على إعدادات المخزون"""
        return {
            'low_stock_alert': self.get('inventory.low_stock_alert', True),
            'low_stock_percentage': self.get('inventory.low_stock_percentage', 20),
            'expiry_alert_days': self.get('inventory.expiry_alert_days', 30),
            'costing_method': self.get('inventory.costing_method', 'fifo'),
            'track_by_batch': self.get('inventory.track_by_batch', True),
            'allow_negative_stock': self.get('inventory.allow_negative_stock', False)
        }
    
    def get_loyalty_settings(self) -> Dict[str, Any]:
        """الحصول على إعدادات برنامج الولاء"""
        return {
            'enabled': self.get('loyalty.enabled', True),
            'points_per_currency': self.get('loyalty.points_per_currency', 1.0),
            'currency_per_point': self.get('loyalty.currency_per_point', 0.01),
            'points_expiry_days': self.get('loyalty.points_expiry_days', 365),
            'min_redeem_points': self.get('loyalty.min_redeem_points', 100),
            'max_redeem_percent': self.get('loyalty.max_redeem_percent', 50)
        }
    
    def register_observer(self, callback: Callable):
        """تسجيل دالة لاستدعائها عند تغيير الإعدادات"""
        self._observers.append(callback)
        logger.info(f"✅ Observer registered: {callback.__name__}")
    
    def _notify_observers(self, key: str, value: Any):
        """إشعار المراقبين بتغيير إعداد"""
        for callback in self._observers:
            try:
                callback(key, value)
            except Exception as e:
                logger.error(f"❌ Observer callback failed: {e}")
    
    def export_settings(self, file_path: str) -> bool:
        """تصدير الإعدادات إلى ملف JSON"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self._cache, f, ensure_ascii=False, indent=2, default=str)
            logger.info(f"✅ Settings exported to {file_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to export settings: {e}")
            return False
    
    def import_settings(self, file_path: str) -> bool:
        """استيراد الإعدادات من ملف JSON"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            for key, value in settings.items():
                self.set(key, value)
            
            logger.info(f"✅ Settings imported from {file_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to import settings: {e}")
            return False
    
    def reset_to_defaults(self, group: Optional[str] = None) -> bool:
        """إعادة تعيين الإعدادات إلى القيم الافتراضية"""
        try:
            if group:
                defaults = self.DEFAULTS.get(group, {})
                for key, value in defaults.items():
                    self.set(f"{group}.{key}", value)
            else:
                for group_name, defaults in self.DEFAULTS.items():
                    for key, value in defaults.items():
                        self.set(f"{group_name}.{key}", value)
            
            logger.info(f"✅ Settings reset to defaults for group: {group}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to reset settings: {e}")
            return False
    
    def backup_settings(self, backup_path: Optional[str] = None) -> bool:
        """إنشاء نسخة احتياطية من الإعدادات"""
        if not backup_path:
            backup_path = f"settings_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        return self.export_settings(backup_path)
    
    def restore_settings(self, backup_path: str) -> bool:
        """استعادة الإعدادات من نسخة احتياطية"""
        return self.import_settings(backup_path)


# Singleton instance
_settings_manager: Optional[SettingsManager] = None

def get_settings_manager(db_manager: Optional[DatabaseManager] = None) -> SettingsManager:
    """الحصول على نسخة واحدة من مدير الإعدادات (Singleton)"""
    global _settings_manager
    if _settings_manager is None:
        _settings_manager = SettingsManager(db_manager)
    return _settings_manager
