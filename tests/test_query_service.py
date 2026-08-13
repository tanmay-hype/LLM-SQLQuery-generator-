from unittest.mock import MagicMock

import pytest

from app.exceptions import SQLValidationError
from app.models.response import SQLResponse
from app.services.query_service import QueryService


# ============================================================
# FIXTURES
# ============================================================


@pytest.fixture
def query_service():
    """
    Create a QueryService instance with all external
    dependencies replaced by mocks.

    This keeps the test isolated from:

    - Real database
    - Gemini API
    - FAISS
    - SQL execution
    - Real LLM generation
    """

    service = QueryService(
        db_engine=MagicMock()
    )

    # --------------------------------------------------------
    # Mock schema pipeline
    # --------------------------------------------------------

    service.schema_loader = MagicMock()

    service.schema_document_builder = MagicMock()

    service.schema_index_service = MagicMock()

    service.schema_retriever = MagicMock()

    service.schema_compressor = MagicMock()

    service.schema_formatter = MagicMock()

    # --------------------------------------------------------
    # Mock intent / examples
    # --------------------------------------------------------

    service.intent_detector = MagicMock()

    service.example_retriever = MagicMock()

    # --------------------------------------------------------
    # Mock LLM
    # --------------------------------------------------------

    service.prompt_builder = MagicMock()

    service.sql_generator = MagicMock()

    service.sql_corrector = MagicMock()

    # --------------------------------------------------------
    # Mock validation / execution
    # --------------------------------------------------------

    service.sql_validator = MagicMock()

    service.sql_executor = MagicMock()

    return service


# ============================================================
# BASIC VALIDATION
# ============================================================


def test_empty_question_is_rejected(query_service):
    """
    QueryService should reject an empty question before
    starting the expensive pipeline.
    """

    with pytest.raises(ValueError):
        query_service.generate_sql("")


def test_whitespace_question_is_rejected(query_service):
    """
    Whitespace-only questions should also be rejected.
    """

    with pytest.raises(ValueError):
        query_service.generate_sql("   ")


# ============================================================
# SUCCESSFUL PIPELINE
# ============================================================


