-- Create the test database
--CREATE DATABASE Ecommerce;

-- Connect to the database
--\c Ecommerce

-- 1. Customers table
CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_purchase_date DATE
);

-- 2. Categories table
CREATE TABLE categories (
    category_id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    description TEXT,
    parent_category_id INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_category_id) REFERENCES categories(category_id)
);

-- 3. Products table (linked to categories)
CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL CHECK (price >= 0),
    stock_quantity INTEGER NOT NULL CHECK (stock_quantity >= 0),
    category_id INTEGER,
    FOREIGN KEY (category_id) REFERENCES categories(category_id)
);

-- 4. Orders table (linked to customers)
CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('Completed', 'Processing', 'Pending', 'Cancelled')),
    shipping_address TEXT,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- 5. Order Items table (linked to orders and products)
CREATE TABLE order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price DECIMAL(10,2) NOT NULL CHECK (unit_price >= 0),
    subtotal DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- Create indexes for optimization
CREATE INDEX idx_customers_email ON customers(email);
CREATE INDEX idx_orders_customer_id ON orders(customer_id);
CREATE INDEX idx_orders_date ON orders(order_date DESC);
CREATE INDEX idx_order_items_order_id ON order_items(order_id);
CREATE INDEX idx_order_items_product_id ON order_items(product_id);
CREATE INDEX idx_products_category ON products(category_id);

-- Insert sample data for customers (1000 records)
INSERT INTO customers (first_name, last_name, email, phone, created_at, last_purchase_date)
SELECT 
    'First' || n,
    'Last' || n,
    'user' || n || '@example.com',
    '555-0' || LPAD(n::text, 3, '0'),
    CURRENT_TIMESTAMP - INTERVAL '1 day' * (random() * 365),
    CURRENT_DATE - (random() * 30)::integer
FROM generate_series(1, 1000) n;

-- Insert sample data for categories (100 records)
INSERT INTO categories (name, description, parent_category_id, is_active)
SELECT 
    'Category' || n,
    'Description for category ' || n,
    CASE 
        WHEN n > 5 AND random() > 0.2 THEN ((random() * (n-1))::integer + 1)  -- Valid IDs from 1 to n-1
        ELSE 6 
    END,
    TRUE
FROM generate_series(1, 100) n;

-- Insert sample data for products (1000 records, linked to categories)
INSERT INTO products (name, description, price, stock_quantity, category_id)
SELECT 
    'Product' || n,
    'Description for product ' || n,
    (random() * 999 + 1)::decimal(10,2),
    (random() * 100)::integer,
    ((n - 1) % 100 + 1)::integer  -- Ensures category_id is between 1 and 100
FROM generate_series(1, 1000) n;

-- Insert sample data for orders (1000 records, linked to customers)
INSERT INTO orders (customer_id, total_amount, status, shipping_address)
SELECT 
    ((n - 1) % 1000 + 1)::integer,  -- Ensures customer_id is between 1 and 1000
    (random() * 1000 + 50)::decimal(10,2),
    CASE 
        WHEN random() < 0.7 THEN 'Completed'
        WHEN random() < 0.85 THEN 'Processing'
        WHEN random() < 0.95 THEN 'Pending'
        ELSE 'Cancelled'
    END,
    'Address ' || n || ', Sample City'
FROM generate_series(1, 1000) n;

-- Insert sample data for order_items (1000 records, linked to orders and products)
INSERT INTO order_items (order_id, product_id, quantity, unit_price, subtotal)
SELECT 
    o.order_id,
    p.product_id,
    (random() * 5 + 1)::integer AS quantity,
    p.price AS unit_price,
    (random() * 5 + 1)::integer * p.price AS subtotal
FROM orders o
CROSS JOIN LATERAL (
    SELECT product_id, price 
    FROM products 
    ORDER BY random() 
    LIMIT 1
) p
WHERE o.order_id IN (SELECT order_id FROM orders ORDER BY random() LIMIT 1000);

-- Create a view for customer order summary
CREATE OR REPLACE VIEW customer_order_summary AS
SELECT 
    c.customer_id,
    c.first_name,
    c.last_name,
    c.email,
    COUNT(o.order_id) AS total_orders,
    COALESCE(SUM(o.total_amount), 0) AS total_spent
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.first_name, c.last_name, c.email;

-- Create a materialized view for performance optimization
CREATE MATERIALIZED VIEW customer_order_summary_mat AS
SELECT 
    c.customer_id,
    c.first_name,
    c.last_name,
    c.email,
    COUNT(o.order_id) AS total_orders,
    COALESCE(SUM(o.total_amount), 0) AS total_spent
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.first_name, c.last_name, c.email;

-- Analyze tables for performance optimization
ANALYZE;
