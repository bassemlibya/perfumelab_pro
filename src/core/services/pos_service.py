# core/services/pos_service.py
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
import json
import logging
import traceback

from core.database.connection import DatabaseManager
from core.managers.currency_manager import CurrencyManager
from core.services.inventory_service import InventoryService
from core.services.treasury_service import TreasuryService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class POSServiceError(Exception):
    """Custom exception for POS service"""
    pass

class POSService:
    """POS Service - Managing invoices and sales"""
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None, 
                 currency_manager: Optional[CurrencyManager] = None):
        """
        Initialize POS Service
        
        Args:
            db_manager: Database manager instance
            currency_manager: Currency manager instance (optional)
        """
        try:
            self.db = db_manager or DatabaseManager()
            self.currency_manager = currency_manager or CurrencyManager(self.db)
            self.inventory_service = InventoryService(self.db)
            self.treasury_service = TreasuryService(self.db)
            logger.info("✅ POSService initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize POSService: {e}")
            traceback.print_exc()
            raise POSServiceError(f"Failed to initialize POSService: {e}") from e
    
    def generate_invoice_number(self) -> str:
        """
        Generate a new invoice number
        
        Returns:
            Invoice number string
        """
        today = datetime.now().strftime('%Y%m%d')
        try:
            count_result = self.db.execute_one(
                "SELECT COUNT(*) as cnt FROM sales WHERE DATE(created_at) = DATE('now')"
            )
            count_value = (count_result['cnt'] if count_result else 0) + 1
            invoice_number = f"INV-{today}-{count_value:04d}"
        except Exception as e:
            logger.warning(f"⚠️ Failed to generate sequential invoice number: {e}")
            # Fallback: use current time
            invoice_number = f"INV-{today}-{datetime.now().strftime('%H%M%S')}"
        
        return invoice_number
    
    def create_invoice(self, items: List[Dict], customer_id: Optional[int] = None,
                       currency_code: Optional[str] = None, user_id: int = 1,
                       branch_id: int = 1, warehouse_id: int = 1,
                       discount_type: Optional[str] = None, discount_value: float = 0,
                       discount_percent: float = 0, payments: Optional[List[Dict]] = None,
                       note: Optional[str] = None) -> Dict:
        """
        Create a new sales invoice
        
        Args:
            items: List of products in invoice
            customer_id: Customer ID (optional)
            currency_code: Currency code
            user_id: User ID
            branch_id: Branch ID
            warehouse_id: Warehouse ID
            discount_type: Discount type ('percent' or 'amount')
            discount_value: Discount value
            discount_percent: Discount percentage
            payments: List of payments
            note: Invoice notes
            
        Returns:
            Invoice information dictionary
        """
        if not items:
            raise POSServiceError("❌ Cannot create invoice without products")
        
        try:
            # Get default currency if not specified
            default_currency = self.currency_manager.get_default_currency()
            if not default_currency:
                raise POSServiceError("❌ No default currency set")
            
            currency = currency_code or default_currency['code']
            
            # Get exchange rate with fallback
            try:
                rate = self.currency_manager.get_exchange_rate(
                    currency, 
                    default_currency['code']
                )
                if not rate or rate <= 0:
                    logger.warning(f"⚠️ Invalid exchange rate, using 1.0")
                    rate = Decimal('1.0')
                else:
                    rate = Decimal(str(rate))
            except Exception as e:
                logger.warning(f"⚠️ Exchange rate lookup failed, using 1.0: {e}")
                rate = Decimal('1.0')
            
            # Convert to Decimal for precision
            discount_percent_dec = Decimal(str(discount_percent))
            discount_value_dec = Decimal(str(discount_value))
            
            subtotal = Decimal('0')
            total_cost = Decimal('0')
            sale_items = []
            
            # Process each product in cart
            for idx, item in enumerate(items):
                try:
                    # Get product information
                    product = self.db.execute_one(
                        """SELECT p.*, u.abbreviation as unit_abbr 
                           FROM products p 
                           LEFT JOIN units u ON p.unit_id = u.id 
                           WHERE p.id = ? AND p.is_active = 1""",
                        (item.get('product_id'),)
                    )
                    
                    if not product:
                        raise POSServiceError(f"❌ Product not found: {item.get('product_id')}")
                    
                    qty = Decimal(str(item.get('quantity', 1)))
                    unit_price = Decimal(str(item.get('unit_price', product.get('sale_price', 0))))
                    unit_cost = Decimal(str(product.get('cost_price', 0)))
                    
                    # Validate stock availability
                    try:
                        available = self.inventory_service.get_available_stock(
                            product['id'], 
                            warehouse_id
                        )
                        available_dec = Decimal(str(available))
                        if available_dec < qty:
                            if not self._allow_negative_stock():
                                raise POSServiceError(
                                    f"❌ Insufficient stock for {product.get('name_ar', 'Product')}: "
                                    f"Required {qty}, Available {available_dec}"
                                )
                    except POSServiceError:
                        raise
                    except Exception as e:
                        logger.error(f"❌ Stock check failed: {e}")
                        if not self._allow_negative_stock():
                            raise POSServiceError(f"Stock verification failed: {e}")
                    
                    # Calculate discount and tax
                    item_discount_percent = Decimal(str(item.get('discount_percent', 0)))
                    item_tax_percent = Decimal(str(item.get('tax_percent', product.get('tax_percent', 0))))
                    
                    item_subtotal = qty * unit_price
                    item_discount_amount = item_subtotal * item_discount_percent / Decimal('100')
                    taxable_amount = item_subtotal - item_discount_amount
                    item_tax_amount = taxable_amount * item_tax_percent / Decimal('100')
                    item_total = item_subtotal - item_discount_amount + item_tax_amount
                    item_profit = (unit_price - unit_cost) * qty - item_discount_amount
                    
                    sale_items.append({
                        'product_id': product['id'],
                        'quantity': qty,
                        'unit_id': item.get('unit_id', product.get('unit_id')),
                        'unit_cost': unit_cost,
                        'unit_price': unit_price,
                        'discount_percent': item_discount_percent,
                        'discount_amount': item_discount_amount,
                        'tax_percent': item_tax_percent,
                        'tax_amount': item_tax_amount,
                        'total_price': item_total,
                        'profit': item_profit
                    })
                    
                    subtotal += item_subtotal
                    total_cost += unit_cost * qty
                    
                except POSServiceError:
                    raise
                except Exception as e:
                    logger.error(f"❌ Error processing item {idx}: {e}")
                    raise POSServiceError(f"Error processing item {idx}: {e}")
            
            # Calculate total discount
            discount_total = Decimal('0')
            if discount_type == 'percent':
                discount_total = subtotal * discount_percent_dec / Decimal('100')
            elif discount_type == 'amount':
                discount_total = discount_value_dec
            elif discount_percent_dec > 0:
                discount_total = subtotal * discount_percent_dec / Decimal('100')
            
            # Calculate totals
            tax_total = sum(Decimal(str(item['tax_amount'])) for item in sale_items)
            total = subtotal - discount_total + tax_total
            profit = sum(Decimal(str(item['profit'])) for item in sale_items)
            
            # Calculate profit margin
            profit_margin = Decimal('0')
            if subtotal > 0:
                profit_margin = (profit / subtotal * Decimal('100')).quantize(Decimal('0.01'), ROUND_HALF_UP)
            
            # Generate invoice number
            invoice_number = self.generate_invoice_number()
            
            # Insert invoice
            sale_id = self.db.execute_insert(
                """INSERT INTO sales (
                    invoice_number, invoice_type, customer_id, user_id, branch_id, 
                    warehouse_id, currency_code, exchange_rate, subtotal, discount_total, 
                    tax_total, total, profit, profit_margin, discount_type, discount_value, 
                    status, payment_status, notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    invoice_number, 'sale', customer_id, user_id, branch_id,
                    warehouse_id, currency, float(rate),
                    float(subtotal), float(discount_total), float(tax_total), float(total),
                    float(profit), float(profit_margin),
                    discount_type or ('percent' if discount_percent > 0 else None),
                    float(discount_value or discount_percent),
                    'completed', 'pending', note, datetime.now().isoformat()
                )
            )
            
            # Insert sale items
            for si in sale_items:
                self.db.execute_insert(
                    """INSERT INTO sale_items (
                        sale_id, product_id, quantity, unit_id, unit_cost, unit_price,
                        discount_percent, discount_amount, tax_percent, tax_amount,
                        total_price, profit
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        sale_id, si['product_id'], float(si['quantity']), si['unit_id'],
                        float(si['unit_cost']), float(si['unit_price']),
                        float(si['discount_percent']), float(si['discount_amount']),
                        float(si['tax_percent']), float(si['tax_amount']),
                        float(si['total_price']), float(si['profit'])
                    )
                )
            
            # Deduct stock
            for item in items:
                try:
                    self.inventory_service.deduct_stock(
                        item['product_id'], 
                        Decimal(str(item.get('quantity', 1))), 
                        warehouse_id, 
                        sale_id, 
                        'sale'
                    )
                except Exception as e:
                    logger.error(f"⚠️ Stock deduction failed: {e}")
            
            # Process payments
            paid_amount = Decimal('0')
            if payments:
                for payment in payments:
                    try:
                        payment_amount = Decimal(str(payment.get('amount', 0)))
                        if payment_amount > 0:
                            self.treasury_service.record_payment(
                                sale_id, 'sale', payment
                            )
                            paid_amount += payment_amount
                    except Exception as e:
                        logger.warning(f"⚠️ Payment recording failed: {e}")
            
            # Update payment status
            remaining = total - paid_amount
            payment_status = 'paid'
            if remaining > 0:
                payment_status = 'partial' if paid_amount > 0 else 'unpaid'
            
            self.db.execute_update(
                "UPDATE sales SET payment_status = ?, paid = ?, remaining = ? WHERE id = ?",
                (payment_status, float(paid_amount), float(remaining), sale_id)
            )
            
            # Update customer balance if debt
            if remaining > 0 and customer_id:
                try:
                    self.db.execute_update(
                        "UPDATE customers SET balance = balance + ? WHERE id = ?",
                        (float(remaining), customer_id)
                    )
                    
                    # Record customer transaction
                    self.db.execute_insert(
                        """INSERT INTO customer_transactions (
                            customer_id, transaction_type, reference_type, reference_id,
                            debit, balance, currency_code, exchange_rate, user_id
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            customer_id, 'sale', 'sale', sale_id,
                            float(remaining), float(self._get_customer_balance(customer_id) + remaining),
                            currency, float(rate), user_id
                        )
                    )
                except Exception as e:
                    logger.warning(f"⚠️ Customer balance update failed: {e}")
            
            logger.info(f"✅ Invoice created: {invoice_number} (ID: {sale_id})")
            
            return {
                'sale_id': sale_id,
                'invoice_number': invoice_number,
                'subtotal': float(subtotal),
                'discount_total': float(discount_total),
                'tax_total': float(tax_total),
                'total': float(total),
                'paid': float(paid_amount),
                'remaining': float(remaining),
                'profit': float(profit),
                'profit_margin': float(profit_margin),
                'currency': currency
            }
                
        except POSServiceError:
            raise
        except Exception as e:
            logger.error(f"❌ Failed to create invoice: {e}")
            traceback.print_exc()
            raise POSServiceError(f"Failed to create invoice: {str(e)}") from e
    
    def _allow_negative_stock(self) -> bool:
        """Check if negative stock is allowed"""
        try:
            setting = self.db.execute_one(
                "SELECT setting_value FROM settings WHERE setting_key = ?",
                ('pos_allow_negative_stock',)
            )
            return setting and setting.get('setting_value') == '1'
        except:
            return False
    
    def _get_customer_balance(self, customer_id: int) -> Decimal:
        """Get customer current balance"""
        try:
            result = self.db.execute_one(
                "SELECT balance FROM customers WHERE id = ?",
                (customer_id,)
            )
            return Decimal(str(result['balance'])) if result else Decimal('0')
        except:
            return Decimal('0')
    
    def get_products_for_pos(self, category_id: Optional[int] = None, search: Optional[str] = None) -> List[Dict]:
        """
        Get products list for POS
        
        Args:
            category_id: Category ID (optional)
            search: Search text (optional)
            
        Returns:
            List of products
        """
        query = """
            SELECT 
                p.*, 
                c.name_ar as category_name, 
                b.name_ar as brand_name,
                u.abbreviation as unit_abbr
            FROM products p
            LEFT JOIN product_categories c ON p.category_id = c.id
            LEFT JOIN product_brands b ON p.brand_id = b.id
            LEFT JOIN units u ON p.unit_id = u.id
            WHERE p.is_active = 1
        """
        params = []
        
        if category_id:
            query += " AND p.category_id = ?"
            params.append(category_id)
        
        if search and search.strip():
            search_term = f"%{search.strip()}%"
            query += " AND (p.name_ar LIKE ? OR p.name_en LIKE ? OR p.barcode LIKE ? OR p.sku LIKE ?)"
            params.extend([search_term, search_term, search_term, search_term])
        
        query += " ORDER BY p.is_featured DESC, p.name_ar"
        
        try:
            results = self.db.execute(query, tuple(params))
            
            # Add stock information
            for product in results:
                try:
                    stock_info = self.inventory_service.get_product_stock_info(
                        product['id']
                    )
                    product['current_stock'] = stock_info.get('total_quantity', 0)
                    product['available_stock'] = stock_info.get('available_quantity', 0)
                except Exception as e:
                    logger.warning(f"⚠️ Failed to get stock info: {e}")
                    product['current_stock'] = 0
                    product['available_stock'] = 0
            
            return results
        except Exception as e:
            logger.error(f"❌ Failed to get products for POS: {e}")
            return []
    
    def hold_invoice(self, items: List[Dict], customer_id: Optional[int] = None, 
                     user_id: int = 1) -> str:
        """
        Hold an invoice for later resume
        
        Args:
            items: List of products
            customer_id: Customer ID
            user_id: User ID
            
        Returns:
            Hold number
        """
        try:
            today = datetime.now().strftime('%Y%m%d')
            count_result = self.db.execute_one(
                "SELECT COUNT(*) as cnt FROM held_sales WHERE DATE(created_at) = DATE('now')"
            )
            count_value = (count_result['cnt'] if count_result else 0) + 1
            hold_number = f"HLD-{today}-{count_value:04d}"
            
            # Convert items to JSON
            items_json = json.dumps(items, ensure_ascii=False, default=str)
            
            totals = {
                'items_count': len(items),
                'total_quantity': sum(float(item.get('quantity', 0)) for item in items),
                'created_at': datetime.now().isoformat()
            }
            totals_json = json.dumps(totals, ensure_ascii=False)
            
            self.db.execute_insert(
                """INSERT INTO held_sales 
                   (hold_number, customer_id, user_id, items_json, totals_json, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (hold_number, customer_id, user_id, items_json, totals_json, datetime.now().isoformat())
            )
            
            logger.info(f"✅ Invoice held: {hold_number}")
            return hold_number
            
        except Exception as e:
            logger.error(f"❌ Failed to hold invoice: {e}")
            raise POSServiceError(f"Failed to hold invoice: {str(e)}") from e
    
    def get_held_invoices(self, user_id: Optional[int] = None) -> List[Dict]:
        """
        Get list of held invoices
        
        Args:
            user_id: User ID (optional)
            
        Returns:
            List of held invoices
        """
        query = "SELECT * FROM held_sales WHERE 1=1"
        params = []
        
        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
        
        query += " ORDER BY created_at DESC"
        
        try:
            results = self.db.execute(query, tuple(params))
            
            # Convert JSON to dict
            for result in results:
                try:
                    if result.get('items_json'):
                        result['items'] = json.loads(result['items_json'])
                    if result.get('totals_json'):
                        result['totals'] = json.loads(result['totals_json'])
                except Exception as e:
                    logger.warning(f"⚠️ Failed to parse JSON: {e}")
                    result['items'] = []
                    result['totals'] = {}
            
            return results
        except Exception as e:
            logger.error(f"❌ Failed to get held invoices: {e}")
            return []
    
    def resume_held_invoice(self, hold_id: int) -> Dict:
        """
        Resume a held invoice
        
        Args:
            hold_id: Held invoice ID
            
        Returns:
            Resume invoice data
        """
        try:
            held = self.db.execute_one(
                "SELECT * FROM held_sales WHERE id = ?",
                (hold_id,)
            )
            
            if not held:
                raise POSServiceError("❌ Held invoice not found")
            
            items = json.loads(held.get('items_json', '[]'))
            
            # Delete after resume
            self.db.execute_update(
                "DELETE FROM held_sales WHERE id = ?",
                (hold_id,)
            )
            
            logger.info(f"✅ Invoice resumed: {held.get('hold_number')}")
            
            return {
                'items': items,
                'customer_id': held.get('customer_id'),
                'hold_number': held.get('hold_number')
            }
            
        except POSServiceError:
            raise
        except Exception as e:
            logger.error(f"❌ Failed to resume held invoice: {e}")
            raise POSServiceError(f"Failed to resume invoice: {str(e)}") from e
    
    def get_today_sales_summary(self, branch_id: Optional[int] = None) -> Dict:
        """
        Get today's sales summary
        
        Args:
            branch_id: Branch ID (optional)
            
        Returns:
            Sales summary
        """
        query = """
            SELECT 
                COUNT(*) as total_invoices,
                COALESCE(SUM(total), 0) as total_amount,
                COALESCE(SUM(profit), 0) as total_profit,
                COALESCE(AVG(profit_margin), 0) as avg_margin,
                COALESCE(SUM(CASE WHEN payment_status = 'paid' THEN total ELSE 0 END), 0) as cash_amount,
                COALESCE(SUM(CASE WHEN payment_status IN ('partial', 'unpaid') THEN remaining ELSE 0 END), 0) as debt_amount
            FROM sales
            WHERE DATE(created_at) = DATE('now')
            AND status = 'completed'
        """
        params = []
        
        if branch_id:
            query += " AND branch_id = ?"
            params.append(branch_id)
        
        try:
            result = self.db.execute_one(query, tuple(params))
            return result or {
                'total_invoices': 0,
                'total_amount': 0,
                'total_profit': 0,
                'avg_margin': 0,
                'cash_amount': 0,
                'debt_amount': 0
            }
        except Exception as e:
            logger.error(f"❌ Failed to get sales summary: {e}")
            return {}


if __name__ == "__main__":
    # Test standalone
    try:
        from core.database.connection import DatabaseManager
        
        db = DatabaseManager(":memory:")
        pos = POSService(db)
        print("✅ POSService initialized successfully")
    except Exception as e:
        print(f"❌ Error: {e}")
        traceback.print_exc()
