-- Assignment 4 SQL: Required functions and triggers for Ecommerce DB (PostgreSQL)
-- Assumes tables: products, customers, orders, orderitems, reviews already exist.

-- 1) Check product stock: returns TRUE if enough stock is available
CREATE OR REPLACE FUNCTION check_product_stock(
    p_product_id INT,
    p_requested_qty INT
) RETURNS BOOLEAN AS $$
DECLARE
    v_stock INT;
BEGIN
    SELECT stockquantity
    INTO v_stock
    FROM products
    WHERE productid = p_product_id;

    IF v_stock IS NULL THEN
        RETURN FALSE;
    END IF;

    IF v_stock >= p_requested_qty THEN
        RETURN TRUE;
    ELSE
        RETURN FALSE;
    END IF;
END;
$$ LANGUAGE plpgsql;


-- 2) Get restock alerts: products with stock below a threshold
CREATE OR REPLACE FUNCTION getrestockalerts(
    p_threshold INT
) RETURNS TABLE (
    productid INT,
    productname VARCHAR,
    stockquantity INT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.productid,
        p.productname,
        p.stockquantity
    FROM products p
    WHERE p.stockquantity < p_threshold
    ORDER BY p.stockquantity ASC;
END;
$$ LANGUAGE plpgsql;




-- 3) Place order: create order header and return new orderid
CREATE OR REPLACE FUNCTION placeorder(
    p_customer_id INT,
    p_shipping_address TEXT,
    p_payment_method TEXT
) RETURNS INT AS $$
DECLARE
    v_order_id INT;
BEGIN
    INSERT INTO orders (customerid, shippingaddress, paymentmethod)
    VALUES (p_customer_id, p_shipping_address, p_payment_method)
    RETURNING orderid INTO v_order_id;

    RETURN v_order_id;
END;
$$ LANGUAGE plpgsql;


-- 4) Calculate order total: sum of orderitems subtotals
CREATE OR REPLACE FUNCTION calculate_order_total(
    p_order_id INT
) RETURNS NUMERIC AS $$
DECLARE
    v_total NUMERIC(12,2);
BEGIN
    SELECT COALESCE(SUM(subtotal), 0)
    INTO v_total
    FROM orderitems
    WHERE orderid = p_order_id;

    UPDATE orders
    SET totalamount = v_total
    WHERE orderid = p_order_id;

    RETURN v_total;
END;
$$ LANGUAGE plpgsql;


-- Trigger to automatically recalculate total after orderitems change
CREATE OR REPLACE FUNCTION trg_orderitems_recalc_total()
RETURNS TRIGGER AS $$
DECLARE
    v_order_id INT;
BEGIN
    IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
        v_order_id := NEW.orderid;
    ELSE
        v_order_id := OLD.orderid;
    END IF;

    PERFORM calculate_order_total(v_order_id);
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS orderitems_recalc_total_after ON orderitems;

CREATE TRIGGER orderitems_recalc_total_after
AFTER INSERT OR UPDATE OR DELETE ON orderitems
FOR EACH ROW
EXECUTE FUNCTION trg_orderitems_recalc_total();


-- Trigger to keep product stock in sync and prevent overselling
CREATE OR REPLACE FUNCTION trg_orderitems_stock()
RETURNS TRIGGER AS $$
DECLARE
    v_diff INT;
BEGIN
    IF TG_OP = 'INSERT' THEN
        v_diff := NEW.quantity;

        IF NOT check_product_stock(NEW.productid, v_diff) THEN
            RAISE EXCEPTION 'Not enough stock for product %', NEW.productid;
        END IF;

        UPDATE products
        SET stockquantity = stockquantity - v_diff
        WHERE productid = NEW.productid;

        RETURN NEW;

    ELSIF TG_OP = 'UPDATE' THEN
        v_diff := NEW.quantity - OLD.quantity;

        IF v_diff > 0 THEN
            IF NOT check_product_stock(NEW.productid, v_diff) THEN
                RAISE EXCEPTION 'Not enough stock for product %', NEW.productid;
            END IF;

            UPDATE products
            SET stockquantity = stockquantity - v_diff
            WHERE productid = NEW.productid;

        ELSIF v_diff < 0 THEN
            UPDATE products
            SET stockquantity = stockquantity - v_diff  
            WHERE productid = NEW.productid;
        END IF;

        RETURN NEW;

    ELSIF TG_OP = 'DELETE' THEN
        UPDATE products
        SET stockquantity = stockquantity + OLD.quantity
        WHERE productid = OLD.productid;

        RETURN OLD;
    END IF;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS orderitems_stock_before ON orderitems;

CREATE TRIGGER orderitems_stock_before
BEFORE INSERT OR UPDATE OR DELETE ON orderitems
FOR EACH ROW
EXECUTE FUNCTION trg_orderitems_stock();
