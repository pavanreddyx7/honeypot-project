import socket
import threading
import sqlite3
import datetime
import requests
import smtplib
from email.message import EmailMessage
from collections import defaultdict
import os

HONEYPOT_PORT = 2222
DB_PATH = 'honeypot.db'
brute_force_attempts = defaultdict(int)

# Email and Twilio Config (use environment variables for credentials)
EMAIL_SENDER = os.environ.get('EMAIL_SENDER')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')
EMAIL_RECEIVER = os.environ.get('EMAIL_RECEIVER')

TWILIO_SID = os.environ.get('TWILIO_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_FROM = os.environ.get('TWILIO_FROM')
TWILIO_TO = os.environ.get('TWILIO_TO')

def geoip_lookup(ip):
    try:
        r = requests.get(f'http://ip-api.com/json/{ip}', timeout=5)
        data = r.json()
        return data.get("country", "Unknown"), f'{data.get("city", "")}, {data.get("regionName", "")}'
    except Exception:
        return "Unknown", "Unknown"

def send_email_alert(ip, port):
    try:
        msg = EmailMessage()
        msg.set_content(f'Connection from {ip}:{port}')
        msg['Subject'] = 'Honeypot Alert'
        msg['From'] = EMAIL_SENDER
        msg['To'] = EMAIL_RECEIVER

        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        print("[+] Email alert sent.")
    except Exception as e:
        print(f"[❌] Email failed: {e}")

def send_sms_alert(ip, port):
    try:
        from twilio.rest import Client
        client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)
        msg = client.messages.create(
            body=f"Honeypot Alert: Connection from {ip}:{port}",
            from_=TWILIO_FROM,
            to=TWILIO_TO
        )
        print("[+] SMS alert sent.")
    except Exception as e:
        print(f"[❌] SMS failed: {e}")

def log_to_db(data):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
            INSERT INTO logs (
                timestamp, src_ip, src_port, dest_ip, dest_port,
                location, country, attack_type, brute_force
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', data)
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[❌] DB Error: {e}")

def handle_connection(client_socket, addr):
    src_ip, src_port = addr
    # Get local IP address in a reliable way
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        dest_ip = s.getsockname()[0]
        s.close()
    except Exception:
        dest_ip = '127.0.0.1'
    dest_port = HONEYPOT_PORT
    country, location = geoip_lookup(src_ip)

    print(f"[!] Connection from {src_ip}:{src_port}")
    print(f"[+] Logged to text: {src_ip}:{src_port} from {country}")

    brute_force_attempts[src_ip] += 1
    is_brute_force = 1 if brute_force_attempts[src_ip] >= 5 else 0

    if is_brute_force:
        print(f"[⚠] Brute-force from {src_ip}! Attempts: {brute_force_attempts[src_ip]}")
        print(f"[🚫] Blocking IP: {src_ip}")

    timestamp = datetime.datetime.now().isoformat()
    log_data = (
        timestamp, src_ip, src_port, dest_ip, dest_port,
        location, country, 'unknown', is_brute_force
    )
    log_to_db(log_data)
    send_email_alert(src_ip, src_port)
    send_sms_alert(src_ip, src_port)
    client_socket.close()

def start_honeypot():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', HONEYPOT_PORT))
    server.listen(5)
    print(f"[+] Honeypot listening on port {HONEYPOT_PORT}...")

    while True:
        client_socket, addr = server.accept()
        threading.Thread(target=handle_connection, args=(client_socket, addr)).start()

if __name__ == "__main__":
    start_honeypot()
