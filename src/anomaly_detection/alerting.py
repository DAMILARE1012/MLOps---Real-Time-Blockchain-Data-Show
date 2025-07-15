import csv
import os

def send_alert(tx: dict, score: float):
    print(f"ALERT: Anomalous transaction detected! Score: {score}")
    print(f"Transaction: {tx}")
    # Log to CSV for dashboard
    log_path = "anomaly_events.csv"
    file_exists = os.path.isfile(log_path)
    with open(log_path, "a", newline="") as csvfile:
        writer = csv.writer(csvfile)
        if not file_exists:
            writer.writerow(["hash", "score", "total_value", "fee", "input_count", "output_count"])
        writer.writerow([
            tx.get("hash"),
            score,
            sum(out.get("value", 0) for out in tx.get("out", [])),
            tx.get("fee", 0),
            len(tx.get("inputs", [])),
            len(tx.get("out", []))
        ]) 