def test_generate_sql_success(query_service):
    """
    Test the complete successful QueryService pipeline.

    Expected flow:

        Question
          ↓
        Schema
          ↓
        Documents
          ↓
        Index
          ↓
        Intent
          ↓
        Retrieval
          ↓
        Compression
          ↓
        Formatting
          ↓
        Examples
          ↓
        Prompt
          ↓
        SQL generation
          ↓
        Validation
          ↓
        Execution
          ↓
        SQLResponse
    """

    # --------------------------------------------------------
    # Arrange
    # --------------------------------------------------------

    question = "Show customer names and email addresses"

    schema = {
        "customers": {
            "columns": [
                {
                    "name": "id",
                    "type": "INTEGER",
                },
                {
                    "name": "name",
                    "type": "VARCHAR",
                },
                {
                    "name": "email",
                    "type": "VARCHAR",
                },
            ],
            "primary_keys": {
                "constrained_columns": ["id"],
            },
            "foreign_keys": [],
        }
    }

    documents = [
        MagicMock()
    ]

    intent_analysis = MagicMock()

    intent_analysis.primary = MagicMock(
        name="LOOKUP"
    )

    intent_analysis.secondary = []

    relevant_schema = {
        "customers": schema["customers"]
    }

    compressed_schema = {
        "customers": {
            "columns": [
                {
                    "name": "name",
                    "type": "VARCHAR",
                },
                {
                    "name": "email",
                    "type": "VARCHAR",
                },
            ]
        }
    }

    formatted_schema = """
Table: customers
Columns:
- name (VARCHAR)
- email (VARCHAR)
"""

    examples = [
        MagicMock()
    ]

    prompt = "GENERATED PROMPT"

    generated_sql = """
SELECT
name,
email
FROM customers;
"""

    execution_results = [
        {
            "name": "Alice",
            "email": "alice@example.com",
        }
    ]

    # --------------------------------------------------------
    # Configure mocks
    # --------------------------------------------------------

    query_service.schema_loader.load_schema.return_value = (
        schema
    )

    query_service.schema_document_builder.build.return_value = (
        documents
    )

    query_service.schema_retriever.retrieve.return_value = (
        relevant_schema
    )

    query_service.intent_detector.detect.return_value = (
        intent_analysis
    )

    query_service.schema_compressor.compress.return_value = (
        compressed_schema
    )

    query_service.schema_formatter.format.return_value = (
        formatted_schema
    )

    query_service.example_retriever.retrieve.return_value = (
        examples
    )

    query_service.prompt_builder.build_prompt.return_value = (
        prompt
    )

    query_service.sql_generator.generate_sql.return_value = (
        generated_sql
    )

    query_service.sql_validator.validate.return_value = (
        generated_sql.strip()
    )

    query_service.sql_executor.execute.return_value = (
        execution_results
    )

    # --------------------------------------------------------
    # Act
    # --------------------------------------------------------

    response = query_service.generate_sql(
        question
    )

    # --------------------------------------------------------
    # Assert
    # --------------------------------------------------------

    assert isinstance(
        response,
        SQLResponse,
    )

    assert response.sql == generated_sql.strip()

    assert response.results == execution_results

    # --------------------------------------------------------
    # Verify schema pipeline
    # --------------------------------------------------------

    query_service.schema_loader.load_schema.assert_called_once()

    query_service.schema_document_builder.build.assert_called_once_with(
        schema
    )

    query_service.schema_index_service.initialize.assert_called_once_with(
        documents
    )

    # --------------------------------------------------------
    # Verify intent analysis
    # --------------------------------------------------------

    query_service.intent_detector.detect.assert_called_once_with(
        question
    )

    # --------------------------------------------------------
    # Verify schema retrieval
    # --------------------------------------------------------

    query_service.schema_retriever.retrieve.assert_called_once_with(
        schema=schema,
        question=question,
        documents=documents,
    )

    # --------------------------------------------------------
    # Verify compression
    # --------------------------------------------------------

    query_service.schema_compressor.compress.assert_called_once_with(
        schema=relevant_schema,
        question=question,
        intent=intent_analysis,
    )

    # --------------------------------------------------------
    # Verify formatting
    # --------------------------------------------------------

    query_service.schema_formatter.format.assert_called_once_with(
        compressed_schema
    )

    # --------------------------------------------------------
    # Verify examples
    # --------------------------------------------------------

    query_service.example_retriever.retrieve.assert_called_once_with(
        analysis=intent_analysis
    )

    # --------------------------------------------------------
    # Verify prompt construction
    # --------------------------------------------------------

    query_service.prompt_builder.build_prompt.assert_called_once_with(
        schema=formatted_schema,
        user_question=question,
        intent=intent_analysis,
        examples=examples,
    )

    # --------------------------------------------------------
    # Verify SQL generation
    # --------------------------------------------------------

    query_service.sql_generator.generate_sql.assert_called_once_with(
        prompt
    )

    # --------------------------------------------------------
    # Verify validation
    # --------------------------------------------------------

    query_service.sql_validator.validate.assert_called_once_with(
        generated_sql,
        schema,
    )

    # --------------------------------------------------------
    # Verify execution
    # --------------------------------------------------------

    query_service.sql_executor.execute.assert_called_once_with(
        generated_sql.strip()
    )


# ============================================================
# SQL VALIDATION FAILURE + CORRECTION
# ============================================================


