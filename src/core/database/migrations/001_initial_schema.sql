-- ============================================================
-- PerfumeLab Pro ERP/POS Enterprise Edition
-- Database Schema v2.1 (FIXED & ENHANCED)
-- Multi-Currency | Arabic RTL | Production Ready
-- ============================================================

-- ============================================================
-- 1. CORE SYSTEM TABLES (ORDERED CORRECTLY)
-- ============================================================

-- الفروع
CREATE TABLE branches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name_ar VARCHAR(100) NOT NULL,
    name_en VARCHAR(100),
    address TEXT,
    phone VARCHAR(20),
    email VARCHAR(100),
    tax_number VARCHAR(50),
    commercial_register VARCHAR(50),
    manager_name VARCHAR(100),
    is_active BOOLEAN DEFAULT 1,
    is_main BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- العملات
CREATE TABLE currencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code VARCHAR(3) NOT NULL UNIQUE,
    name_ar VARCHAR(100) NOT NULL,
    name_en VARCHAR(100) NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    symbol_ar VARCHAR(10),
    decimal_places INTEGER DEFAULT 2,
    is_default BOOLEAN DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,
    position VARCHAR(10) DEFAULT 'after',
    exchange_rate_to_default DECIMAL(15,6),
    last_update TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- أسعار الصرف (مصحح)
CREATE TABLE exchange_rates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_currency VARCHAR(3) NOT NULL,
    to_currency VARCHAR(3) NOT NULL,
    rate DECIMAL(15,6) NOT NULL,
    inverse_rate DECIMAL(15,6) NOT NULL,
    source VARCHAR(50) DEFAULT 'manual',
    effective_date DATE NOT NULL,
    effective_time TIME DEFAULT '00:00:00',
    is_active BOOLEAN DEFAULT 1,
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_exchange_rates_currencies ON exchange_rates(from_currency, to_currency, effective_date);

-- الوحدات
CREATE TABLE units (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name_ar VARCHAR(50) NOT NULL,
    name_en VARCHAR(50),
    abbreviation VARCHAR(10),
    is_active BOOLEAN DEFAULT 1
);

-- البنوك (قبل cashboxes)
CREATE TABLE banks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name_ar VARCHAR(100) NOT NULL,
    name_en VARCHAR(100),
    swift_code VARCHAR(20),
    is_active BOOLEAN DEFAULT 1
);

-- الخزائن النقدية
CREATE TABLE cashboxes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name_ar VARCHAR(100) NOT NULL,
    name_en VARCHAR(100),
    currency_code VARCHAR(3) NOT NULL,
    branch_id INTEGER,
    opening_balance DECIMAL(15,2) DEFAULT 0,
    current_balance DECIMAL(15,2) DEFAULT 0,
    is_main BOOLEAN DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,
    FOREIGN KEY (currency_code) REFERENCES currencies(code),
    FOREIGN KEY (branch_id) REFERENCES branches(id)
);

-- الحسابات البنكية
CREATE TABLE bank_accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bank_id INTEGER NOT NULL,
    account_name_ar VARCHAR(100) NOT NULL,
    account_name_en VARCHAR(100),
    account_number VARCHAR(50),
    iban VARCHAR(50),
    currency_code VARCHAR(3) NOT NULL,
    branch_id INTEGER,
    current_balance DECIMAL(15,2) DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,
    FOREIGN KEY (bank_id) REFERENCES banks(id),
    FOREIGN KEY (currency_code) REFERENCES currencies(code),
    FOREIGN KEY (branch_id) REFERENCES branches(id)
);

-- ============================================================
-- 2. USERS & SECURITY
-- ============================================================

-- الأدوار
CREATE TABLE roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name_ar VARCHAR(50) NOT NULL,
    name_en VARCHAR(50),
    description TEXT,
    is_active BOOLEAN DEFAULT 1
);

-- المستخدمين (مصحح)
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name_ar VARCHAR(100) NOT NULL,
    full_name_en VARCHAR(100),
    email VARCHAR(100),
    phone VARCHAR(20),
    branch_id INTEGER,
    role_id INTEGER NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    last_login TIMESTAMP,
    last_password_change TIMESTAMP,
    failed_login_attempts INTEGER DEFAULT 0,
    is_locked BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (branch_id) REFERENCES branches(id),
    FOREIGN KEY (role_id) REFERENCES roles(id)
);

-- الصلاحيات
CREATE TABLE permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    module VARCHAR(50) NOT NULL,
    action VARCHAR(50) NOT NULL,
    name_ar VARCHAR(100) NOT NULL,
    name_en VARCHAR(100),
    description TEXT,
    UNIQUE(module, action)
);

-- صلاحيات الأدوار
CREATE TABLE role_permissions (
    role_id INTEGER NOT NULL,
    permission_id INTEGER NOT NULL,
    is_allowed BOOLEAN DEFAULT 0,
    PRIMARY KEY (role_id, permission_id),
    FOREIGN KEY (role_id) REFERENCES roles(id),
    FOREIGN KEY (permission_id) REFERENCES permissions(id)
);

