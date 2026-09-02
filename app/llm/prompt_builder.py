from app.models.intent import QueryIntent
from app.models.intent_analysis import IntentAnalysis
from app.models.prompt_example import PromptExample


class PromptBuilder:
    """
    Responsible for constructing structured prompts for the LLM.

    The PromptBuilder combines:

    - System instructions
    - Detected query intent
    - Intent confidence
    - Retrieved few-shot examples
    - Retrieved database schema
    - SQL generation rules
    - Safety constraints
    - User question

    Intent detection is treated as guidance only.
    The user's question and database schema remain authoritative.
    """

    # ======================================================
    # SYSTEM INSTRUCTIONS
    # ======================================================

    SYSTEM_INSTRUCTIONS = """
You are an expert PostgreSQL SQL generator.

Convert the user's natural language question into syntactically
correct PostgreSQL SQL.

Return ONLY the SQL query.

Do not explain your reasoning.

Do not use markdown.

Do not include comments.
"""

    # ======================================================
    # SQL RULES
    # ======================================================

    SQL_RULES = """
Rules:

- Use PostgreSQL syntax.
- Only use tables provided in the database schema.
- Only use columns provided in the database schema.
- Never invent tables, columns, relationships, or values.
- Use explicit JOIN statements.
- Prefer foreign-key relationships when joining tables.
- Avoid Cartesian products.
- Use table aliases when multiple tables are involved.
- Qualify columns when ambiguity is possible.
- Use DISTINCT only when required by the user's request.
- Use aggregate functions only when required.
- Use GROUP BY correctly when aggregation is used.
- Use ORDER BY when ordering is requested or implied.
- Use LIMIT for explicit Top-N requests.
- Use appropriate PostgreSQL date/time functions for time-series queries.
- Preserve the meaning of the user's question.
- Do not add unnecessary filters.
- Do not add unnecessary joins.
- Do not assume values that are not present in the question or schema.
- Prefer simple and efficient SQL over unnecessarily complex SQL.

If the question cannot be answered from the provided schema,
return:

SELECT 'Insufficient information';

"""


    AMBIGUITY_RULES = """
Ambiguity handling:

- Return SELECT 'Insufficient information'; only when the user's request is genuinely too vague or underspecified to determine one reliable SQL interpretation.

- Do not invent a table, metric, ranking criterion, aggregation, relationship, or business meaning when the user has not provided enough information.

- Requests such as "show totals", "show activity", or "show the best customers" are underspecified because they do not identify what should be totaled, what activity means, or what criterion defines "best".

- Do NOT return insufficient information merely because the request uses natural-language wording instead of exact schema column names.

- If the request clearly identifies an entity or operation that can be mapped to the provided schema, generate the SQL.

- Natural-language filters are sufficient when they map unambiguously to schema columns and SQL operators. Examples:
  - "after January 1, 2025" means a date comparison using >.
  - "before January 1, 2025" means a date comparison using <.
  - "more than 1000" means > 1000.
  - "not from Delhi" means a non-equality filter.

- Normalize clear natural-language date values into SQL-compatible date literals when necessary.

- Unsupported requested information that does not exist anywhere in the provided schema should still return exactly:

SELECT 'Insufficient information';
"""


    # ======================================================
    # SAFETY RULES
    # ======================================================

    SAFETY_RULES = """
Safety Constraints:

- Only generate SELECT statements.
- Never generate INSERT.
- Never generate UPDATE.
- Never generate DELETE.
- Never generate DROP.
- Never generate ALTER.
- Never generate CREATE.
- Never generate TRUNCATE.
- Never generate GRANT.
- Never generate REVOKE.
"""

    # ======================================================
    # INTENT RULES
    # ======================================================

    INTENT_RULES = {
        QueryIntent.LOOKUP: """
Return the requested rows.

Avoid unnecessary joins.

Select only the columns required to answer the user's question.
""",

        QueryIntent.AGGREGATION: """
For aggregation queries:

- Use appropriate aggregate functions such as COUNT, SUM, AVG,
  MIN, or MAX.
- Identify the correct numeric or categorical column from the schema.
- Use GROUP BY when aggregation is performed per entity or category.
- Do not aggregate columns that do not match the requested metric.
- Do not introduce unnecessary aggregation.
""",

        QueryIntent.GROUP_BY: """
For GROUP BY queries:

- Use GROUP BY whenever aggregating by categories or entities.
- Ensure all non-aggregated selected columns are grouped.
- Group by the correct entity or category requested by the user.
- Do not group by unnecessary columns.
""",

        QueryIntent.FILTER: """
For filtering queries:

- Apply filtering conditions using WHERE clauses.
- Use only columns available in the schema.
- Preserve the filtering conditions requested by the user.
- Avoid unnecessary filtering.
- Do not invent filter values.
""",

        QueryIntent.SORT: """
For sorting queries:

- Use ORDER BY.
- Determine the appropriate column from the user's wording and schema.
- Use DESC for highest, largest, newest, latest, or most recent values.
- Use ASC for lowest, smallest, oldest, or earliest values when appropriate.
- Use LIMIT when the user explicitly requests Top-N or a limited number
  of results.
- Do not invent a sorting column.
""",

        QueryIntent.TIME_SERIES: """
For time-series queries:

- Identify the appropriate date/time column from the schema.
- Use PostgreSQL date/time functions such as DATE_TRUNC when appropriate.
- Group results by the requested time period.
- Order results chronologically.
- Do not invent date columns.
- Do not assume a time granularity that contradicts the user's request.
""",

        QueryIntent.COMPARISON: """
For comparison queries:

- Identify the entities or metrics being compared.
- Use aggregation, JOINs, subqueries, or CTEs when required.
- Ensure both sides of the comparison use compatible metrics.
- Do not invent comparison values.
- Preserve the comparison requested by the user.
""",

        QueryIntent.JOIN: """
For JOIN queries:

- Join tables using known foreign-key relationships whenever possible.
- Use explicit JOIN ... ON syntax.
- Ensure JOIN conditions use the correct primary-key/foreign-key relationship.
- Avoid Cartesian products.
- Do not join unrelated tables merely because they are available in the schema.
- Use DISTINCT when the relationship can produce duplicate entities and
  the user's question asks for unique entities.
""",

        QueryIntent.UNKNOWN: """
Generate the simplest valid SQL based on the user's request.

Do not make unnecessary assumptions.

Use the database schema to determine which tables and columns are
available.

If the request cannot be answered reliably from the provided schema,
return:

SELECT 'Insufficient information';
""",
    }

    # ======================================================
    # PUBLIC API
    # ======================================================

    def build_prompt(
        self,
        schema: str,
        user_question: str,
        intent: IntentAnalysis,
        examples: list[PromptExample],
    ) -> str:
        """
        Construct the final prompt sent to the LLM.

        Parameters
        ----------
        schema:
            Formatted database schema.

        user_question:
            Original natural-language user question.

        intent:
            Intent analysis containing primary intent,
            secondary intents, scores and confidence.

        examples:
            Retrieved few-shot SQL examples.

        Returns
        -------
        str
            Fully constructed LLM prompt.
        """

        sections = [
            self._system_prompt(),
            self._intent_prompt(intent),
            self._examples_prompt(examples),
            self._schema_prompt(schema),
            self._rules_prompt(),
            self._safety_prompt(),
            self._question_prompt(user_question),
        ]

        return "\n\n".join(sections)

    # ======================================================
    # SECTION BUILDER
    # ======================================================

    @staticmethod
    def _section(
        title: str,
        content: str,
    ) -> str:
        """
        Create a consistently formatted prompt section.
        """

        return f"""
----------------------------------------
{title}
----------------------------------------

{content.strip()}
""".strip()

    # ======================================================
    # SYSTEM PROMPT
    # ======================================================

    def _system_prompt(self) -> str:
        """
        Build the system instruction section.
        """

        return self._section(
            "SYSTEM INSTRUCTIONS",
            self.SYSTEM_INSTRUCTIONS,
        )

    # ======================================================
    # INTENT PROMPT
    # ======================================================

    def _intent_prompt(
        self,
        intent: IntentAnalysis,
    ) -> str:
        """
        Build intent-specific instructions.

        Intent classification is treated as guidance rather than
        absolute truth.

        The user's actual question and database schema always
        take precedence.
        """

        instructions = []

        # --------------------------------------------------
        # Primary intent
        # --------------------------------------------------

        primary_instruction = self.INTENT_RULES.get(
            intent.primary,
            self.INTENT_RULES[QueryIntent.UNKNOWN],
        )

        instructions.append(
            f"Primary intent: {intent.primary.value}"
        )

        # --------------------------------------------------
        # Confidence
        # --------------------------------------------------

        instructions.append(
            f"Intent confidence: {intent.confidence}"
        )

        instructions.append(
            primary_instruction.strip()
        )

        # --------------------------------------------------
        # Secondary intents
        # --------------------------------------------------

        if intent.secondary:

            secondary_names = ", ".join(
                secondary.value
                for secondary in intent.secondary
            )

            instructions.append(
                f"Secondary intents: {secondary_names}"
            )

            for secondary in intent.secondary:

                secondary_instruction = self.INTENT_RULES.get(
                    secondary
                )

                if secondary_instruction:

                    instructions.append(
                        secondary_instruction.strip()
                    )

        # --------------------------------------------------
        # Intent priority rule
        # --------------------------------------------------

        instructions.append(
            """
Intent classification is guidance only.

Always prioritize:

1. The user's actual question.
2. The provided database schema.
3. Known foreign-key relationships.
4. SQL correctness.

Do not force an intent-specific SQL pattern if it does
not match the user's request.

If the detected intent conflicts with the user's question,
follow the user's question instead.
""".strip()
        )

        return self._section(
            "INTENT INSTRUCTIONS",
            "\n\n".join(instructions),
        )

    # ======================================================
    # EXAMPLES PROMPT
    # ======================================================

    def _examples_prompt(
        self,
        examples: list[PromptExample],
    ) -> str:
        """
        Format retrieved few-shot examples.
        """

        if not examples:

            return self._section(
                "EXAMPLES",
                "No examples available.",
            )

        formatted_examples = []

        for example in examples:

            formatted_examples.append(
                f"""
Question:
{example.question}

SQL:
{example.sql}
""".strip()
            )

        return self._section(
            "EXAMPLES",
            "\n\n".join(formatted_examples),
        )

    # ======================================================
    # SCHEMA PROMPT
    # ======================================================

    def _schema_prompt(
        self,
        schema: str,
    ) -> str:
        """
        Build the database schema section.
        """

        return self._section(
            "DATABASE SCHEMA",
            schema,
        )

    # ======================================================
    # SQL RULES PROMPT
    # ======================================================

    def _rules_prompt(self) -> str:
        """
        Build the SQL rules section.
        
        """
        
        content = "\n\n".join(
            [
                self.SQL_RULES,
                self.AMBIGUITY_RULES,
            ]
        )

        return self._section(
           "SQL RULES",
           content,
        )

    # ======================================================
    # SAFETY PROMPT
    # ======================================================

    def _safety_prompt(self) -> str:
        """
        Build the SQL safety section.
        """

        return self._section(
            "SAFETY RULES",
            self.SAFETY_RULES,
        )

    # ======================================================
    # USER QUESTION PROMPT
    # ======================================================

    def _question_prompt(
        self,
        question: str,
    ) -> str:
        """
        Build the final user-question section.

        The question is intentionally placed near the end of
        the prompt so that all relevant context is established
        before the model receives the actual task.
        """

        return self._section(
            "USER QUESTION",
            f"""
{question}

SQL:
""",
        )