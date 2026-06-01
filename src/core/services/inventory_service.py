# core/services/inventory_service.py
from typing import Dict, List, Optional
from datetime import datetime
from core.database.connection import DatabaseManager

class InventoryService:
    def __init__(self, db_manager: DatabaseManager = None):
        self.db = db_manager or DatabaseManager()

    def get_available_stock(self, product_id: int, warehouse_id: int = None) -> float:
        if warehouse_id:
            result = self.db.execute_one(
                "SELECT available_quantity FROM warehouse_stock WHERE product_id = ? AND warehouse_id = ?",
                (product_id, warehouse_id)
            )
            return result['available_quantity'] if result else 0
        else:
            result = self.db.execute_one(
                "SELECT SUM(available_quantity) as total FROM warehouse_stock WHERE product_id = ?",
                (product_id,)
            )
            return result['total'] if result else 0

    def deduct_stock(self, product_id: int, quantity: float, warehouse_id: int,
                     reference_id: int, reference_type: str, batch_id: int = None):
        # Update warehouse stock
        self.db.execute_update(
            "UPDATE warehouse_stock SET quantity = quantity - ?, available_quantity = available_quantity - ? WHERE product_id = ? AND warehouse_id = ?",
            (quantity, quantity, product_id, warehouse_id)
        )

        # Update product stock
        self.db.execute_update(
            "UPDATE products SET current_stock = current_stock - ? WHERE id = ?",
            (quantity, product_id)
        )

        # Record movement
        self.db.execute_insert(
            "INSERT INTO stock_movements (product_id, warehouse_id, batch_id, movement_type, quantity, reference_type, reference_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (product_id, warehouse_id, batch_id, 'out', -quantity, reference_type, reference_id, datetime.now())
        )

    def add_stock(self, product_id: int, quantity: float, warehouse_id: int,
                  unit_cost: float, reference_id: int, reference_type: str,
                  batch_number: str = None, expiry_date: str = None):
        # Update warehouse stock
        existing = self.db.execute_one(
            "SELECT id FROM warehouse_stock WHERE product_id = ? AND warehouse_id = ?",
            (product_id, warehouse_id)
        )

        if existing:
            self.db.execute_update(
                "UPDATE warehouse_stock SET quantity = quantity + ?, available_quantity = available_quantity + ? WHERE product_id = ? AND warehouse_id = ?",
                (quantity, quantity, product_id, warehouse_id)
            )
        else:
            self.db.execute_insert(
                "INSERT INTO warehouse_stock (warehouse_id, product_id, quantity, available_quantity) VALUES (?, ?, ?, ?)",
                (warehouse_id, product_id, quantity, quantity)
            )

        # Update product stock
        self.db.execute_update(
            "UPDATE products SET current_stock = current_stock + ? WHERE id = ?",
            (quantity, product_id)
        )

        # Create batch if needed
        batch_id = None
        if batch_number:
            batch_id = self.db.execute_insert(
                "INSERT INTO stock_batches (product_id, warehouse_id, batch_number, quantity, unit_cost, expiry_date) VALUES (?, ?, ?, ?, ?, ?)",
                (product_id, warehouse_id, batch_number, quantity, unit_cost, expiry_date)
            )

        # Record movement
        self.db.execute_insert(
            "INSERT INTO stock_movements (product_id, warehouse_id, batch_id, movement_type, quantity, unit_cost, reference_type, reference_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (product_id, warehouse_id, batch_id, 'in', quantity, unit_cost, reference_type, reference_id, datetime.now())
        )

    def get_low_stock_products(self) -> List[Dict]:
        return self.db.execute(
            "SELECT p.*, ws.quantity as warehouse_qty FROM products p LEFT JOIN warehouse_stock ws ON p.id = ws.product_id WHERE p.current_stock <= p.minimum_stock AND p.is_active = 1"
        )

    def get_stock_movements(self, product_id: int = None, warehouse_id: int = None,
                            start_date: str = None, end_date: str = None) -> List[Dict]:
        query = "SELECT sm.*, p.name_ar as product_name, w.name_ar as warehouse_name FROM stock_movements sm LEFT JOIN products p ON sm.product_id = p.id LEFT JOIN warehouses w ON sm.warehouse_id = w.id WHERE 1=1"
        params = []

        if product_id:
            query += " AND sm.product_id = ?"
            params.append(product_id)
        if warehouse_id:
            query += " AND sm.warehouse_id = ?"
            params.append(warehouse_id)
        if start_date:
            query += " AND DATE(sm.created_at) >= ?"
            params.append(start_date)
        if end_date:
            query += " AND DATE(sm.created_at) <= ?"
            params.append(end_date)

        query += " ORDER BY sm.created_at DESC"
        return self.db.execute(query, tuple(params))
