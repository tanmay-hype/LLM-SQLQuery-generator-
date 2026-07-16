from app.models.intent_analysis import IntentAnalysis
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
    def build_prompt(self, schema: str, user_question: str, intent: IntentAnalysis) -> str:
        intent_rules = self._intent_instructions(intent)
        """
        Constructs the final prompt for the LLM.

        Args:
            schema: Formatted database schema.
            user_question: Natural language query.
            intent: Analyzed query intent.

        Returns:
            Complete prompt for the LLM.
        """

        prompt = f"""
{cls.SYSTEM_INSTRUCTIONS}

----------------------------------------
DATABASE SCHEMA
----------------------------------------

Intent-Specific Instructions:
{intent_rules}


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
    
INTENT_RULES = {

    QueryIntent.LOOKUP:
"""
Return the requested rows.
Avoid unnecessary joins.
""",

    QueryIntent.AGGREGATION:
"""
Use aggregate functions when appropriate.
Include GROUP BY whenever required.
""",

    QueryIntent.TIME_SERIES:
"""
When analyzing dates,
group chronologically
and order results by time.
""",

    QueryIntent.SORT:
"""
Sort the results appropriately.
Use LIMIT when the user requests Top-N.
""",

    QueryIntent.COMPARISON:
"""
Generate SQL that compares datasets accurately.
Use joins or CTEs when needed.
""",

    QueryIntent.JOIN:
"""
Join related tables using foreign-key relationships.
Avoid Cartesian products.
""",

}

    def _intent_instructions(self, intent: IntentAnalysis) -> str:
        """
        Generates prompt instructions based on the detected intent.
        """
        instructions = []
        instructions.append(self.INTENT_RULES[intent.primary])
        for secondary in intent.secondary: 
            if secondary in intent.secondary:
                instructions.append(self.INTENT_RULES[secondary])
        return "\n".join(instructions)
    