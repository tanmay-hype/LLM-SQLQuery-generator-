from app.llm.sql_generator import SQLGenerator


class SQLCorrector:
    """
    Corrects structurally invalid or semantically incorrect
    PostgreSQL SQL using a language model.

    The corrector is intentionally more constrained than the
    initial SQL generator.

    It must:
        - preserve the original user question
        - obey the supplied schema exactly
        - fix the validator's specific complaint
        - avoid inventing tables or columns
        - preserve the requested business metric
        - preserve time-series semantics when present
    """

    def __init__(self):
        self.sql_generator = SQLGenerator()

    # ======================================================
    # PUBLIC API
    # ======================================================

    def correct(
        self,
        question: str,
        schema: str,
        invalid_sql: str,
        validation_error: str,
    ) -> str:
        """
        Correct generated SQL using:

            - original question
            - provided schema
            - invalid SQL
            - validator feedback
        """

        prompt = self._build_prompt(
            question=question,
            schema=schema,
            invalid_sql=invalid_sql,
            validation_error=validation_error,
        )

        return self.sql_generator.generate_sql(
            prompt
        )

    # ======================================================
    # PROMPT
    # ======================================================

    def _build_prompt(
        self,
        question: str,
        schema: str,
        invalid_sql: str,
        validation_error: str,
    ) -> str:
        """
        Build a highly constrained SQL-correction prompt.

        The correction model must re-ground itself in the
        provided schema before attempting a rewrite.
        """

        return f"""
You are an expert PostgreSQL SQL correction system.

Your job is to repair an invalid or semantically incorrect
SQL query.

You MUST correct the SQL using ONLY information from the
provided database schema.

----------------------------------------
ORIGINAL USER QUESTION
----------------------------------------

{question}

----------------------------------------
INVALID SQL
----------------------------------------

{invalid_sql}

----------------------------------------
VALIDATION ERROR
----------------------------------------

{validation_error}

----------------------------------------
DATABASE SCHEMA
----------------------------------------

{schema}

----------------------------------------
CORRECTION PROCEDURE
----------------------------------------

Before producing the corrected SQL, internally verify:

1. Which tables are actually available in the provided schema.
2. Which columns actually exist in those tables.
3. Which foreign-key relationships are explicitly available.
4. Which existing column best represents the metric requested
   by the user.
5. Which existing date/time column best represents the time
   dimension requested by the user.
6. Whether aggregation, grouping, ordering, DISTINCT, or LIMIT
   are required by the original question.

Do NOT output this analysis.

Return only the corrected SQL.

----------------------------------------
SCHEMA GROUNDING RULES
----------------------------------------

- Use ONLY tables explicitly present in the provided schema.
- Use ONLY columns explicitly present in the provided schema.
- Never invent a table.
- Never invent a column.
- Never invent a date column.
- Never invent a metric column.
- Never invent a foreign-key relationship.
- If the invalid SQL references an unknown column, replace it
  only with a real column from the provided schema.
- If no valid replacement exists, return:

SELECT 'Insufficient information';

----------------------------------------
BUSINESS METRIC RULES
----------------------------------------

- Preserve the metric requested by the original user question.
- Do not replace a monetary metric with quantity or count.
- Do not replace quantity with monetary value.
- For words such as spending, spent, sales, revenue, amount,
  purchase value, or transaction value, prefer a real monetary
  column explicitly present in the schema.
- If a table contains a column such as total_amount and the
  question asks about spending, sales, revenue, or purchase
  value, prefer that column when it correctly represents the
  requested metric.
- Use SUM only when the question requests or implies an
  aggregated total.
- Use COUNT only when the question asks for counts, numbers of
  records, orders, items, or similar quantities.

----------------------------------------
TIME-SERIES RULES
----------------------------------------

- For monthly, daily, weekly, yearly, trend, history, recent,
  chronological, or time-based questions, identify an ACTUAL
  date/time column from the provided schema.
- Never assume columns such as created_at, updated_at,
  timestamp, date, or order_date unless that exact column
  appears in the supplied schema.
- If the schema contains order_date and the question concerns
  orders, purchases, sales activity, or purchase history over
  time, prefer order_date unless another schema column is more
  appropriate.
- Use PostgreSQL DATE_TRUNC when grouping by a requested time
  period.
- Order time-series results chronologically unless the user
  explicitly requests otherwise.

----------------------------------------
AGGREGATION AND GROUPING RULES
----------------------------------------

- If aggregation is performed per entity or category, use
  GROUP BY correctly.
- Every selected non-aggregated column must be valid under
  PostgreSQL grouping rules.
- Do not add aggregation unless required by the question.
- Do not remove aggregation when the validator indicates that
  the question requires it.

----------------------------------------
JOIN RULES
----------------------------------------

- Use explicit JOIN ... ON syntax.
- Use only relationships represented by the supplied schema.
- Prefer primary-key / foreign-key relationships.
- Do not add unrelated tables.
- Do not create Cartesian products.
- Add a JOIN only when it is required to answer the original
  question.

----------------------------------------
CORRECTION RULES
----------------------------------------

- Fix the exact validator problem.
- Preserve the meaning of the ORIGINAL USER QUESTION.
- Do not merely make the SQL structurally valid if it still
  answers the wrong question.
- Do not silently change the requested metric.
- Do not silently change the requested entity.
- Do not add unnecessary filters.
- Do not invent values.
- Use valid PostgreSQL syntax.
- Only generate SELECT statements.
- Never generate INSERT.
- Never generate UPDATE.
- Never generate DELETE.
- Never generate DROP.
- Never generate ALTER.
- Never generate CREATE.
- Never generate TRUNCATE.
- Do not include comments.
- Do not use markdown.
- Do not explain anything.
- Return ONLY the corrected SQL.

----------------------------------------
CORRECTED SQL
----------------------------------------

SQL:
""".strip()