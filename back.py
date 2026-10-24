import json
import ssl
import os
import socket
from flask import Flask, render_template
from flask_socketio import SocketIO
import paho.mqtt.client as mqtt

# ==================== CONFIGURATION ====================
# Using .strip() ensures we remove hidden '\n' newline characters from the config file
with open("cfg.txt") as f:
    cfg = [line.strip() for line in f.readlines() if line.strip()]
    PRINTER_IP = cfg[0]         # Change to your P1S IP
    ACCESS_CODE = cfg[1]        # Change to your Access Code
    SERIAL_NUM = cfg[2]         # Change to your P1S Serial Number
# =======================================================

# AUTOMATIC CERTIFICATE FETCHING
# Instead of relying on bash/mosquitto_sub hanging, Python safely grabs the cert natively
if not os.path.exists("bblcert.pem"):
    os.system(f"openssl s_client -showcerts -connect {PRINTER_IP}:8883 </dev/null | sed -n -e '/-.BEGIN/,/-.END/ p' > bblcert.pem")

# Change async_mode to "gevent" to utilize the websocket server engine
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="gevent")

# This callback triggers when Flask successfully connects to the P1S
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("Connected to P1S Broker!")
        topic = f"device/{SERIAL_NUM}/report"
        client.subscribe(topic)
        print(f"Subscribed to topic: {topic}")
    else:
        print(f"Connection failed with result code {rc}")

# This callback triggers whenever the P1S broadcasts new telemetry
def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
        # Forward the raw JSON data to the frontend via WebSockets
        socketio.emit("printer_data", payload)
        print(payload)
    except Exception as e:
        print(f"Error parsing message: {e}")

# Initialize and configure the background MQTT client
mqtt_client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
mqtt_client.username_pw_set("bblp", ACCESS_CODE)

# Configure SSL/TLS to bypass the printer's self-signed certificate restriction
mqtt_client.tls_set(ca_certs="bblb_cert.pem" if os.path.exists("bblb_cert.pem") else "bblcert.pem")
mqtt_client.tls_insecure_set(True)

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    print("Connecting to printer via MQTT...")
    mqtt_client.connect_async(PRINTER_IP, 8883, 60)
    mqtt_client.loop_start()
    
    print("Starting Gevent-WebSocket Web Server on http://127.0.0.1:2080")
    # socketio.run automatically picks up 'gevent' and overrides the broken standard Werkzeug server
    socketio.run(app, host="127.0.0.1", port=2080)
