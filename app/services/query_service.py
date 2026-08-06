import logging

from app.core.database import engine

from app.exceptions import SQLValidationError

from app.llm.prompt_builder import PromptBuilder
from app.llm.sql_corrector import SQLCorrector
from app.llm.sql_generator import SQLGenerator

from app.llm.prompt_examples.repository import ExampleRepository
from app.llm.prompt_examples.retriever import ExampleRetriever

from app.models.response import SQLResponse

from app.schema.compression.schema_compressor import SchemaCompressor
from app.schema.embeddings.gemini_embedding_service import GeminiEmbeddingService
from app.schema.indexing.schema_index_service import SchemaIndexService
from app.schema.retrievers.keywords_retriever import KeywordRetriever
from app.schema.retrievers.semantic_retriever import SemanticRetriever
from app.schema.schema_document_builder import SchemaDocumentBuilder
from app.schema.schema_formatter import SchemaFormatter
from app.schema.schema_loader import SchemaLoader
from app.schema.schema_retriever import SchemaRetriever
from app.schema.vector_store.faiss_store import FAISSVectorStore

from app.services.intent_detector import IntentDetector
from app.services.sql_executor import SQLExecutor
from app.services.validator import SQLValidator


logger = logging.getLogger(__name__)


class QueryService:
    """
    Coordinates the complete Natural Language → SQL workflow.
    """

    def __init__(self, db_engine=engine):

        # -----------------------------
        # Schema
        # -----------------------------

        self.schema_loader = SchemaLoader(db_engine)
        self.schema_formatter = SchemaFormatter()
        self.schema_document_builder = SchemaDocumentBuilder()
        self.schema_compressor = SchemaCompressor()

        # -----------------------------
        # Semantic Retrieval
        # -----------------------------

        self.embedding_service = GeminiEmbeddingService()

        self.vector_store = FAISSVectorStore()

        self.schema_index_service = SchemaIndexService(
            embedding_service=self.embedding_service,
            vector_store=self.vector_store,
        )

        keyword_retriever = KeywordRetriever()

        semantic_retriever = SemanticRetriever(
            index_service=self.schema_index_service,
        )

        self.schema_retriever = SchemaRetriever(
            retrievers=[
                keyword_retriever,
                semantic_retriever,
            ]
        )

        # -----------------------------
        # Intent Detection
        # -----------------------------

        self.intent_detector = IntentDetector()

        # -----------------------------
        # Prompt Examples
        # -----------------------------

        self.example_repository = ExampleRepository()

        self.example_retriever = ExampleRetriever(
            self.example_repository
        )

        # -----------------------------
        # LLM
        # -----------------------------

        self.prompt_builder = PromptBuilder()

        self.sql_generator = SQLGenerator()

        self.sql_corrector = SQLCorrector()

        # -----------------------------
        # SQL Pipeline
        # -----------------------------

        self.sql_validator = SQLValidator()

        self.sql_executor = SQLExecutor()

    def generate_sql(
        self,
        question: str,
    ) -> SQLResponse:
        """
        Complete Natural Language → SQL pipeline.
        """

        logger.info("Loading database schema...")

        schema = self.schema_loader.load_schema()

        logger.info("Building schema documents...")

        documents = self.schema_document_builder.build(
            schema
        )

        logger.info("Initializing semantic index...")

        self.schema_index_service.initialize(
            documents
        )

        logger.info("Detecting query intent...")

        intent_analysis = self.intent_detector.detect(
            question
        )

        logger.info("Retrieving relevant schema...")

        relevant_schema = self.schema_retriever.retrieve(
            schema=schema,
            question=question,
            documents=documents,
        )

        logger.info("Compressing schema...")

        compressed_schema = self.schema_compressor.compress(
            schema=relevant_schema,
            question=question,
            intent=intent_analysis,
        )

        logger.info("Formatting schema...")

        formatted_schema = self.schema_formatter.format(
            compressed_schema
        )

        logger.info("Retrieving prompt examples...")

        examples = self.example_retriever.retrieve(
            analysis=intent_analysis,
        )

        logger.info("Building prompt...")

        prompt = self.prompt_builder.build_prompt(
            schema=formatted_schema,
            user_question=question,
            intent=intent_analysis,
            examples=examples,
        )

        logger.info("Generating SQL...")

        sql = self.sql_generator.generate_sql(
            prompt
        )

        logger.info("Validating SQL...")

        try:

            validated_sql = self.sql_validator.validate(
                sql,
                schema,
            )

        except SQLValidationError as exc:

            logger.warning(
                "Generated SQL failed validation. Attempting correction..."
            )

            corrected_sql = self.sql_corrector.correct(
                question=question,
                schema=formatted_schema,
                invalid_sql=sql,
                validation_error=str(exc),
            )

            logger.info("Validating corrected SQL...")

            validated_sql = self.sql_validator.validate(
                corrected_sql,
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