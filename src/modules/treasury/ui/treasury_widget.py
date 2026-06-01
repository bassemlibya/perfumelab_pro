# modules/treasury/ui/treasury_widget.py
from typing import Optional, Dict, Any
from datetime import datetime
import traceback
import csv
import logging

from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Safe imports with fallbacks
try:
    from core.services.treasury_service import TreasuryService, TreasuryServiceError
    from core.managers.currency_manager import CurrencyManager
    from core.database.connection import DatabaseManager
    from ui.widgets.arabic_widgets import ArabicTableWidget, ArabicLineEdit, ArabicComboBox
except ImportError as e:
    logger.warning(f"⚠️ Import error: {e}")
    # Create dummy classes for testing
    class TreasuryServiceError(Exception): 
        pass
    
    TreasuryService = None
    CurrencyManager = None
    DatabaseManager = None
    ArabicTableWidget = QTableWidget
    ArabicLineEdit = QLineEdit
    ArabicComboBox = QComboBox

class TreasuryWidget(QWidget):
    """Treasury and bank accounts management module"""
    
    def __init__(self, parent=None, db_manager: Optional[DatabaseManager] = None,
                 currency_manager: Optional[CurrencyManager] = None):
        super().__init__(parent)
        
        # Store managers
        self.db_manager = db_manager
        
        # Initialize services with proper managers
        try:
            if TreasuryService:
                self.treasury_service = TreasuryService(db_manager, currency_manager)
            else:
                self.treasury_service = None
                logger.warning("⚠️ TreasuryService not available")
            
            self.currency_manager = currency_manager or (CurrencyManager(db_manager) if CurrencyManager else None)
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize services: {e}")
            traceback.print_exc()
            self.treasury_service = None
            self.currency_manager = None
        
        # Setup UI
        self.setLayoutDirection(Qt.RightToLeft)
        self.setup_ui()
        
        # Auto-refresh timer (30 seconds)
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(30000)
        
        # Load initial data
        self.refresh_data()
    
    def setup_ui(self):
        """Setup user interface"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header with title and buttons
        header = self.create_header()
        layout.addLayout(header)
        
        # Statistics cards
        stats_layout = self.create_stats_cards()
        layout.addLayout(stats_layout)
        
        # Cashboxes section
        cashbox_group = self.create_cashbox_section()
        layout.addWidget(cashbox_group)
        
        # Bank accounts section
        bank_group = self.create_bank_section()
        layout.addWidget(bank_group)
        
        # Transactions section
        trans_group = self.create_transactions_section()
        layout.addWidget(trans_group)
        
        # Status bar
        self.status_label = QLabel("آخر تحديث: --")
        self.status_label.setStyleSheet("font-size: 11px; color: #757575; margin-top: 10px;")
        layout.addWidget(self.status_label)
    
    def create_header(self) -> QHBoxLayout:
        """Create header with title and action buttons"""
        header = QHBoxLayout()
        
        title = QLabel("🏦 إدارة الخزينة والحسابات البنكية")
        title.setStyleSheet("""
            font-size: 22px;
            font-weight: bold;
            color: #2E7D32;
        """)
        header.addWidget(title)
        header.addStretch()
        
        # Action buttons
        buttons = [
            ("💰 سند قبض", "#1565C0", self.on_create_receipt),
            ("💸 سند صرف", "#FF6F00", self.on_create_payment),
            ("🔄 تحويل", "#6C5CE7", self.on_transfer),
            ("📊 تقرير", "#00ACC1", self.on_treasury_report),
            ("🔄 تحديث", "#4CAF50", self.refresh_data),
        ]
        
        for text, color, callback in buttons:
            btn = QPushButton(text)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: white;
                    padding: 8px 16px;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 13px;
                }}
                QPushButton:hover {{
                    background-color: {self._darken_color(color)};
                }}
            """)
            btn.clicked.connect(callback)
            header.addWidget(btn)
        
        return header
    
    def create_stats_cards(self) -> QHBoxLayout:
        """Create quick statistics cards"""
        layout = QHBoxLayout()
        layout.setSpacing(15)
        
        # Total cash
        self.total_cash_card = self._create_stat_card(
            "💰 إجمالي الخزائن",
            "0.00",
            "#2E7D32"
        )
        layout.addWidget(self.total_cash_card)
        
        # Total banks
        self.total_bank_card = self._create_stat_card(
            "🏦 إجمالي البنوك",
            "0.00",
            "#1565C0"
        )
        layout.addWidget(self.total_bank_card)
        
        # Today's transactions
        self.today_trans_card = self._create_stat_card(
            "📊 معاملات اليوم",
            "0",
            "#FF6F00"
        )
        layout.addWidget(self.today_trans_card)
        
        return layout
    
    def _create_stat_card(self, title: str, value: str, color: str) -> QFrame:
        """Create a statistics card"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 1px solid #E0E0E0;
                border-radius: 10px;
                padding: 15px;
            }}
        """)
        
        layout = QVBoxLayout(card)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 13px; color: #757575;")
        layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setStyleSheet(f"font-size: 28px; font-weight: bold; color: {color};")
        layout.addWidget(value_label)
        
        # Store reference for updates
        setattr(self, f"stat_{title.replace(' ', '_')}_value", value_label)
        
        return card
    
    def create_cashbox_section(self) -> QGroupBox:
        """Create cashboxes section"""
        group = QGroupBox("💰 الخزائن النقدية")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px;
            }
        """)
        
        layout = QVBoxLayout(group)
        
        self.cashbox_table = ArabicTableWidget(columns=[
            "الخزينة", "الفرع", "العملة", "الرصيد الحالي",
            "الرصيد الافتتاحي", "آخر تحديث", "الحالة", ""
        ])
        self.cashbox_table.setMinimumHeight(200)
        layout.addWidget(self.cashbox_table)
        
        return group
    
    def create_bank_section(self) -> QGroupBox:
        """Create bank accounts section"""
        group = QGroupBox("🏦 الحسابات البنكية")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px;
            }
        """)
        
        layout = QVBoxLayout(group)
        
        self.bank_table = ArabicTableWidget(columns=[
            "البنك", "اسم الحساب", "رقم الحساب", "IBAN",
            "العملة", "الرصيد", "الحالة", ""
        ])
        self.bank_table.setMinimumHeight(200)
        layout.addWidget(self.bank_table)
        
        return group
    
    def create_transactions_section(self) -> QGroupBox:
        """Create transactions section"""
        group = QGroupBox("📋 المعاملات الأخيرة")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px;
            }
        """)
        
        layout = QVBoxLayout(group)
        
        # Filter and export
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("فلترة:"))
        
        self.filter_type = ArabicComboBox()
        self.filter_type.addItem("كل المعاملات", "all")
        self.filter_type.addItem("سندات قبض", "receipt")
        self.filter_type.addItem("سندات صرف", "payment")
        self.filter_type.addItem("تحويلات", "transfer")
        self.filter_type.currentIndexChanged.connect(self.on_filter_changed)
        filter_layout.addWidget(self.filter_type)
        
        filter_layout.addStretch()
        
        export_btn = QPushButton("📥 تصدير")
        export_btn.setFixedWidth(100)
        export_btn.clicked.connect(self.export_transactions)
        filter_layout.addWidget(export_btn)
        
        layout.addLayout(filter_layout)
        
        self.trans_table = ArabicTableWidget(columns=[
            "التاريخ", "النوع", "من", "إلى",
            "المبلغ", "العملة", "طريقة الدفع", "المرجع", "المستخدم"
        ])
        self.trans_table.setMinimumHeight(250)
        layout.addWidget(self.trans_table)
        
        return group
    
    def refresh_data(self):
        """Refresh all data"""
        if not self.treasury_service:
            self._show_error("❌ خدمة الخزينة غير متوفرة")
            return
        
        try:
            self._refresh_cashboxes()
            self._refresh_bank_accounts()
            self._refresh_transactions()
            self._refresh_statistics()
            
            # Update last refresh time
            self.status_label.setText(f"آخر تحديث: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("✅ Treasury data refreshed")
            
        except Exception as e:
            logger.error(f"❌ Error refreshing data: {e}")
            traceback.print_exc()
            self._show_error(f"خطأ في تحديث البيانات: {str(e)[:100]}")
    
    def _refresh_cashboxes(self):
        """Refresh cashboxes data"""
        self.cashbox_table.setRowCount(0)
        
        try:
            if hasattr(self.treasury_service, 'get_cashboxes_with_balance'):
                cashboxes = self.treasury_service.get_cashboxes_with_balance()
            else:
                # Fallback to direct query
                cashboxes = self.treasury_service.db.execute("""
                    SELECT cb.*, b.name_ar as branch_name, c.symbol, c.symbol_ar
                    FROM cashboxes cb
                    LEFT JOIN branches b ON cb.branch_id = b.id
                    LEFT JOIN currencies c ON cb.currency_code = c.code
                    WHERE cb.is_active = 1
                """)
            
            for cb in cashboxes:
                status = "🟢 نشط" if cb.get('is_active', 1) else "🔴 معطل"
                
                self.cashbox_table.add_arabic_row([
                    cb.get('name_ar', '-'),
                    cb.get('branch_name', '-'),
                    cb.get('symbol_ar') or cb.get('symbol', '-'),
                    self._format_amount(cb.get('current_balance', 0), cb.get('currency_code')),
                    self._format_amount(cb.get('opening_balance', 0), cb.get('currency_code')),
                    cb.get('last_updated', '-'),
                    status,
                    "🔍"
                ])
                
        except Exception as e:
            logger.error(f"❌ Error loading cashboxes: {e}")
            self.cashbox_table.add_arabic_row(["❌ خطأ في تحميل البيانات", "", "", "", "", "", "", ""])
    
    def _refresh_bank_accounts(self):
        """Refresh bank accounts data"""
        self.bank_table.setRowCount(0)
        
        try:
            if hasattr(self.treasury_service, 'get_bank_accounts_with_balance'):
                accounts = self.treasury_service.get_bank_accounts_with_balance()
            else:
                # Fallback to direct query
                accounts = self.treasury_service.db.execute("""
                    SELECT ba.*, b.name_ar as bank_name, c.symbol, c.symbol_ar
                    FROM bank_accounts ba
                    LEFT JOIN banks b ON ba.bank_id = b.id
                    LEFT JOIN currencies c ON ba.currency_code = c.code
                    WHERE ba.is_active = 1
                """)
            
            for acc in accounts:
                status = "🟢 نشط" if acc.get('is_active', 1) else "🔴 معطل"
                
                self.bank_table.add_arabic_row([
                    acc.get('bank_name', '-'),
                    acc.get('account_name_ar', '-'),
                    acc.get('account_number', '-'),
                    acc.get('iban', '-'),
                    acc.get('symbol_ar') or acc.get('symbol', '-'),
                    self._format_amount(acc.get('current_balance', 0), acc.get('currency_code')),
                    status,
                    "🔍"
                ])
                
        except Exception as e:
            logger.error(f"❌ Error loading bank accounts: {e}")
    
    def _refresh_transactions(self):
        """Refresh transactions data"""
        self.trans_table.setRowCount(0)
        
        try:
            filter_type = self.filter_type.currentData()
            
            if hasattr(self.treasury_service, 'get_recent_transactions'):
                transactions = self.treasury_service.get_recent_transactions(
                    limit=100,
                    trans_type=filter_type if filter_type != 'all' else None
                )
            else:
                # Fallback to direct query
                query = """
                    SELECT tt.*, c.symbol, c.symbol_ar, u.full_name_ar as user_name
                    FROM treasury_transactions tt
                    LEFT JOIN currencies c ON tt.currency_code = c.code
                    LEFT JOIN users u ON tt.user_id = u.id
                    WHERE 1=1
                """
                params = []
                
                if filter_type and filter_type != 'all':
                    query += " AND tt.transaction_type = ?"
                    params.append(filter_type)
                
                query += " ORDER BY tt.created_at DESC LIMIT 100"
                transactions = self.treasury_service.db.execute(query, tuple(params))
            
            trans_type_names = {
                'receipt': '💰 سند قبض',
                'payment': '💸 سند صرف',
                'transfer': '🔄 تحويل',
                'exchange': '💱 صرف عملات'
            }
            
            for trans in transactions:
                trans_type = trans_type_names.get(
                    trans.get('transaction_type', ''),
                    trans.get('transaction_type', '-')
                )
                
                self.trans_table.add_arabic_row([
                    trans.get('created_at', '-')[:19] if trans.get('created_at') else '-',
                    trans_type,
                    trans.get('from_name', '-'),
                    trans.get('to_name', '-'),
                    self._format_amount(trans.get('amount', 0), trans.get('currency_code')),
                    trans.get('symbol_ar') or trans.get('symbol', '-'),
                    trans.get('payment_method', '-'),
                    trans.get('reference_number', '-'),
                    trans.get('user_name', '-')
                ])
                
        except Exception as e:
            logger.error(f"❌ Error loading transactions: {e}")
    
    def _refresh_statistics(self):
        """Refresh statistics cards"""
        try:
            if self.treasury_service:
                # Total cash
                if hasattr(self.treasury_service, 'get_total_cash_balance'):
                    total_cash = self.treasury_service.get_total_cash_balance()
                else:
                    result = self.treasury_service.db.execute_one(
                        "SELECT COALESCE(SUM(current_balance), 0) as total FROM cashboxes WHERE is_active = 1"
                    )
                    total_cash = result.get('total', 0) if result else 0
                
                if hasattr(self, 'stat_إجمالي_الخزائن_value'):
                    self.stat_إجمالي_الخزائن_value.setText(self._format_amount(total_cash))
                
                # Total bank
                if hasattr(self.treasury_service, 'get_total_bank_balance'):
                    total_bank = self.treasury_service.get_total_bank_balance()
                else:
                    result = self.treasury_service.db.execute_one(
                        "SELECT COALESCE(SUM(current_balance), 0) as total FROM bank_accounts WHERE is_active = 1"
                    )
                    total_bank = result.get('total', 0) if result else 0
                
                if hasattr(self, 'stat_إجمالي_البنوك_value'):
                    self.stat_إجمالي_البنوك_value.setText(self._format_amount(total_bank))
                
                # Today's transactions
                result = self.treasury_service.db.execute_one(
                    "SELECT COUNT(*) as count FROM treasury_transactions WHERE DATE(created_at) = DATE('now')"
                )
                today_count = result.get('count', 0) if result else 0
                
                if hasattr(self, 'stat_معاملات_اليوم_value'):
                    self.stat_معاملات_اليوم_value.setText(str(today_count))
                    
        except Exception as e:
            logger.warning(f"⚠️ Error updating statistics: {e}")
    
    def _format_amount(self, amount: Any, currency_code: Optional[str] = None) -> str:
        """Format amount with currency"""
        if amount is None:
            return "0.00"
        
        try:
            float_amount = float(amount)
            if self.currency_manager and currency_code:
                return self.currency_manager.format_amount(float_amount, currency_code)
            return f"{float_amount:,.2f}"
        except Exception as e:
            logger.warning(f"⚠️ Error formatting amount: {e}")
            return str(amount)
    
    def _darken_color(self, hex_color: str) -> str:
        """Darken color for hover effect"""
        try:
            color = QColor(hex_color)
            darker = color.darker(110)
            return darker.name()
        except:
            return "#333333"
    
    def _show_error(self, message: str):
        """Show error message"""
        QMessageBox.warning(self, "خطأ", message)
    
    def on_create_receipt(self):
        """Create receipt"""
        QMessageBox.information(self, "💰 سند قبض", "فتح شاشة إنشاء سند القبض - قيد التطوير")
    
    def on_create_payment(self):
        """Create payment"""
        QMessageBox.information(self, "💸 سند صرف", "فتح شاشة إنشاء سند الصرف - قيد التطوير")
    
    def on_transfer(self):
        """Transfer between cashboxes"""
        QMessageBox.information(self, "🔄 تحويل", "فتح شاشة التحويل بين الخزائن - قيد التطوير")
    
    def on_treasury_report(self):
        """Show treasury report"""
        QMessageBox.information(self, "📊 تقرير الخزينة", "فتح تقرير الخزينة - قيد التطوير")
    
    def on_filter_changed(self):
        """Handle filter change"""
        self._refresh_transactions()
    
    def export_transactions(self):
        """Export transactions to CSV"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "حفظ التقرير",
                f"treasury_report_{datetime.now().strftime('%Y%m%d')}.csv",
                "CSV Files (*.csv)"
            )
            
            if file_path:
                transactions = self.treasury_service.db.execute(
                    "SELECT * FROM treasury_transactions ORDER BY created_at DESC LIMIT 500"
                )
                
                with open(file_path, 'w', encoding='utf-8-sig', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['التاريخ', 'النوع', 'المبلغ', 'العملة', 'المرجع'])
                    
                    for trans in transactions:
                        writer.writerow([
                            trans.get('created_at', '')[:19],
                            trans.get('transaction_type', ''),
                            trans.get('amount', 0),
                            trans.get('currency_code', ''),
                            trans.get('reference_number', '')
                        ])
                
                QMessageBox.information(self, "✅ تم", f"تم تصدير {len(transactions)} معاملة")
                logger.info(f"✅ Exported {len(transactions)} transactions")
                
        except Exception as e:
            logger.error(f"❌ Export failed: {e}")
            self._show_error(f"فشل التصدير: {str(e)[:100]}")
    
    def on_show(self):
        """Called when widget is shown"""
        self.refresh_data()
    
    def on_close(self):
        """Called when widget is closed"""
        if hasattr(self, 'refresh_timer'):
            self.refresh_timer.stop()


if __name__ == "__main__":
    import sys
    
    app = QApplication(sys.argv)
    
    # For standalone testing
    widget = TreasuryWidget()
    widget.show()
    
    sys.exit(app.exec())
