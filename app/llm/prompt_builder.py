"""
Builds structured prompts for the LLM.

This module combines:
1. System instructions
2. Database schema
3. SQL generation rules
4. Safety constraints
5. User question
"""


class PromptBuilder:
    """Responsible for constructing structured prompts for the LLM."""

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

    @classmethod
    def build_prompt(cls, schema: str, user_question: str) -> str:
        """
        Constructs the final prompt for the LLM.

        Args:
            schema: Formatted database schema.
            user_question: Natural language query.

        Returns:
            Complete prompt for the LLM.
        """

        prompt = f"""
{cls.SYSTEM_INSTRUCTIONS}

----------------------------------------
DATABASE SCHEMA
----------------------------------------

{schema}

----------------------------------------
SQL RULES
----------------------------------------

{cls.SQL_RULES}

----------------------------------------
SAFETY RULES
----------------------------------------

{cls.SAFETY_RULES}

----------------------------------------
USER QUESTION
----------------------------------------

{user_question}

SQL:
"""

        return prompt.strip()
