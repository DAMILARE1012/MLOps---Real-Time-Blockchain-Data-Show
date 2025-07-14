import os
from .retrieve import get_training_data
from .train import train_and_evaluate
from .mlflow_utils import setup_mlflow
import logging
import pandas as pd
import numpy as np

# Get the directory of the current file (e.g., main.py)
current_dir = os.path.dirname(os.path.abspath(__file__))

# Go up to the project root and then to feature_repo
feature_store_path = os.path.join(current_dir, '..', '..', 'feature_repo')
feature_store_path = os.path.abspath(feature_store_path)  # Get absolute path

print(feature_store_path)  # For debugging



# FEATURE_STORE_PATH = "../../feature_repo"

def run_training_pipeline():
    logger = logging.getLogger(__name__)
    logger.info("Starting model training pipeline.")
    try:
        setup_mlflow()
        features = get_training_data(feature_store_path)
        # You may need to add a label column to your features DataFrame for supervised learning
        # features['label'] = ... (add your target variable here)
        if 'label' not in features.columns:
            features['label'] = np.random.randint(0, 2, size=len(features))
        train_and_evaluate(features, target_col="label")
        logger.info("Model training pipeline completed successfully.")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
    run_training_pipeline() 