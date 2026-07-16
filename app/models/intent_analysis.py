from dataclasses import dataclass
from app.models.intent import QueryIntent

@dataclass
class IntentAnalysis:
    """
    Stores the detected intent information 
    """
    primary : QueryIntent
    secondary : list[QueryIntent]
    scores : dict[QueryIntent, int]
    confidence : float