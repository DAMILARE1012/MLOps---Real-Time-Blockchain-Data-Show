import pandas as pd
import logging
import mlflow
from entities import address

def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Performs feature engineering (e.g., aggregates per address).
    """
    logger = logging.getLogger(__name__)
    logger.info("Starting feature engineering.")
    try:
        with mlflow.start_run(run_name="feature_engineering"):
            features = df.groupby('address').agg(
                total_value=pd.NamedAgg(column='total_value', aggfunc='sum'),
                tx_count=pd.NamedAgg(column='tx_hash', aggfunc='count'),
                avg_value=pd.NamedAgg(column='total_value', aggfunc='mean'),
            ).reset_index()
            logger.info(f"Engineered features for {len(features)} addresses.")
            mlflow.log_param("num_input_rows", len(df))
            mlflow.log_param("num_output_features", len(features))
            # Save features as artifact
            features.to_csv("features.csv", index=False)
            mlflow.log_artifact("features.csv")
        return features
    except Exception as e:
        logger.error(f"Error in feature engineering: {e}")
        return pd.DataFrame()  # Return empty DataFrame on error 