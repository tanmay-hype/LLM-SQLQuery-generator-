from app.models.intent import QueryIntent
from app.models.prompt_example import PromptExample


class ExampleRepository:
    """
    Repository that stores and provides few-shot prompt examples.

    The examples demonstrate SQL patterns rather than depending on a
    specific database schema. The actual database schema is supplied
    separately to the LLM by the prompt pipeline.
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

    # --------------------------------------------------
    # LOOKUP
    # --------------------------------------------------

    PromptExample(
        intents={QueryIntent.LOOKUP},
        question="Show all records",
        sql="""
SELECT
    *
FROM some_table;
""",
    ),

    PromptExample(
        intents={QueryIntent.LOOKUP},
        question="Show names and email addresses",
        sql="""
SELECT
    name,
    email
FROM some_table;
""",
    ),

    # --------------------------------------------------
    # FILTER
    # --------------------------------------------------

    PromptExample(
        intents={QueryIntent.LOOKUP, QueryIntent.FILTER},
        question="Show records where status is active",
        sql="""
SELECT
    *
FROM some_table
WHERE status = 'active';
""",
    ),

    PromptExample(
        intents={QueryIntent.LOOKUP, QueryIntent.FILTER},
        question="Show records created after a specific date",
        sql="""
SELECT
    *
FROM some_table
WHERE created_at >= DATE '2025-01-01';
""",
    ),

    # --------------------------------------------------
    # SORT
    # --------------------------------------------------

    PromptExample(
        intents={QueryIntent.LOOKUP, QueryIntent.SORT},
        question="Show the 10 most recent records",
        sql="""
SELECT
    *
FROM some_table
ORDER BY created_at DESC
LIMIT 10;
""",
    ),

    PromptExample(
        intents={QueryIntent.LOOKUP, QueryIntent.SORT},
        question="Show the 5 records with the highest value",
        sql="""
SELECT
    *
FROM some_table
ORDER BY value DESC
LIMIT 5;
""",
    ),

    # --------------------------------------------------
    # AGGREGATION
    # --------------------------------------------------

    PromptExample(
        intents={QueryIntent.AGGREGATION},
        question="Show the total value",
        sql="""
SELECT
    SUM(value) AS total_value
FROM some_table;
""",
    ),

    PromptExample(
        intents={QueryIntent.AGGREGATION},
        question="Count all records",
        sql="""
SELECT
    COUNT(*) AS record_count
FROM some_table;
""",
    ),

    PromptExample(
        intents={QueryIntent.AGGREGATION},
        question="Show the average value",
        sql="""
SELECT
    AVG(value) AS average_value
FROM some_table;
""",
    ),

    # --------------------------------------------------
    # GROUP BY
    # --------------------------------------------------

    PromptExample(
        intents={QueryIntent.AGGREGATION, QueryIntent.GROUP_BY},
        question="Show total value by category",
        sql="""
SELECT
    category,
    SUM(value) AS total_value
FROM some_table
GROUP BY category
ORDER BY total_value DESC;
""",
    ),

    PromptExample(
        intents={QueryIntent.AGGREGATION, QueryIntent.GROUP_BY},
        question="Count records by status",
        sql="""
SELECT
    status,
    COUNT(*) AS record_count
FROM some_table
GROUP BY status
ORDER BY record_count DESC;
""",
    ),

    # --------------------------------------------------
    # JOIN
    # --------------------------------------------------

    PromptExample(
        intents={QueryIntent.JOIN, QueryIntent.LOOKUP},
        question="Show information from two related tables",
        sql="""
SELECT
    a.id,
    b.name
FROM first_table AS a
JOIN second_table AS b
    ON b.id = a.second_table_id;
""",
    ),

    PromptExample(
        intents={
            QueryIntent.JOIN,
            QueryIntent.AGGREGATION,
            QueryIntent.GROUP_BY,
        },
        question="Show total value for each related entity",
        sql="""
SELECT
    b.name,
    SUM(a.value) AS total_value
FROM first_table AS a
JOIN second_table AS b
    ON b.id = a.second_table_id
GROUP BY b.id, b.name
ORDER BY total_value DESC;
""",
    ),

    # --------------------------------------------------
    # TIME SERIES
    # --------------------------------------------------

    PromptExample(
        intents={
            QueryIntent.TIME_SERIES,
            QueryIntent.AGGREGATION,
            QueryIntent.GROUP_BY,
        },
        question="Show monthly record counts",
        sql="""
SELECT
    DATE_TRUNC('month', created_at) AS month,
    COUNT(*) AS record_count
FROM some_table
GROUP BY month
ORDER BY month;
""",
    ),

    PromptExample(
        intents={
            QueryIntent.TIME_SERIES,
            QueryIntent.AGGREGATION,
            QueryIntent.GROUP_BY,
        },
        question="Show monthly total value",
        sql="""
SELECT
    DATE_TRUNC('month', created_at) AS month,
    SUM(value) AS total_value
FROM some_table
GROUP BY month
ORDER BY month;
""",
    ),

    PromptExample(
        intents={
            QueryIntent.TIME_SERIES,
            QueryIntent.AGGREGATION,
            QueryIntent.GROUP_BY,
        },
        question="Show daily record counts",
        sql="""
SELECT
    DATE_TRUNC('day', created_at) AS day,
    COUNT(*) AS record_count
FROM some_table
GROUP BY day
ORDER BY day;
""",
    ),

    # --------------------------------------------------
    # COMPARISON
    # --------------------------------------------------

    PromptExample(
        intents={
            QueryIntent.COMPARISON,
            QueryIntent.AGGREGATION,
            QueryIntent.GROUP_BY,
        },
        question="Compare counts by status",
        sql="""
SELECT
    status,
    COUNT(*) AS record_count
FROM some_table
GROUP BY status
ORDER BY record_count DESC;
""",
    ),

    PromptExample(
        intents={
            QueryIntent.COMPARISON,
            QueryIntent.TIME_SERIES,
            QueryIntent.AGGREGATION,
        },
        question="Show month-over-month value changes",
        sql="""
WITH monthly_values AS (
    SELECT
        DATE_TRUNC('month', created_at) AS month,
        SUM(value) AS total_value
    FROM some_table
    GROUP BY month
)
SELECT
    month,
    total_value,
    total_value
        - LAG(total_value) OVER (ORDER BY month)
        AS value_change
FROM monthly_values
ORDER BY month;
""",
    ),

    # --------------------------------------------------
    # FILTER + AGGREGATION
    # --------------------------------------------------

    PromptExample(
        intents={
            QueryIntent.FILTER,
            QueryIntent.AGGREGATION,
        },
        question="Count records created this month",
        sql="""
SELECT
    COUNT(*) AS record_count
FROM some_table
WHERE created_at >= DATE_TRUNC('month', CURRENT_DATE)
  AND created_at < DATE_TRUNC('month', CURRENT_DATE)
      + INTERVAL '1 month';
""",
    ),

    # --------------------------------------------------
    # SORT + AGGREGATION + GROUP BY
    # --------------------------------------------------

    PromptExample(
        intents={
            QueryIntent.SORT,
            QueryIntent.AGGREGATION,
            QueryIntent.GROUP_BY,
        },
        question="Show the top 5 categories by total value",
        sql="""
SELECT
    category,
    SUM(value) AS total_value
FROM some_table
GROUP BY category
ORDER BY total_value DESC
LIMIT 5;
""",
    ),

]