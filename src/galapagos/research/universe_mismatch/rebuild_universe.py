import pandas as pd

def rebuild_canonical_universe(df_preds: pd.DataFrame, df_dataset: pd.DataFrame):
    # This is a placeholder for the "ideal" path we might find
    # For now, just return the inner join
    df = df_preds.join(df_dataset, how="inner", rsuffix="_ds")
    return df