-- سجل التدقيق
CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    action VARCHAR(100) NOT NULL,
    module VARCHAR(50) NOT NULL,
    record_id INTEGER,
    record_type VARCHAR(50),
    before_state TEXT,
    after_state TEXT,
    ip_address VARCHAR(45),
    device_info VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- ============================================================
-- 3. INVENTORY
-- ============================================================

-- الفئات
CREATE TABLE product_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name_ar VARCHAR(100) NOT NULL,
    name_en VARCHAR(100),
    parent_id INTEGER,
    description TEXT,
    is_active BOOLEAN DEFAULT 1,
    FOREIGN KEY (parent_id) REFERENCES product_categories(id)
);

-- الماركات
CREATE TABLE product_brands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name_ar VARCHAR(100) NOT NULL,
    name_en VARCHAR(100),
    logo_path VARCHAR(255),
    is_active BOOLEAN DEFAULT 1
);

-- المواد الخام (قبل المنتجات)
CREATE TABLE raw_materials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name_ar VARCHAR(200) NOT NULL,
    name_en VARCHAR(200),
    material_type VARCHAR(50),
    supplier_id INTEGER,
    unit_id INTEGER NOT NULL,
    current_stock DECIMAL(10,3) DEFAULT 0,
    minimum_stock DECIMAL(10,3) DEFAULT 0,
    cost_per_unit DECIMAL(15,4) DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
    FOREIGN KEY (unit_id) REFERENCES units(id)
);

-- المنتجات (مصحح)
CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name_ar VARCHAR(200) NOT NULL,
    name_en VARCHAR(200),
    sku VARCHAR(50) UNIQUE,
    barcode VARCHAR(50) UNIQUE,
    category_id INTEGER,
    brand_id INTEGER,
    unit_id INTEGER NOT NULL,
    supplier_id INTEGER,
    
    -- التسعير
    cost_price DECIMAL(15,4) DEFAULT 0,
    sale_price DECIMAL(15,4) DEFAULT 0,
    wholesale_price DECIMAL(15,4) DEFAULT 0,
    min_price DECIMAL(15,4) DEFAULT 0,
    
    -- المخزون
    current_stock DECIMAL(10,3) DEFAULT 0,
    minimum_stock DECIMAL(10,3) DEFAULT 0,
    maximum_stock DECIMAL(10,3) DEFAULT 0,
    reorder_point DECIMAL(10,3) DEFAULT 0,
    
    -- الضريبة
    tax_percent DECIMAL(5,2) DEFAULT 0,
    is_tax_inclusive BOOLEAN DEFAULT 0,
    
    -- العطور
    is_perfume BOOLEAN DEFAULT 0,
    concentration VARCHAR(20),
    volume_ml DECIMAL(8,2),
    gender VARCHAR(10),
    
    -- الحالة
    is_active BOOLEAN DEFAULT 1,
    is_featured BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (category_id) REFERENCES product_categories(id),
    FOREIGN KEY (brand_id) REFERENCES product_brands(id),
    FOREIGN KEY (unit_id) REFERENCES units(id),
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
);

-- المستودعات
CREATE TABLE warehouses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name_ar VARCHAR(100) NOT NULL,
    name_en VARCHAR(100),
    branch_id INTEGER,
    location TEXT,
    manager_id INTEGER,
    is_active BOOLEAN DEFAULT 1,
    FOREIGN KEY (branch_id) REFERENCES branches(id),
    FOREIGN KEY (manager_id) REFERENCES users(id)
);

-- مخزون المستودعات
CREATE TABLE warehouse_stock (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    warehouse_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity DECIMAL(10,3) DEFAULT 0,
    reserved_quantity DECIMAL(10,3) DEFAULT 0,
    available_quantity DECIMAL(10,3) DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(warehouse_id, product_id),
    FOREIGN KEY (warehouse_id) REFERENCES warehouses(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- الدفعات (مصحح)
CREATE TABLE stock_batches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    warehouse_id INTEGER NOT NULL,
    batch_number VARCHAR(50),
    batch_code VARCHAR(50) UNIQUE,
    quantity DECIMAL(10,3) DEFAULT 0,
    received_quantity DECIMAL(10,3),
    remaining_quantity DECIMAL(10,3),
    unit_cost DECIMAL(15,4) DEFAULT 0,
    expiry_date DATE,
    production_date DATE,
    supplier_id INTEGER,
    purchase_invoice_id INTEGER,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (warehouse_id) REFERENCES warehouses(id)
);

-- حركات المخزون
CREATE TABLE stock_movements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    warehouse_id INTEGER NOT NULL,
    batch_id INTEGER,
    movement_type VARCHAR(20) NOT NULL,
    quantity DECIMAL(10,3) NOT NULL,
    unit_cost DECIMAL(15,4),
    reference_type VARCHAR(50),
    reference_id INTEGER,
    notes TEXT,
    user_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (warehouse_id) REFERENCES warehouses(id),
    FOREIGN KEY (batch_id) REFERENCES stock_batches(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- تعديلات المخزون
CREATE TABLE stock_adjustments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    warehouse_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    batch_id INTEGER,
    adjustment_type VARCHAR(20) NOT NULL,
    quantity_before DECIMAL(10,3) NOT NULL,
    quantity_after DECIMAL(10,3) NOT NULL,
    difference DECIMAL(10,3) NOT NULL,
    reason TEXT,
    user_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (warehouse_id) REFERENCES warehouses(id),
    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- الجرد الدوري (جديد)
CREATE TABLE inventory_counts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    warehouse_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    expected_quantity DECIMAL(10,3),
    actual_quantity DECIMAL(10,3),
    difference DECIMAL(10,3),
    counted_by INTEGER,
    counted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'draft',
    FOREIGN KEY (warehouse_id) REFERENCES warehouses(id),
    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (counted_by) REFERENCES users(id)
);

-- إشعارات المخزون (جديد)
CREATE TABLE inventory_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    warehouse_id INTEGER NOT NULL,
    alert_type VARCHAR(20),
    threshold_value DECIMAL(10,3),
    current_value DECIMAL(10,3),
    is_resolved BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    resolved_by INTEGER,
    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (warehouse_id) REFERENCES warehouses(id),
    FOREIGN KEY (resolved_by) REFERENCES users(id)
);

