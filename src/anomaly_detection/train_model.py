import pandas as pd
from sklearn.ensemble import IsolationForest
import joblib
import os
import logging
import matplotlib.pyplot as plt

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
logger = logging.getLogger(__name__)

def train_anomaly_model(features: pd.DataFrame, model_path: str = "../../models/anomaly_model.pkl"):
    model = IsolationForest(contamination=0.01, random_state=42)
    model.fit(features)
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    joblib.dump(model, model_path)
    logger.info(f"Model saved to {model_path}")
    return model

def main():
    features_path = "./historical_features.csv"
    if not os.path.exists(features_path):
        logger.error(f"Features file {features_path} not found. Run feature extraction first.")
        return
    features = pd.read_csv(features_path)
    logger.info(f"Loaded {len(features)} feature rows for training.")
    model = train_anomaly_model(features, model_path="../../models/anomaly_model.pkl")

    # Evaluate: Anomaly scores and predictions
    scores = model.decision_function(features)
    preds = model.predict(features)  # -1 = anomaly, 1 = normal
    n_anomalies = (preds == -1).sum()
    logger.info(f"Number of anomalies detected in training data: {n_anomalies}")

    # Plot anomaly score distribution
    plt.figure(figsize=(12, 8))
    plt.hist(scores, bins=50)
    plt.title("Anomaly Scores (Higher = More Normal)")
    plt.xlabel("Score")
    plt.ylabel("Frequency")
    plt.grid(linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.savefig("anomaly_score_distribution.png")
    logger.info("Saved anomaly score distribution plot as anomaly_score_distribution.png")

    # Save top anomalies to CSV
    features['anomaly_score'] = scores
    features['is_anomaly'] = preds
    anomalies = features[features['is_anomaly'] == -1]
    anomalies.sort_values('anomaly_score', inplace=True)
    anomalies.head(100).to_csv("top_anomalies.csv", index=False)
    logger.info(f"Saved top 100 anomalies to top_anomalies.csv")

if __name__ == "__main__":
    main() 