from app.models.intent import QueryIntent
from app.models.prompt_example import PromptExample


class ExampleRepository:
    """
    Repository that stores and provides all few-shot prompt examples.
    """

    def __init__(self) -> None:
        self.examples: list[PromptExample] = EXAMPLES

    def get_examples(self) -> list[PromptExample]:
        """
        Return all available prompt examples.

        A copy of the internal list is returned to prevent accidental
        modification by callers.
        """
        return list(self.examples)

EXAMPLES = [
    PromptExample(
        intents={QueryIntent.LOOKUP, QueryIntent.FILTER},
        question="List active customers from California",
        sql="""
SELECT
    customer_id,
    full_name,
    email
FROM customers
WHERE state = 'CA'
  AND is_active = TRUE;
""",
    ),
    PromptExample(
        intents={QueryIntent.AGGREGATION, QueryIntent.GROUP_BY},
        question="Total sales by category",
        sql="""
SELECT
    category,
    SUM(amount) AS total_sales
FROM sales
GROUP BY category
ORDER BY total_sales DESC;
""",
    ),
    PromptExample(
        intents={QueryIntent.SORT, QueryIntent.AGGREGATION, QueryIntent.GROUP_BY},
        question="Top 5 customers by total purchase amount",
        sql="""
SELECT
    customer_id,
    SUM(total_amount) AS total_purchases
FROM orders
GROUP BY customer_id
ORDER BY total_purchases DESC
LIMIT 5;
""",
    ),
    PromptExample(
        intents={QueryIntent.JOIN, QueryIntent.LOOKUP},
        question="Show order id, customer name, and order date",
        sql="""
SELECT
    o.order_id,
    c.full_name AS customer_name,
    o.order_date
FROM orders AS o
JOIN customers AS c
  ON c.customer_id = o.customer_id;
""",
    ),
    PromptExample(
        intents={QueryIntent.TIME_SERIES, QueryIntent.AGGREGATION, QueryIntent.GROUP_BY},
        question="Monthly revenue for the last 12 months",
        sql="""
SELECT
    DATE_TRUNC('month', order_date) AS month,
    SUM(total_amount) AS revenue
FROM orders
WHERE order_date >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '11 months'
GROUP BY month
ORDER BY month;
""",
    ),
    PromptExample(
        intents={QueryIntent.COMPARISON, QueryIntent.AGGREGATION, QueryIntent.GROUP_BY},
        question="Compare paid and unpaid invoice counts",
        sql="""
SELECT
    payment_status,
    COUNT(*) AS invoice_count
FROM invoices
GROUP BY payment_status
ORDER BY invoice_count DESC;
""",
    ),
    PromptExample(
        intents={QueryIntent.FILTER, QueryIntent.AGGREGATION},
        question="How many orders were placed this week",
        sql="""
SELECT
    COUNT(*) AS orders_this_week
FROM orders
WHERE order_date >= DATE_TRUNC('week', CURRENT_DATE)
  AND order_date < DATE_TRUNC('week', CURRENT_DATE) + INTERVAL '1 week';
""",
    ),
    PromptExample(
        intents={QueryIntent.JOIN, QueryIntent.AGGREGATION, QueryIntent.GROUP_BY},
        question="Average order value by customer segment",
        sql="""
SELECT
    c.segment,
    AVG(o.total_amount) AS avg_order_value
FROM orders AS o
JOIN customers AS c
  ON c.customer_id = o.customer_id
GROUP BY c.segment
ORDER BY avg_order_value DESC;
""",
    ),
    PromptExample(
        intents={QueryIntent.SORT, QueryIntent.LOOKUP},
        question="Show the 10 most recently created products",
        sql="""
SELECT
    product_id,
    product_name,
    created_at
FROM products
ORDER BY created_at DESC
LIMIT 10;
""",
    ),
    PromptExample(
        intents={QueryIntent.TIME_SERIES, QueryIntent.AGGREGATION, QueryIntent.GROUP_BY},
        question="Daily active users in the last 30 days",
        sql="""
SELECT
    DATE_TRUNC('day', last_login_at) AS day,
    COUNT(DISTINCT user_id) AS active_users
FROM user_sessions
WHERE last_login_at >= CURRENT_DATE - INTERVAL '29 days'
GROUP BY day
ORDER BY day;
""",
    ),
    PromptExample(
        intents={QueryIntent.JOIN, QueryIntent.COMPARISON, QueryIntent.AGGREGATION},
        question="Which products have never been ordered",
        sql="""
SELECT
    p.product_id,
    p.product_name
FROM products AS p
LEFT JOIN order_items AS oi
  ON oi.product_id = p.product_id
WHERE oi.product_id IS NULL;
""",
    ),
    PromptExample(
        intents={QueryIntent.AGGREGATION, QueryIntent.GROUP_BY, QueryIntent.FILTER},
        question="Count orders per status for the current month",
        sql="""
SELECT
    status,
    COUNT(*) AS order_count
FROM orders
WHERE order_date >= DATE_TRUNC('month', CURRENT_DATE)
  AND order_date < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
GROUP BY status
ORDER BY order_count DESC;
""",
    ),
    PromptExample(
        intents={QueryIntent.SORT, QueryIntent.AGGREGATION, QueryIntent.GROUP_BY},
        question="Top 3 sales reps by revenue this quarter",
        sql="""
SELECT
    o.sales_rep_id,
    SUM(o.total_amount) AS quarter_revenue
FROM orders AS o
WHERE o.order_date >= DATE_TRUNC('quarter', CURRENT_DATE)
  AND o.order_date < DATE_TRUNC('quarter', CURRENT_DATE) + INTERVAL '3 months'
GROUP BY o.sales_rep_id
ORDER BY quarter_revenue DESC
LIMIT 3;
""",
    ),
    PromptExample(
        intents={QueryIntent.COMPARISON, QueryIntent.TIME_SERIES, QueryIntent.AGGREGATION},
        question="Month-over-month revenue change",
        sql="""
WITH monthly_revenue AS (
    SELECT
        DATE_TRUNC('month', order_date) AS month,
        SUM(total_amount) AS revenue
    FROM orders
    GROUP BY month
)
SELECT
    month,
    revenue,
    revenue - LAG(revenue) OVER (ORDER BY month) AS revenue_change
FROM monthly_revenue
ORDER BY month;
""",
    ),
    PromptExample(
        intents={QueryIntent.GROUP_BY, QueryIntent.AGGREGATION},
        question="Average delivery time by shipping method",
        sql="""
SELECT
    shipping_method,
    AVG(EXTRACT(EPOCH FROM (delivered_at - shipped_at)) / 3600.0) AS avg_delivery_hours
FROM shipments
WHERE delivered_at IS NOT NULL
GROUP BY shipping_method
ORDER BY avg_delivery_hours;
""",
    ),
    PromptExample(
        intents={QueryIntent.JOIN, QueryIntent.AGGREGATION, QueryIntent.GROUP_BY},
        question="Revenue by product category in 2025",
        sql="""
SELECT
    p.category,
    SUM(oi.quantity * oi.unit_price) AS category_revenue
FROM order_items AS oi
JOIN orders AS o
  ON o.order_id = oi.order_id
JOIN products AS p
  ON p.product_id = oi.product_id
WHERE o.order_date >= DATE '2025-01-01'
  AND o.order_date < DATE '2026-01-01'
GROUP BY p.category
ORDER BY category_revenue DESC;
""",
    ),
    PromptExample(
        intents={QueryIntent.FILTER, QueryIntent.LOOKUP, QueryIntent.SORT},
        question="Show high-priority open support tickets",
        sql="""
SELECT
    ticket_id,
    subject,
    created_at
FROM support_tickets
WHERE priority = 'high'
  AND status <> 'closed'
ORDER BY created_at ASC;
""",
    ),
    PromptExample(
        intents={QueryIntent.TIME_SERIES, QueryIntent.COMPARISON, QueryIntent.AGGREGATION},
        question="Weekly signups this year versus last year",
        sql="""
WITH weekly_signups AS (
    SELECT
        DATE_TRUNC('week', created_at) AS week_start,
        EXTRACT(YEAR FROM created_at)::int AS signup_year,
        COUNT(*) AS signup_count
    FROM users
    WHERE created_at >= DATE_TRUNC('year', CURRENT_DATE) - INTERVAL '1 year'
    GROUP BY week_start, signup_year
)
SELECT
    week_start,
    COALESCE(SUM(signup_count) FILTER (WHERE signup_year = EXTRACT(YEAR FROM CURRENT_DATE)::int), 0) AS signups_this_year,
    COALESCE(SUM(signup_count) FILTER (WHERE signup_year = EXTRACT(YEAR FROM CURRENT_DATE)::int - 1), 0) AS signups_last_year
FROM weekly_signups
GROUP BY week_start
ORDER BY week_start;
""",
    ),
]