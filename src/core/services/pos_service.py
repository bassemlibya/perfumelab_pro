# core/services/pos_service.py
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from core.database.connection import DatabaseManager
from core.managers.currency_manager import CurrencyManager
from core.services.inventory_service import InventoryService
from core.services.treasury_service import TreasuryService

class POSService:
    def __init__(self, db_manager: DatabaseManager = None):
        self.db = db_manager or DatabaseManager()
        self.currency_manager = CurrencyManager(self.db)
        self.inventory_service = InventoryService(self.db)
        self.treasury_service = TreasuryService(self.db)

    def create_invoice(self, items: List[Dict], customer_id: int = None,
                       currency_code: str = None, user_id: int = 1,
                       branch_id: int = 1, warehouse_id: int = 1,
                       discount_type: str = None, discount_value: float = 0,
                       payments: List[Dict] = None) -> Dict:
        currency = currency_code or self.currency_manager.get_default_currency()['code']
        rate = self.currency_manager.get_exchange_rate(currency, self.currency_manager.get_default_currency()['code'])

        subtotal = 0
        total_cost = 0
        sale_items = []

        for item in items:
            product = self.db.execute_one(
                "SELECT * FROM products WHERE id = ?", (item['product_id'],)
            )
            if not product:
                raise ValueError("Product not found: %s" % item['product_id'])

            qty = item['quantity']
            unit_price = item.get('unit_price', product['sale_price'])
            unit_cost = product['cost_price']

            available = self.inventory_service.get_available_stock(product['id'], warehouse_id)
            if available < qty:
                raise ValueError("Insufficient stock for %s: available %s" % (product['name_ar'], available))

            item_discount = item.get('discount_percent', 0)
            item_tax = item.get('tax_percent', product['tax_percent'])

            item_subtotal = qty * unit_price
            item_discount_amount = item_subtotal * (item_discount / 100)
            item_tax_amount = (item_subtotal - item_discount_amount) * (item_tax / 100)
            item_total = item_subtotal - item_discount_amount + item_tax_amount
            item_profit = (unit_price - unit_cost) * qty - item_discount_amount

            sale_items.append({
                'product_id': product['id'],
                'quantity': qty,
                'unit_id': item.get('unit_id', product['unit_id']),
                'unit_cost': unit_cost,
                'unit_price': unit_price,
                'discount_percent': item_discount,
                'discount_amount': item_discount_amount,
                'tax_percent': item_tax,
                'tax_amount': item_tax_amount,
                'total_price': item_total,
                'profit': item_profit
            })

            subtotal += item_subtotal
            total_cost += unit_cost * qty

        discount_total = subtotal * (discount_value / 100) if discount_type == 'percent' else discount_value
        tax_total = sum(i['tax_amount'] for i in sale_items)
        total = subtotal - discount_total + tax_total
        profit = sum(i['profit'] for i in sale_items)

        today = datetime.now().strftime('%Y%m%d')
        count = self.db.execute_one(
            "SELECT COUNT(*) as cnt FROM sales WHERE DATE(created_at) = DATE('now')"
        )['cnt'] + 1
        invoice_number = "INV-%s-%04d" % (today, count)

        sale_id = self.db.execute_insert(
            "INSERT INTO sales (invoice_number, customer_id, user_id, branch_id, warehouse_id, currency_code, exchange_rate, subtotal, discount_total, tax_total, total, profit, profit_margin, discount_type, discount_value, status, payment_status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (invoice_number, customer_id, user_id, branch_id, warehouse_id, currency, rate,
             subtotal, discount_total, tax_total, total, profit,
             (profit / subtotal * 100) if subtotal > 0 else 0,
             discount_type, discount_value, 'completed', 'paid')
        )

        for si in sale_items:
            self.db.execute_insert(
                "INSERT INTO sale_items (sale_id, product_id, quantity, unit_id, unit_cost, unit_price, discount_percent, discount_amount, tax_percent, tax_amount, total_price, profit) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (sale_id, si['product_id'], si['quantity'], si['unit_id'],
                 si['unit_cost'], si['unit_price'], si['discount_percent'],
                 si['discount_amount'], si['tax_percent'], si['tax_amount'],
                 si['total_price'], si['profit'])
            )

        for item in items:
            self.inventory_service.deduct_stock(
                item['product_id'], item['quantity'], warehouse_id, sale_id, 'sale'
            )

        paid = 0
        if payments:
            for payment in payments:
                self.treasury_service.record_payment(sale_id, 'sale', payment)
                paid += payment['amount']

        remaining = total - paid
        if remaining > 0 and customer_id:
            self.db.execute_update(
                "UPDATE customers SET balance = balance + ? WHERE id = ?",
                (remaining, customer_id)
            )

        return {
            'sale_id': sale_id,
            'invoice_number': invoice_number,
            'total': total,
            'paid': paid,
            'remaining': remaining
        }

    def get_products_for_pos(self, category_id: int = None, search: str = None) -> List[Dict]:
        query = "SELECT p.*, c.name_ar as category_name, b.name_ar as brand_name FROM products p LEFT JOIN product_categories c ON p.category_id = c.id LEFT JOIN product_brands b ON p.brand_id = b.id WHERE p.is_active = 1"
        params = []

        if category_id:
            query += " AND p.category_id = ?"
            params.append(category_id)

        if search:
            query += " AND (p.name_ar LIKE ? OR p.barcode LIKE ? OR p.sku LIKE ?)"
            params.extend(["%%%s%%" % search, "%%%s%%" % search, "%%%s%%" % search])

        query += " ORDER BY p.is_featured DESC, p.name_ar"
        return self.db.execute(query, tuple(params))

    def hold_invoice(self, items: List[Dict], customer_id: int = None, user_id: int = 1) -> str:
        hold_count = self.db.execute_one(
            "SELECT COUNT(*) as cnt FROM held_sales WHERE DATE(created_at) = DATE('now')"
        )['cnt'] + 1
        hold_number = "HLD-%s-%04d" % (datetime.now().strftime('%Y%m%d'), hold_count)

        import json
        self.db.execute_insert(
            "INSERT INTO held_sales (hold_number, customer_id, user_id, items_json, totals_json) VALUES (?, ?, ?, ?, ?)",
            (hold_number, customer_id, user_id, json.dumps(items), json.dumps({}))
        )
        return hold_number

    def get_held_invoices(self, user_id: int = None) -> List[Dict]:
        query = "SELECT * FROM held_sales WHERE 1=1"
        params = []
        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
        query += " ORDER BY created_at DESC"
        return self.db.execute(query, tuple(params))
