import websocket
import json

def on_open(ws):
    print("WebSocket connection opened.")
    # Subscribe to unconfirmed transactions
    ws.send(json.dumps({
        "op": "unconfirmed_sub"
    }))

def on_message(ws, message):
    data = json.loads(message)
    print("New Transaction Received:")
    print(json.dumps(data, indent=2))

def on_close(ws, close_status_code, close_msg):
    print("WebSocket connection closed.")

def on_error(ws, error):
    print("Error:", error)

if __name__ == "__main__":
    socket_url = "wss://ws.blockchain.info/inv"

    ws = websocket.WebSocketApp(socket_url,
                                on_open=on_open,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    
    ws.run_forever()
