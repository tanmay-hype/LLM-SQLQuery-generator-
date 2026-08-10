from datetime import datetime

from sqlalchemy import (
    create_engine,
    MetaData,
    Table,
    Column,
    Integer,
    String,
    Numeric,
    DateTime,
    ForeignKey,
)

from app.core.config import settings


def create_database():
    """
    Creates the PostgreSQL test database schema
    and inserts sample data.

    WARNING:
    This script drops and recreates the test tables.
    Do not run this against a production database.
    """

    engine = create_engine(
        settings.database_url
    )

    metadata = MetaData()

    # --------------------------------------------------
    # Customers
    # --------------------------------------------------

    customers = Table(
        "customers",
        metadata,

        Column(
            "id",
            Integer,
            primary_key=True,
        ),

        Column(
            "name",
            String(100),
            nullable=False,
        ),

        Column(
            "email",
            String(150),
            nullable=False,
            unique=True,
        ),

        Column(
            "city",
            String(100),
            nullable=False,
        ),

        Column(
            "created_at",
            DateTime,
            nullable=False,
        ),
    )

    # --------------------------------------------------
    # Products
    # --------------------------------------------------

    products = Table(
        "products",
        metadata,

        Column(
            "id",
            Integer,
            primary_key=True,
        ),

        Column(
            "name",
            String(150),
            nullable=False,
        ),

        Column(
            "category",
            String(100),
            nullable=False,
        ),

        Column(
            "price",
            Numeric(10, 2),
            nullable=False,
        ),
    )

    # --------------------------------------------------
    # Orders
    # --------------------------------------------------

    orders = Table(
        "orders",
        metadata,

        Column(
            "id",
            Integer,
            primary_key=True,
        ),

        Column(
            "customer_id",
            Integer,
            ForeignKey(
                "customers.id"
            ),
            nullable=False,
        ),

        Column(
            "order_date",
            DateTime,
            nullable=False,
        ),

        Column(
            "total_amount",
            Numeric(10, 2),
            nullable=False,
        ),
    )

    # --------------------------------------------------
    # Order Items
    # --------------------------------------------------

    order_items = Table(
        "order_items",
        metadata,

        Column(
            "id",
            Integer,
            primary_key=True,
        ),

        Column(
            "order_id",
            Integer,
            ForeignKey(
                "orders.id"
            ),
            nullable=False,
        ),

        Column(
            "product_id",
            Integer,
            ForeignKey(
                "products.id"
            ),
            nullable=False,
        ),

        Column(
            "quantity",
            Integer,
            nullable=False,
        ),

        Column(
            "unit_price",
            Numeric(10, 2),
            nullable=False,
        ),
    )

    # --------------------------------------------------
    # Recreate schema
    # --------------------------------------------------

    print("Dropping existing test tables...")

    metadata.drop_all(engine)

    print("Creating test tables...")

    metadata.create_all(engine)

    # --------------------------------------------------
    # Sample customers
    # --------------------------------------------------

    customer_data = [
        {
            "id": 1,
            "name": "Rahul Sharma",
            "email": "rahul@example.com",
            "city": "Delhi",
            "created_at": datetime(2025, 1, 10),
        },
        {
            "id": 2,
            "name": "Priya Singh",
            "email": "priya@example.com",
            "city": "Mumbai",
            "created_at": datetime(2025, 1, 15),
        },
        {
            "id": 3,
            "name": "Amit Kumar",
            "email": "amit@example.com",
            "city": "Bangalore",
            "created_at": datetime(2025, 2, 5),
        },
        {
            "id": 4,
            "name": "Neha Verma",
            "email": "neha@example.com",
            "city": "Delhi",
            "created_at": datetime(2025, 2, 20),
        },
        {
            "id": 5,
            "name": "Arjun Mehta",
            "email": "arjun@example.com",
            "city": "Pune",
            "created_at": datetime(2025, 3, 1),
        },
    ]

    # --------------------------------------------------
    # Sample products
    # --------------------------------------------------

    product_data = [
        {
            "id": 1,
            "name": "Laptop Pro 15",
            "category": "Electronics",
            "price": 85000.00,
        },
        {
            "id": 2,
            "name": "Wireless Mouse",
            "category": "Electronics",
            "price": 1500.00,
        },
        {
            "id": 3,
            "name": "Mechanical Keyboard",
            "category": "Electronics",
            "price": 4500.00,
        },
        {
            "id": 4,
            "name": "Office Chair",
            "category": "Furniture",
            "price": 12000.00,
        },
        {
            "id": 5,
            "name": "Standing Desk",
            "category": "Furniture",
            "price": 25000.00,
        },
        {
            "id": 6,
            "name": "USB-C Hub",
            "category": "Accessories",
            "price": 3000.00,
        },
    ]

    # --------------------------------------------------
    # Sample orders
    # --------------------------------------------------

    order_data = [
        {
            "id": 1,
            "customer_id": 1,
            "order_date": datetime(2025, 3, 5),
            "total_amount": 86500.00,
        },
        {
            "id": 2,
            "customer_id": 2,
            "order_date": datetime(2025, 3, 10),
            "total_amount": 12000.00,
        },
        {
            "id": 3,
            "customer_id": 1,
            "order_date": datetime(2025, 4, 2),
            "total_amount": 4500.00,
        },
        {
            "id": 4,
            "customer_id": 3,
            "order_date": datetime(2025, 4, 15),
            "total_amount": 28000.00,
        },
        {
            "id": 5,
            "customer_id": 4,
            "order_date": datetime(2025, 5, 1),
            "total_amount": 3000.00,
        },
        {
            "id": 6,
            "customer_id": 5,
            "order_date": datetime(2025, 5, 20),
            "total_amount": 97000.00,
        },
    ]

    # --------------------------------------------------
    # Sample order items
    # --------------------------------------------------

    order_item_data = [
        {
            "id": 1,
            "order_id": 1,
            "product_id": 1,
            "quantity": 1,
            "unit_price": 85000.00,
        },
        {
            "id": 2,
            "order_id": 1,
            "product_id": 2,
            "quantity": 1,
            "unit_price": 1500.00,
        },
        {
            "id": 3,
            "order_id": 2,
            "product_id": 4,
            "quantity": 1,
            "unit_price": 12000.00,
        },
        {
            "id": 4,
            "order_id": 3,
            "product_id": 3,
            "quantity": 1,
            "unit_price": 4500.00,
        },
        {
            "id": 5,
            "order_id": 4,
            "product_id": 5,
            "quantity": 1,
            "unit_price": 25000.00,
        },
        {
            "id": 6,
            "order_id": 4,
            "product_id": 6,
            "quantity": 1,
            "unit_price": 3000.00,
        },
        {
            "id": 7,
            "order_id": 5,
            "product_id": 6,
            "quantity": 1,
            "unit_price": 3000.00,
        },
        {
            "id": 8,
            "order_id": 6,
            "product_id": 1,
            "quantity": 1,
            "unit_price": 85000.00,
        },
        {
            "id": 9,
            "order_id": 6,
            "product_id": 3,
            "quantity": 1,
            "unit_price": 4500.00,
        },
        {
            "id": 10,
            "order_id": 6,
            "product_id": 4,
            "quantity": 1,
            "unit_price": 7500.00,
        },
    ]

    # --------------------------------------------------
    # Insert data
    # --------------------------------------------------

    print("Inserting customers...")

    with engine.begin() as connection:

        connection.execute(
            customers.insert(),
            customer_data,
        )

        print("Inserting products...")

        connection.execute(
            products.insert(),
            product_data,
        )

        print("Inserting orders...")

        connection.execute(
            orders.insert(),
            order_data,
        )

        print("Inserting order items...")

        connection.execute(
            order_items.insert(),
            order_item_data,
        )

    print()
    print("======================================")
    print("Test database created successfully!")
    print("======================================")
    print()
    print("Tables:")
    print("  customers")
    print("  products")
    print("  orders")
    print("  order_items")
    print()
    print("Foreign-key relationships:")
    print("  orders.customer_id → customers.id")
    print("  order_items.order_id → orders.id")
    print("  order_items.product_id → products.id")
    print()


if __name__ == "__main__":
    create_database()