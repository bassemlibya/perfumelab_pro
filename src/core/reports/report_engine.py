# core/reports/report_engine.py
from typing import Dict, List, Any
from datetime import datetime, timedelta
from core.database.connection import DatabaseManager
from core.managers.currency_manager import CurrencyManager

class ReportEngine:
    def __init__(self, db_manager: DatabaseManager = None):
        self.db = db_manager or DatabaseManager()
        self.currency_manager = CurrencyManager(self.db)

    def get_dashboard_kpis(self, branch_id: int = None) -> Dict[str, Any]:
        today = datetime.now().strftime('%Y-%m-%d')

        # Sales today
        sales_today = self.db.execute_one(
            "SELECT COUNT(*) as invoice_count, COALESCE(SUM(total), 0) as total_sales, COALESCE(SUM(profit), 0) as total_profit, COALESCE(AVG(profit_margin), 0) as avg_margin FROM sales WHERE DATE(created_at) = ? AND status = 'completed'",
            (today,)
        )

        # Low stock
        low_stock = self.db.execute_one(
            "SELECT COUNT(*) as low_stock_count FROM products WHERE current_stock <= minimum_stock AND is_active = 1"
        )['low_stock_count']

        # New customers
        new_customers = self.db.execute_one(
            "SELECT COUNT(*) as new_customers FROM customers WHERE DATE(created_at) = ?",
            (today,)
        )['new_customers']

        # Treasury balances
        treasury = self.db.execute(
            "SELECT c.name_ar, c.symbol, c.symbol_ar, SUM(cb.current_balance) as balance FROM cashboxes cb JOIN currencies c ON cb.currency_code = c.code WHERE cb.is_active = 1 GROUP BY c.code"
        )

        # Top products today
        top_products = self.db.execute(
            "SELECT p.name_ar, SUM(si.quantity) as qty, SUM(si.total_price) as total FROM sale_items si JOIN products p ON si.product_id = p.id JOIN sales s ON si.sale_id = s.id WHERE DATE(s.created_at) = ? AND s.status = 'completed' GROUP BY si.product_id ORDER BY total DESC LIMIT 5",
            (today,)
        )

        # Weekly comparison
        week_start = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        weekly_sales = self.db.execute_one(
            "SELECT COALESCE(SUM(total), 0) as total FROM sales WHERE DATE(created_at) >= ? AND status = 'completed'",
            (week_start,)
        )['total']

        return {
            'today_sales': sales_today,
            'low_stock_count': low_stock,
            'new_customers': new_customers,
            'treasury_balances': treasury,
            'top_products': top_products,
            'weekly_sales': weekly_sales,
            'default_currency': self.currency_manager.get_default_currency()
        }

    def get_sales_report(self, start_date: str, end_date: str, group_by: str = 'day') -> List[Dict]:
        if group_by == 'day':
            date_format = '%Y-%m-%d'
        elif group_by == 'month':
            date_format = '%Y-%m'
        else:
            date_format = '%Y'

        return self.db.execute(
            "SELECT STRFTIME('%s', created_at) as period, COUNT(*) as invoice_count, SUM(total) as total_amount, SUM(profit) as total_profit, SUM(discount_total) as total_discounts, AVG(total) as avg_invoice FROM sales WHERE DATE(created_at) BETWEEN ? AND ? AND status = 'completed' GROUP BY period ORDER BY period" % date_format,
            (start_date, end_date)
        )

    def get_inventory_report(self, warehouse_id: int = None) -> List[Dict]:
        query = "SELECT p.*, c.name_ar as category_name, COALESCE(ws.quantity, 0) as stock_qty, COALESCE(ws.available_quantity, 0) as available_qty FROM products p LEFT JOIN product_categories c ON p.category_id = c.id LEFT JOIN warehouse_stock ws ON p.id = ws.product_id"
        params = []

        if warehouse_id:
            query += " AND ws.warehouse_id = ?"
            params.append(warehouse_id)

        query += " WHERE p.is_active = 1 ORDER BY p.name_ar"
        return self.db.execute(query, tuple(params))

    def get_customer_report(self, customer_id: int = None) -> List[Dict]:
        if customer_id:
            return self.db.execute(
                "SELECT c.*, cg.name_ar as group_name, COUNT(s.id) as total_invoices, SUM(s.total) as total_purchases FROM customers c LEFT JOIN customer_groups cg ON c.group_id = cg.id LEFT JOIN sales s ON c.id = s.customer_id AND s.status = 'completed' WHERE c.id = ? GROUP BY c.id",
                (customer_id,)
            )
        return self.db.execute(
            "SELECT c.*, cg.name_ar as group_name, COUNT(s.id) as total_invoices, SUM(s.total) as total_purchases FROM customers c LEFT JOIN customer_groups cg ON c.group_id = cg.id LEFT JOIN sales s ON c.id = s.customer_id AND s.status = 'completed' WHERE c.is_active = 1 GROUP BY c.id ORDER BY total_purchases DESC"
        )

    def get_profit_report(self, start_date: str, end_date: str) -> Dict:
        sales = self.db.execute_one(
            "SELECT SUM(total) as revenue, SUM(profit) as profit, SUM(cost_total) as costs FROM (SELECT s.total, s.profit, SUM(si.unit_cost * si.quantity) as cost_total FROM sales s JOIN sale_items si ON s.id = si.sale_id WHERE DATE(s.created_at) BETWEEN ? AND ? AND s.status = 'completed' GROUP BY s.id)",
            (start_date, end_date)
        )

        purchases = self.db.execute_one(
            "SELECT SUM(total) as total_purchases FROM purchases WHERE DATE(created_at) BETWEEN ? AND ? AND status IN ('completed', 'received')",
            (start_date, end_date)
        )

        expenses = self.db.execute_one(
            "SELECT SUM(amount) as total_expenses FROM payments WHERE payment_type = 'expense' AND DATE(created_at) BETWEEN ? AND ?",
            (start_date, end_date)
        )

        return {
            'revenue': sales['revenue'] or 0,
            'profit': sales['profit'] or 0,
            'costs': sales['costs'] or 0,
            'purchases': purchases['total_purchases'] or 0,
            'expenses': expenses['total_expenses'] or 0,
            'profit_margin': (sales['profit'] / sales['revenue'] * 100) if sales['revenue'] else 0
        }
