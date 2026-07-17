from app.models.prompt_example import PromptExample

class ExampleRepository:
    """
    Repository for managing prompt examples.
    """

"""    def __init__(self):
        self.examples = EXAMPLES

    def get_examples(self) -> list[PromptExample]:
        """
        Returns all prompt examples.
        """
        return self.examples """

EXAMPLES = [
    PromptExample(
        question="Show all customers.",
        intent=QueryIntent.SHOW_CUSTOMERS,
        sql="SELECT * FROM customers;"
    ),
    PromptExample(
        question="Show all orders.",
        intent=QueryIntent.SHOW_ORDERS,
        sql="SELECT * FROM orders;"
    ),
    PromptExample(
        question="Show all products.",
        intent=QueryIntent.SHOW_PRODUCTS,
        sql="SELECT * FROM products;"
    ),
    PromptExample(
        question="Show customer orders.",
        intent=QueryIntent.SHOW_CUSTOMER_ORDERS,
        sql="SELECT * FROM orders WHERE customer_id = ?;"
    ),
    PromptExample(
        question="Count all the orders.",
        intent=QueryIntent.COUNT_ORDERS,
        sql="SELECT COUNT(*) AS order_count FROM orders;"
    ),
    PromptExample(
        question="Show order details.",
        intent=QueryIntent.SHOW_ORDER_DETAILS,
        sql="SELECT * FROM order_details WHERE order_id = ?;"
    ),
    PromptExample(
        question="Show the total sales per product.",
        intent=QueryIntent.SHOW_TOTAL_SALES_PER_PRODUCT,
        sql="SELECT product_id, SUM(quantity * price) AS total_sales FROM order_details GROUP BY product_id;"
    ),
    PromptExample(
        question="Show the average order value.",
        intent=QueryIntent.SHOW_AVERAGE_ORDER_VALUE,
        sql="SELECT AVG(total_amount) AS average_order_value FROM orders;"
    ),
    PromptExample(
        question="Show the total revenue.",
        intent=QueryIntent.SHOW_TOTAL_REVENUE,
        sql="SELECT SUM(total_amount) AS total_revenue FROM orders;"
    ),
    PromptExample(
        question="Total sales by category.",
        intent=QueryIntent.SHOW_TOTAL_SALES_BY_CATEGORY,
        sql="SELECT category, SUM(amount) AS total_sales FROM sales GROUP BY category;"
    ),
    PromptExample(
        question="Show the top 5 customers by total purchase amount.",
        intent=QueryIntent.SHOW_TOP_CUSTOMERS,
        sql="SELECT customer_id, SUM(total_amount) AS total_purchases FROM orders GROUP BY customer_id ORDER BY total_purchases DESC LIMIT 5;"
    ),
    PromptExample(
        question="Show the bottom 5 customers by total purchase amount.",
        intent=QueryIntent.SHOW_BOTTOM_CUSTOMERS,
        sql="SELECT customer_id, SUM(total_amount) AS total_purchases FROM orders GROUP BY customer_id ORDER BY total_purchases ASC LIMIT 5;"
    ),
    PromptExample(
        question="Show the total number of products.",
        intent=QueryIntent.SHOW_TOTAL_PRODUCTS,
        sql="SELECT COUNT(*) AS total_products FROM products;"
    ),
    PromptExample(
        question="Show the total number of customers.",
        intent=QueryIntent.SHOW_TOTAL_CUSTOMERS,
        sql="SELECT COUNT(*) AS total_customers FROM customers;"
    ),
    PromptExample(
        question="Show customer names and their orders.",
        intent=QueryIntent.SHOW_CUSTOMER_ORDERS_DETAILS,
        sql="SELECT c.name, o.* FROM customers c JOIN orders o ON c.customer_id = o.customer_id;"
    ),
    PromptExample(
        question="Show all orders.",
        intent=QueryIntent.SHOW_ORDERS,
        sql="SELECT * FROM orders;"
    ),
    PromptExample(
        question="Show all products.",
        intent=QueryIntent.SHOW_PRODUCTS,
        sql="SELECT * FROM products;"
    ),
    PromptExample(
        question="Show customer orders.",
        intent=QueryIntent.SHOW_CUSTOMER_ORDERS,
        sql="SELECT * FROM orders WHERE customer_id = ?;"
    ),
    PromptExample(
            question="Count all the orders.",
            intent=QueryIntent.COUNT_ORDERS,
            sql="SELECT COUNT(*) AS order_count FROM orders;"
    ),
    PromptExample(
            question="Show order details.",
            intent=QueryIntent.SHOW_ORDER_DETAILS,
            sql="SELECT * FROM order_details WHERE order_id = ?;"
    ),
    PromptExample(
            question="Show the total sales per product.",
            intent=QueryIntent.SHOW_TOTAL_SALES_PER_PRODUCT,
            sql="SELECT product_id, SUM(quantity * price) AS total_sales FROM order_details GROUP BY product_id;"
    ),
    PromptExample(
            question="Show the average order value.",
            intent=QueryIntent.SHOW_AVERAGE_ORDER_VALUE,
            sql="SELECT AVG(total_amount) AS average_order_value FROM orders;"
    ),
    PromptExample(
            question="Show the total revenue.",
            intent=QueryIntent.SHOW_TOTAL_REVENUE,
            sql="SELECT SUM(total_amount) AS total_revenue FROM orders;"
    ),
    PromptExample(
            question="Total sales by category.",
            intent=QueryIntent.SHOW_TOTAL_SALES_BY_CATEGORY,
            sql="SELECT category, SUM(amount) AS total_sales FROM sales GROUP BY category;"
    ),
    PromptExample(
            question="Show the top 5 customers by total purchase amount.",
            intent=QueryIntent.SHOW_TOP_5_CUSTOMERS,
            sql="SELECT customer_id, SUM(total_amount) AS total_purchases FROM orders GROUP BY customer_id ORDER BY total_purchases DESC"
                LIMIT 5;",
    ),
    PromptExample(
            question="Show the bottom 5 customers by total purchase amount.",
            intent=QueryIntent.SHOW_BOTTOM_5_CUSTOMERS,
            sql="SELECT customer_id, SUM(total_amount) AS total_purchases FROM orders GROUP BY customer_id ORDER BY total_purchases ASC LIMIT 5;",
    ),
    PromptExample(
            question="Show the total number of products.",
            intent=QueryIntent.SHOW_TOTAL_PRODUCTS,
            sql="SELECT COUNT(*) AS total_products FROM products;",
    ),
    PromptExample(
            question="Show the total number of customers.",
            intent=QueryIntent.SHOW_TOTAL_CUSTOMERS,
            sql="SELECT COUNT(*) AS total_customers FROM customers;",
    ),
    PromptExample(
            question="Show customer names and their orders.",
            intent=QueryIntent.SHOW_CUSTOMER_ORDERS_DETAILS,
            sql="SELECT c.name, o.* FROM customers c JOIN orders o ON c.customer_id = o.customer_id;",
    ),
    PromptExample(
            question="Show the total sales for each month.",
            intent=QueryIntent.SHOW_TOTAL_SALES_PER_MONTH,
            sql="SELECT strftime('%Y-%m', order_date) AS month, SUM(total_amount) AS total_sales FROM orders GROUP BY month;",
    ),
    PromptExample(
            question="Show the total sales for each year.",
            intent=QueryIntent.SHOW_TOTAL_SALES_PER_YEAR,
            sql="SELECT strftime('%Y', order_date) AS year, SUM(total_amount) AS total_sales FROM orders GROUP BY year;",
    ),
    PromptExample(
            question="Show the total sales for each quarter.",
            intent=QueryIntent.SHOW_TOTAL_SALES_PER_QUARTER,
            sql="SELECT strftime('%Y-Q%q', order_date) AS quarter, SUM(total_amount) AS total_sales FROM orders GROUP BY quarter;",
    ),
    PromptExample(
            question="Show the total sales for each day.",
            intent=QueryIntent.SHOW_TOTAL_SALES_PER_DAY,
            sql="SELECT strftime('%Y-%m-%d', order_date) AS day, SUM(total_amount) AS total_sales FROM orders GROUP BY day;",
    ),
    PromptExample(
            question="Top 10 products by revenue.",
            intent=QueryIntent.SHOW_TOP_10_PRODUCTS_BY_REVENUE,
            sql="SELECT product_id, SUM(quantity * price) AS total_revenue FROM order_details GROUP BY product_id ORDER BY total_revenue DESC LIMIT 10;",
    ),
    PromptExample(
            question="Show the total sales for each product.",
            intent=QueryIntent.SHOW_TOTAL_SALES_PER_PRODUCT,
            sql="SELECT product_id, SUM(quantity * price) AS total_sales FROM order_details GROUP BY product_id;",
    ),
    PromptExample(
            question="Show the total sales for each customer.",
            intent=QueryIntent.SHOW_TOTAL_SALES_PER_CUSTOMER,   
            sql="SELECT customer_id, SUM(total_amount) AS total_sales FROM orders GROUP BY customer_id;",   
    ),
    PromptExample(
            question="Show the total sales for each category.",
            intent=QueryIntent.SHOW_TOTAL_SALES_PER_CATEGORY,
            sql="SELECT category, SUM(amount) AS total_sales FROM sales GROUP BY category;",
    ),
    PromptExample(
            question="Show the total sales for each region.",
            intent=QueryIntent.SHOW_TOTAL_SALES_PER_REGION,
            sql="SELECT region, SUM(amount) AS total_sales FROM sales GROUP BY region;",
    ),
    PromptExample(
            question="Show the total sales for each salesperson.",
            intent=QueryIntent.SHOW_TOTAL_SALES_PER_SALESPERSON,
            sql="SELECT salesperson_id, SUM(amount) AS total_sales FROM sales GROUP BY salesperson_id ;",
    ),
    PromptExample(
            question="Show the total sales for each product category.",
            intent=QueryIntent.SHOW_TOTAL_SALES_PER_PRODUCT_CATEGORY,
            sql="SELECT p.category, SUM(od.quantity * od.price) AS total_sales FROM order_details od JOIN products p ON od.product_id = p.product_id GROUP BY p.category;",
    ),
    PromptExample(
            question="Show the total sales for each customer region.",
            intent=QueryIntent.SHOW_TOTAL_SALES_PER_CUSTOMER_REGION,
            sql="SELECT c.region, SUM(o.total_amount) AS total_sales FROM customers c JOIN  orders o ON c.customer_id = o.customer_id GROUP BY c.region;",
    ),
    PromptExample(
        question="Show the bottom 5 customers by total purchase amount.",
        intent=QueryIntent.SHOW_BOTTOM_5_CUSTOMERS_BY_TOTAL_PURCHASE_AMOUNT,
        sql="SELECT customer_id, SUM(total_amount) AS total_purchases
                FROM orders
                GROUP BY customer_id
                ORDER BY total_purchases ASC
                LIMIT 5;",
    ),
    PromptExample(
        question="Show the total sales for each product.",
        intent=QueryIntent.SHOW_TOTAL_SALES_PER_PRODUCT,
        sql="SELECT product_id, SUM(quantity * price) AS total_sales
                FROM order_details
                GROUP BY product_id;",
    ),
    PromptExample(
        question="Show the total sales for each customer.",
        intent=QueryIntent.SHOW_TOTAL_SALES_PER_CUSTOMER,
        sql="SELECT customer_id, SUM(total_amount) AS total_sales   
                FROM orders
                    GROUP BY customer_id;",
    ),
    PromptExample(
        question="Show the total number of products.",
        intent=QueryIntent.SHOW_TOTAL_NUMBER_OF_PRODUCTS,
        sql="SELECT COUNT(*) AS total_products
                FROM products;",
    )
]