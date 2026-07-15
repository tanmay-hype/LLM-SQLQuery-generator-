import logging

from app.core.database import engine

from app.llm.prompt_builder import PromptBuilder
from app.llm.sql_generator import SQLGenerator

from app.models.response import SQLResponse

from app.schema.schema_loader import SchemaLoader
from app.schema.schema_formatter import SchemaFormatter
from app.schema.schema_retriever import SchemaRetriever

from app.services.sql_executor import SQLExecutor
from app.services.validator import SQLValidator


logger = logging.getLogger(__name__)


class QueryService:
    """
    Coordinates the complete Natural Language → SQL workflow.
    """

    def __init__(self, db_engine=engine):
        self.schema_loader = SchemaLoader(db_engine)
        self.schema_retriever = SchemaRetriever()
        self.schema_formatter = SchemaFormatter()

        self.prompt_builder = PromptBuilder()
        self.sql_generator = SQLGenerator()

        self.sql_validator = SQLValidator()
        self.sql_executor = SQLExecutor()

    def generate_sql(self, question: str) -> SQLResponse:
        """
        Complete workflow:
        1. Load schema
        2. Retrieve relevant tables
        3. Format schema
        4. Build prompt
        5. Generate SQL
        6. Validate SQL
        7. Execute SQL
        8. Return response
        """

        logger.info("Loading database schema...")
        schema = self.schema_loader.load_schema()

        logger.info("Retrieving relevant schema...")
        relevant_schema = self.schema_retriever.retrieve(
            schema=schema,
            question=question,
        )

        logger.info("Formatting schema...")
        formatted_schema = self.schema_formatter.format(
            relevant_schema
        )

        logger.info("Building prompt...")
        prompt = self.prompt_builder.build_prompt(
            schema=formatted_schema,
            user_question=question,
        )

        logger.info("Generating SQL using LLM...")
        sql = self.sql_generator.generate_sql(prompt)

        logger.info("Validating generated SQL...")
        validated_sql = self.sql_validator.validate(
            sql,
            schema,
        )

        logger.info("Executing SQL...")
        results = self.sql_executor.execute(
            validated_sql
        )

        logger.info("Query completed successfully.")

        return SQLResponse(
            sql=validated_sql,
            results=results,
        )