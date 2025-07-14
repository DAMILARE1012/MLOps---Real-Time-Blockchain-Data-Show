import pandas as pd
from sqlalchemy import create_engine
import logging

def extract_transactions(database_url: str) -> pd.DataFrame:
    """
    Extracts transactions from PostgreSQL using pandas and SQLAlchemy.
    """
    logger = logging.getLogger(__name__)
    logger.info("Starting data extraction from PostgreSQL.")
    try:
        engine = create_engine(database_url)
        query = "SELECT * FROM transactions"
        df = pd.read_sql(query, engine)
        logger.info(f"Extracted {len(df)} records from transactions table.")
        return df
    except Exception as e:
        logger.error(f"Error extracting transactions: {e}")
        return pd.DataFrame()  # Return empty DataFrame on error

def write_features_to_postgres(features: pd.DataFrame, database_url: str, table_name: str = "address_features_table"):
    """
    Writes engineered features to PostgreSQL table for Feast ingestion.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Writing {len(features)} features to table '{table_name}'.")
    try:
        engine = create_engine(database_url)
        features.to_sql(table_name, engine, if_exists='replace', index=False)
        logger.info(f"Successfully wrote features to '{table_name}'.")
    except Exception as e:
        logger.error(f"Error writing features to PostgreSQL: {e}") 