def test_generate_sql_corrects_invalid_sql(
    query_service,
):
    """
    If the first generated SQL fails validation:

        SQLGenerator
             ↓
        SQLValidator
             ↓
        FAIL
             ↓
        SQLCorrector
             ↓
        SQLValidator
             ↓
        PASS
             ↓
        SQLExecutor

    """

    # --------------------------------------------------------
    # Arrange
    # --------------------------------------------------------

    question = "Show customer names"

    schema = {
        "customers": {
            "columns": [
                {
                    "name": "id",
                    "type": "INTEGER",
                },
                {
                    "name": "name",
                    "type": "VARCHAR",
                },
            ],
            "primary_keys": {
                "constrained_columns": ["id"],
            },
            "foreign_keys": [],
        }
    }

    documents = [
        MagicMock()
    ]

    intent_analysis = MagicMock()

    relevant_schema = {
        "customers": schema["customers"]
    }

    compressed_schema = {
        "customers": {
            "columns": [
                {
                    "name": "name",
                    "type": "VARCHAR",
                }
            ]
        }
    }

    formatted_schema = """
Table: customers
Columns:
- name (VARCHAR)
"""

    examples = []

    prompt = "GENERATED PROMPT"

    invalid_sql = """
SELECT customer_name
FROM customers;
"""

    corrected_sql = """
SELECT name
FROM customers;
"""

    execution_results = [
        {
            "name": "Alice",
        }
    ]

    validation_error = SQLValidationError(
        "Unknown column: customer_name"
    )

    # --------------------------------------------------------
    # Configure pipeline mocks
    # --------------------------------------------------------

    query_service.schema_loader.load_schema.return_value = (
        schema
    )

    query_service.schema_document_builder.build.return_value = (
        documents
    )

    query_service.schema_index_service.initialize.return_value = (
        None
    )

    query_service.intent_detector.detect.return_value = (
        intent_analysis
    )

    query_service.schema_retriever.retrieve.return_value = (
        relevant_schema
    )

    query_service.schema_compressor.compress.return_value = (
        compressed_schema
    )

    query_service.schema_formatter.format.return_value = (
        formatted_schema
    )

    query_service.example_retriever.retrieve.return_value = (
        examples
    )

    query_service.prompt_builder.build_prompt.return_value = (
        prompt
    )

    query_service.sql_generator.generate_sql.return_value = (
        invalid_sql
    )

    # First validation fails, second validation succeeds.
    query_service.sql_validator.validate.side_effect = [
        validation_error,
        corrected_sql.strip(),
    ]

    query_service.sql_corrector.correct.return_value = (
        corrected_sql
    )

    query_service.sql_executor.execute.return_value = (
        execution_results
    )

    # --------------------------------------------------------
    # Act
    # --------------------------------------------------------

    response = query_service.generate_sql(
        question
    )

    # --------------------------------------------------------
    # Assert
    # --------------------------------------------------------

    assert isinstance(
        response,
        SQLResponse,
    )

    assert response.sql == corrected_sql.strip()

    assert response.results == execution_results

    # --------------------------------------------------------
    # SQL generator called once
    # --------------------------------------------------------

    query_service.sql_generator.generate_sql.assert_called_once_with(
        prompt
    )

    # --------------------------------------------------------
    # Validator called twice
    # --------------------------------------------------------

    assert (
        query_service.sql_validator.validate.call_count
        == 2
    )

    # --------------------------------------------------------
    # Corrector called once
    # --------------------------------------------------------

    query_service.sql_corrector.correct.assert_called_once_with(
        question=question,
        schema=formatted_schema,
        invalid_sql=invalid_sql,
        validation_error=str(validation_error),
    )

    # --------------------------------------------------------
    # Corrected SQL executed
    # --------------------------------------------------------

    query_service.sql_executor.execute.assert_called_once_with(
        corrected_sql.strip()
    )


# ============================================================
# SQL CORRECTION FAILURE
# ============================================================


