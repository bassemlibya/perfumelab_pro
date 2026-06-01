# core/services/treasury_service.py
from typing import Dict, List, Optional
from datetime import datetime
from core.database.connection import DatabaseManager
from core.managers.currency_manager import CurrencyManager

class TreasuryService:
    def __init__(self, db_manager: DatabaseManager = None):
        self.db = db_manager or DatabaseManager()
        self.currency_manager = CurrencyManager(self.db)

    def record_payment(self, reference_id: int, reference_type: str, payment: Dict):
        method = payment.get('method', 'cash')
        amount = payment['amount']
        currency = payment.get('currency', self.currency_manager.get_default_currency()['code'])
        rate = self.currency_manager.get_exchange_rate(currency, self.currency_manager.get_default_currency()['code'])
        base_amount = amount * rate

        cashbox_id = payment.get('cashbox_id')
        bank_account_id = payment.get('bank_account_id')

        # Update cashbox balance
        if cashbox_id and method == 'cash':
            self.db.execute_update(
                "UPDATE cashboxes SET current_balance = current_balance + ? WHERE id = ?",
                (amount, cashbox_id)
            )

        # Update bank account balance
        if bank_account_id and method in ['bank', 'card']:
            self.db.execute_update(
                "UPDATE bank_accounts SET current_balance = current_balance + ? WHERE id = ?",
                (amount, bank_account_id)
            )

        # Record sale payment
        if reference_type == 'sale':
            self.db.execute_insert(
                "INSERT INTO sale_payments (sale_id, payment_method, cashbox_id, bank_account_id, currency_code, amount, exchange_rate, base_amount, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (reference_id, method, cashbox_id, bank_account_id, currency, amount, rate, base_amount, datetime.now())
            )

        # Record treasury transaction
        self.db.execute_insert(
            "INSERT INTO treasury_transactions (transaction_type, to_cashbox_id, to_bank_account_id, currency_code, amount, exchange_rate, base_amount, reference_type, reference_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ('receipt', cashbox_id, bank_account_id, currency, amount, rate, base_amount, reference_type, reference_id, datetime.now())
        )

    def create_receipt(self, receipt_data: Dict) -> int:
        today = datetime.now().strftime('%Y%m%d')
        count = self.db.execute_one(
            "SELECT COUNT(*) as cnt FROM receipts WHERE DATE(created_at) = DATE('now')"
        )['cnt'] + 1
        receipt_number = "REC-%s-%04d" % (today, count)

        currency = receipt_data.get('currency', self.currency_manager.get_default_currency()['code'])
        rate = self.currency_manager.get_exchange_rate(currency, self.currency_manager.get_default_currency()['code'])
        amount = receipt_data['amount']
        base_amount = amount * rate

        receipt_id = self.db.execute_insert(
            "INSERT INTO receipts (receipt_number, from_entity_id, from_entity_type, to_cashbox_id, to_bank_account_id, currency_code, amount, exchange_rate, base_amount, payment_method, reference_number, notes, user_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (receipt_number, receipt_data.get('entity_id'), receipt_data.get('entity_type'),
             receipt_data.get('cashbox_id'), receipt_data.get('bank_account_id'),
             currency, amount, rate, base_amount, receipt_data.get('method', 'cash'),
             receipt_data.get('reference'), receipt_data.get('notes'), receipt_data.get('user_id', 1))
        )

        # Update balances
        if receipt_data.get('cashbox_id'):
            self.db.execute_update(
                "UPDATE cashboxes SET current_balance = current_balance + ? WHERE id = ?",
                (amount, receipt_data['cashbox_id'])
            )

        return receipt_id

    def create_payment(self, payment_data: Dict) -> int:
        today = datetime.now().strftime('%Y%m%d')
        count = self.db.execute_one(
            "SELECT COUNT(*) as cnt FROM payments WHERE DATE(created_at) = DATE('now')"
        )['cnt'] + 1
        payment_number = "PAY-%s-%04d" % (today, count)

        currency = payment_data.get('currency', self.currency_manager.get_default_currency()['code'])
        rate = self.currency_manager.get_exchange_rate(currency, self.currency_manager.get_default_currency()['code'])
        amount = payment_data['amount']
        base_amount = amount * rate

        payment_id = self.db.execute_insert(
            "INSERT INTO payments (payment_number, to_entity_id, to_entity_type, from_cashbox_id, from_bank_account_id, currency_code, amount, exchange_rate, base_amount, payment_method, reference_number, notes, user_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (payment_number, payment_data.get('entity_id'), payment_data.get('entity_type'),
             payment_data.get('cashbox_id'), payment_data.get('bank_account_id'),
             currency, amount, rate, base_amount, payment_data.get('method', 'cash'),
             payment_data.get('reference'), payment_data.get('notes'), payment_data.get('user_id', 1))
        )

        # Update balances
        if payment_data.get('cashbox_id'):
            self.db.execute_update(
                "UPDATE cashboxes SET current_balance = current_balance - ? WHERE id = ?",
                (amount, payment_data['cashbox_id'])
            )

        return payment_id

    def get_cashbox_balance(self, cashbox_id: int = None) -> List[Dict]:
        if cashbox_id:
            return self.db.execute(
                "SELECT c.*, cur.symbol, cur.symbol_ar FROM cashboxes c JOIN currencies cur ON c.currency_code = cur.code WHERE c.id = ?",
                (cashbox_id,)
            )
        return self.db.execute(
            "SELECT c.*, cur.symbol, cur.symbol_ar FROM cashboxes c JOIN currencies cur ON c.currency_code = cur.code WHERE c.is_active = 1"
        )

    def get_treasury_summary(self) -> Dict:
        cashboxes = self.db.execute(
            "SELECT c.currency_code, SUM(c.current_balance) as total FROM cashboxes c WHERE c.is_active = 1 GROUP BY c.currency_code"
        )
        banks = self.db.execute(
            "SELECT ba.currency_code, SUM(ba.current_balance) as total FROM bank_accounts ba WHERE ba.is_active = 1 GROUP BY ba.currency_code"
        )
        return {'cashboxes': cashboxes, 'banks': banks}
