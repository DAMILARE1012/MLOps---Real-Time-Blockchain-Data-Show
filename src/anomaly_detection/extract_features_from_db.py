import pandas as pd
from sqlalchemy import create_engine
from feature_extraction import extract_features_from_transaction
import ast
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
logger = logging.getLogger(__name__)

def main():
    database_url = "postgresql://blockchain_user:blockchain_password@localhost:5432/blockchain_ml"
    engine = create_engine(database_url)
    logger.info("Reading transactions from database...")
    transactions = pd.read_sql("SELECT raw_data FROM transactions LIMIT 10000", engine)
    logger.info(f"Loaded {len(transactions)} transactions.")
    features_list = []
    for idx, tx in transactions.iterrows():
        try:
            tx_dict = tx['raw_data']
            if isinstance(tx_dict, str):
                tx_dict = ast.literal_eval(tx_dict)
            features = extract_features_from_transaction(tx_dict)
            features_list.append(features)
        except Exception as e:
            logger.error(f"Error extracting features for transaction {idx}: {e}")
    if features_list:
        features_df = pd.concat(features_list, ignore_index=True)
        features_df.to_csv("historical_features.csv", index=False)
        logger.info(f"Saved features to historical_features.csv ({len(features_df)} rows).")
    else:
        logger.warning("No features extracted.")

if __name__ == "__main__":
    main() 