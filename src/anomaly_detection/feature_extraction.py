import pandas as pd

def extract_features_from_transaction(tx: dict) -> pd.DataFrame:
    features = {
        "total_value": sum(out.get("value", 0) for out in tx.get("out", [])),
        "fee": tx.get("fee", 0),
        "input_count": len(tx.get("inputs", [])),
        "output_count": len(tx.get("out", [])),
    }
    return pd.DataFrame([features]) 