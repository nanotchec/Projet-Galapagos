from .universe_schema import CANONICAL_KEYS, ALLOWED_SELECTION_COLUMNS, FORBIDDEN_SELECTION_COLUMNS, ALLOWED_OUTCOME_COLUMNS

def get_dataset_split_policy():
    return {
        "version": "V1.37",
        "index_columns": CANONICAL_KEYS,
        "selection_columns": ALLOWED_SELECTION_COLUMNS,
        "outcome_columns": ALLOWED_OUTCOME_COLUMNS,
        "forbidden_selection_columns": FORBIDDEN_SELECTION_COLUMNS,
        "split_policy_status": "CANONICAL_DATASET_SPLIT_POLICY_DEFINED"
    }
