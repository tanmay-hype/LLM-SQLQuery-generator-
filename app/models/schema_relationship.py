from dataclasses import dataclass


@dataclass(frozen=True)
class SchemaRelationship:
    """
    Represents one physical foreign-key relationship.

    Example:

        orders.customer_id -> customers.id
    """

    source_table: str
    source_column: str

    target_table: str
    target_column: str

    def matches(
        self,
        left_table: str,
        left_column: str,
        right_table: str,
        right_column: str,
    ) -> bool:
        """
        Return True when the supplied column pair represents
        this FK relationship.

        Equality direction does not matter.

        Both of these therefore match:

            orders.customer_id = customers.id

            customers.id = orders.customer_id
        """

        forward = (
            left_table == self.source_table
            and left_column == self.source_column
            and right_table == self.target_table
            and right_column == self.target_column
        )

        reverse = (
            left_table == self.target_table
            and left_column == self.target_column
            and right_table == self.source_table
            and right_column == self.source_column
        )

        return forward or reverse