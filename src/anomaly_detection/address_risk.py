import pandas as pd
import os

def compute_address_risk(anomaly_csv="anomaly_events.csv", whale_csv="whale_events.csv", output_csv="address_risk_scores.csv"):
    # Load anomaly and whale events
    anomaly_df = pd.read_csv(anomaly_csv) if os.path.exists(anomaly_csv) else pd.DataFrame()
    whale_df = pd.read_csv(whale_csv) if os.path.exists(whale_csv) else pd.DataFrame()
    # Extract addresses
    anomaly_addresses = anomaly_df['address'] if 'address' in anomaly_df.columns else pd.Series(dtype=str)
    whale_addresses = whale_df['address'] if 'address' in whale_df.columns else pd.Series(dtype=str)
    # Count frequency
    anomaly_counts = anomaly_addresses.value_counts().rename('anomaly_count')
    whale_counts = whale_addresses.value_counts().rename('whale_count')
    # Combine
    risk_df = pd.concat([anomaly_counts, whale_counts], axis=1).fillna(0)
    # Simple risk score: weighted sum
    risk_df['risk_score'] = risk_df['anomaly_count'] * 2 + risk_df['whale_count']
    risk_df = risk_df.sort_values('risk_score', ascending=False)
    risk_df.to_csv(output_csv)
    return risk_df

if __name__ == "__main__":
    compute_address_risk() 