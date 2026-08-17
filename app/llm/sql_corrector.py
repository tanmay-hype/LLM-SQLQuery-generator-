from app.llm.sql_generator import SQLGenerator


class SQLCorrector:
    """
    Corrects invalid or semantically incorrect SQL
    using a language model.
    """

    def __init__(self):
        self.sql_generator = SQLGenerator()

    def correct(
        self,
        question: str,
        schema: str,
        invalid_sql: str,
        validation_error: str,
    ) -> str:
        """
        Correct generated SQL using the original question,
        schema, generated SQL, and validation error.
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

    def _build_prompt(
        self,
        question: str,
        schema: str,
        invalid_sql: str,
        validation_error: str,
    ) -> str:

        return f"""
You are correcting a PostgreSQL SQL query.

The original user question was:

{question}

The generated SQL was:

{invalid_sql}

The validator detected the following problem:

{validation_error}

Database schema:

{schema}

Your task is to generate a corrected SQL query that answers
the ORIGINAL USER QUESTION.

Rules:

- Return ONLY the corrected SQL.
- Do not explain anything.
- Do not use markdown.
- Do not include comments.
- Only generate SELECT statements.
- Use only tables from the provided schema.
- Use only columns from the provided schema.
- Use known relationships between tables.
- Preserve the meaning of the original question.
- Use the correct business metric requested by the user.
- Do not replace the requested metric with a different metric.
- Do not add unnecessary joins.
- Do not add unnecessary filters.
- Do not invent values.
- Generate syntactically valid PostgreSQL.

Corrected SQL:
""".strip()