import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import mlflow
import mlflow.sklearn
import logging

def train_and_evaluate(features: pd.DataFrame, target_col: str = "label"):
    logger = logging.getLogger(__name__)
    logger.info("Starting model training and evaluation.")
    try:
        X = features.drop(columns=[target_col, "address"], errors='ignore')
        y = features[target_col]
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        with mlflow.start_run(run_name="RandomForest"):
            model = RandomForestClassifier(n_estimators=100, random_state=42)
            model.fit(X_train, y_train)
            preds = model.predict(X_test)
            acc = accuracy_score(y_test, preds)
            mlflow.log_param("n_estimators", 100)
            mlflow.log_metric("accuracy", acc)
            mlflow.sklearn.log_model(model, "model")
            logger.info(f"Test Accuracy: {acc:.4f}")
        return model, acc
    except Exception as e:
        logger.error(f"Error in model training or evaluation: {e}")
        return None, None 