-- ============================================================
-- 4. CUSTOMERS
-- ============================================================

-- مجموعات العملاء
CREATE TABLE customer_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name_ar VARCHAR(100) NOT NULL,
    name_en VARCHAR(100),
    discount_percent DECIMAL(5,2) DEFAULT 0,
    credit_limit DECIMAL(15,2) DEFAULT 0,
    credit_days INTEGER DEFAULT 0,
    points_per_currency DECIMAL(8,4) DEFAULT 1,
    is_active BOOLEAN DEFAULT 1
);

-- العملاء
CREATE TABLE customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name_ar VARCHAR(200) NOT NULL,
    name_en VARCHAR(200),
    phone VARCHAR(20),
    phone2 VARCHAR(20),
    email VARCHAR(100),
    group_id INTEGER,
    
    -- الحساب
    balance DECIMAL(15,2) DEFAULT 0,
    credit_limit DECIMAL(15,2) DEFAULT 0,
    credit_days INTEGER DEFAULT 0,
    
    -- الولاء
    loyalty_points DECIMAL(10,2) DEFAULT 0,
    total_points_earned DECIMAL(10,2) DEFAULT 0,
    total_points_redeemed DECIMAL(10,2) DEFAULT 0,
    
    -- العنوان
    address TEXT,
    city VARCHAR(50),
    country VARCHAR(50),
    
    -- الحالة
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (group_id) REFERENCES customer_groups(id)
);

-- عناوين العملاء
CREATE TABLE customer_addresses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    address_type VARCHAR(20) DEFAULT 'home',
    address TEXT NOT NULL,
    city VARCHAR(50),
    country VARCHAR(50),
    is_default BOOLEAN DEFAULT 0,
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

-- معاملات العملاء
CREATE TABLE customer_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    transaction_type VARCHAR(20) NOT NULL,
    reference_type VARCHAR(50),
    reference_id INTEGER,
    debit DECIMAL(15,2) DEFAULT 0,
    credit DECIMAL(15,2) DEFAULT 0,
    balance DECIMAL(15,2) DEFAULT 0,
    currency_code VARCHAR(3) NOT NULL,
    exchange_rate DECIMAL(15,6) DEFAULT 1,
    notes TEXT,
    user_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (currency_code) REFERENCES currencies(code),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- ============================================================
-- 5. SUPPLIERS
-- ============================================================

CREATE TABLE suppliers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name_ar VARCHAR(200) NOT NULL,
    name_en VARCHAR(200),
    contact_person VARCHAR(100),
    phone VARCHAR(20),
    phone2 VARCHAR(20),
    email VARCHAR(100),
    address TEXT,
    city VARCHAR(50),
    country VARCHAR(50),
    tax_number VARCHAR(50),
    commercial_register VARCHAR(50),
    balance DECIMAL(15,2) DEFAULT 0,
    credit_limit DECIMAL(15,2) DEFAULT 0,
    credit_days INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 6. SALES & POS
-- ============================================================

-- الفواتير
CREATE TABLE sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_number VARCHAR(50) NOT NULL UNIQUE,
    invoice_type VARCHAR(20) DEFAULT 'sale',
    
    -- العلاقات
    customer_id INTEGER,
    user_id INTEGER NOT NULL,
    branch_id INTEGER,
    warehouse_id INTEGER,
    
    -- العملة
    currency_code VARCHAR(3) NOT NULL,
    exchange_rate DECIMAL(15,6) DEFAULT 1,
    
    -- المبالغ
    subtotal DECIMAL(15,2) DEFAULT 0,
    discount_total DECIMAL(15,2) DEFAULT 0,
    tax_total DECIMAL(15,2) DEFAULT 0,
    total DECIMAL(15,2) DEFAULT 0,
    paid DECIMAL(15,2) DEFAULT 0,
    remaining DECIMAL(15,2) DEFAULT 0,
    
    -- المبالغ بالعملة الأجنبية
    foreign_subtotal DECIMAL(15,2),
    foreign_total DECIMAL(15,2),
    
    -- الربح
    profit DECIMAL(15,2) DEFAULT 0,
    profit_margin DECIMAL(5,2),
    
    -- الخصومات
    discount_type VARCHAR(20),
    discount_value DECIMAL(15,2) DEFAULT 0,
    coupon_code VARCHAR(50),
    
    -- الولاء
    points_earned DECIMAL(10,2) DEFAULT 0,
    points_redeemed DECIMAL(10,2) DEFAULT 0,
    points_value DECIMAL(15,2) DEFAULT 0,
    
    -- الحالة
    status VARCHAR(20) DEFAULT 'completed',
    payment_status VARCHAR(20) DEFAULT 'paid',
    
    -- التوقيت
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (branch_id) REFERENCES branches(id),
    FOREIGN KEY (warehouse_id) REFERENCES warehouses(id),
    FOREIGN KEY (currency_code) REFERENCES currencies(code)
);

