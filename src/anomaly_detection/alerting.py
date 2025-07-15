import csv
import os
import asyncio
from src.alerting.telegram_alert import send_telegram_alert_async

async def send_alert(tx: dict, score: float):
    print(f"ALERT: Anomalous transaction detected! Score: {score}")
    print(f"Transaction: {tx}")
    # Extract first output address if available
    address = None
    outs = tx.get("out", [])
    if outs and isinstance(outs, list):
        address = outs[0].get("addr")
    # Log to CSV for dashboard
    log_path = "anomaly_events.csv"
    file_exists = os.path.isfile(log_path)
    with open(log_path, "a", newline="") as csvfile:
        writer = csv.writer(csvfile)
        if not file_exists:
            writer.writerow(["hash", "score", "total_value", "fee", "input_count", "output_count", "address"])
        writer.writerow([
            tx.get("hash"),
            score,
            sum(out.get("value", 0) for out in tx.get("out", [])),
            tx.get("fee", 0),
            len(tx.get("inputs", [])),
            len(tx.get("out", [])),
            address
        ])
    # Send Telegram alert
    try:
        message = f"ANOMALY DETECTED!\nHash: {tx.get('hash')}\nScore: {score:.4f}\nValue: {sum(out.get('value', 0) for out in tx.get('out', []))}\nFee: {tx.get('fee', 0)}\nInputs: {len(tx.get('inputs', []))}\nOutputs: {len(tx.get('out', []))}\nAddress: {address}"
        success = await send_telegram_alert_async(message)
        if success:
            print("Telegram alert sent successfully")
        else:
            print("Failed to send Telegram alert")
    except Exception as e:
        print(f"Error sending Telegram alert: {e}") 