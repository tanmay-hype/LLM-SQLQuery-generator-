from dataclasses import dataclass, field


@dataclass(frozen=True)
class SemanticContract:
    """
    Represents deterministic semantic requirements that
    generated SQL should satisfy before execution.

    These requirements are derived from the detected
    query intent and later checked by the semantic validator.
    """

    requires_aggregation: bool = False
    requires_group_by: bool = False
    requires_order_by: bool = False
    requires_join: bool = False

    required_tables: frozenset[str] = field(
        default_factory=frozenset
    )

    required_columns: frozenset[str] = field(
        default_factory=frozenset
    )