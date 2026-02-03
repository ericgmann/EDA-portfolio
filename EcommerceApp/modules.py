from psycopg2 import Error

# //**** HELPER ******//

def q(conn, query, params=None, fetchone=False, fetchall=False):
    try:
        with conn.cursor() as cur:
            cur.execute(query, params or ())
            if fetchone: return cur.fetchone()
            if fetchall: return cur.fetchall()
    except Error as e:
        conn.rollback()
        print("Database error:", e)
        return None

#//**************** PRODUCT MANAGEMENT *****************//
def search_products(conn):
    name = input("Name search: ").strip().lower()
    rows = q(conn,
        """
        SELECT * FROM products
        WHERE lower(productname) LIKE %s AND isactive = TRUE;
        """,
        (f"%{name}%",),
        fetchall=True
    )
    for r in rows or []:
        print(r)

def filter_by_category(conn):
    cat = input("Category: ").strip().lower()
    rows = q(conn,
        """
        SELECT *
        FROM products p
        JOIN categories c ON p.categoryid = c.categoryid
        WHERE lower(c.categoryname) = %s AND p.isactive = TRUE;
        """,
        (cat,),
        fetchall=True
    )
    for r in rows or []:
        print(r)

def product_details(conn):
    productid = input("Product ID: ")
    row = q(conn,
        """
        SELECT * FROM products
        WHERE productid = %s;
        """,
        (productid,),
        fetchone=True
    )
    print(row or "Not found.")

def low_stock_alerts(conn):
    threshold = 50  
    rows = q(conn,
        "SELECT * FROM getrestockalerts(%s);",
        (threshold,),
        fetchall=True
    )
    for r in rows or []:
        print(r)


def add_product(conn):
    try:
        data = (
            int(input("Product ID: ")),          # productid
            input("Product Name: "),             # productname
            int(input("Category ID: ")),         # categoryid
            float(input("Price: ")),             # price
            int(input("Stock Quantity: ")),      # stockquantity
            input("Description: "),              # description
            input("Brand: "),                    # brand
            float(input("Weight: "))             # weight
        )
    except:
        print("Invalid input.")
        return

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO products
                (productid, productname, categoryid, price, stockquantity, description, brand, weight, isactive)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,TRUE);
                """,
                data
            )
        conn.commit()
        print("Product added.")
    except Exception as e:
        conn.rollback()
        print("Error adding product:", e)

def update_product(conn):
    pid = input("Product ID: ")
    print("1 Price  2 Stock  3 Description")
    choice = input("Choose: ").strip()

    match choice:
        case "1":
            val = float(input("New price: "))
            sql = "UPDATE products SET price=%s WHERE productid=%s"
        case "2":
            val = int(input("New stock: "))
            sql = "UPDATE products SET stockqty=%s WHERE productid=%s"
        case "3":
            val = input("New description: ")
            sql = "UPDATE products SET description=%s WHERE productid=%s"
        case _:
            return

    try:
        with conn.cursor() as cur:
            cur.execute(sql, (val, pid))
        conn.commit()
        print("Updated.")
    except:
        conn.rollback()

def toggle_product_active(conn):
    pid = input("Product ID: ")
    row = q(conn, "SELECT isactive FROM products WHERE productid=%s;", (pid,), fetchone=True)
    if not row:
        print("Not found.")
        return

    new = not row[0]
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE products SET isactive=%s WHERE productid=%s;", (new, pid))
        conn.commit()
        print("Active set to", new)
    except:
        conn.rollback()

# //******************** CUSTOMER MANAGEMENT ************************//

def register_customer(conn):
    data = (
       input("CustomerID: "), input("First name: "), input("Last name: "), input("Email: "), input("Phone: "), input("date of birth: ")
    )
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO customers(customerid, firstname, lastname, email, phone, dateofbirth, isactive)
                VALUES (%s,%s,%s,%s,%s,%s, TRUE);
            """, data)
        conn.commit()
        print("Customer added.")
    except:
        conn.rollback()
        print("Error registering.")

def update_customer_info(conn):
    cid = input("Customer ID: ")
    print("1 Phone  2 Email")
    match input("Choose: "):
        case "1":
            val = input("New phone: ")
            sql = "UPDATE customers SET phone=%s WHERE customerid=%s"
        case "2":
            val = input("New email: ")
            sql = "UPDATE customers SET email=%s WHERE customerid=%s"
        case _:
            return

    try:
        with conn.cursor() as cur:
            cur.execute(sql, (val, cid))
        conn.commit()
        print("Updated.")
    except:
        conn.rollback()

def view_customer_profile(conn):
    customerid = input("Customer ID: ")
    row = q(conn,
        """
        SELECT *
        FROM customers
        WHERE customerid = %s;
        """,
        (customerid,),
        fetchone=True
    )
    print(row or "Not found.")

