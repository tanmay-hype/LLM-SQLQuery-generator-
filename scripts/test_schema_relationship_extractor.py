from app.models.schema_relationship import (
    SchemaRelationship,
)
from app.services.schema_relationship_extractor import (
    SchemaRelationshipExtractor,
)


def build_schema() -> dict:
    """
    Reproduce the FK metadata shape returned by the
    current SQLAlchemy SchemaLoader.
    """

    return {
        "customers": {
            "foreign_keys": [],
        },

        "orders": {
            "foreign_keys": [
                {
                    "name": "orders_customer_id_fkey",
                    "constrained_columns": [
                        "customer_id",
                    ],
                    "referred_schema": "public",
                    "referred_table": "customers",
                    "referred_columns": [
                        "id",
                    ],
                    "options": {},
                    "comment": None,
                },
            ],
        },

        "order_items": {
            "foreign_keys": [
                {
                    "name": "order_items_order_id_fkey",
                    "constrained_columns": [
                        "order_id",
                    ],
                    "referred_schema": "public",
                    "referred_table": "orders",
                    "referred_columns": [
                        "id",
                    ],
                    "options": {},
                    "comment": None,
                },
                {
                    "name": "order_items_product_id_fkey",
                    "constrained_columns": [
                        "product_id",
                    ],
                    "referred_schema": "public",
                    "referred_table": "products",
                    "referred_columns": [
                        "id",
                    ],
                    "options": {},
                    "comment": None,
                },
            ],
        },

        "products": {
            "foreign_keys": [],
        },
    }


def main():
    print("=" * 70)
    print("SCHEMA RELATIONSHIP EXTRACTOR TEST")
    print("=" * 70)

    extractor = SchemaRelationshipExtractor()

    relationships = extractor.extract(
        build_schema()
    )

    # ------------------------------------------------------
    # Exactly three relationships
    # ------------------------------------------------------

    assert len(relationships) == 3

    print(
        "[PASS] Correct relationship count"
    )

    # ------------------------------------------------------
    # orders -> customers
    # ------------------------------------------------------

    orders_customers = SchemaRelationship(
        source_table="orders",
        source_column="customer_id",
        target_table="customers",
        target_column="id",
    )

    assert (
        orders_customers
        in relationships
    )

    print(
        "[PASS] orders.customer_id -> customers.id"
    )

    # ------------------------------------------------------
    # order_items -> orders
    # ------------------------------------------------------

    items_orders = SchemaRelationship(
        source_table="order_items",
        source_column="order_id",
        target_table="orders",
        target_column="id",
    )

    assert (
        items_orders
        in relationships
    )

    print(
        "[PASS] order_items.order_id -> orders.id"
    )

    # ------------------------------------------------------
    # order_items -> products
    # ------------------------------------------------------

    items_products = SchemaRelationship(
        source_table="order_items",
        source_column="product_id",
        target_table="products",
        target_column="id",
    )

    assert (
        items_products
        in relationships
    )

    print(
        "[PASS] order_items.product_id -> products.id"
    )

    # ------------------------------------------------------
    # Direction-independent matching
    # ------------------------------------------------------

    assert orders_customers.matches(
        left_table="orders",
        left_column="customer_id",
        right_table="customers",
        right_column="id",
    )

    assert orders_customers.matches(
        left_table="customers",
        left_column="id",
        right_table="orders",
        right_column="customer_id",
    )

    print(
        "[PASS] Relationship matching is direction-independent"
    )

    # ------------------------------------------------------
    # Invalid relationship
    # ------------------------------------------------------

    assert not orders_customers.matches(
        left_table="orders",
        left_column="id",
        right_table="customers",
        right_column="id",
    )

    print(
        "[PASS] Invalid relationship rejected"
    )

    print()
    print("=" * 70)
    print(
        "ALL SCHEMA RELATIONSHIP EXTRACTOR TESTS PASSED"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()