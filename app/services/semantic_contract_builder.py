from app.models.intent import QueryIntent
from app.models.intent_analysis import IntentAnalysis
from app.models.semantic_contract import SemanticContract


class SemanticContractBuilder:
    """
    Builds deterministic semantic requirements from
    the detected query intent.

    The generated contract is later used to verify that
    SQL actually satisfies the user's requested operation.
    """

    def build(
        self,
        intent: IntentAnalysis,
    ) -> SemanticContract:
        """
        Build a semantic contract from an IntentAnalysis.
        """

        intents = {
            intent.primary,
            *intent.secondary,
        }

        return SemanticContract(
            requires_aggregation=(
                QueryIntent.AGGREGATION
                in intents
            ),
            requires_group_by=(
                QueryIntent.GROUP_BY
                in intents
            ),
            requires_order_by=(
                QueryIntent.SORT
                in intents
            ),
            requires_join=(
                QueryIntent.JOIN
                in intents
            ),
        )