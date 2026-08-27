import re


class RetrievalQueryExpander:
    """
    Expands natural-language retrieval queries with
    canonical database concepts.

    The expander is used only for schema retrieval.

    It does NOT modify the user's original question used
    for SQL generation.

    Example:

        "Which buyers spent the most?"

    becomes approximately:

        "Which buyers spent the most?
         customers customer orders order
         spending total_amount"

    This helps both deterministic keyword retrieval and
    embedding-based semantic retrieval understand common
    business-language aliases.
    """

    # ======================================================
    # PHRASE ALIASES
    # ======================================================

    PHRASE_ALIASES = {
        "sales activity": {
            "orders",
            "order",
            "total_amount",
        },
        "purchase history": {
            "orders",
            "order",
            "order_date",
        },
        "catalog items": {
            "products",
            "product",
        },
        "catalog item": {
            "products",
            "product",
        },
        "number of items": {
            "order_items",
            "quantity",
        },
        "number of products": {
            "order_items",
            "quantity",
            "products",
        },
        "sales value": {
            "total_amount",
            "unit_price",
            "products",
            "order_items",
        },
        "total purchases": {
            "orders",
            "total_amount",
        },
    }

    # ======================================================
    # TOKEN ALIASES
    # ======================================================

    TOKEN_ALIASES = {
        # --------------------------------------------------
        # Customer/entity vocabulary
        # --------------------------------------------------

        "buyer": {
            "customer",
            "customers",
        },
        "buyers": {
            "customer",
            "customers",
        },
        "person": {
            "customer",
            "customers",
        },
        "people": {
            "customer",
            "customers",
        },
        "client": {
            "customer",
            "customers",
        },
        "clients": {
            "customer",
            "customers",
        },
        "shopper": {
            "customer",
            "customers",
        },
        "shoppers": {
            "customer",
            "customers",
        },

        # --------------------------------------------------
        # Order / purchase vocabulary
        # --------------------------------------------------

        "purchase": {
            "order",
            "orders",
        },
        "purchases": {
            "order",
            "orders",
        },
        "purchased": {
            "order",
            "orders",
        },
        "buy": {
            "order",
            "orders",
        },
        "bought": {
            "order",
            "orders",
        },
        "transaction": {
            "order",
            "orders",
        },
        "transactions": {
            "order",
            "orders",
        },

        # --------------------------------------------------
        # Product vocabulary
        # --------------------------------------------------

        "merchandise": {
            "product",
            "products",
        },
        "catalog": {
            "product",
            "products",
        },

        # --------------------------------------------------
        # Financial vocabulary
        # --------------------------------------------------

        "spent": {
            "spending",
            "total_amount",
            "orders",
        },
        "spending": {
            "total_amount",
            "orders",
        },
        "revenue": {
            "total_amount",
            "unit_price",
        },
        "sales": {
            "total_amount",
        },
        "value": {
            "amount",
            "price",
            "total_amount",
        },

        # --------------------------------------------------
        # Quantity vocabulary
        # --------------------------------------------------

        "units": {
            "quantity",
            "order_items",
        },
    }

    # ======================================================
    # PUBLIC API
    # ======================================================

    def expand(
        self,
        question: str,
    ) -> str:
        """
        Return a retrieval-only expanded query.

        The original question is always preserved.
        """

        if not question or not question.strip():
            return question

        normalized_question = (
            question.lower()
        )

        concepts: set[str] = set()

        # ==================================================
        # 1. PHRASE EXPANSION
        # ==================================================

        for (
            phrase,
            aliases,
        ) in self.PHRASE_ALIASES.items():

            if phrase in normalized_question:

                concepts.update(
                    aliases
                )

        # ==================================================
        # 2. TOKEN EXPANSION
        # ==================================================

        tokens = re.findall(
            r"\b\w+\b",
            normalized_question,
        )

        for token in tokens:

            aliases = (
                self.TOKEN_ALIASES.get(
                    token
                )
            )

            if aliases:

                concepts.update(
                    aliases
                )

        # ==================================================
        # 3. NOTHING TO EXPAND
        # ==================================================

        if not concepts:
            return question

        # ==================================================
        # 4. BUILD RETRIEVAL QUERY
        # ==================================================

        concept_text = " ".join(
            sorted(
                concepts
            )
        )

        return (
            f"{question}\n"
            f"Retrieval concepts: "
            f"{concept_text}"
        )