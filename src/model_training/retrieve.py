from feast import FeatureStore
import pandas as pd
import logging
from sqlalchemy import create_engine

def get_training_data(feature_store_path: str, database_url: str = "postgresql://blockchain_user:blockchain_password@localhost:5432/blockchain_ml") -> pd.DataFrame:
    logger = logging.getLogger(__name__)
    logger.info("Starting feature retrieval from Feast.")
    try:
        # Connect to PostgreSQL and get addresses and event_timestamps
        engine = create_engine(database_url)
        entity_df = pd.read_sql("SELECT address, event_timestamp FROM address_features_table LIMIT 100", engine)
        logger.info(f"Sample entity_df for Feast: {entity_df.head()}")
        store = FeatureStore(repo_path=feature_store_path)
        features = store.get_historical_features(
            entity_df=entity_df,
            features=[
                "address_features:total_value",
                "address_features:tx_count",
                "address_features:avg_value"
            ]
        ).to_df()
        logger.info(f"Retrieved {len(features)} feature rows from Feast.")
        return features
    except Exception as e:
        logger.error(f"Error retrieving features from Feast: {e}")
        return pd.DataFrame()  # Return empty DataFrame on error 