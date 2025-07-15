import joblib
from .feature_extraction import extract_features_from_transaction
from .alerting import send_alert

def score_transaction(tx: dict, model_path: str = "../../models/anomaly_model.pkl"):
    model = joblib.load(model_path)
    features = extract_features_from_transaction(tx)
    score = model.decision_function(features)[0]
    is_anomaly = model.predict(features)[0] == -1
    if is_anomaly:
        send_alert(tx, score)
    return is_anomaly, score 