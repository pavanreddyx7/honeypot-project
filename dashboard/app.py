from flask import Flask, render_template
import sqlite3

app = Flask(__name__)

@app.route('/')
def index():
    conn = sqlite3.connect('../honeypot.db')  # Adjust path if needed
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, timestamp, src_ip, src_port, dest_ip, dest_port,
               location, country, attack_type, brute_force
        FROM logs
        ORDER BY timestamp DESC
        LIMIT 100
    ''')
    logs = cursor.fetchall()
    conn.close()
    return render_template('index.html', logs=logs)

if __name__ == '__main__':
    app.run(debug=False)