-- عناصر الفاتورة
CREATE TABLE sale_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    batch_id INTEGER,
    
    -- الكمية
    quantity DECIMAL(10,3) NOT NULL,
    unit_id INTEGER NOT NULL,
    unit_conversion DECIMAL(10,4) DEFAULT 1,
    
    -- الأسعار
    unit_cost DECIMAL(15,4) NOT NULL,
    unit_price DECIMAL(15,4) NOT NULL,
    discount_percent DECIMAL(5,2) DEFAULT 0,
    discount_amount DECIMAL(15,2) DEFAULT 0,
    tax_percent DECIMAL(5,2) DEFAULT 0,
    tax_amount DECIMAL(15,2) DEFAULT 0,
    total_price DECIMAL(15,2) NOT NULL,
    
    -- الربح
    profit DECIMAL(15,2) DEFAULT 0,
    
    FOREIGN KEY (sale_id) REFERENCES sales(id),
    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (batch_id) REFERENCES stock_batches(id),
    FOREIGN KEY (unit_id) REFERENCES units(id)
);

-- مرتجعات المبيعات (جديد)
CREATE TABLE sales_returns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    original_sale_id INTEGER NOT NULL,
    return_number VARCHAR(50) NOT NULL UNIQUE,
    return_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reason TEXT,
    total_amount DECIMAL(15,2),
    restock_items BOOLEAN DEFAULT 1,
    user_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (original_sale_id) REFERENCES sales(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- مدفوعات الفاتورة
CREATE TABLE sale_payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_id INTEGER NOT NULL,
    payment_method VARCHAR(20) NOT NULL,
    cashbox_id INTEGER,
    bank_account_id INTEGER,
    
    currency_code VARCHAR(3) NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    exchange_rate DECIMAL(15,6) DEFAULT 1,
    base_amount DECIMAL(15,2),
    
    reference_number VARCHAR(100),
    notes TEXT,
    user_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (sale_id) REFERENCES sales(id),
    FOREIGN KEY (cashbox_id) REFERENCES cashboxes(id),
    FOREIGN KEY (bank_account_id) REFERENCES bank_accounts(id),
    FOREIGN KEY (currency_code) REFERENCES currencies(code),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- فواتير معلقة
CREATE TABLE held_sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hold_number VARCHAR(20) NOT NULL,
    customer_id INTEGER,
    user_id INTEGER NOT NULL,
    items_json TEXT NOT NULL,
    totals_json TEXT NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- ============================================================
-- 7. PURCHASES
-- ============================================================

CREATE TABLE purchases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_number VARCHAR(50) NOT NULL UNIQUE,
    supplier_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    branch_id INTEGER,
    warehouse_id INTEGER,
    
    currency_code VARCHAR(3) NOT NULL,
    exchange_rate DECIMAL(15,6) DEFAULT 1,
    
    subtotal DECIMAL(15,2) DEFAULT 0,
    discount_total DECIMAL(15,2) DEFAULT 0,
    tax_total DECIMAL(15,2) DEFAULT 0,
    shipping_cost DECIMAL(15,2) DEFAULT 0,
    total DECIMAL(15,2) DEFAULT 0,
    paid DECIMAL(15,2) DEFAULT 0,
    remaining DECIMAL(15,2) DEFAULT 0,
    
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (currency_code) REFERENCES currencies(code)
);

