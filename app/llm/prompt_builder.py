from app.models.intent import QueryIntent
from app.models.intent_analysis import IntentAnalysis
from app.models.prompt_example import PromptExample


class PromptBuilder:
    """
    Responsible for constructing structured prompts for the LLM.
    """

    SYSTEM_INSTRUCTIONS = """
You are an expert PostgreSQL SQL generator.

Convert natural language into syntactically correct PostgreSQL SQL.

Return ONLY the SQL query.

Do not explain your reasoning.

Do not use markdown.

Do not include comments.
"""

    SQL_RULES = """
Rules:

- Use PostgreSQL syntax.
- Only use tables provided in the schema.
- Only use columns provided in the schema.
- Use explicit JOIN statements.
- Use aliases where appropriate.
- Never invent table names.
- Never invent column names.
- Prefer foreign-key relationships when joining tables.
- Generate efficient SQL whenever possible.
- If insufficient information exists, return:

SELECT 'Insufficient information';
"""

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
"""

    INTENT_RULES = {
        QueryIntent.LOOKUP: """
Return the requested rows.
Avoid unnecessary joins.
""",
        QueryIntent.AGGREGATION: """
Use aggregate functions when appropriate.
Include GROUP BY whenever required.
""",
        QueryIntent.GROUP_BY: """
Use GROUP BY whenever aggregating by categories.
Ensure all non-aggregated selected columns are grouped.
""",
        QueryIntent.FILTER: """
Apply filtering conditions using WHERE clauses.
Avoid unnecessary filtering.
""",
        QueryIntent.SORT: """
Sort the results appropriately.
Use ORDER BY.
Use LIMIT when the user requests Top-N.
""",
        QueryIntent.TIME_SERIES: """
When analyzing dates,
group chronologically
and order results by time.
""",
        QueryIntent.COMPARISON: """
Generate SQL that compares datasets accurately.
Use joins or CTEs when needed.
""",
        QueryIntent.JOIN: """
Join related tables using foreign-key relationships.
Avoid Cartesian products.
""",
        QueryIntent.UNKNOWN: """
Generate the simplest valid SQL based on the user's request.
Do not make unnecessary assumptions.
""",
    }

    def build_prompt(
        self,
        schema: str,
        user_question: str,
        intent: IntentAnalysis,
        examples: list[PromptExample],
    ) -> str:
        """
        Construct the final prompt sent to the LLM.
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

    def _section(
        self,
        title: str,
        content: str,
    ) -> str:
        """
        Create a formatted prompt section.
        """

        return f"""
----------------------------------------
{title}
----------------------------------------

{content.strip()}
""".strip()

    def _system_prompt(self) -> str:
        return self._section(
            "SYSTEM INSTRUCTIONS",
            self.SYSTEM_INSTRUCTIONS,
        )

    def _intent_prompt(
        self,
        intent: IntentAnalysis,
    ) -> str:
        """
        Build intent-specific instructions.
        """

        instructions = []

        if intent.primary in self.INTENT_RULES:
            instructions.append(
                self.INTENT_RULES[intent.primary].strip()
            )

        for secondary in intent.secondary:

            if secondary in self.INTENT_RULES:
                instructions.append(
                    self.INTENT_RULES[secondary].strip()
                )

        return self._section(
            "INTENT INSTRUCTIONS",
            "\n\n".join(instructions),
        )

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

    def _schema_prompt(
        self,
        schema: str,
    ) -> str:
        return self._section(
            "DATABASE SCHEMA",
            schema,
        )

    def _rules_prompt(self) -> str:
        return self._section(
            "SQL RULES",
            self.SQL_RULES,
        )

    def _safety_prompt(self) -> str:
        return self._section(
            "SAFETY RULES",
            self.SAFETY_RULES,
        )

    def _question_prompt(
        self,
        question: str,
    ) -> str:
        return self._section(
            "USER QUESTION",
            f"""
{question}

SQL:
""",
        )