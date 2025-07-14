import os
import logging
import mlflow
from .extract import extract_transactions
from .transform import engineer_features
from .feature_store import ingest_features_to_feast

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://blockchain_user:blockchain_password@localhost:5432/blockchain_ml")
FEATURE_STORE_PATH = "../../feature_repo"

mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment("blockchain_feature_engineering")

def run_feature_pipeline():
    logger = logging.getLogger(__name__)
    logger.info("Starting feature engineering pipeline.")
    try:
        df = extract_transactions(DATABASE_URL)
        features = engineer_features(df)
        ingest_features_to_feast(features, FEATURE_STORE_PATH)
        logger.info("Feature engineering pipeline completed successfully.")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
    run_feature_pipeline() 