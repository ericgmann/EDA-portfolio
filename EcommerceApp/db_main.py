import psycopg2
from psycopg2 import Error
import modules 

# //************************ DATABASE CONNECTION ***********************//

def get_connection():
    host_name = input("Host: ").strip()
    port_input = input("Port: ").strip()
    dbname = input("Database name: ").strip()
    user = input("Username: ").strip()
    password = input("Password: ").strip()

    try:
        conn = psycopg2.connect(
            host=host_name,
            port=port_input,
            dbname=dbname,
            user=user,
            password=password
        )
        conn.autocommit = False
        print("Connected successfully.\n")
        return conn
    except Exception as e:
        print("\nFailed to connect:", e)
        print("Please try again.\n")
        return get_connection() 

#//****************** MAIN CLI MENUS (match-case) **********************??

def product_menu(conn):
    while True:
        print("""
=== PRODUCT MANAGEMENT ===
1. Search products by name
2. Filter by category
3. View product details
4. Low stock alerts (<50)
5. Add product
6. Update product (price/stock/desc)
7. Activate/Deactivate product
8. Back
""")
        match input("Choose: ").strip():
            case "1": modules.search_products(conn)
            case "2": modules.filter_by_category(conn)
            case "3": modules.product_details(conn)
            case "4": modules.low_stock_alerts(conn)
            case "5": modules.add_product(conn)
            case "6": modules.update_product(conn)
            case "7": modules.toggle_product_active(conn)
            case "8": return
            case _: print("Invalid choice.")

def customer_menu(conn):
    while True:
        print("""
=== CUSTOMER MANAGEMENT ===
1. Register customer
2. Update customer info
3. View customer profile
4. Deactivate customer
5. Back
""")
        match input("Choose: ").strip():
            case "1": modules.register_customer(conn)
            case "2": modules.update_customer_info(conn)
            case "3": modules.view_customer_profile(conn)
            case "4": modules.deactivate_customer(conn)
            case "5": return
            case _: print("Invalid choice.")

def order_menu(conn):
    while True:
        print("""
=== ORDER PROCESSING ===
1. Place order
2. View all orders
3. View order details
4. Back
""")
        match input("Choose: ").strip():
            case "1": modules.place_order(conn)
            case "2": modules.view_all_orders(conn)
            case "3": modules.view_order_details(conn)
            case "4": return
            case _: print("Invalid choice.")

def review_menu(conn):
    while True:
        print("""
=== REVIEW MANAGEMENT ===
1. Write review (purchased products only)
2. View my reviews
3. View reviews for product
4. View average product rating
5. Back
""")
        match input("Choose: ").strip():
            case "1": modules.write_review(conn)
            case "2": modules.view_own_reviews(conn)
            case "3": modules.view_product_reviews(conn)
            case "4": modules.view_average_rating(conn)
            case "5": return
            case _: print("Invalid choice.")

# //********************* MAIN PROGRAM LOOP **********************//

def main():
    conn = get_connection()
    try:
        while True:
            print("""
=== E-COMMERCE CLI (Individual) ===
1. Product Management
2. Customer Management
3. Order Processing
4. Review Management
5. Exit
""")
            match input("Choose: ").strip():
                case "1": product_menu(conn)
                case "2": customer_menu(conn)
                case "3": order_menu(conn)
                case "4": review_menu(conn)
                case "5":
                    print("Goodbye!")
                    break
                case _:
                    print("Invalid choice.")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
