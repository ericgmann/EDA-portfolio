how to run
1) in terminal run : python db_main.py
2) use login.txt for login credentials -> it should say connected successfully
3) a menu with 5 options will appear
4) choose option 5 to exit

db_main handles menu options
modules.py handles the operations
assignment4.sql handles the procedures and event trigger


db_main functions:
    get_connection()
    product_menu(conn)
    customer_menu(conn)
    order_menu(conn)
    review_menu(conn)
    main()

modules functions:
    q(conn, query, params=None, fetchone=False, fetchall=False)
    Product Management:
    Customer Management:
    Order Processing: 
    Review Management: 