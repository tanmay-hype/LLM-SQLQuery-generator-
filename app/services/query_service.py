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

from app.schema.retrievers.keywords_retriever import (
    KeywordRetriever,
)

from app.schema.retrievers.semantic_retriever import (
    SemanticRetriever,
)

from app.schema.schema_document_builder import (
    SchemaDocumentBuilder,
)

from app.schema.schema_formatter import SchemaFormatter

from app.schema.schema_loader import SchemaLoader

from app.schema.schema_retriever import SchemaRetriever

from app.schema.vector_store.faiss_store import (
    FAISSVectorStore,
)

from app.services.intent_detector import IntentDetector
from app.services.semantic_validator import SemanticValidator
from app.services.sql_executor import SQLExecutor
from app.services.validator import SQLValidator


logger = logging.getLogger(__name__)


class QueryService:
    """
    Coordinates the complete Natural Language → SQL workflow.

    Pipeline:

        Natural Language Question
                ↓
        Schema Loading
                ↓
        Schema Documents
                ↓
        Semantic Index
                ↓
        Intent Detection
                ↓
        Keyword + Semantic Schema Retrieval
                ↓
        Schema Compression
                ↓
        Schema Formatting
                ↓
        Few-Shot Example Retrieval
                ↓
        Prompt Construction
                ↓
        SQL Generation
                ↓
        SQL Validation
                ↓
        SQL Correction (if required)
                ↓
        SQL Execution
                ↓
        SQLResponse
    """

    def __init__(self, db_engine=engine):
        """
        Initialize all dependencies required by the SQL pipeline.

        Parameters
        ----------
        db_engine:
            SQLAlchemy database engine.
        """

        # ==================================================
        # DATABASE / SCHEMA
        # ==================================================

        self.schema_loader = SchemaLoader(db_engine)

        self.schema_document_builder = (
            SchemaDocumentBuilder()
        )

        self.schema_compressor = SchemaCompressor()

        self.schema_formatter = SchemaFormatter()

        # ==================================================
        # EMBEDDING SERVICE
        # ==================================================

        self.embedding_service = (
            GeminiEmbeddingService()
        )

        # ==================================================
        # VECTOR STORE
        # ==================================================

        self.vector_store = FAISSVectorStore()

        # ==================================================
        # SCHEMA INDEX
        # ==================================================

        self.schema_index_service = SchemaIndexService(
            embedding_service=self.embedding_service,
            vector_store=self.vector_store,
        )

        # ==================================================
        # SCHEMA RETRIEVERS
        # ==================================================

        self.keyword_retriever = KeywordRetriever()

        self.semantic_retriever = SemanticRetriever(
            embedding_service=self.embedding_service,
            vector_store=self.vector_store,
        )

        # ==================================================
        # SCHEMA RETRIEVER COORDINATOR
        # ==================================================

        self.schema_retriever = SchemaRetriever(
            retrievers=[
                self.keyword_retriever,
                self.semantic_retriever,
            ]
        )

        # ==================================================
        # INTENT DETECTION
        # ==================================================

        self.intent_detector = IntentDetector()

        # ==================================================
        # FEW-SHOT EXAMPLES
        # ==================================================

        self.example_repository = ExampleRepository()

        self.example_retriever = ExampleRetriever(
            self.example_repository
        )

        # ==================================================
        # LLM
        # ==================================================

        self.prompt_builder = PromptBuilder()

        self.sql_generator = SQLGenerator()

        self.sql_corrector = SQLCorrector()

        # ==================================================
        # SQL VALIDATION / EXECUTION
        # ==================================================

        self.sql_validator = SQLValidator()

        self.sql_executor = SQLExecutor()

        # ==================================================
        # SEMANTIC VALIDATION
        # ==================================================

        self.semantic_validator = SemanticValidator()

    # ======================================================
    # PUBLIC API
    # ======================================================

    def generate_sql(
        self,
        question: str,
    ) -> SQLResponse:
        """
        Execute the complete Natural Language → SQL pipeline.

        Parameters
        ----------
        question:
            Natural language database question.

        Returns
        -------
        SQLResponse
            Validated SQL and query execution results.
        """

        self._validate_question(question)

        logger.info(
            "Starting SQL generation pipeline."
        )

        # --------------------------------------------------
        # 1. Load database schema
        # --------------------------------------------------

        schema = self._load_schema()

        # --------------------------------------------------
        # 2. Build schema documents
        # --------------------------------------------------

        documents = self._build_schema_documents(
            schema
        )

        # --------------------------------------------------
        # 3. Initialize semantic schema index
        # --------------------------------------------------

        self._initialize_schema_index(
            documents
        )

        # --------------------------------------------------
        # 4. Detect intent
        # --------------------------------------------------

        intent_analysis = self._detect_intent(
            question
        )

        logger.info(
            "Detected primary intent: %s",
            intent_analysis.primary,
        )

        logger.info(
            "Detected secondary intents: %s",
            intent_analysis.secondary,
        )

        # --------------------------------------------------
        # 5. Retrieve relevant schema
        # --------------------------------------------------

        relevant_schema = (
            self._retrieve_schema(
                schema=schema,
                question=question,
                documents=documents,
            )
        )

        logger.info(
            "Relevant schema tables: %s",
            list(relevant_schema.keys()),
        )

        # --------------------------------------------------
        # 6. Compress schema
        # --------------------------------------------------

        compressed_schema = (
            self._compress_schema(
                schema=relevant_schema,
                question=question,
                intent=intent_analysis,
            )
        )

        # --------------------------------------------------
        # 7. Format schema
        # --------------------------------------------------

        formatted_schema = (
            self._format_schema(
                compressed_schema
            )
        )

        # --------------------------------------------------
        # 8. Retrieve few-shot examples
        # --------------------------------------------------

        examples = (
            self._retrieve_examples(
                intent_analysis
            )
        )

        logger.info(
            "Retrieved %d prompt examples.",
            len(examples),
        )

        # --------------------------------------------------
        # 9. Build prompt
        # --------------------------------------------------

        prompt = self._build_prompt(
            schema=formatted_schema,
            question=question,
            intent=intent_analysis,
            examples=examples,
        )

        # --------------------------------------------------
        # 10-12. Generate, validate and correct SQL
        # --------------------------------------------------

        validated_sql = (
            self._generate_and_validate_sql(
                prompt=prompt,
                question=question,
                formatted_schema=formatted_schema,
                full_schema=schema,
                intent=intent_analysis,
            )
        )

        # --------------------------------------------------
        # 13. Execute SQL
        # --------------------------------------------------

        results = self._execute_sql(
            validated_sql
        )

        # --------------------------------------------------
        # 14. Return response
        # --------------------------------------------------

        logger.info(
            "SQL generation pipeline completed successfully."
        )

        return SQLResponse(
            sql=validated_sql,
            results=results,
        )

    # ======================================================
    # PIPELINE STAGES
    # ======================================================

    @staticmethod
    def _validate_question(
        question: str,
    ) -> None:
        """
        Validate the user's question before starting
        the expensive retrieval / embedding / LLM pipeline.
        """

        if not question or not question.strip():
            raise ValueError(
                "Question cannot be empty."
            )

    # ------------------------------------------------------

    def _load_schema(self) -> dict:
        """
        Load the current database schema.
        """

        logger.info(
            "Loading database schema..."
        )

        schema = (
            self.schema_loader.load_schema()
        )

        if not schema:
            raise RuntimeError(
                "Database schema is empty."
            )

        logger.info(
            "Loaded %d database tables.",
            len(schema),
        )

        return schema

    # ------------------------------------------------------

    def _build_schema_documents(
        self,
        schema: dict,
    ) -> list[SchemaDocument]:
        """
        Convert the raw database schema into
        searchable schema documents.
        """

        logger.info(
            "Building schema documents..."
        )

        documents = (
            self.schema_document_builder.build(
                schema
            )
        )

        if not documents:
            raise RuntimeError(
                "No schema documents were created."
            )

        logger.info(
            "Created %d schema documents.",
            len(documents),
        )

        return documents

    # ------------------------------------------------------

    def _initialize_schema_index(
        self,
        documents: list[SchemaDocument],
    ) -> None:
        """
        Initialize or load the semantic schema index.
        """

        logger.info(
            "Initializing schema vector index..."
        )

        self.schema_index_service.initialize(
            documents
        )

        logger.info(
            "Schema vector index initialized."
        )

    # ------------------------------------------------------

    def _detect_intent(
        self,
        question: str,
    ):
        """
        Detect the primary and secondary query intents.
        """

        logger.info(
            "Detecting query intent..."
        )

        return self.intent_detector.detect(
            question
        )

    # ------------------------------------------------------

    def _retrieve_schema(
        self,
        schema: dict,
        question: str,
        documents: list[SchemaDocument],
    ) -> dict:
        """
        Retrieve the most relevant database schema
        using the configured schema retriever.

        SchemaRetriever acts as the coordinator for:

            KeywordRetriever
            SemanticRetriever
        """

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

        if not relevant_schema:
            logger.warning(
                "Schema retrieval returned no tables."
            )

        return relevant_schema

    # ------------------------------------------------------

    def _compress_schema(
        self,
        schema: dict,
        question: str,
        intent,
    ) -> dict:
        """
        Remove unnecessary schema information before
        sending the schema to the LLM.
        """

        logger.info(
            "Compressing relevant schema..."
        )

        compressed_schema = (
            self.schema_compressor.compress(
                schema=schema,
                question=question,
                intent=intent,
            )
        )

        logger.info(
            "Schema compression completed."
        )

        return compressed_schema

    # ------------------------------------------------------

    def _format_schema(
        self,
        schema: dict,
    ) -> str:
        """
        Convert compressed schema into the textual
        representation used by the LLM prompt.
        """

        logger.info(
            "Formatting schema for prompt..."
        )

        formatted_schema = (
            self.schema_formatter.format(
                schema
            )
        )

        return formatted_schema

    # ------------------------------------------------------

    def _retrieve_examples(
        self,
        intent,
    ):
        """
        Retrieve relevant few-shot SQL examples
        based on the detected query intent.
        """

        logger.info(
            "Retrieving prompt examples..."
        )

        return self.example_retriever.retrieve(
            analysis=intent
        )

    # ------------------------------------------------------

    def _build_prompt(
        self,
        schema: str,
        question: str,
        intent,
        examples,
    ) -> str:
        """
        Build the final SQL-generation prompt.
        """

        logger.info(
            "Building SQL generation prompt..."
        )

        return self.prompt_builder.build_prompt(
            schema=schema,
            user_question=question,
            intent=intent,
            examples=examples,
        )

    # ------------------------------------------------------

    def _generate_and_validate_sql(
        self,
        prompt: str,
        question: str,
        formatted_schema: str,
        full_schema: dict,
        intent,
    ) -> str:
        """
        Generate SQL and validate it.

        If validation fails, attempt one self-correction
        pass and validate the corrected SQL again.
         
         LLM generation
            ↓
        Structural validation
            ↓
        Semantic validation
            ↓
        SQL correction if required
            ↓
        Structural validation
            ↓
        Semantic validation
        """

        # --------------------------------------------------
        # Generate SQL
        # --------------------------------------------------

        logger.info(
            "Generating SQL using LLM..."
        )

        sql = self.sql_generator.generate_sql(
            prompt
        )

        if not sql or not sql.strip():
            raise RuntimeError(
                "LLM returned an empty SQL query."
            )

        # --------------------------------------------------
        # First structural validation
        # --------------------------------------------------

        logger.info(
            "Validating generated SQL..."
        )

        try:
            validated_sql = (
                self.sql_validator.validate(
                    sql,
                    full_schema,
                )
            )

        except SQLValidationError as exc:

            logger.warning(
                "Generated SQL failed validation. "
                "Attempting SQL correction."
            )

            # --------------------------------------------------
            # SQL Correction
            # --------------------------------------------------

            corrected_sql = (
                self.sql_corrector.correct(
                    question=question,
                    schema=formatted_schema,
                    invalid_sql=sql,
                    validation_error=str(exc),
                )
            )

            if (
                not corrected_sql
                or not corrected_sql.strip()
            ):
                raise SQLValidationError(
                    "SQL correction returned an empty query."
                )

            # --------------------------------------------------
            # Validate corrected SQL
            # --------------------------------------------------

            logger.info(
                "Validating corrected SQL..."
            )

            validated_sql = (
                self.sql_validator.validate(
                    corrected_sql,
                    full_schema,
                )
            )
            
            # ==================================================
            # SEMANTIC VALIDATION
            # ==================================================
        
        logger.info(
            "Performing semantic validation of SQL..."
        )
        
        semantic_result = (self.semantic_validator.validate(
            sql=validated_sql,
            schema=full_schema,
            question=question,
            intent=intent,
        )
        )
        
        if semantic_result.valid:
            logger.info(
                "Semantic validation passed."
            )
            return validated_sql
        
    # ==================================================
    # SEMANTIC CORRECTION
    # ==================================================
        
        semantic_error = "\n".join(semantic_result.errors)
        
        logger.warning(
            "Semantic validation failed: %s",
            semantic_error,
        )
        
        corrected_sql = (
            self.sql_corrector.correct(
                question=question,
                schema=formatted_schema,
                invalid_sql=validated_sql,
                validation_error=semantic_error,
            )
        )
        
        if (
            not corrected_sql
            or not corrected_sql.strip()
        ):
            raise SQLValidationError(
                "Semantic correction returned an empty query."
            )
            
    # ==================================================
    # SECOND STRUCTURAL VALIDATION
    # ==================================================
        
        corrected_sql = (
            self.sql_validator.validate(
                corrected_sql,
                full_schema,
            )
        )
        
    # ==================================================
    # SECOND SEMANTIC VALIDATION
    # ==================================================
        
        logger.info(
            "re-validating corrected SQL semantically..."
        )
        
        corrected_semantic_result = (
            self.semantic_validator.validate(
                sql=corrected_sql,
                schema=full_schema,
                question=question,
                intent=intent,
            )
        )
        
        if not corrected_semantic_result.valid:
            corrected_semantic_error = "\n".join(corrected_semantic_result.errors)
            raise SQLValidationError(
                f"Corrected SQL failed semantic validation: {corrected_semantic_error}"
            )
        
        logger.info(
            "Corrected SQL passed semantic validation."
        )
        
        return corrected_sql


    # ------------------------------------------------------

    def _execute_sql(
        self,
        sql: str,
    ):
        """
        Execute validated SQL against the database.
        """

        logger.info(
            "Executing validated SQL..."
        )

        results = (
            self.sql_executor.execute(
                sql
            )
        )

        logger.info(
            "SQL execution completed."
        )

        return results

    # ======================================================
    # INDEX MANAGEMENT
    # ======================================================

    def rebuild_index(
        self,
        documents: list[SchemaDocument],
    ) -> None:
        """
        Rebuild the semantic schema index.

        Use this when the database schema changes.
        """

        if not documents:
            raise ValueError(
                "Cannot rebuild schema index without documents."
            )

        logger.info(
            "Rebuilding schema vector index..."
        )

        self.schema_index_service.rebuild(
            documents
        )

        logger.info(
            "Schema vector index rebuilt successfully."
        )