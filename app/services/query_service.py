from app.models.response import SQLResponse


class QueryService:


    """Coordinates the full natural-language-to-SQL workflow."""

    def __init__(
        self,
        schema_loader,
        schema_formatter,
        prompt_builder,
        sql_generator,
        sql_validator,
        sql_executor,
    ):
        self.schema_loader = schema_loader
        self.schema_formatter = schema_formatter
        self.prompt_builder = prompt_builder
        self.sql_generator = sql_generator
        self.sql_validator = sql_validator
        self.sql_executor = sql_executor

    def generate_sql(self, question: str) -> SQLResponse:
        """
        Build the prompt, generate SQL, validate it, and execute it.
        """

        schema = self.schema_loader.load_schema()
        formatted_schema = self.schema_formatter.format(schema)
        prompt = self.prompt_builder.build_prompt(
            schema=formatted_schema,
            user_question=question,
        )
        sql = self.sql_generator.generate_sql(prompt)
        validated_sql = self.sql_validator.validate(sql, schema)
        results = self.sql_executor.execute(validated_sql)

        return SQLResponse(
            sql=validated_sql,
            results=results,
        )