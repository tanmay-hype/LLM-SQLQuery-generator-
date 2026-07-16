from enum import Enum

class QueryIntent(str, Enum):
    LOOKUP = "LOOKUP"
    AGGREGATION = "AGGREGATION"
    GROUP_BY = "GROUP_BY"
    JOIN = "JOIN"
    FILTER = "FILTER"
    SORT = "SORT"
    TIME_SERIES = "TIME_SERIES"
    COMPARISON = "COMPARISON"
    UNKNOWN = "UNKNOWN"
    
    