CREATE TABLE purchase_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    purchase_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity DECIMAL(10,3) NOT NULL,
    unit_id INTEGER NOT NULL,
    unit_cost DECIMAL(15,4) NOT NULL,
    discount_percent DECIMAL(5,2) DEFAULT 0,
    tax_percent DECIMAL(5,2) DEFAULT 0,
    total_cost DECIMAL(15,2) NOT NULL,
    FOREIGN KEY (purchase_id) REFERENCES purchases(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- مرتجعات المشتريات (جديد)
CREATE TABLE purchase_returns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    original_purchase_id INTEGER NOT NULL,
    return_number VARCHAR(50) NOT NULL UNIQUE,
    return_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reason TEXT,
    total_amount DECIMAL(15,2),
    user_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (original_purchase_id) REFERENCES purchases(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- ============================================================
-- 8. TREASURY
-- ============================================================

-- سندات القبض
CREATE TABLE receipts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    receipt_number VARCHAR(50) NOT NULL UNIQUE,
    receipt_type VARCHAR(20) DEFAULT 'customer',
    
    from_entity_id INTEGER,
    from_entity_type VARCHAR(20),
    
    to_cashbox_id INTEGER,
    to_bank_account_id INTEGER,
    
    currency_code VARCHAR(3) NOT NULL,
    exchange_rate DECIMAL(15,6) DEFAULT 1,
    amount DECIMAL(15,2) NOT NULL,
    base_amount DECIMAL(15,2),
    
    payment_method VARCHAR(20) NOT NULL,
    reference_number VARCHAR(100),
    cheque_date DATE,
    
    notes TEXT,
    user_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (to_cashbox_id) REFERENCES cashboxes(id),
    FOREIGN KEY (to_bank_account_id) REFERENCES bank_accounts(id),
    FOREIGN KEY (currency_code) REFERENCES currencies(code),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- سندات الصرف
CREATE TABLE payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    payment_number VARCHAR(50) NOT NULL UNIQUE,
    payment_type VARCHAR(20) DEFAULT 'supplier',
    
    to_entity_id INTEGER,
    to_entity_type VARCHAR(20),
    
    from_cashbox_id INTEGER,
    from_bank_account_id INTEGER,
    
    currency_code VARCHAR(3) NOT NULL,
    exchange_rate DECIMAL(15,6) DEFAULT 1,
    amount DECIMAL(15,2) NOT NULL,
    base_amount DECIMAL(15,2),
    
    payment_method VARCHAR(20) NOT NULL,
    reference_number VARCHAR(100),
    
    notes TEXT,
    user_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (from_cashbox_id) REFERENCES cashboxes(id),
    FOREIGN KEY (from_bank_account_id) REFERENCES bank_accounts(id),
    FOREIGN KEY (currency_code) REFERENCES currencies(code),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- معاملات الخزينة
CREATE TABLE treasury_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_type VARCHAR(20) NOT NULL,
    
    from_cashbox_id INTEGER,
    from_bank_account_id INTEGER,
    to_cashbox_id INTEGER,
    to_bank_account_id INTEGER,
    
    currency_code VARCHAR(3) NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    exchange_rate DECIMAL(15,6) DEFAULT 1,
    base_amount DECIMAL(15,2),
    
    reference_type VARCHAR(50),
    reference_id INTEGER,
    
    notes TEXT,
    user_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (from_cashbox_id) REFERENCES cashboxes(id),
    FOREIGN KEY (from_bank_account_id) REFERENCES bank_accounts(id),
    FOREIGN KEY (to_cashbox_id) REFERENCES cashboxes(id),
    FOREIGN KEY (to_bank_account_id) REFERENCES bank_accounts(id),
    FOREIGN KEY (currency_code) REFERENCES currencies(code),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- ============================================================
-- 9. MANUFACTURING
-- ============================================================

-- الوصفات (مصححة)
CREATE TABLE recipes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name_ar VARCHAR(200) NOT NULL,
    name_en VARCHAR(200),
    product_id INTEGER,
    category_id INTEGER,
    volume_ml DECIMAL(8,2) NOT NULL,
    concentration VARCHAR(20),
    batch_size DECIMAL(10,3),
    wastage_percent DECIMAL(5,2) DEFAULT 0,
    total_cost DECIMAL(15,4) DEFAULT 0,
    notes TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (category_id) REFERENCES product_categories(id)
);

-- مكونات الوصفة
CREATE TABLE recipe_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipe_id INTEGER NOT NULL,
    raw_material_id INTEGER NOT NULL,
    quantity_ml DECIMAL(10,3) NOT NULL,
    percentage DECIMAL(5,2) DEFAULT 0,
    cost DECIMAL(15,4) DEFAULT 0,
    notes TEXT,
    FOREIGN KEY (recipe_id) REFERENCES recipes(id),
    FOREIGN KEY (raw_material_id) REFERENCES raw_materials(id)
);

