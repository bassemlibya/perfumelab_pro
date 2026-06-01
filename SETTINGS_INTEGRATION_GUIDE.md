# Integration Guide: Adding Settings System to PerfumeLab Pro
# دليل التكامل: إضافة نظام الإعدادات إلى بروفيوم لاب

"""
================================================================================
STEP 1: Update main_app.py to initialize SettingsManager
================================================================================
"""

# In src/main_app.py, update the __init__ method:

from core.managers.settings_manager import get_settings_manager

class MainApplication(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        
        # ... existing code ...
        
        # Initialize Settings Manager (must be after database initialization)
        self.settings_manager = get_settings_manager(self.db_manager)
        
        # Set application metadata from settings
        company_name = self.settings_manager.get('company.name_en', 'PerfumeLab Pro')
        self.setApplicationName(company_name)
        self.setApplicationVersion("2.0.0")
        
        # ... rest of initialization ...


"""
================================================================================
STEP 2: Update MainShell to include Settings Module
================================================================================
"""

# In src/ui/shell/main_shell.py:

from modules.settings.ui.settings_widget import SettingsWidget

class MainShell(QMainWindow):
    def setup_ui(self):
        # ... existing modules ...
        
        self.modules = {
            'dashboard': DashboardWidget(),
            'pos': POSWindow(),
            'inventory': InventoryWidget(),
            'customers': CustomersWidget(),
            'treasury': TreasuryWidget(),
            'manufacturing': ManufacturingWidget(),
            'reports': ReportsWidget(),
            'settings': SettingsWidget(),  # ✅ ADD THIS
        }
    
    def create_navigation(self):
        # ... existing navigation items ...
        
        nav_items = [
            # ... existing items ...
            ('settings', '⚙️ الإعدادات | Settings', '#333333'),
        ]
        
        # ... rest of navigation setup ...


"""
================================================================================
STEP 3: Database Migration Steps
================================================================================
"""

# Run these migrations on first startup:

# 1. Apply the settings schema (002_settings_schema.sql)
#    Place in: src/core/database/migrations/002_settings_schema.sql

# 2. Update DatabaseManager to support multiple migration files:
# In src/core/database/connection.py, modify initialize_database():

def initialize_database(self, migrations_dir: str = None):
    """Initialize database with all migration files"""
    if migrations_dir is None:
        current_file = os.path.abspath(__file__)
        migrations_dir = os.path.join(os.path.dirname(current_file), 'migrations')
    
    # Apply all SQL files in order
    migration_files = sorted([f for f in os.listdir(migrations_dir) if f.endswith('.sql')])
    
    for migration_file in migration_files:
        migration_path = os.path.join(migrations_dir, migration_file)
        
        # Check if this migration was already applied
        # (You can add a migrations_applied table for tracking)
        
        with open(migration_path, 'r', encoding='utf-8') as f:
            migration_sql = f.read()
        
        try:
            with self.get_connection() as conn:
                conn.executescript(migration_sql)
                conn.commit()
            print(f"✅ Applied migration: {migration_file}")
        except Exception as e:
            print(f"⚠️ Migration {migration_file} might already be applied: {e}")


"""
================================================================================
STEP 4: Usage Examples in Other Modules
================================================================================
"""

# Example 1: In POSWindow - respect POS settings
from core.managers.settings_manager import get_settings_manager

class POSWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = get_settings_manager()
        
        # Load POS settings
        pos_settings = self.settings.get_pos_settings()
        self.allow_debt_sales = pos_settings['allow_debt_sales']
        self.max_discount = pos_settings['max_discount_percent']
        self.auto_print = pos_settings['auto_print_receipt']
        
        # Register as observer for changes
        self.settings.register_observer(self.on_settings_changed)
    
    def on_settings_changed(self, key, value):
        """Called when settings change"""
        if key.startswith('pos.'):
            # Reload POS settings
            self.reload_pos_settings()


# Example 2: In InventoryWidget - respect inventory settings
class InventoryWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.settings = get_settings_manager()
        
        # Load inventory settings
        inv_settings = self.settings.get_inventory_settings()
        self.low_stock_alert = inv_settings['low_stock_alert']
        self.low_stock_percent = inv_settings['low_stock_percentage']
        self.costing_method = inv_settings['costing_method']


# Example 3: In Treasury Module - use currency settings
class TreasuryWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.settings = get_settings_manager()
        
        # Get base currency
        base_currency = self.settings.get('currency.base_currency', 'SAR')
        decimal_places = self.settings.get('currency.decimal_places', 2)


"""
================================================================================
STEP 5: Settings Menu Integration
================================================================================
"""

# Add to MainShell or MainApplication:

def create_menu_bar(self):
    """Create menu bar with settings access"""
    menubar = self.menuBar()
    
    # Tools Menu
    tools_menu = menubar.addMenu("🔧 الأدوات | Tools")
    
    settings_action = tools_menu.addAction("⚙️ الإعدادات | Settings")
    settings_action.triggered.connect(self.open_settings)
    
    tools_menu.addSeparator()
    
    backup_action = tools_menu.addAction("💾 نسخة احتياطية | Backup")
    backup_action.triggered.connect(self.create_backup)
    
    restore_action = tools_menu.addAction("♻️ استعادة | Restore")
    restore_action.triggered.connect(self.restore_backup)

def open_settings(self):
    """Open settings dialog"""
    from ui.dialogs.settings_dialog import show_settings_dialog
    show_settings_dialog(self)

def create_backup(self):
    """Create database backup"""
    from core.managers.settings_manager import get_settings_manager
    settings = get_settings_manager()
    
    backup_path = settings.backup_settings()
    QMessageBox.information(self, "نجح | Success", f"تم إنشاء نسخة احتياطية: {backup_path}")

def restore_backup(self):
    """Restore from backup"""
    file_path, _ = QFileDialog.getOpenFileName(
        self,
        "اختر ملف النسخة الاحتياطية",
        "",
        "Database Backup (*.db)"
    )
    
    if file_path:
        # Restore backup
        import shutil
        shutil.copy(file_path, self.db_manager._db_path)
        QMessageBox.information(self, "نجح | Success", "تم استعادة النسخة الاحتياطية")


"""
================================================================================
STEP 6: Configuration File Example
================================================================================
"""

# Create config.json in project root for initial settings:
{
  "company": {
    "name_ar": "بروفيوم لاب",
    "name_en": "PerfumeLab Pro",
    "tax_number": "3103123123",
    "commercial_register": "1010123456",
    "phone": "+966123456789",
    "email": "info@perfumelab.com",
    "address": "الرياض، المملكة العربية السعودية"
  },
  "system": {
    "language": "ar",
    "timezone": "Asia/Riyadh",
    "theme": "light",
    "rtl": true
  },
  "database": {
    "filename": "perfumelab.db",
    "backup_path": "./backups"
  },
  "pos": {
    "allow_debt_sales": true,
    "max_discount_percent": 50,
    "auto_print_receipt": true
  }
}


"""
================================================================================
STEP 7: Testing the Settings System
================================================================================
"""

# Test script: test_settings.py

from core.database.connection import DatabaseManager
from core.managers.settings_manager import get_settings_manager

def test_settings():
    # Initialize database
    db = DatabaseManager("test_perfumelab.db")
    db.initialize_database()
    
    # Get settings manager
    settings = get_settings_manager(db)
    
    # Test 1: Get company info
    print("=" * 50)
    print("TEST 1: Company Information")
    print("=" * 50)
    company_info = settings.get_company_info()
    for key, value in company_info.items():
        print(f"  {key}: {value}")
    
    # Test 2: Get POS settings
    print("\n" + "=" * 50)
    print("TEST 2: POS Settings")
    print("=" * 50)
    pos_settings = settings.get_pos_settings()
    for key, value in pos_settings.items():
        print(f"  {key}: {value}")
    
    # Test 3: Get all settings
    print("\n" + "=" * 50)
    print("TEST 3: All Settings")
    print("=" * 50)
    all_settings = settings.get_all()
    print(f"  Total settings: {len(all_settings)}")
    for key, value in list(all_settings.items())[:5]:
        print(f"  {key}: {value}")
    
    # Test 4: Set and get single setting
    print("\n" + "=" * 50)
    print("TEST 4: Set/Get Single Setting")
    print("=" * 50)
    settings.set('company.test_value', 'Test Value 123')
    retrieved = settings.get('company.test_value')
    print(f"  Set: 'company.test_value' = 'Test Value 123'")
    print(f"  Retrieved: {retrieved}")
    
    # Test 5: Export and import
    print("\n" + "=" * 50)
    print("TEST 5: Export/Import Settings")
    print("=" * 50)
    exported = settings.export_settings('settings_export.json')
    print(f"  Export successful: {exported}")
    
    # Test 6: Observer pattern
    print("\n" + "=" * 50)
    print("TEST 6: Observer Pattern")
    print("=" * 50)
    
    def my_observer(key, value):
        print(f"  OBSERVER: Setting changed - {key} = {value}")
    
    settings.register_observer(my_observer)
    settings.set('test.observer_key', 'Observer Value')
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    test_settings()


"""
================================================================================
STEP 8: File Structure
================================================================================
"""

# Final directory structure should be:

"""
perfumelab_pro/
├── src/
│   ├── core/
│   │   ├── managers/
│   │   │   ├── __init__.py
│   │   │   ├── settings_manager.py          ✅ NEW
│   │   │   ├── theme_manager.py
│   │   │   └── currency_manager.py
│   │   ├── database/
│   │   │   ├── connection.py
│   │   │   ├── migrations/
│   │   │   │   ├── 001_initial_schema.sql
│   │   │   │   └── 002_settings_schema.sql ✅ NEW
│   │   │   └── __init__.py
│   │   └── services/
│   ├── ui/
│   │   ├── dialogs/
│   │   │   ├── __init__.py
│   │   │   └── settings_dialog.py           ✅ NEW
│   │   ├── widgets/
│   │   ├── shell/
│   │   │   └── main_shell.py                (UPDATE)
│   │   └── __init__.py
│   ├── modules/
│   │   ├── settings/                        ✅ NEW MODULE
│   │   │   ├── __init__.py
│   │   │   ├── ui/
│   │   │   │   └── settings_widget.py
│   │   │   └── services/
│   │   ├── pos/
│   │   ├── inventory/
│   │   ├── treasury/
│   │   ├── dashboard/
│   │   ├── customers/
│   │   ├── manufacturing/
│   │   └── reports/
│   └── main_app.py                          (UPDATE)
└── tests/
    └── test_settings.py                     ✅ NEW
"""


"""
================================================================================
STEP 9: Environment Setup
================================================================================
"""

# Add to requirements.txt if not already present:
# PySide6>=6.4.0
# python-dotenv>=0.19.0

# Create .env file for development:
# DATABASE_PATH=perfumelab.db
# SETTINGS_BACKUP_PATH=./backups
# DEBUG=True


"""
================================================================================
STEP 10: Next Steps
================================================================================
"""

CHECKLIST = {
    "✅ Database Schema": "002_settings_schema.sql created",
    "✅ Settings Manager": "settings_manager.py with caching and observers",
    "✅ Settings Dialog": "12-tab comprehensive settings UI",
    "✅ Settings Module": "SettingsWidget for dashboard display",
    "⏳ Integration": "Update main_app.py and main_shell.py",
    "⏳ Testing": "Run test_settings.py to verify",
    "⏳ Documentation": "Create user guide for settings management",
    "⏳ Deployment": "Deploy to production with backup strategy",
}

print("Settings System Implementation Checklist:")
for key, value in CHECKLIST.items():
    print(f"  {key} {value}")
