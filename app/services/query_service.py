from app.models.response import SQLResponse

import logging
logger = logging.getLogger(__name__)

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
        logger.info("Loading database schema")
        schema = self.schema_loader.load_schema()
        logger.info("Formatting database schema")
        formatted_schema = self.schema_formatter.format(schema)
        logger.info("Building prompt")
        prompt = self.prompt_builder.build_prompt(
            schema=formatted_schema,
            user_question=question,
        )
        logger.info("Generating SQL using LLM")
        sql = self.sql_generator.generate_sql(prompt)
        logger.info("Validating SQL")
        validated_sql = self.sql_validator.validate(sql, schema)
        logger.info("Executing SQL")
        results = self.sql_executor.execute(validated_sql)

        return SQLResponse(
            sql=validated_sql,
            results=results,
        )