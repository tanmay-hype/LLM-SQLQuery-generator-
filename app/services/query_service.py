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
from app.schema.embeddings.gemini_embedding_service import (
    GeminiEmbeddingService,
)
from app.schema.indexing.schema_index_service import (
    SchemaIndexService,
)
from app.schema.models.schema_document import SchemaDocument
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

        # --------------------------------------------------
        # Database / Schema
        # --------------------------------------------------

        self.schema_loader = SchemaLoader(db_engine)

        self.schema_document_builder = (
            SchemaDocumentBuilder()
        )

        self.schema_compressor = SchemaCompressor()

        self.schema_formatter = SchemaFormatter()

        # --------------------------------------------------
        # Embeddings
        # --------------------------------------------------

        self.embedding_service = (
            GeminiEmbeddingService()
        )

        # --------------------------------------------------
        # Vector Store
        # --------------------------------------------------

        self.vector_store = FAISSVectorStore()

        # --------------------------------------------------
        # Schema Index
        # --------------------------------------------------

        self.schema_index_service = SchemaIndexService(
            embedding_service=self.embedding_service,
            vector_store=self.vector_store,
        )

        # --------------------------------------------------
        # Schema Retrieval
        #
        # IMPORTANT:
        # The same embedding service and vector store are
        # shared between SchemaIndexService and
        # SchemaRetriever.
        # --------------------------------------------------

        self.schema_retriever = SchemaRetriever(
            embedding_service=self.embedding_service,
            vector_store=self.vector_store,
        )

        # --------------------------------------------------
        # Intent Detection
        # --------------------------------------------------

        self.intent_detector = IntentDetector()

        # --------------------------------------------------
        # Few-Shot Examples
        # --------------------------------------------------

        self.example_repository = ExampleRepository()

        self.example_retriever = ExampleRetriever(
            self.example_repository
        )

        # --------------------------------------------------
        # LLM
        # --------------------------------------------------

        self.prompt_builder = PromptBuilder()

        self.sql_generator = SQLGenerator()

        self.sql_corrector = SQLCorrector()

        # --------------------------------------------------
        # SQL Validation / Execution
        # --------------------------------------------------

        self.sql_validator = SQLValidator()

        self.sql_executor = SQLExecutor()

    def generate_sql(
        self,
        question: str,
    ) -> SQLResponse:
        """
        Complete Natural Language → SQL pipeline.

        Pipeline:

        1. Load database schema
        2. Build schema documents
        3. Initialize/load semantic index
        4. Detect intent
        5. Retrieve relevant schema
        6. Compress schema
        7. Format schema
        8. Retrieve few-shot examples
        9. Build prompt
        10. Generate SQL
        11. Validate SQL
        12. Correct SQL if necessary
        13. Execute SQL
        14. Return response
        """

        # --------------------------------------------------
        # 1. Load database schema
        # --------------------------------------------------

        logger.info(
            "Loading database schema..."
        )

        schema = self.schema_loader.load_schema()

        # --------------------------------------------------
        # 2. Build schema documents
        # --------------------------------------------------

        logger.info(
            "Building schema documents..."
        )

        documents = (
            self.schema_document_builder.build(
                schema
            )
        )

        # --------------------------------------------------
        # 3. Initialize semantic index
        # --------------------------------------------------

        logger.info(
            "Initializing schema vector index..."
        )

        self.schema_index_service.initialize(
            documents
        )

        # --------------------------------------------------
        # 4. Detect query intent
        # --------------------------------------------------

        logger.info(
            "Detecting query intent..."
        )

        intent_analysis = (
            self.intent_detector.detect(
                question
            )
        )

        # --------------------------------------------------
        # 5. Retrieve relevant schema
        # --------------------------------------------------

        logger.info(
            "Retrieving relevant schema..."
        )

        relevant_schema = (
            self.schema_retriever.retrieve(
                schema=schema,
                question=question,
                documents=documents,
            )
        )

        # --------------------------------------------------
        # 6. Compress schema
        # --------------------------------------------------

        logger.info(
            "Compressing relevant schema..."
        )

        compressed_schema = (
            self.schema_compressor.compress(
                schema=relevant_schema,
                question=question,
                intent=intent_analysis,
            )
        )

        # --------------------------------------------------
        # 7. Format schema
        # --------------------------------------------------

        logger.info(
            "Formatting schema for prompt..."
        )

        formatted_schema = (
            self.schema_formatter.format(
                compressed_schema
            )
        )

        # --------------------------------------------------
        # 8. Retrieve few-shot examples
        # --------------------------------------------------

        logger.info(
            "Retrieving prompt examples..."
        )

        examples = (
            self.example_retriever.retrieve(
                analysis=intent_analysis,
            )
        )

        # --------------------------------------------------
        # 9. Build prompt
        # --------------------------------------------------

        logger.info(
            "Building SQL generation prompt..."
        )

        prompt = self.prompt_builder.build_prompt(
            schema=formatted_schema,
            user_question=question,
            intent=intent_analysis,
            examples=examples,
        )

        # --------------------------------------------------
        # 10. Generate SQL
        # --------------------------------------------------

        logger.info(
            "Generating SQL using LLM..."
        )

        sql = self.sql_generator.generate_sql(
            prompt
        )

        # --------------------------------------------------
        # 11. Validate SQL
        # --------------------------------------------------

        logger.info(
            "Validating generated SQL..."
        )

        try:

            validated_sql = (
                self.sql_validator.validate(
                    sql,
                    schema,
                )
            )

        # --------------------------------------------------
        # 12. Self-correction
        # --------------------------------------------------

        except SQLValidationError as exc:

            logger.warning(
                "Generated SQL failed validation. "
                "Attempting SQL correction..."
            )

            corrected_sql = (
                self.sql_corrector.correct(
                    question=question,
                    schema=formatted_schema,
                    invalid_sql=sql,
                    validation_error=str(exc),
                )
            )

            logger.info(
                "Validating corrected SQL..."
            )

            validated_sql = (
                self.sql_validator.validate(
                    corrected_sql,
                    schema,
                )
            )

        # --------------------------------------------------
        # 13. Execute SQL
        # --------------------------------------------------

        logger.info(
            "Executing validated SQL..."
        )

        results = self.sql_executor.execute(
            validated_sql
        )

        # --------------------------------------------------
        # 14. Return response
        # --------------------------------------------------

        logger.info(
            "Query completed successfully."
        )

        return SQLResponse(
            sql=validated_sql,
            results=results,
        )

    def rebuild_index(
        self,
        documents: list[SchemaDocument],
    ) -> None:
        """
        Rebuild the semantic schema index.

        Use this when the database schema changes.
        """

        logger.info(
            "Rebuilding schema vector index..."
        )

        self.schema_index_service.rebuild(
            documents
        )

        logger.info(
            "Schema vector index rebuilt successfully."
        )

