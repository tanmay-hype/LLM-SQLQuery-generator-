import re

from app.core.config import settings

from app.schema.models.retrieval_result import RetrievalResult
from app.schema.models.schema_document import SchemaDocument
from app.schema.retrievers.base import BaseSchemaRetriever


class KeywordRetriever(BaseSchemaRetriever):
    """
    Retrieves relevant database tables using deterministic
    keyword matching against:

        - table names
        - table-name components
        - column names
        - foreign-key columns

    Scoring intentionally prioritizes direct entity/table
    matches over incidental foreign-key column matches.

    Example:

        "Show customer contact details"

    should rank:

        customers

    above:

        orders

    even though orders contains customer_id.
    """

    # ======================================================
    # SCORING
    # ======================================================

    # Direct entity/table match.
    #
    # customer -> customers
    # product  -> products
    # order    -> orders
    TABLE_ENTITY_MATCH = 12

    # Match against the main/head component of a compound
    # table name.
    #
    # item -> order_items
    TABLE_HEAD_MATCH = 6

    # Match against a non-head component.
    #
    # order -> order_items
    #
    # Deliberately weaker than a direct orders match.
    TABLE_COMPONENT_MATCH = 3

    # Weak substring fallback.
    TABLE_PARTIAL_MATCH = 2

    # Normal physical columns.
    COLUMN_EXACT_MATCH = 3
    COLUMN_PARTIAL_MATCH = 1

    # FK identifiers should provide supporting evidence,
    # not beat the table representing the entity itself.
    FOREIGN_KEY_EXACT_MATCH = 1

    # ======================================================
    # RETRIEVAL
    # ======================================================

    def retrieve(
        self,
        schema: dict,
        question: str,
        documents: list[SchemaDocument],
        top_k: int | None = None,
    ) -> RetrievalResult:
        """
        Retrieve relevant tables using keyword matching.

        Process:

            1. Tokenize and normalize the question.
            2. Score table names.
            3. Score physical columns.
            4. Give FK columns only supporting weight.
            5. Select high-confidence tables.
            6. Expand one FK level for relationship context.
            7. Preserve zero scores for expanded-only tables.

        Expanded tables are useful as schema context but
        do not count as direct retrieval evidence during RRF.
        """

        if not schema:
            return RetrievalResult(
                schema={},
                scores={},
            )

        if not question or not question.strip():
            return RetrievalResult(
                schema={},
                scores={},
            )

        if top_k is None:
            top_k = (
                settings.schema_retrieval_top_k
            )

        tokens = self._tokenize(
            question
        )

        scores = self._score_tables(
            schema=schema,
            tokens=tokens,
        )

        selected_tables = (
            self._select_tables(
                scores=scores,
                top_k=top_k,
            )
        )

        # --------------------------------------------------
        # Relationship expansion
        # --------------------------------------------------

        expanded_tables = (
            self._expand_related_tables(
                schema=schema,
                selected_tables=set(
                    selected_tables
                ),
            )
        )

        final_schema = {
            table_name: schema[table_name]
            for table_name in expanded_tables
            if table_name in schema
        }

        # --------------------------------------------------
        # Direct matches keep their real score.
        #
        # Tables included only through relationship expansion
        # receive zero so RRF does not interpret them as
        # independent retrieval evidence.
        # --------------------------------------------------

        final_scores = {
            table_name:( scores.get(
                table_name,
                0,
            )
            if table_name in selected_tables
            else 0
            )
            for table_name in final_schema
        }

        return RetrievalResult(
            schema=final_schema,
            scores=final_scores,
        )

    # ======================================================
    # TOKENIZATION / NORMALIZATION
    # ======================================================

    @classmethod
    def _tokenize(
        cls,
        question: str,
    ) -> list[str]:
        """
        Convert the question into normalized tokens.

        Examples:

            customers  -> customer
            products   -> product
            categories -> category
            prices     -> price
            ordered    -> order

        This deliberately uses lightweight deterministic
        normalization rather than an NLP dependency.
        """

        raw_tokens = re.findall(
            r"[a-zA-Z0-9_]+",
            question.lower(),
        )

        return [
            cls._normalize_word(token)
            for token in raw_tokens
            if token
        ]

    # ------------------------------------------------------

    @staticmethod
    def _normalize_word(
        word: str,
    ) -> str:
        """
        Apply conservative normalization for common English
        plural and verb forms.

        This is intentionally small and predictable.

        Examples:

            customers  -> customer
            products   -> product
            categories -> category
            ordered    -> order
        """

        word = word.lower().strip()

        if not word:
            return word

        # ----------------------------------------------
        # Plural: categories -> category
        # ----------------------------------------------

        if (
            word.endswith("ies")
            and len(word) > 4
        ):
            return (
                word[:-3]
                + "y"
            )

        # ----------------------------------------------
        # Past tense:
        # ordered -> order
        # ----------------------------------------------

        if (
            word.endswith("ed")
            and len(word) > 4
        ):
            candidate = word[:-2]

            if candidate:
                return candidate

        # ----------------------------------------------
        # Basic plural:
        #
        # customers -> customer
        # products  -> product
        # prices    -> price
        #
        # Avoid damaging words ending in "ss".
        # ----------------------------------------------

        if (
            word.endswith("s")
            and not word.endswith("ss")
            and len(word) > 3
        ):
            return word[:-1]

        return word

    # ======================================================
    # SCORING
    # ======================================================

    def _score_tables(
        self,
        schema: dict,
        tokens: list[str],
    ) -> dict[str, int]:
        """
        Calculate relevance scores for every physical table.
        """

        scores: dict[str, int] = {}

        for (
            table_name,
            table_info,
        ) in schema.items():

            score = 0

            # ----------------------------------------------
            # Table-name relevance
            # ----------------------------------------------

            score += self._table_score(
                table_name=table_name,
                tokens=tokens,
            )

            # ----------------------------------------------
            # Column relevance
            # ----------------------------------------------

            score += self._column_score(
                columns=table_info.get(
                    "columns",
                    [],
                ),
                foreign_keys=table_info.get(
                    "foreign_keys",
                    [],
                ),
                tokens=tokens,
            )

            if score > 0:
                scores[
                    table_name
                ] = score

        return scores

    # ======================================================
    # TABLE SELECTION
    # ======================================================

    @staticmethod
    def _select_tables(
        scores: dict[str, int],
        top_k: int,
    ) -> list[str]:
        """
        Select the strongest directly matched tables.

        Tables below the configured minimum score are not
        considered direct keyword-retrieval candidates.
        """

        min_score = (
            settings.schema_retrieval_min_score
        )

        filtered_scores = {
            table_name: score
            for (
                table_name,
                score,
            ) in scores.items()
            if score >= min_score
        }

        if not filtered_scores:
            return []

        ranked_tables = sorted(
            filtered_scores.items(),
            key=lambda item: (
                -item[1],
                item[0],
            ),
        )

        return [
            table_name
            for (
                table_name,
                _,
            ) in ranked_tables[
                :top_k
            ]
        ]

    # ======================================================
    # TABLE SCORING
    # ======================================================

    @classmethod
    def _table_score(
        cls,
        table_name: str,
        tokens: list[str],
    ) -> int:
        """
        Score a physical table name.

        Direct entity matches receive the strongest weight.

        Examples:

            customer -> customers
                strong entity match

            order -> order_items
                weak component match

            item -> order_items
                stronger head/entity match
        """

        score = 0

        raw_table_tokens = re.findall(
            r"\w+",
            table_name.lower().replace(
                "_",
                " ",
            ),
        )

        table_tokens = [
            cls._normalize_word(token)
            for token in raw_table_tokens
        ]

        if not table_tokens:
            return 0

        normalized_question_tokens = set(
            tokens
        )

        # --------------------------------------------------
        # Single-component table.
        #
        # customer -> customers
        # product  -> products
        # order    -> orders
        # --------------------------------------------------

        if len(table_tokens) == 1:

            table_entity = table_tokens[0]

            if (
                table_entity
                in normalized_question_tokens
            ):
                return (
                    cls.TABLE_ENTITY_MATCH
                )

            # Weak substring fallback.
            for token in tokens:

                if (
                    token
                    and (
                        token in table_entity
                        or table_entity in token
                    )
                ):
                    score += (
                        cls.TABLE_PARTIAL_MATCH
                    )

            return score

        # --------------------------------------------------
        # Compound table.
        #
        # Example:
        #
        # order_items -> ["order", "item"]
        # --------------------------------------------------

        # Exact phrase/entity-component coverage.
        if set(table_tokens).issubset(
            normalized_question_tokens
        ):
            score += (
                cls.TABLE_ENTITY_MATCH
            )

        head_token = table_tokens[-1]

        for token in tokens:

            if token == head_token:

                score += (
                    cls.TABLE_HEAD_MATCH
                )

            elif token in table_tokens:

                score += (
                    cls.TABLE_COMPONENT_MATCH
                )

            elif any(
                token
                and (
                    token in table_token
                    or table_token in token
                )
                for table_token
                in table_tokens
            ):

                score += (
                    cls.TABLE_PARTIAL_MATCH
                )

        return score

    # ======================================================
    # COLUMN SCORING
    # ======================================================

    @classmethod
    def _column_score(
        cls,
        columns: list[dict],
        foreign_keys: list[dict],
        tokens: list[str],
    ) -> int:
        """
        Score table columns.

        Foreign-key identifier columns intentionally receive
        lower scores than normal columns.

        This prevents:

            customer

        from making:

            orders.customer_id

        outrank:

            customers
        """

        score = 0

        foreign_key_columns = (
            cls._foreign_key_columns(
                foreign_keys
            )
        )

        for column in columns:

            column_name = column.get(
                "name"
            )

            if not column_name:
                continue

            normalized_column_name = (
                column_name.lower()
            )

            raw_column_tokens = re.findall(
                r"\w+",
                normalized_column_name.replace(
                    "_",
                    " ",
                ),
            )

            column_tokens = {
                cls._normalize_word(token)
                for token in raw_column_tokens
            }

            is_foreign_key = (
                column_name
                in foreign_key_columns
            )

            for token in tokens:

                # ------------------------------------------
                # Exact component match
                # ------------------------------------------

                if token in column_tokens:

                    if is_foreign_key:
                        score += (
                            cls.FOREIGN_KEY_EXACT_MATCH
                        )
                    else:
                        score += (
                            cls.COLUMN_EXACT_MATCH
                        )

                    continue

                # ------------------------------------------
                # Weak substring match
                #
                # Do not reward FK substring matches.
                # ------------------------------------------

                if is_foreign_key:
                    continue

                if any(
                    token
                    and (
                        token in column_token
                        or column_token in token
                    )
                    for column_token
                    in column_tokens
                ):
                    score += (
                        cls.COLUMN_PARTIAL_MATCH
                    )

        return score

    # ======================================================
    # FOREIGN-KEY COLUMN EXTRACTION
    # ======================================================

    @staticmethod
    def _foreign_key_columns(
        foreign_keys: list[dict],
    ) -> set[str]:
        """
        Return the local columns participating in foreign keys.
        """

        columns: set[str] = set()

        for foreign_key in foreign_keys:

            for column_name in (
                foreign_key.get(
                    "constrained_columns",
                    [],
                )
            ):

                if column_name:
                    columns.add(
                        column_name
                    )

        return columns

    # ======================================================
    # FOREIGN-KEY EXPANSION
    # ======================================================

    @staticmethod
    def _expand_related_tables(
        schema: dict,
        selected_tables: set[str],
    ) -> set[str]:
        """
        Expand directly selected tables by one relationship
        level.

        Expanded-only tables receive a retrieval score of zero
        and therefore do not influence Reciprocal Rank Fusion.

        The coordinator's graph-expansion stage remains
        responsible for preserving required bridge tables in
        the final hybrid schema.
        """

        if not selected_tables:
            return set()

        expanded = set(
            selected_tables
        )

        # --------------------------------------------------
        # Outgoing relationships
        # --------------------------------------------------

        for table_name in selected_tables:

            table_info = schema.get(
                table_name,
                {},
            )

            for foreign_key in (
                table_info.get(
                    "foreign_keys",
                    [],
                )
            ):

                referred_table = (
                    foreign_key.get(
                        "referred_table"
                    )
                )

                if (
                    referred_table
                    and referred_table in schema
                ):
                    expanded.add(
                        referred_table
                    )

        # --------------------------------------------------
        # Incoming relationships
        # --------------------------------------------------

        for (
            table_name,
            table_info,
        ) in schema.items():

            for foreign_key in (
                table_info.get(
                    "foreign_keys",
                    [],
                )
            ):

                referred_table = (
                    foreign_key.get(
                        "referred_table"
                    )
                )

                if (
                    referred_table
                    in selected_tables
                ):
                    expanded.add(
                        table_name
                    )

        return expanded