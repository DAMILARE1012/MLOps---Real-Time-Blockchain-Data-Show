import csv
import os

def send_whale_alert(tx: dict, threshold_btc: float, btc_per_satoshi: float = 1e-8):
    total_value_btc = sum(out.get("value", 0) for out in tx.get("out", [])) * btc_per_satoshi
    if total_value_btc >= threshold_btc:
        print(f"WHALE ALERT: Transaction {tx.get('hash')} with value {total_value_btc:.2f} BTC")
        # Extract first output address if available
        address = None
        outs = tx.get("out", [])
        if outs and isinstance(outs, list):
            address = outs[0].get("addr")
        log_path = "whale_events.csv"
        file_exists = os.path.isfile(log_path)
        with open(log_path, "a", newline="") as csvfile:
            writer = csv.writer(csvfile)
            if not file_exists:
                writer.writerow(["hash", "total_value_btc", "fee", "input_count", "output_count", "address"])
            writer.writerow([
                tx.get("hash"),
                total_value_btc,
                tx.get("fee", 0),
                len(tx.get("inputs", [])),
                len(outs),
                address
            ])
        return True
    return False 