def test_generate_sql_raises_when_correction_fails(
    query_service,
):
    """
    If generated SQL fails validation and the corrected SQL
    also fails validation, QueryService should propagate the
    SQLValidationError.
    """

    # --------------------------------------------------------
    # Arrange
    # --------------------------------------------------------

    question = "Show customer names"

    schema = {
        "customers": {
            "columns": [
                {
                    "name": "id",
                    "type": "INTEGER",
                },
                {
                    "name": "name",
                    "type": "VARCHAR",
                },
            ],
            "primary_keys": {
                "constrained_columns": ["id"],
            },
            "foreign_keys": [],
        }
    }

    documents = [
        MagicMock()
    ]

    intent_analysis = MagicMock()

    relevant_schema = schema

    compressed_schema = schema

    formatted_schema = "Table: customers"

    examples = []

    prompt = "GENERATED PROMPT"

    invalid_sql = """
SELECT wrong_column
FROM customers;
"""

    corrected_sql = """
SELECT still_wrong
FROM customers;
"""

    first_error = SQLValidationError(
        "Unknown column: wrong_column"
    )

    second_error = SQLValidationError(
        "Unknown column: still_wrong"
    )

    # --------------------------------------------------------
    # Configure mocks
    # --------------------------------------------------------

    query_service.schema_loader.load_schema.return_value = (
        schema
    )

    query_service.schema_document_builder.build.return_value = (
        documents
    )

    query_service.intent_detector.detect.return_value = (
        intent_analysis
    )

    query_service.schema_retriever.retrieve.return_value = (
        relevant_schema
    )

    query_service.schema_compressor.compress.return_value = (
        compressed_schema
    )

    query_service.schema_formatter.format.return_value = (
        formatted_schema
    )

    query_service.example_retriever.retrieve.return_value = (
        examples
    )

    query_service.prompt_builder.build_prompt.return_value = (
        prompt
    )

    query_service.sql_generator.generate_sql.return_value = (
        invalid_sql
    )

    query_service.sql_validator.validate.side_effect = [
        first_error,
        second_error,
    ]

    query_service.sql_corrector.correct.return_value = (
        corrected_sql
    )

    # --------------------------------------------------------
    # Act + Assert
    # --------------------------------------------------------

    with pytest.raises(SQLValidationError):
        query_service.generate_sql(
            question
        )

    # --------------------------------------------------------
    # Validator called twice
    # --------------------------------------------------------

    assert (
        query_service.sql_validator.validate.call_count
        == 2
    )

    # --------------------------------------------------------
    # Corrector called once
    # --------------------------------------------------------

    query_service.sql_corrector.correct.assert_called_once()

    # --------------------------------------------------------
    # SQL must NOT be executed
    # --------------------------------------------------------

    query_service.sql_executor.execute.assert_not_called()


# ============================================================
# EMPTY SQL FROM LLM
# ============================================================


def test_generate_sql_rejects_empty_llm_response(
    query_service,
):
    """
    If the LLM returns an empty SQL string, QueryService
    should stop immediately.
    """

    # --------------------------------------------------------
    # Arrange
    # --------------------------------------------------------

    schema = {
        "customers": {
            "columns": [
                {
                    "name": "id",
                    "type": "INTEGER",
                }
            ],
            "primary_keys": {
                "constrained_columns": ["id"],
            },
            "foreign_keys": [],
        }
    }

    documents = [
        MagicMock()
    ]

    intent_analysis = MagicMock()

    query_service.schema_loader.load_schema.return_value = (
        schema
    )

    query_service.schema_document_builder.build.return_value = (
        documents
    )

    query_service.intent_detector.detect.return_value = (
        intent_analysis
    )

    query_service.schema_retriever.retrieve.return_value = (
        schema
    )

    query_service.schema_compressor.compress.return_value = (
        schema
    )

    query_service.schema_formatter.format.return_value = (
        "Table: customers"
    )

    query_service.example_retriever.retrieve.return_value = (
        []
    )

    query_service.prompt_builder.build_prompt.return_value = (
        "PROMPT"
    )

    query_service.sql_generator.generate_sql.return_value = (
        ""
    )

    # --------------------------------------------------------
    # Act + Assert
    # --------------------------------------------------------

    with pytest.raises(RuntimeError):
        query_service.generate_sql(
            "Show customers"
        )

    # --------------------------------------------------------
    # Validation should never happen
    # --------------------------------------------------------

    query_service.sql_validator.validate.assert_not_called()

    # --------------------------------------------------------
    # Execution should never happen
    # --------------------------------------------------------

    query_service.sql_executor.execute.assert_not_called()


# ============================================================
# INDEX REBUILD
# ============================================================


def test_rebuild_index(query_service):
    """
    Verify that QueryService correctly delegates index
    rebuilding to SchemaIndexService.
    """

    documents = [
        MagicMock(),
        MagicMock(),
    ]

    query_service.rebuild_index(
        documents
    )

    query_service.schema_index_service.rebuild.assert_called_once_with(
        documents
    )


def test_rebuild_index_rejects_empty_documents(
    query_service,
):
    """
    Rebuilding the index without documents should fail.
    """

    with pytest.raises(ValueError):
        query_service.rebuild_index([])

    query_service.schema_index_service.rebuild.assert_not_called()