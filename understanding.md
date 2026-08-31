# LLM SQL Generator - Comprehensive Technical Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Technology Stack](#technology-stack)
4. [Core Pipeline](#core-pipeline)
5. [Module Breakdown](#module-breakdown)
6. [Data Flow Diagrams](#data-flow-diagrams)
7. [Key Components](#key-components)
8. [Exception Handling](#exception-handling)
9. [Deployment](#deployment)
10. [Configuration](#configuration)

---

## Project Overview

**LLM SQL Generator** is an intelligent system that converts natural language questions into PostgreSQL queries using Large Language Models (LLMs). It combines multiple strategies including semantic retrieval, intent detection, prompt engineering, and multi-stage validation to generate accurate, executable SQL from natural language input.

### Key Objectives:
- Convert natural language questions to syntactically correct PostgreSQL SQL
- Support multiple LLM providers (Gemini, OpenAI, Ollama)
- Validate generated SQL before execution
- Cache results for performance optimization
- Handle schema retrieval intelligently using hybrid approaches
- Provide semantic validation of generated queries

---

## System Architecture

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         FastAPI Web Server                              │
│                     (Port 8000 - uvicorn)                               │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                    POST /generate-sql (JSON)
                                 │
                    ┌────────────▼────────────┐
                    │  API Routes Handler     │
                    │  (app/api/routes.py)    │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │  QueryService           │
                    │  (Core Pipeline)        │
                    └────────────┬────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
        ▼                        ▼                        ▼
    ┌────────────┐        ┌──────────────┐      ┌──────────────────┐
    │SQL Cache   │        │Schema Loader │      │Embedding Service │
    │(In-Memory) │        │(PostgreSQL)  │      │(Gemini)          │
    └────────────┘        └──────────────┘      └──────────────────┘
                                 │                        │
                                 │                        │
                          ┌──────▼──────────┐      ┌──────▼────────┐
                          │Schema Documents │      │FAISS Vector   │
                          │& Index          │      │Store (Disk)   │
                          └──────┬──────────┘      └─────────────┬─┘
                                 │                              │
                    ┌────────────┴──────────────┬───────────────┘
                    │                          │
                    ▼                          ▼
            ┌──────────────────┐      ┌──────────────────┐
            │Keyword Retriever │      │Semantic Retriever│
            │(Lexical Search)  │      │(Embedding Search)│
            └────────┬─────────┘      └────────┬─────────┘
                     │                         │
                     └────────────┬────────────┘
                                  │
                          ┌───────▼────────┐
                          │Schema Retriever│
                          │(RRF Fusion)    │
                          └───────┬────────┘
                                  │
                    ┌─────────────┴──────────────┐
                    │                           │
                    ▼                           ▼
        ┌───────────────────────┐      ┌──────────────────┐
        │Intent Detector        │      │Schema Compressor │
        │(Pattern Matching)     │      │(Smart Filtering) │
        └───────┬───────────────┘      └────────┬─────────┘
                │                              │
                └──────────────┬───────────────┘
                               │
                    ┌──────────▼───────────┐
                    │Prompt Builder        │
                    │(Few-shot Examples)   │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │LLM Provider          │
                    │• Gemini              │
                    │• OpenAI              │
                    │• Ollama              │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │SQL Validator         │
                    │(Syntax & Safety)     │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │SQL Corrector (if     │
                    │validation fails)     │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │SQL Executor          │
                    │(PostgreSQL)          │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │SQLResponse           │
                    │(SQL + Results)       │
                    └──────────────────────┘
```

---

## Technology Stack

### Core Technologies
| Component | Technology | Version |
|-----------|-----------|---------|
| Web Framework | FastAPI | 0.139.0 |
| ASGI Server | uvicorn | 0.50.2 |
| Python Version | Python | 3.12 |
| Database | PostgreSQL | 16 |
| Database Driver | psycopg2-binary | 2.9.12 |
| ORM | SQLAlchemy | 2.0.51 |

### ML & AI Components
| Component | Technology | Version |
|-----------|-----------|---------|
| Vector Store | FAISS | (cpu version) |
| Numerical Computing | NumPy | Latest |
| SQL Parser | sqlglot | 26.21.0 |
| LLM Providers | Google Genai, OpenAI | 1.30.0, 2.44.0 |
| Ollama Integration | httpx | 0.28.1 |
| Data Validation | Pydantic | 2.13.4 |

### Containerization & Deployment
| Component | Technology |
|-----------|-----------|
| Container Runtime | Docker |
| Orchestration | Docker Compose |
| Base Image | python:3.12-slim |

---

## Core Pipeline

### Complete Query Generation Pipeline

```
Natural Language Question
           │
           ▼
┌──────────────────────────────┐
│ 1. SQL Cache Lookup          │
│    Key: normalized question  │
└──────────────────────────────┘
           │
     [HIT] │ [MISS]
           │        │
         Return     │
           │        ▼
           │ ┌──────────────────────────────┐
           │ │ 2. Schema Loading            │
           │ │    SQLAlchemy Inspector      │
           │ │    → Tables, Columns, Keys   │
           │ └──────────────────────────────┘
           │        │
           │        ▼
           │ ┌──────────────────────────────┐
           │ │ 3. Schema Document Creation  │
           │ │    Build searchable objects  │
           │ │    with relationships        │
           │ └──────────────────────────────┘
           │        │
           │        ▼
           │ ┌──────────────────────────────┐
           │ │ 4. Schema Index (if needed)  │
           │ │    Generate embeddings       │
           │ │    Add to FAISS vector store │
           │ └──────────────────────────────┘
           │        │
           │        ▼
           │ ┌──────────────────────────────┐
           │ │ 5. Intent Detection          │
           │ │    Keyword scoring           │
           │ │    Pattern matching          │
           │ │    Intent: LOOKUP, AGGREGATE,│
           │ │            JOIN, FILTER, etc │
           │ └──────────────────────────────┘
           │        │
           │        ▼
           │ ┌──────────────────────────────┐
           │ │ 6. Schema Retrieval          │
           │ │    a) Query Expansion        │
           │ │    b) Keyword Retrieval      │
           │ │    c) Semantic Retrieval     │
           │ │    d) RRF Fusion             │
           │ │    e) Anchor Detection       │
           │ │    f) Relationship Expansion │
           │ └──────────────────────────────┘
           │        │
           │        ▼
           │ ┌──────────────────────────────┐
           │ │ 7. Schema Compression        │
           │ │    Remove unnecessary cols   │
           │ │    Keep PKs, FKs, metrics    │
           │ │    Preserve time columns     │
           │ └──────────────────────────────┘
           │        │
           │        ▼
           │ ┌──────────────────────────────┐
           │ │ 8. Few-Shot Example Retrieval│
           │ │    Get similar past examples │
           │ └──────────────────────────────┘
           │        │
           │        ▼
           │ ┌──────────────────────────────┐
           │ │ 9. Prompt Construction       │
           │ │    • System instructions     │
           │ │    • Intent info             │
           │ │    • Few-shot examples       │
           │ │    • Schema                  │
           │ │    • SQL rules               │
           │ │    • User question           │
           │ └──────────────────────────────┘
           │        │
           │        ▼
           │ ┌──────────────────────────────┐
           │ │ 10. SQL Generation (LLM)     │
           │ │     Provider routing:        │
           │ │     • Gemini                 │
           │ │     • OpenAI (GPT-4)         │
           │ │     • Ollama (local)         │
           │ └──────────────────────────────┘
           │        │
           │        ▼
           │ ┌──────────────────────────────┐
           │ │ 11. SQL Validation           │
           │ │     • Syntax check           │
           │ │     • Table validation       │
           │ │     • Column validation      │
           │ │     • Safety check (no DML)  │
           │ │     • No SQL comments        │
           │ └──────────────────────────────┘
           │        │
           │   [VALID]│[INVALID]
           │        │        │
           │        │        ▼
           │        │ ┌──────────────────────┐
           │        │ │ 12. SQL Correction   │
           │        │ │     LLM Feedback     │
           │        │ │     Iterative fix    │
           │        │ └──────────────────────┘
           │        │        │
           │        │        ▼
           │        │ Re-validate SQL
           │        │        │
           │        └────────┘
           │
           ▼
   ┌──────────────────────────────┐
   │ 13. Cache Storage            │
   │     Store validated SQL      │
   │     Normalized key mapping   │
   └──────────────────────────────┘
           │
           ▼
   ┌──────────────────────────────┐
   │ 14. SQL Execution            │
   │     Run against PostgreSQL   │
   │     Return results           │
   └──────────────────────────────┘
           │
           ▼
   ┌──────────────────────────────┐
   │ 15. Response Formatting      │
   │     {                        │
   │       "sql": "...",          │
   │       "results": [...]       │
   │     }                        │
   └──────────────────────────────┘
```

---

## Module Breakdown

### 1. API Layer (`app/api/`)

#### `routes.py`
**Purpose**: HTTP endpoint definitions

**Key Endpoints**:
- `POST /generate-sql` - Main endpoint to generate and execute SQL
  - Input: `SQLRequest` with `question` field
  - Output: `SQLResponse` with `sql` and `results` fields
- `GET /` - Health check endpoint

**Dependencies**:
- `QueryService` - Injected via FastAPI dependency
- `SQLRequest`, `SQLResponse` - Pydantic models

**Error Handling**:
- Returns HTTP errors via exception handlers
- Validates input with Pydantic

---

### 2. Core Configuration (`app/core/`)

#### `config.py`
**Purpose**: Centralized application configuration using Pydantic Settings

**Key Configuration Fields**:

| Field | Type | Default | Purpose |
|-------|------|---------|---------|
| `app_name` | str | "LLM SQL Generator" | App identifier |
| `debug` | bool | False | Debug mode |
| `database_url` | str | "" | PostgreSQL connection string |
| `postgres_user` | str | "postgres" | DB username |
| `postgres_password` | str | "postgres" | DB password |
| `postgres_db` | str | "llm_sql" | DB name |
| `llm_provider` | str | "gemini" | LLM provider (gemini/openai/ollama) |
| `openai_api_key` | str | "" | OpenAI API key |
| `openai_model` | str | "gpt-4.1" | OpenAI model |
| `gemini_api_key` | str | "" | Gemini API key |
| `gemini_model` | str | "gemini-2.5-pro" | Gemini model |
| `gemini_embedding_model` | str | "gemini-embedding-2" | Gemini embedding model |
| `ollama_base_url` | str | "http://ollama:11434" | Ollama service URL |
| `ollama_model` | str | "mistral" | Ollama model name |
| `schema_retrieval_top_k` | int | 5 | Top-K for schema retrieval |
| `sql_cache_size` | int | 256 | Max SQL cache entries |
| `compression_level` | str | "medium" | Schema compression aggressiveness |

**Loading Mechanism**:
- Loads from `.env` file via `python-dotenv`
- Environment variables override defaults
- Case-insensitive variable names

#### `database.py`
**Purpose**: Database engine and session management

**Key Components**:
- SQLAlchemy `create_engine()` - Creates PostgreSQL engine
- `SessionLocal` - Session factory for DB connections
- Handles connection pooling and lifecycle

#### `dependencies.py`
**Purpose**: Dependency injection for FastAPI

**Key Providers**:
- `get_sql_cache()` - Singleton SQLCache instance
- `get_query_service()` - Singleton QueryService with all dependencies
- `get_db()` - Database session provider (per-request)

#### `logging.py`
**Purpose**: Centralized logging configuration

**Setup**:
- Configures Python logging module
- Sets up handlers, formatters, log levels

---

### 3. Models (`app/models/`)

#### `request.py`
```python
class SQLRequest(BaseModel):
    question: str  # Natural language question
```

#### `response.py`
```python
class SQLResponse(BaseModel):
    sql: str                    # Generated SQL
    results: list[dict[str, Any]]  # Query results
```

#### `intent.py`
**Purpose**: Enum of query intent types

```python
class QueryIntent(Enum):
    LOOKUP = "LOOKUP"              # SELECT with no aggregation
    AGGREGATION = "AGGREGATION"    # SUM, COUNT, AVG, etc.
    GROUP_BY = "GROUP_BY"          # GROUP BY clause
    JOIN = "JOIN"                  # Multi-table join
    FILTER = "FILTER"              # WHERE clause focus
    SORT = "SORT"                  # ORDER BY focus
    TIME_SERIES = "TIME_SERIES"    # Time-based aggregation
    COMPARISON = "COMPARISON"      # Multiple datasets
    UNKNOWN = "UNKNOWN"            # Cannot determine
```

#### `intent_analysis.py`
**Purpose**: Result of intent detection

```python
class IntentAnalysis:
    primary_intent: QueryIntent
    confidence: float              # 0.0-1.0
    secondary_intents: list[QueryIntent]
    reasoning: str
```

#### `prompt_example.py`
**Purpose**: Few-shot learning examples

```python
class PromptExample:
    question: str                  # Example natural language
    sql: str                       # Corresponding SQL
    intent: QueryIntent            # Query intent
```

#### `error.py`
**Purpose**: Error response models

#### `error.py`
**Purpose**: Error response models

---

### 4. Services Layer (`app/services/`)

#### `query_service.py`
**Purpose**: Main orchestrator for the entire SQL generation pipeline

**Initialization** (Constructor):
- Sets up SQL cache (if provided)
- Initializes schema loader and builder
- Creates embedding service (Gemini-based)
- Sets up FAISS vector store
- Initializes schema index service
- Creates keyword and semantic retrievers
- Sets up intent detector
- Initializes example retriever
- Initializes prompt builder, SQL generator, and corrector
- Sets up validators

**Main Method: `generate_sql(question: str) -> SQLResponse`**

**Flow**:
1. Check cache using normalized question
2. Load schema from database
3. Create schema documents
4. Load or build schema index
5. Detect query intent
6. Retrieve relevant schema (hybrid: keyword + semantic)
7. Compress schema
8. Retrieve few-shot examples
9. Build prompt with context
10. Generate SQL via LLM
11. Validate syntax and safety
12. Correct if invalid
13. Execute SQL
14. Cache result
15. Return response

**Dependencies Owned**:
- SchemaLoader
- SchemaDocumentBuilder
- SchemaCompressor
- SchemaFormatter
- GeminiEmbeddingService
- FAISSVectorStore
- SchemaIndexService
- KeywordRetriever
- SemanticRetriever
- SchemaRetriever
- IntentDetector
- ExampleRepository
- ExampleRetriever
- PromptBuilder
- SQLGenerator
- SQLCorrector
- SQLValidator
- SemanticValidator
- SQLExecutor

#### `intent_detector.py`
**Purpose**: Detects user query intent using keyword scoring and pattern matching

**Algorithm**:
1. Split question into words
2. Score against predefined keyword dictionaries:
   - LOOKUP_KEYWORDS (show, list, find)
   - AGGREGATION_KEYWORDS (sum, total, count)
   - GROUP_BY_KEYWORDS (per, group, each)
   - SORT_KEYWORDS (top, highest, lowest)
   - TIME_SERIES_KEYWORDS (daily, monthly, yearly)
   - COMPARISON_KEYWORDS (vs, compared to)
   - FILTER_KEYWORDS (where, filter, with)
   - JOIN_KEYWORDS (cross, union, merge)

3. Calculate confidence scores per intent
4. Rank intents by confidence
5. Return primary and secondary intents

**Key Methods**:
- `detect(question: str) -> IntentAnalysis`

#### `validator.py`
**Purpose**: SQL syntax and safety validation

**Validation Steps**:
1. Type check (must be string)
2. Non-empty check
3. Single SELECT statement check
4. Forbidden keywords check (INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE, GRANT, REVOKE)
5. No SQL comments check
6. Syntax validation using sqlglot
7. Table existence check against schema
8. Column existence check against schema
9. Support for CTEs, aliases, subqueries

**Error Types**: `SQLValidationError` (custom exception)

#### `semantic_validator.py`
**Purpose**: Semantic correctness validation (does SQL match intent?)

**Validation Rules**:
- If aggregation intent: check for GROUP BY or aggregate functions
- If time series intent: check for date/time columns and grouping
- If join intent: verify multiple tables in FROM clause
- Check metric keywords match column names
- Verify filter columns exist

**Result**: `SemanticValidationResult` (valid: bool, errors: list[str])

#### `sql_executor.py`
**Purpose**: Execute validated SQL against PostgreSQL

**Key Method**:
- `execute(sql: str) -> List[Dict[str, Any]]`

**Process**:
1. Use SQLAlchemy connection
2. Execute with `text(sql)`
3. Map results to dictionaries
4. Handle SQLAlchemyError → `SQLExecutionError`

---

### 5. LLM Module (`app/llm/`)

#### `sql_generator.py`
**Purpose**: Main LLM interface for SQL generation

**Supported Providers**:
- **Gemini** - Google's generative AI
  - Uses `google.genai` library
  - Model: `gemini-2.5-pro` (configurable)
  - API Key: `GEMINI_API_KEY`
  
- **OpenAI** - OpenAI GPT models
  - Uses `openai` library
  - Model: `gpt-4.1` (configurable)
  - API Key: `OPENAI_API_KEY`
  
- **Ollama** - Local LLM via HTTP
  - Uses httpx for HTTP requests
  - Base URL: `http://ollama:11434`
  - Model: `mistral` (configurable)

**Main Method**: `generate_sql(prompt: str) -> str`

**Flow**:
1. Check `settings.llm_provider`
2. Route to appropriate provider
3. Call provider with prompt
4. Extract SQL from response
5. Handle provider-specific errors

**Provider Selection Logic**:
- Validates provider is configured
- Checks required API keys
- Falls back if primary provider unavailable

#### `prompt_builder.py`
**Purpose**: Constructs structured LLM prompts

**Components**:

**System Instructions**:
```
You are an expert PostgreSQL SQL generator.
Convert the user's natural language question into syntactically
correct PostgreSQL SQL.
Return ONLY the SQL query.
Do not explain your reasoning.
Do not use markdown.
Do not include comments.
```

**SQL Rules**:
- Use PostgreSQL syntax
- Only use provided tables/columns
- Never invent tables, columns, relationships
- Use explicit JOIN statements
- Prefer foreign-key relationships
- Avoid Cartesian products
- Use table aliases
- Qualify columns when ambiguous
- Use DISTINCT only when required

**Prompt Structure**:
1. System instructions
2. Query intent information
3. Few-shot examples (similar past questions)
4. Database schema (compressed)
5. SQL rules
6. User question

**Key Method**: `build(question, intent, schema, examples) -> str`

#### `sql_corrector.py`
**Purpose**: Corrects invalid SQL using LLM feedback

**Correction Constraints**:
- Preserve original user question
- Obey supplied schema exactly
- Fix specific validation error
- Avoid inventing tables/columns
- Preserve business metrics
- Maintain time-series semantics

**Main Method**: `correct(question, schema, invalid_sql, validation_error) -> str`

**Process**:
1. Build correction prompt with:
   - Original question
   - Database schema
   - Invalid SQL
   - Validator feedback
2. Call SQL generator with correction prompt
3. Return corrected SQL

#### `prompt_examples/`

**`repository.py`**:
- Stores and retrieves few-shot examples
- Example selection based on intent similarity

**`retriever.py`**:
- Finds similar examples for given question/intent
- Uses similarity matching

---

### 6. Schema Module (`app/schema/`)

#### `schema_loader.py`
**Purpose**: Extract database schema using SQLAlchemy Inspector

**Key Methods**:
- `get_tables()` → list[str]
- `get_columns(table)` → list[dict]
- `get_primary_keys(table)` → dict
- `get_foreign_keys(table)` → list[dict]
- `get_indexes(table)` → list[dict]

**Output Format**:
```python
{
    "table_name": {
        "columns": [
            {"name": "id", "type": "INTEGER", ...},
            {"name": "email", "type": "VARCHAR", ...}
        ],
        "primary_keys": {"constrained_columns": ["id"]},
        "foreign_keys": [
            {
                "constrained_columns": ["user_id"],
                "referred_table": "users",
                "referred_columns": ["id"]
            }
        ]
    }
}
```

#### `schema_formatter.py`
**Purpose**: Format schema dict into human-readable text

**Format**:
```
Table: users
Columns:
- id (INTEGER)
- email (VARCHAR)
Primary Key: id
Foreign Keys:
- user_id → orders.id
```

#### `schema_document_builder.py`
**Purpose**: Convert raw schema into searchable SchemaDocument objects

**SchemaDocument Contents**:
- Table name
- Column list
- Primary keys
- Foreign keys
- Outgoing relationships
- Incoming relationships
- Semantic hints

**Relationship Map Building**:
- Bidirectional relationship tracking
- Example: `orders.customer_id → customers.id` creates:
  - Forward: `orders` → `customers`
  - Reverse: `customers` → `orders`

**Key Method**: `build(schema: dict) -> list[SchemaDocument]`

#### `schema_retriever.py`
**Purpose**: Coordinates schema retrieval strategies

**Pipeline**:
1. Query expansion (adds retrieval concepts)
2. Run all configured retrievers:
   - Keyword-based retriever
   - Semantic/embedding-based retriever
3. Detect strong lexical anchors
4. Reciprocal Rank Fusion (RRF) to combine rankings
5. Anchor-aware seed selection
6. Relationship-aware bridge expansion
7. Return final relevant schema

**Key Method**: `retrieve(schema, question, documents) -> dict`

#### `query_expander.py`
**Purpose**: Expand natural language query with retrieval concepts

#### `schema_compressor.py`
**Purpose**: Remove non-essential columns while preserving critical ones

**Preserved Columns**:
- Primary keys (always)
- Foreign keys (always)
- Relationship columns (joins)
- Metric columns (SUM, AVG, COUNT targets)
- Time columns (dates, timestamps)
- Common semantic columns (name, status, etc.)

**Compression Levels**:
- **aggressive**: Maximum reduction, high risk
- **medium**: Balanced (default)
- **conservative**: Minimal reduction, comprehensive

**Compression Rules**:
- Remove non-critical columns beyond Top-K
- Keep business-critical identifiers
- Preserve temporal columns for time-series
- Maintain relationship integrity

**Key Method**: `compress(schema, intent, question) -> dict`

#### `vector_store/` - Vector Store Implementations

**`base.py`**:
```python
class BaseVectorStore(ABC):
    @abstractmethod
    def add(documents, embeddings) -> None
    @abstractmethod
    def search(embedding, top_k) -> list[SemanticMatch]
    @abstractmethod
    def save(index_path, metadata_path) -> None
    @abstractmethod
    def load(index_path, metadata_path) -> None
    @abstractmethod
    def exists(index_path, metadata_path) -> bool
```

**`faiss_store.py`**:
- FAISS (Facebook AI Similarity Search) implementation
- Efficient semantic similarity search
- Persistent storage (index + metadata)
- Normalized embeddings for cosine similarity
- Top-K retrieval with distance scoring

#### `embeddings/` - Embedding Services

**`base.py`**:
```python
class EmbeddingService(ABC):
    @abstractmethod
    def create_embeddings(text: list[str]) -> list[list[float]]
```

**`gemini_embedding_service.py`**:
- Google Gemini API for embeddings
- Model: `gemini-embedding-2`
- Batch embedding support
- Handles API key configuration

#### `retrievers/` - Retrieval Strategies

**`base.py`**:
```python
class BaseSchemaRetriever(ABC):
    @abstractmethod
    def retrieve(question, schema, documents) -> list[RetrievalResult]
```

**`keywords_retriever.py`**:
- Keyword/lexical matching
- TF-IDF style scoring
- Exact and partial matches
- Fast, deterministic retrieval

**`semantic_retriever.py`**:
- Embedding-based semantic search
- Uses vector store (FAISS)
- Similarity-based ranking
- Captures semantic relationships

#### `fusion/`

**`rrf.py`** - Reciprocal Rank Fusion:
- Combines multiple ranking sources
- Formula: RRF = Σ(1 / (k + rank))
- Merges keyword and semantic results
- Reduces individual biases

#### `indexing/`

**`schema_index_service.py`**:
- Manages FAISS index lifecycle
- Creates embeddings for all schema documents
- Saves/loads index from disk
- Lazy initialization

**`schema_fingerprint.py`**:
- Creates stable fingerprints of schema
- Detects schema changes
- Invalidates stale indexes

#### `persistence/`

**`metadata_store.py`**:
- Stores metadata alongside vector index
- Maps vector IDs to schema documents
- Enables result reconstruction

#### `models/`

**`schema_document.py`**:
```python
class SchemaDocument:
    table_name: str
    columns: list[str]
    primary_keys: list[str]
    foreign_keys: list[ForeignKey]
    related_tables: list[str]
    searchable_text: str  # Concatenated for keyword search
```

**`retrieval_result.py`**:
```python
class RetrievalResult:
    document: SchemaDocument
    score: float
    matched_fields: list[str]  # Which fields matched
```

**`semantic_match.py`**:
```python
class SemanticMatch:
    document: SchemaDocument
    similarity: float
```

**`retrieval_strategy.py`**:
```python
enum RetrievalStrategy:
    KEYWORD
    SEMANTIC
    HYBRID
```

---

### 7. Caching Module (`app/cache/`)

#### `base.py`
**Purpose**: Abstract cache interface

```python
class BaseSQLCache(ABC):
    @abstractmethod
    def get(key: str) -> str | None
    @abstractmethod
    def set(key: str, sql: str) -> None
    @abstractmethod
    def clear() -> None
    @abstractmethod
    def __len__() -> int
```

#### `sql_cache.py`
**Purpose**: Thread-safe, bounded LRU cache implementation

**Features**:
- **Bounded LRU**: Max size configurable (default: 256 entries)
- **Thread-safe**: Uses `RLock` for concurrent access
- **Question Normalization**:
  - Strips whitespace
  - Converts to lowercase
  - Removes extra spaces
  - Consistent punctuation
- **Key Generation**: SHA256 hash of normalized question
- **In-memory storage**: OrderedDict for LRU tracking

**Methods**:
- `get(key)` - Retrieve cached SQL
- `set(key, sql)` - Store validated SQL
- `clear()` - Remove all entries
- `__len__()` - Cache size

**LRU Eviction**:
- When cache reaches max size, oldest entry is removed
- Most recently used entries stay

---

### 8. Exception Handling (`app/exceptions/`)

#### `base.py`
**Purpose**: Base exception class for all custom exceptions

```python
class AppException(Exception):
    message: str
    status_code: int = 500
    details: Any | None = None
```

#### `database.py`
```python
class DatabaseError(AppException):
    pass
```

#### `llm.py`
```python
class LLMError(AppException):
    pass
```

#### `validation.py`
```python
class SQLValidationError(AppException):
    pass
```

#### `handlers.py`
**Purpose**: FastAPI exception handlers

**Handlers**:
- `AppException` handler: Returns JSON with message/details, appropriate status code
- Generic `Exception` handler: Returns 500 with generic error message, logs full traceback

**Features**:
- Structured error responses
- Logging integration
- Status code mapping
- Client-friendly error messages

---

### 9. Main Application (`app/`)

#### `main.py`
**Purpose**: FastAPI application factory and setup

**Setup**:
```python
app = FastAPI(
    title="LLM SQL Generator",
    version="1.0.0",
)

configure_logging()
register_exception_handlers(app)
app.include_router(router)
```

**Default Endpoint**: `GET /` returns `{"status": "ok"}`

---

## Data Flow Diagrams

### Request-Response Flow

```
User Request
   │
   ├─ POST /generate-sql
   │   └─ Body: { "question": "Show total sales by month" }
   │
   ▼
Router (routes.py)
   │
   ├─ Dependency: get_query_service()
   │
   ▼
QueryService.generate_sql(question)
   │
   ├─ [1] Cache Lookup
   │   ├─ Normalize: "show total sales by month"
   │   ├─ Generate Key: SHA256(normalized)
   │   └─ Hit? → Return cached SQL
   │
   ├─ [2] Database Schema Loading
   │   ├─ SchemaLoader.get_tables()
   │   ├─ SchemaLoader.get_columns(table)
   │   ├─ SchemaLoader.get_foreign_keys(table)
   │   └─ Result: { "tables": {...}, "columns": {...}, ... }
   │
   ├─ [3] Schema Documents & Index
   │   ├─ SchemaDocumentBuilder.build(schema)
   │   ├─ SchemaIndexService.build_index(documents)
   │   │   ├─ GeminiEmbeddingService.create_embeddings(texts)
   │   │   └─ FAISSVectorStore.add(documents, embeddings)
   │   └─ Result: Indexed schema ready for retrieval
   │
   ├─ [4] Intent Detection
   │   ├─ IntentDetector.detect(question)
   │   ├─ Keyword scoring against intent keywords
   │   ├─ Pattern matching
   │   └─ Result: IntentAnalysis(primary=AGGREGATION, confidence=0.95)
   │
   ├─ [5] Schema Retrieval
   │   ├─ QueryExpander.expand(question)
   │   ├─ KeywordRetriever.retrieve(expanded_question)
   │   ├─ SemanticRetriever.retrieve(expanded_question)
   │   ├─ ReciprocalRankFusion.fuse([keyword_results, semantic_results])
   │   ├─ Anchor detection & selection
   │   ├─ Relationship expansion
   │   └─ Result: Top-K relevant schema tables
   │
   ├─ [6] Schema Compression
   │   ├─ SchemaCompressor.compress(schema, intent, question)
   │   ├─ Preserve PK, FK, metric columns
   │   ├─ Remove non-essential columns
   │   └─ Result: Compact, relevant schema
   │
   ├─ [7] Few-Shot Examples
   │   ├─ ExampleRetriever.retrieve(question, intent)
   │   └─ Result: list[PromptExample]
   │
   ├─ [8] Prompt Construction
   │   ├─ PromptBuilder.build(
   │   │       question=question,
   │   │       intent=detected_intent,
   │   │       schema=compressed_schema,
   │   │       examples=examples
   │   │   )
   │   └─ Result: Full prompt with context
   │
   ├─ [9] SQL Generation
   │   ├─ SQLGenerator.generate_sql(prompt)
   │   ├─ Provider routing:
   │   │   ├─ if llm_provider == "gemini": genai.Client.generate_content()
   │   │   ├─ elif llm_provider == "openai": OpenAI.chat.completions.create()
   │   │   └─ elif llm_provider == "ollama": httpx POST to ollama:11434/api/generate
   │   ├─ Extract SQL from LLM response
   │   └─ Result: Generated SQL string
   │
   ├─ [10] SQL Validation
   │   ├─ SQLValidator.validate(sql, schema)
   │   ├─ Type check
   │   ├─ Syntax check (sqlglot parser)
   │   ├─ Table existence check
   │   ├─ Column existence check
   │   ├─ Safety check (no DDL/DML)
   │   └─ Valid? → Continue : Go to [11]
   │
   ├─ [11] SQL Correction (if invalid)
   │   ├─ SQLCorrector.correct(question, schema, invalid_sql, error)
   │   ├─ Build correction prompt
   │   ├─ Call SQL generator
   │   ├─ Recursively validate
   │   └─ Result: Corrected SQL
   │
   ├─ [12] Semantic Validation
   │   ├─ SemanticValidator.validate(sql, intent)
   │   ├─ Intent-specific checks
   │   └─ Warnings (non-fatal)
   │
   ├─ [13] Cache Storage
   │   ├─ SQLCache.set(key, validated_sql)
   │   └─ Add to LRU cache
   │
   ├─ [14] SQL Execution
   │   ├─ SQLExecutor.execute(validated_sql)
   │   ├─ SQLAlchemy connection.execute()
   │   ├─ Map results to dicts
   │   └─ Result: List[Dict[str, Any]]
   │
   └─ [15] Response Construction
       ├─ SQLResponse(sql=generated_sql, results=query_results)
       └─ Return JSON to client
```

### Cache Hit Path (Fast)

```
User Request
   │
   ▼
Router
   │
   ▼
QueryService.generate_sql()
   │
   ├─ Cache Lookup
   │   ├─ Normalize question
   │   ├─ Generate key
   │   └─ Hit! ✓
   │
   ├─ SQL Execution (cached SQL)
   │   └─ Execute directly
   │
   └─ Response (< 100ms typically)
```

---

## Key Components

### Intent Detection Algorithm

**Keyword-Based Scoring**:

```
Question: "Show total sales by month"

Words: ["show", "total", "sales", "by", "month"]

Scoring:
  LOOKUP:      show(1) = 1
  AGGREGATION: total(4) + sales(4) = 8
  GROUP_BY:    by(1) = 1
  TIME_SERIES: month(3) = 3

Results:
  AGGREGATION: 8 (primary)
  TIME_SERIES: 3 (secondary)
  GROUP_BY:    1 (secondary)
  LOOKUP:      1 (secondary)
```

### Schema Compression Example

```
Original Schema (orders table):
  id, customer_id, product_id, order_date, created_at,
  updated_at, status, amount, tax, discount, total_amount,
  notes, metadata, internal_flag, ...

Detected Intent: AGGREGATION + TIME_SERIES

Compressed Schema:
  id (PK),
  customer_id (FK),
  product_id (FK),
  order_date (TIME),
  amount (METRIC),
  total_amount (METRIC),
  status (COMMON)

Removed: tax, discount, notes, metadata, internal_flag, ...
```

### Reciprocal Rank Fusion (RRF)

```
Query: "customer orders"

Keyword Retriever Results:        Semantic Retriever Results:
  1. customers (rank 1)              1. orders (rank 1)
  2. orders (rank 2)                 2. customers (rank 2)
  3. invoices (rank 3)               3. payments (rank 3)

RRF Calculation (k=60):
  customers: 1/(60+1) + 1/(60+2) = 0.0164 + 0.0161 = 0.0325
  orders:    1/(60+2) + 1/(60+1) = 0.0161 + 0.0164 = 0.0325
  invoices:  1/(60+3) = 0.0159
  payments:  1/(60+3) = 0.0159

Final Ranking: [customers, orders, invoices, payments]
  (customers and orders tie, maintain relative order)
```

---

## Exception Handling

### Exception Hierarchy

```
Exception
├── AppException
│   ├── DatabaseError
│   ├── LLMError
│   ├── SQLValidationError
│   ├── SQLExecutionError
│   └── ...
└── External Exceptions
    ├── SQLAlchemyError
    ├── httpx.RequestError
    ├── ParseError (sqlglot)
    └── ...
```

### Error Flow

```
Unhandled Exception
        │
        ▼
Exception Middleware
        │
    ┌───┴───┐
    │       │
    ▼       ▼
AppException    Other Exception
    │               │
    ▼               ▼
Structured JSON   500 + Generic Message
+ Status Code     + Full Logging
+ Details Field
```

---

## Deployment

### Docker Architecture

```yaml
Services:
  app:                 # FastAPI application
    - Python 3.12
    - Port 8000
    - Depends: postgres, ollama
    - Volumes: /app/storage (schema index)
    
  postgres:            # Database
    - PostgreSQL 16
    - Port 5432
    - Volumes: postgres_data
    
  ollama:              # Local LLM
    - Ollama latest
    - Port 11434
    - Volumes: ollama_data
```

### Dockerfile

```dockerfile
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Configuration

**.env file**:
```env
# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=llm_sql

# LLM Provider Selection
LLM_PROVIDER=ollama  # gemini | openai | ollama

# Gemini Configuration
GEMINI_API_KEY=<your-key>
GEMINI_MODEL=gemini-2.5-pro

# OpenAI Configuration
OPENAI_API_KEY=<your-key>
OPENAI_MODEL=gpt-4.1

# Ollama Configuration
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=mistral

# Application Settings
SCHEMA_RETRIEVAL_TOP_K=5
SQL_CACHE_SIZE=256
COMPRESSION_LEVEL=medium
```

### Startup Process

1. **Container Startup**
   - Build image from Dockerfile
   - Start services (postgres, ollama, app)
   - Wait for postgres health check

2. **Application Initialization**
   - Load `.env` configuration
   - Initialize logging
   - Create database connection pool
   - Start FastAPI server on :8000

3. **First Request**
   - Initialize schema loader
   - Load database schema
   - Create embedding service
   - Initialize vector store
   - Build FAISS index (first time only)

---

## Configuration

### Environment Variables Precedence

```
1. Command-line/System environment variables (highest)
2. .env file
3. Pydantic defaults (lowest)

Example:
  export LLM_PROVIDER=openai  # System override
  .env: LLM_PROVIDER=gemini   # File value
  config.py: llm_provider="gemini"  # Default

  Result: LLM_PROVIDER=openai (system wins)
```

### Provider Configuration

| Provider | Key Env Var | Model Env Var | Requirements |
|----------|-----------|---------------|--------------|
| Gemini | GEMINI_API_KEY | GEMINI_MODEL | API key required, free tier available |
| OpenAI | OPENAI_API_KEY | OPENAI_MODEL | API key required, paid |
| Ollama | - | OLLAMA_MODEL | Local service at OLLAMA_BASE_URL |

---

## Performance Considerations

### Caching Strategy

**Cache Hit Benefit**:
- Eliminates: Schema loading, embedding, retrieval, LLM call, validation
- Typical speedup: **10-50x**
- Query time: < 100ms vs 2-5 seconds

**Cache Key Generation**:
- Normalizes question (lowercase, whitespace)
- SHA256 hash for key
- Collision probability: negligible

### Vector Store Optimization

**FAISS Benefits**:
- Approximate nearest neighbor search
- O(log n) search complexity
- Memory-efficient embeddings
- Persistent disk storage

**Index Rebuild Triggers**:
- Schema fingerprint mismatch
- Missing vector store files
- Manual invalidation

### Async Considerations

- Currently synchronous (FastAPI blocking)
- Could be optimized with async/await
- Database operations are I/O bound
- LLM calls are network I/O bound

---

## File Organization Summary

### Directory Structure
```
llm-sql-generator/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI app setup
│   ├── api/
│   │   └── routes.py            # API endpoints
│   ├── cache/
│   │   ├── base.py              # Cache interface
│   │   └── sql_cache.py         # LRU cache implementation
│   ├── core/
│   │   ├── config.py            # Pydantic settings
│   │   ├── database.py          # SQLAlchemy engine
│   │   ├── dependencies.py      # FastAPI dependencies
│   │   └── logging.py           # Logging setup
│   ├── exceptions/
│   │   ├── base.py              # AppException base class
│   │   ├── database.py
│   │   ├── llm.py
│   │   ├── validation.py
│   │   └── handlers.py          # Exception handlers
│   ├── llm/
│   │   ├── sql_generator.py     # LLM interface (Gemini/OpenAI/Ollama)
│   │   ├── prompt_builder.py    # Prompt construction
│   │   ├── sql_corrector.py     # Error correction
│   │   └── prompt_examples/
│   │       ├── repository.py    # Example storage
│   │       └── retriever.py     # Example retrieval
│   ├── models/
│   │   ├── request.py           # SQLRequest
│   │   ├── response.py          # SQLResponse
│   │   ├── intent.py            # QueryIntent enum
│   │   ├── intent_analysis.py   # Intent detection result
│   │   ├── prompt_example.py    # Few-shot example
│   │   └── error.py             # Error models
│   ├── schema/
│   │   ├── schema_loader.py     # Database introspection
│   │   ├── schema_formatter.py  # Schema formatting
│   │   ├── schema_document_builder.py  # Document creation
│   │   ├── schema_retriever.py  # Retrieval orchestrator
│   │   ├── query_expander.py    # Query expansion
│   │   ├── schema_compressor.py # Column filtering
│   │   ├── vector_store/
│   │   │   ├── base.py          # Vector store interface
│   │   │   └── faiss_store.py   # FAISS implementation
│   │   ├── embeddings/
│   │   │   ├── base.py          # Embedding interface
│   │   │   └── gemini_embedding_service.py
│   │   ├── retrievers/
│   │   │   ├── base.py          # Retriever interface
│   │   │   ├── keywords_retriever.py
│   │   │   └── semantic_retriever.py
│   │   ├── fusion/
│   │   │   └── rrf.py           # Reciprocal Rank Fusion
│   │   ├── indexing/
│   │   │   ├── schema_index_service.py
│   │   │   └── schema_fingerprint.py
│   │   ├── persistence/
│   │   │   └── metadata_store.py
│   │   └── models/
│   │       ├── schema_document.py
│   │       ├── retrieval_result.py
│   │       ├── semantic_match.py
│   │       └── retrieval_strategy.py
│   └── services/
│       ├── query_service.py     # Main orchestrator
│       ├── intent_detector.py   # Intent detection
│       ├── validator.py         # SQL syntax validation
│       ├── semantic_validator.py # Semantic checks
│       ├── sql_executor.py      # SQL execution
│       └── (more services)
├── docker-compose.yml           # Container orchestration
├── Dockerfile                   # Application image
├── requirements.txt             # Python dependencies
├── .env                         # Configuration
├── scripts/                     # Utility scripts
├── tests/                       # Test suite
└── storage/                     # FAISS indexes (runtime)
```

---

## Summary

**LLM SQL Generator** is a sophisticated system combining:
- **NLU**: Intent detection via pattern matching
- **Information Retrieval**: Hybrid keyword + semantic schema search with RRF fusion
- **LLM Integration**: Multi-provider support (Gemini, OpenAI, Ollama)
- **Validation**: Multi-stage validation (syntax, safety, semantic)
- **Performance**: Intelligent caching, schema compression, efficient vector search
- **Reliability**: Error correction, detailed logging, structured exception handling

The modular architecture allows easy extension and component substitution while maintaining clean separation of concerns.