def deactivate_customer(conn):
    cid = input("Customer ID: ")
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE customers SET isactive=FALSE WHERE customerid=%s;", (cid,))
        conn.commit()
        print("Deactivated.")
    except:
        conn.rollback()

# //******************** ORDER PROCESSING *********************//

def place_order(conn):
    customerid = input("Customer ID: ").strip()
    shipping = input("Shipping Address: ").strip()
    pay = input("Payment Method: ").strip()

    #----------------------------------------------------------
    # 1. Create order header using stored procedure
    #----------------------------------------------------------
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT placeorder(%s, %s, %s);",
                (customerid, shipping, pay)
            )
            orderid = cur.fetchone()[0]

        conn.commit()
        print(f"\nOrder created with ID: {orderid}\n")

    except Exception as e:
        conn.rollback()
        print("Error creating order:", e)
        return

    #----------------------------------------------------------
    # 2. Add items (triggers handle stock + total calculations)
    #----------------------------------------------------------
    while True:
        add = input("Add product to cart? (y/n): ").strip().lower()
        if add != 'y':
            break

        productid = input("Product ID: ").strip()
        quantity = int(input("Quantity: ").strip())

        # optional validation using stored procedure
        row = q(conn,
            "SELECT check_product_stock(%s, %s);",
            (productid, quantity),
            fetchone=True
        )

        if row and row[0] is False:
            print("Not enough stock.")
            continue

        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO orderitems(orderid, productid, quantity, unitprice, subtotal)
                    VALUES (
                        %s,
                        %s,
                        %s,
                        (SELECT price FROM products WHERE productid=%s),
                        (SELECT price * %s FROM products WHERE productid=%s)
                    );
                """, (orderid, productid, quantity, productid, quantity, productid))

            conn.commit()
            print("Item added.")

        except Exception as e:
            conn.rollback()
            print("Error adding item:", e)

    #----------------------------------------------------------
    # 3. PRINT FINAL ORDER TOTAL (triggers already calculated it)
    #----------------------------------------------------------
    try:
        row = q(conn,
            "SELECT totalamount FROM orders WHERE orderid=%s;",
            (orderid,),
            fetchone=True
        )

        if row:
            final_total = row[0]
            print(f"\nFinal Order Total: ${final_total:.2f}\n")
        else:
            print("\nCould not retrieve order total.\n")

    except Exception as e:
        print("Error retrieving final total:", e)

    print("Order complete.\n")


def view_all_orders(conn):
    rows = q(conn,
        "SELECT * FROM orders;",
        fetchall=True
    )
    for r in rows or []:
        print(r)

def view_order_details(conn):
    oid = input("Order ID: ")
    order = q(conn,
        "SELECT * FROM orders WHERE orderid=%s;",
        (oid,),
        fetchone=True
    )
    print(order or "Not found.")

    rows = q(conn,
        """
        SELECT oi.productid,p.productname,oi.quantity,oi.unitprice,oi.subtotal
        FROM orderitems oi
        JOIN products p ON oi.productid=p.productid
        WHERE oi.orderid=%s;
        """,
        (oid,),
        fetchall=True
    )
    for r in rows or []:
        print("  Item:", r)

# //********************* REVIEW MANAGEMENT ********************//

def write_review(conn):
    cid = input("Customer ID: ")
    pid = input("Product ID: ")
    row = q(conn,
        """
        SELECT COUNT(*) FROM orderitems oi
        JOIN orders o ON oi.orderid=o.orderid
        WHERE o.customerid=%s AND oi.productid=%s;
        """,
        (cid, pid),
        fetchone=True
    )
    if not row or row[0] == 0:
        return print("You must purchase before reviewing.")

    rating = int(input("Rating 1-5: "))
    comment = input("Comment: ")

    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO reviews(customerid,productid,rating,reviewtext)
                VALUES (%s,%s,%s,%s);
            """, (cid, pid, rating, comment))
        conn.commit()
        print("Review added.")
    except:
        conn.rollback()

def view_own_reviews(conn):
    cid = input("Customer ID: ")
    rows = q(conn,
        "SELECT * FROM reviews WHERE customerid=%s;",
        (cid,),
        fetchall=True
    )
    for r in rows or []:
        print(r)

def view_product_reviews(conn):
    productid = input("Product ID: ")
    rows = q(conn,
        """
        SELECT r.reviewid,c.firstname,c.lastname,r.rating,r.reviewtext,r.reviewdate
        FROM reviews r
        JOIN customers c ON r.customerid=c.customerid
        WHERE r.productid=%s;
        """,
        (productid,),
        fetchall=True
    )
    for r in rows or []:
        print(r)

def view_average_rating(conn):
    rows = q(conn,
        """
        SELECT p.productid,p.productname,AVG(r.rating),COUNT(r.reviewid)
        FROM products p
        LEFT JOIN reviews r ON p.productid=r.productid
        GROUP BY p.productid,p.productname;
        """,
        fetchall=True
    )
    for r in rows or []:
        print(r)