-- أوامر الإنتاج
CREATE TABLE production_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_number VARCHAR(50) NOT NULL UNIQUE,
    recipe_id INTEGER NOT NULL,
    quantity DECIMAL(10,3) NOT NULL,
    unit_id INTEGER NOT NULL,
    
    -- التكاليف
    materials_cost DECIMAL(15,2) DEFAULT 0,
    labor_cost DECIMAL(15,2) DEFAULT 0,
    overhead_cost DECIMAL(15,2) DEFAULT 0,
    total_cost DECIMAL(15,2) DEFAULT 0,
    
    -- الحالة
    status VARCHAR(20) DEFAULT 'pending',
    
    -- التوقيت
    planned_start DATE,
    planned_end DATE,
    actual_start TIMESTAMP,
    actual_end TIMESTAMP,
    
    user_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (recipe_id) REFERENCES recipes(id),
    FOREIGN KEY (unit_id) REFERENCES units(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- استهلاك الإنتاج (مصحح)
CREATE TABLE production_consumption (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    production_order_id INTEGER NOT NULL,
    raw_material_id INTEGER NOT NULL,
    planned_quantity DECIMAL(10,3) NOT NULL,
    actual_quantity DECIMAL(10,3) NOT NULL,
    cost DECIMAL(15,4) DEFAULT 0,
    unit_cost_at_time DECIMAL(15,4),
    notes TEXT,
    FOREIGN KEY (production_order_id) REFERENCES production_orders(id),
    FOREIGN KEY (raw_material_id) REFERENCES raw_materials(id)
);

-- دفعات الإنتاج
CREATE TABLE production_batches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    production_order_id INTEGER NOT NULL,
    batch_number VARCHAR(50) NOT NULL,
    product_id INTEGER NOT NULL,
    quantity DECIMAL(10,3) NOT NULL,
    unit_cost DECIMAL(15,4) DEFAULT 0,
    expiry_date DATE,
    quality_status VARCHAR(20) DEFAULT 'pending',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (production_order_id) REFERENCES production_orders(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- ============================================================
-- 10. LOYALTY & CRM
-- ============================================================

-- برنامج الولاء
CREATE TABLE loyalty_programs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name_ar VARCHAR(100) NOT NULL,
    name_en VARCHAR(100),
    points_per_currency DECIMAL(8,4) DEFAULT 1,
    currency_per_point DECIMAL(8,4) DEFAULT 0.01,
    minimum_redeem_points DECIMAL(10,2) DEFAULT 100,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- قسائم الخصم
CREATE TABLE coupons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code VARCHAR(50) NOT NULL UNIQUE,
    name_ar VARCHAR(100),
    discount_type VARCHAR(20) NOT NULL,
    discount_value DECIMAL(15,2) NOT NULL,
    minimum_purchase DECIMAL(15,2) DEFAULT 0,
    maximum_discount DECIMAL(15,2),
    usage_limit INTEGER,
    usage_count INTEGER DEFAULT 0,
    start_date DATE,
    end_date DATE,
    is_active BOOLEAN DEFAULT 1
);

-- بطاقات الهدايا
CREATE TABLE gift_cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    card_number VARCHAR(50) NOT NULL UNIQUE,
    initial_balance DECIMAL(15,2) NOT NULL,
    current_balance DECIMAL(15,2) DEFAULT 0,
    currency_code VARCHAR(3) NOT NULL,
    expiry_date DATE,
    customer_id INTEGER,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (currency_code) REFERENCES currencies(code),
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

-- ============================================================
-- 11. TAX SYSTEM (جديد)
-- ============================================================

-- معدلات الضريبة
CREATE TABLE tax_rates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name_ar VARCHAR(100),
    name_en VARCHAR(100),
    tax_percent DECIMAL(5,2) NOT NULL,
    applies_to VARCHAR(50) DEFAULT 'all',
    start_date DATE,
    end_date DATE,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ضرائب المنتجات
CREATE TABLE product_taxes (
    product_id INTEGER NOT NULL,
    tax_rate_id INTEGER NOT NULL,
    PRIMARY KEY (product_id, tax_rate_id),
    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (tax_rate_id) REFERENCES tax_rates(id)
);

-- ============================================================
-- 12. FINANCIAL & BACKUP (جديد)
-- ============================================================

-- الإقفال المالي
CREATE TABLE fiscal_closing (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    closing_date DATE NOT NULL,
    closing_type VARCHAR(20),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    total_revenue DECIMAL(15,2),
    total_expenses DECIMAL(15,2),
    net_profit DECIMAL(15,2),
    closed_by INTEGER,
    is_locked BOOLEAN DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (closed_by) REFERENCES users(id)
);

-- ============================================================
-- 13. SETTINGS
-- ============================================================

CREATE TABLE settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    setting_key VARCHAR(100) NOT NULL UNIQUE,
    setting_value TEXT,
    setting_group VARCHAR(50) NOT NULL,
    description TEXT,
    is_encrypted BOOLEAN DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 14. INDEXES (مكثفة)
-- ============================================================

-- فهارس المبيعات
CREATE INDEX idx_sales_date ON sales(created_at);
CREATE INDEX idx_sales_customer ON sales(customer_id);
CREATE INDEX idx_sales_status ON sales(status);
CREATE INDEX idx_sales_invoice ON sales(invoice_number);

-- فهارس عناصر المبيعات
CREATE INDEX idx_sale_items_sale ON sale_items(sale_id);
CREATE INDEX idx_sale_items_product ON sale_items(product_id);

-- فهارس المشتريات
CREATE INDEX idx_purchases_supplier ON purchases(supplier_id);
CREATE INDEX idx_purchases_date ON purchases(created_at);
CREATE INDEX idx_purchases_invoice ON purchases(invoice_number);

-- فهارس المنتجات
CREATE INDEX idx_products_barcode ON products(barcode);
CREATE INDEX idx_products_sku ON products(sku);
CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_products_supplier ON products(supplier_id);

-- فهارس المخزون
CREATE INDEX idx_stock_movements_product ON stock_movements(product_id);
CREATE INDEX idx_stock_movements_date ON stock_movements(created_at);
CREATE INDEX idx_stock_movements_batch ON stock_movements(batch_id);
CREATE INDEX idx_warehouse_stock_warehouse ON warehouse_stock(warehouse_id);
CREATE INDEX idx_stock_batches_product ON stock_batches(product_id);
CREATE INDEX idx_stock_batches_batch_code ON stock_batches(batch_code);

-- فهارس العملاء والموردين
CREATE INDEX idx_customers_phone ON customers(phone);
CREATE INDEX idx_customers_group ON customers(group_id);
CREATE INDEX idx_suppliers_phone ON suppliers(phone);

-- فهارس الخزينة
CREATE INDEX idx_treasury_transactions_date ON treasury_transactions(created_at);
CREATE INDEX idx_receipts_date ON receipts(created_at);
CREATE INDEX idx_payments_date ON payments(created_at);

-- فهارس التدقيق
CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_date ON audit_logs(created_at);
CREATE INDEX idx_audit_logs_module ON audit_logs(module);

-- فهارس التصنيع
CREATE INDEX idx_production_orders_status ON production_orders(status);
CREATE INDEX idx_production_orders_date ON production_orders(created_at);
CREATE INDEX idx_recipe_items_recipe ON recipe_items(recipe_id);
CREATE INDEX idx_production_batches_product ON production_batches(product_id);
CREATE INDEX idx_production_batches_batch ON production_batches(batch_number);

-- ============================================================
-- 15. DEFAULT DATA (مصححة)
-- ============================================================

-- العملات الافتراضية
INSERT INTO currencies (code, name_ar, name_en, symbol, symbol_ar, is_default, is_active) VALUES
('USD', 'الدولار الأمريكي', 'US Dollar', '$', 'د.أ', 1, 1),
('EUR', 'اليورو', 'Euro', '€', 'يورو', 0, 1),
('SAR', 'الريال السعودي', 'Saudi Riyal', 'SR', 'ر.س', 0, 1),
('AED', 'الدرهم الإماراتي', 'UAE Dirham', 'AED', 'د.إ', 0, 1),
('EGP', 'الجنيه المصري', 'Egyptian Pound', 'EGP', 'ج.م', 0, 1),
('KWD', 'الدينار الكويتي', 'Kuwaiti Dinar', 'KD', 'د.ك', 0, 1),
('QAR', 'الريال القطري', 'Qatari Riyal', 'QR', 'ر.ق', 0, 1),
('BHD', 'الدينار البحريني', 'Bahraini Dinar', 'BD', 'د.ب', 0, 1),
('OMR', 'الريال العماني', 'Omani Rial', 'OMR', 'ر.ع', 0, 1);

-- الوحدات الافتراضية (مصححة - بدون تكرار)
INSERT INTO units (name_ar, name_en, abbreviation) VALUES
('قطعة', 'Piece', 'pc'),
('مليلتر', 'Milliliter', 'ml'),
('لتر', 'Liter', 'L'),
('جرام', 'Gram', 'g'),
('كيلوجرام', 'Kilogram', 'kg'),
('علبة', 'Box', 'box'),
('كرتونة', 'Carton', 'ctn');

-- الأدوار الافتراضية
INSERT INTO roles (name_ar, name_en, description) VALUES
('مدير النظام', 'System Administrator', 'صلاحيات كاملة'),
('مدير الفرع', 'Branch Manager', 'إدارة الفرع'),
('كاشير', 'Cashier', 'نقطة البيع'),
('أمين المخزن', 'Inventory Manager', 'إدارة المخزون'),
('محاسب', 'Accountant', 'الحسابات والخزينة');

-- الصلاحيات (مكتملة)
INSERT INTO permissions (module, action, name_ar, name_en) VALUES
-- نقاط البيع
('pos', 'change_price', 'تغيير السعر', 'Change Price'),
('pos', 'delete_item', 'حذف صنف من الفاتورة', 'Delete Item'),
('pos', 'apply_return', 'إجراء مرتجع', 'Process Return'),
('pos', 'apply_discount', 'تطبيق خصم', 'Apply Discount'),
('pos', 'sell_on_debt', 'البيع بالآجل', 'Sell on Credit'),
('pos', 'cancel_invoice', 'إلغاء فاتورة', 'Cancel Invoice'),
('pos', 'reprint', 'إعادة طباعة', 'Reprint'),
('pos', 'open_drawer', 'فتح الدرج', 'Open Drawer'),
('pos', 'view_profit', 'عرض الربح', 'View Profit'),
-- المخزون
('inventory', 'adjust_stock', 'تعديل المخزون', 'Adjust Stock'),
('inventory', 'view_cost', 'عرض التكلفة', 'View Cost'),
('inventory', 'count_inventory', 'جرد المخزون', 'Count Inventory'),
('inventory', 'transfer_stock', 'نقل مخزون', 'Transfer Stock'),
-- الخزينة
('treasury', 'transfer', 'تحويل بين الخزائن', 'Transfer'),
('treasury', 'manage_cashboxes', 'إدارة الخزائن', 'Manage Cashboxes'),
-- التقارير
('reports', 'view_profit', 'عرض الأرباح', 'View Profits'),
('reports', 'view_all_reports', 'عرض كل التقارير', 'View All Reports'),
-- الإعدادات
('settings', 'manage_users', 'إدارة المستخدمين', 'Manage Users'),
('settings', 'manage_currencies', 'إدارة العملات', 'Manage Currencies'),
('settings', 'manage_branches', 'إدارة الفروع', 'Manage Branches'),
('settings', 'system_backup', 'النسخ الاحتياطي', 'System Backup'),
-- التصنيع
('manufacturing', 'create_recipe', 'إنشاء وصفة', 'Create Recipe'),
('manufacturing', 'modify_recipe', 'تعديل وصفة', 'Modify Recipe'),
('manufacturing', 'delete_recipe', 'حذف وصفة', 'Delete Recipe'),
('manufacturing', 'start_production', 'بدء إنتاج', 'Start Production'),
('manufacturing', 'complete_production', 'إنهاء إنتاج', 'Complete Production'),
('manufacturing', 'view_costs', 'عرض تكاليف التصنيع', 'View Manufacturing Costs');

-- إعدادات النظام (مكتملة)
INSERT INTO settings (setting_key, setting_value, setting_group, description) VALUES
('company_name_ar', 'عطر لاب برو', 'company', 'اسم الشركة بالعربية'),
('company_name_en', 'PerfumeLab Pro', 'company', 'اسم الشركة بالإنجليزية'),
('company_phone', '', 'company', 'هاتف الشركة'),
('company_address', '', 'company', 'عنوان الشركة'),
('company_tax_number', '', 'company', 'الرقم الضريبي'),
('pos_default_currency', 'USD', 'pos', 'العملة الافتراضية للنقاط'),
('pos_allow_negative_stock', '0', 'pos', 'السماح بالمخزون السالب'),
('pos_allow_debt', '1', 'pos', 'السماح بالبيع بالآجل'),
('pos_max_discount_percent', '50', 'pos', 'الحد الأقصى للخصم'),
('pos_receipt_printer', '80mm', 'pos', 'طابعة الإيصالات'),
('inventory_default_warehouse', '1', 'inventory', 'المستودع الافتراضي'),
('tax_default_percent', '15', 'tax', 'نسبة الضريبة الافتراضية'),
('loyalty_enabled', '1', 'loyalty', 'تفعيل برنامج الولاء'),
('loyalty_points_per_currency', '1', 'loyalty', 'النقاط لكل وحدة عملة'),
('manufacturing_enabled', '1', 'manufacturing', 'تفعيل نظام التصنيع'),
('manufacturing_auto_update_cost', '1', 'manufacturing', 'تحديث تكلفة المنتج تلقائياً'),
('backup_auto_enabled', '1', 'backup', 'تفعيل النسخ الاحتياطي التلقائي'),
('backup_frequency', 'daily', 'backup', 'تكرار النسخ الاحتياطي'),
('backup_keep_days', '30', 'backup', 'الاحتفاظ بالنسخ الاحتياطية (أيام)');

-- الفرع الرئيسي
INSERT INTO branches (name_ar, name_en, is_main, is_active) VALUES
('الفرع الرئيسي', 'Main Branch', 1, 1);

-- الخزينة الافتراضية
INSERT INTO cashboxes (name_ar, name_en, currency_code, branch_id, is_main, is_active) VALUES
('الخزينة الرئيسية - دولار', 'Main Cashbox - USD', 'USD', 1, 1, 1),
('الخزينة الرئيسية - ريال', 'Main Cashbox - SAR', 'SAR', 1, 0, 1);

-- برنامج الولاء الافتراضي
INSERT INTO loyalty_programs (name_ar, name_en, points_per_currency, currency_per_point, minimum_redeem_points, is_active) VALUES
('برنامج الولاء القياسي', 'Standard Loyalty Program', 1, 0.01, 100, 1);

-- معدلات الضريبة الافتراضية
INSERT INTO tax_rates (name_ar, name_en, tax_percent, applies_to, is_active) VALUES
('ضريبة القيمة المضافة', 'Value Added Tax (VAT)', 15, 'all', 1),
('ضريبة السلع الكمالية', 'Luxury Tax', 50, 'products', 1);

-- ============================================================
-- 16. TRIGGERS (اختياري للتحسين)
-- ============================================================

-- تحديث available_quantity تلقائياً
CREATE TRIGGER update_available_quantity 
AFTER UPDATE OF quantity, reserved_quantity ON warehouse_stock
BEGIN
    UPDATE warehouse_stock 
    SET available_quantity = NEW.quantity - NEW.reserved_quantity 
    WHERE id = NEW.id;
END;

-- تحديث updated_at في المنتجات
CREATE TRIGGER update_products_timestamp 
AFTER UPDATE ON products
BEGIN
    UPDATE products SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- تحديث updated_at في الإعدادات
CREATE TRIGGER update_settings_timestamp 
AFTER UPDATE ON settings
BEGIN
    UPDATE settings SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- ============================================================
-- تم التصحيح والتحسين بنجاح
-- الإصدار: 2.1 (FINAL)
-- ============================================================
