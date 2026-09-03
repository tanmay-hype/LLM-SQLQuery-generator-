import logging

from sqlalchemy import schema

from app.cache.base import BaseSQLCache
from app.core.config import settings
from app.core.database import engine
from app.exceptions import SQLValidationError

from app.llm.prompt_builder import PromptBuilder
from app.llm.sql_corrector import SQLCorrector
from app.llm.sql_generator import SQLGenerator

from app.llm.prompt_examples.repository import ExampleRepository
from app.llm.prompt_examples.retriever import ExampleRetriever

from app.models import intent_analysis
from app.models.response import SQLResponse
from app.models.intent_analysis import IntentAnalysis

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

    def __init__(self, db_engine=engine, sql_cache: BaseSQLCache | None = None,):
        """
        Initialize all dependencies required by the SQL pipeline.

        Parameters
        ----------
        db_engine:
            SQLAlchemy database engine.
        sql_cache:
            SQL cache to use for caching query results.
        """
        
        # ==================================================
        # SQL CACHE
        # ==================================================

        self.sql_cache = sql_cache

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
        # This is a critical step in the pipeline.
        # The detected intent will guide the rest of the
        # SQL generation process.
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
        # 5. Resolve SQL cache context
        # --------------------------------------------------
        
        schema_fingerprint = (self._get_schema_fingerprint())
        
        llm_provider, llm_model = (self._get_llm_cache_context())   
        
        logger.debug(
            "SQL cache context: provider=%s, model=%s, schema=%s",
            llm_provider,
            llm_model,
            schema_fingerprint[:12],
        )
        
        cache_key = self._build_sql_cache_key(
            question=question,
            schema_fingerprint=schema_fingerprint,
        )
        
        cached_sql = self._get_cached_sql(
            cache_key=cache_key,
            question=question,
            intent=intent_analysis,
            full_schema=schema,
        )
        
        if cached_sql is not None:
            
            results = self._execute_sql(
                cached_sql
            )
            
            logger.info(
                "SQL generation pipeline completed successfully (cache hit)."
            )
            
            return SQLResponse(
                sql=cached_sql,
                results=results,
            )
        
        # --------------------------------------------------
        # 6. Retrieve relevant schema
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
        # 7. Compress schema
        # --------------------------------------------------

        compressed_schema = (
            self._compress_schema(
                schema=relevant_schema,
                question=question,
                intent=intent_analysis,
            )
        )

        # --------------------------------------------------
        # 8. Format schema
        # --------------------------------------------------

        formatted_schema = (
            self._format_schema(
                compressed_schema
            )
        )

        # --------------------------------------------------
        # 9. Retrieve few-shot examples
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
        # 10. Build prompt
        # --------------------------------------------------

        prompt = self._build_prompt(
            schema=formatted_schema,
            question=question,
            intent=intent_analysis,
            examples=examples,
        )

        # --------------------------------------------------
        # 11. Generate, validate and correct SQL
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
        # 12. Store validated SQL
        # --------------------------------------------------
        
        self._store_cached_sql(
            cache_key=cache_key,
            sql=validated_sql,
        )
        
        # --------------------------------------------------
        # 13. Execute SQL
        # --------------------------------------------------

        results = self._execute_sql(
            validated_sql
        )

        # --------------------------------------------------
        #  14. Return response
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
    
    
    def _get_schema_fingerprint(
        self,
    ) -> str:
        """
         Return the fingerprint of the currently initialized
        database schema.

        The fingerprint is generated by SchemaIndexService
        from the same schema documents used by semantic
        retrieval.
        """
        
        fingerprint = (self.schema_index_service.schema_fingerprint)
        
        if not fingerprint:
            raise RuntimeError(
                "Schema fingerprint is empty. "
                "Ensure that the schema index is initialized."
            )
        return fingerprint
    
    @staticmethod
    def _get_llm_cache_context() -> tuple[str, str]:
        """
        Return the LLM provider and model used for SQL generation.

        This is used to create a cache key for SQL queries.
        """
        provider = (settings.llm_provider.strip().lower())
        
        if provider == "gemini":
            model = settings.gemini_model
        
        elif provider == "openai":
            model = settings.openai_model
        
        elif provider == "ollama":
            model = settings.ollama_model
        
        else:
            raise ValueError(
                f"Unsupported LLM provider: {provider}"
            )
        
        return provider, model
    
    def _build_sql_cache_key(
        self,
        question: str,
        schema_fingerprint: str,
    )-> str | None:
        """
        Build a unique cache key for the SQL query based on
        the question, schema fingerprint, LLM provider and model.

        Returns None if SQL caching is disabled.
        """

        if (not settings.sql_cache_enabled or 
            self.sql_cache is None):
            return None
        
        provider, model = self._get_llm_cache_context()
        
        return self.sql_cache.build_key(
            question=question,
            schema_fingerprint=schema_fingerprint,
            provider=provider,
            model=model,
            cache_version=settings.sql_cache_version,
        )
        
    def _get_cached_sql(
        self,
        cache_key: str | None,
        question: str,
        intent: IntentAnalysis,
        full_schema: dict,
    ) -> str | None:
        """
        Retrieve cached SQL for the given cache key.

        Returns None if no cached SQL is found or if caching is disabled.
        """

        if (cache_key is None or 
            self.sql_cache is None):
            return None
        
        cached_sql = self.sql_cache.get(
            cache_key 
        )
        
        if cached_sql is None:
            logger.info(
                "Production SQL cache miss for schema fingerprint",
            )
            return None
        
        logger.info(
            "Production SQL cache hit for schema fingerprint",
        )
        
        try:
            validated_sql = self.sql_validator.validate(
                cached_sql,
                full_schema,
            )
        except SQLValidationError as exc:
            logger.warning(
                "Cached SQL failed structural validation: %s",
                exc,
            )
            
            deleted = self.sql_cache.delete(
                cache_key
            )
            
            if deleted:
                logger.info(
                    "Deleted invalid cached SQL from production cache."
                )
                
            return None
        
        logger.info(
            "Cached SQL passed structural validation."
        )
        
        # ==================================================
        # SEMANTIC VALIDATION
        # ==================================================
        
        semantic_result = (
            self.semantic_validator.validate(
                question=question,
                sql=validated_sql,
                intent=intent,
                schema=full_schema,
            )
        )

        if not semantic_result.valid:

            semantic_error = "\n".join(
                semantic_result.errors
            )

            logger.warning(
                "Cached SQL failed semantic validation: %s",
                semantic_error,
            )

            deleted = self.sql_cache.delete(
                cache_key
            )

            if deleted:
                logger.info(
                    "Deleted semantically invalid cached SQL "
                    "from production cache."
                )

            return None

        logger.info(
            "Cached SQL passed semantic validation."
        )

        return validated_sql
    
    def _store_cached_sql(
        self,
        cache_key: str | None,
        sql: str,
    ) -> None:
        """
        Store the validated SQL in the cache for future queries.

        Does nothing if caching is disabled or if the cache key is None.
        """

        if (cache_key is None or 
            self.sql_cache is None):
            return
        
        self.sql_cache.set(
            cache_key,
            sql,
        )
        
        logger.info(
            "Stored validated SQL in production cache."
        )
        

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
        Generate SQL and validate it through the complete
        structural + semantic validation pipeline.

        Pipeline:

            LLM generation
                 ↓
            Structural validation
                 ↓
            Semantic validation
                 ↓
            Semantic correction if required
                 ↓
            Structural validation
                 ↓
            Semantic validation
                 ↓
            Return validated SQL
        """

        # ==================================================
        # 1. GENERATE SQL
        # ==================================================

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

        # ==================================================
        # 2. STRUCTURAL VALIDATION
        # ==================================================

        logger.info(
            "Validating generated SQL structurally..."
        )

        try:
            validated_sql = self.sql_validator.validate(
                sql,
                full_schema,
            )
        except SQLValidationError as exc:
            logger.warning(
                "Generated SQL failed structural validation: %s",
                exc,
            )

            logger.info(
                "Attempting structural SQL correction..."
            )

            corrected_sql = self.sql_corrector.correct(
                question=question,
                schema=formatted_schema,
                invalid_sql=sql,
                validation_error=str(exc),
            )

            if not corrected_sql or not corrected_sql.strip():
                raise SQLValidationError(
                    "Structural SQL correction returned an empty query."
                )

            # Validate corrected SQL structurally
            logger.info("Validating structurally corrected SQL...")

            validated_sql = self.sql_validator.validate(
                corrected_sql,
                full_schema,
            )

        # ==================================================
        # 3. SEMANTIC VALIDATION
        # ==================================================

        logger.info(
            "Performing semantic validation..."
        )

        semantic_result = (
            self.semantic_validator.validate(
                question=question,
                sql=validated_sql,
                intent=intent,
                schema=full_schema,
            )
        )

        # ==================================================
        # 4. SEMANTIC VALIDATION PASSED
        # ==================================================

        if semantic_result.valid:

            logger.info(
                "Semantic validation passed."
            )

            return validated_sql

        # ==================================================
        # 5. SEMANTIC VALIDATION FAILED
        # ==================================================

        semantic_error = "\n".join(
            semantic_result.errors
        )

        logger.warning(
            "Semantic validation failed: %s",
            semantic_error,
        )

        logger.info(
            "Attempting semantic SQL correction..."
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
                "Semantic SQL correction returned "
                "an empty query."
            )

        # ==================================================
        # 6. SECOND STRUCTURAL VALIDATION
        # ==================================================

        logger.info(
            "Structurally validating corrected SQL..."
        )

        corrected_sql = (
            self.sql_validator.validate(
                corrected_sql,
                full_schema,
            )
        )

        # ==================================================
        # 7. SECOND SEMANTIC VALIDATION
        # ==================================================

        logger.info(
            "Re-validating corrected SQL semantically..."
        )

        corrected_semantic_result = (
            self.semantic_validator.validate(
                question=question,
                sql=corrected_sql,
                intent=intent,
                schema=full_schema,
            )
        )

        # ==================================================
        # 8. CORRECTED SQL STILL INVALID
        # ==================================================

        if not corrected_semantic_result.valid:

            corrected_semantic_error = "\n".join(
                corrected_semantic_result.errors
            )

            logger.error(
                "Corrected SQL failed semantic validation: %s",
                corrected_semantic_error,
            )

            raise SQLValidationError(
                "Corrected SQL failed semantic validation: "
                f"{corrected_semantic_error}"
            )

        # ==================================================
        # 9. SUCCESS
        # ==================================================

        logger.info(
            "Corrected SQL passed structural and "
            "semantic validation."
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