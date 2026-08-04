from app.llm.sql_generator import SQLGenerator

class SQLCorrector:
    
    def __init__(self):
        self.sql_generator = SQLGenerator()
        
    """
    Corrects SQL queries using a language model.
    """

    def correct(
        self,
        question: str,
        schema: str,
        invalid_sql: str,
        validation_error: str,
    ) -> str:
        
        prompt = self._build_prompt(
            question,
            schema,
            invalid_sql,
            validation_error,
        )
        
        return self.sql_generator.generate_sql(prompt)
    
    
    def _build_prompt(
        self,
        question: str,
        schema: str,
        invalid_sql: str,
        validation_error: str,
    ) -> str:
        return f"""
    You generated the following SQL:
    
    {invalid_sql}
    
    The validator returned this error:
    
    {validation_error}
    
    Database schema:
    
    {schema}
    
    Original Question:
    
    {question}
    
    Correct the SQL:
    
    Rules:
    - Return ONLY the corrected SQL.
    - Do not explain anything.
    - Do not use markdown.
    - Do not include comments.
    - Only generate SELECT statements.
    - Use only tables and columns from the schema.
    
    SQL:
    """.strip()
    
    