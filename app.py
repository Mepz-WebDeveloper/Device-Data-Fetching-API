from flask import Flask, jsonify, request
from datetime import datetime
from zk import ZK
import sqlite3
import os
import threading
import time
 
app = Flask(__name__)
DEVICE_IP = "192.168.30.10"
PORT = 4370
TIMEOUT = 20
DB_FILE = "attendance.db" 
#Device Connection Start
def get_device_connection():
    try:
        zk = ZK(DEVICE_IP, port = PORT, timeout = TIMEOUT)
        conn = zk.connect()
        return conn
    except Exception as e:
        print(f"Could not connect to device:{e}")
        return None
#Device Connection End
# SQLite Start
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS attendance(user_id TEXT, timestamp TEXT, date TEXT, PRIMARY KEY(user_id, timestamp))''')
    conn.commit()
    conn.close()
# SQLite End
# SQLite Insert Start
def insert_attendance(record):
    try:
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        cur.execute('''INSERT OR IGNORE INTO Attendance(user_id, timestamp, date) values (?,?,?)''', (record['user_id'], record['timestamp'], record['date']))
        conn.commit()
        conn.close()
        print(f"Inserted:{record}")
    except Exception as e:    
        print(f"Insert Error: {e}")
# SQLite Insert End

#Live Attendance data Insert start
def live_Attendance_Listener():
    while True:
        conn = get_device_connection()
        if conn is None:
            time.sleep(10)
            continue
        try:
            conn.disable_device()
            print(f"Started to listen live server")

            for att in conn.live_captute():
                
                if att is None:
                    continue

                record = {
                    "user_id": str(att.user_id),
                    "timestamp": att.timestamp.strftime("%Y-%m-%d H%:M%:S%"),
                    "timestamp": att.timestamp.strftime("%Y-%m-%d")
                }

                insert_attendance(record)
        except Exception as e:
            print(f"Live Capture Error:{e}")
        finally: 
            try:
                conn.enable_device()
                conn.disconnect()
                print("Device is Disconnected")
            except:
                pass
        time.sleep(5)
#Live Attendance data Insert END

# Schedule every hour
# scheduler = BackgroundScheduler()
# scheduler.add_job(fetch_from_device, 'interval', hours=1)
# scheduler.start()
# atexit.register(lambda: scheduler.shutdown())


@app.route('/fetch', methods=['GET'])
def manual_fetch():
    print(f"🔁 Manual fetch triggered at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🔄 Fetching data from ZKTeco device...")
    try:
        conn = get_device_connection()
        if conn is None:
            return jsonify({"error":"Failed to connect to device"}), 500
        conn.disable_device()
        attendance = conn.get_attendance()

        for att in attendance:
            record = {
                "user_id": str(att.user_id),
                "timestamp": att.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "date": att.timestamp.strftime("%Y-%m-%d")
            }
            insert_attendance(record)

        conn.enable_device()
        conn.disconnect()
        return jsonify({"status": "Manual fetch complete"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/attendance', methods=['GET'])
def get_attendance():
    try:
        conn = sqlite3.connect("attendance.db", check_same_thread=False)
        conn.row_factory = sqlite3.Row  # ✅ enables dictionary-style access
        cur = conn.cursor()
        user_id = request.args.get('id')
        date = request.args.get('date')
        from_date = request.args.get('from_date')
        to_date = request.args.get('to_date')

        query = "SELECT user_id, timestamp, date from attendance where 1 = 1"
        params = []

        if user_id:
            query += "and user_id = ?"
            params.append(user_id)

        if date:
            query += "and timestamp = ?"
            params.append(date)

        if from_date and to_date:
            try:
                query += "and date between ? and ?"
                params.extend(from_date, to_date)
                # from_dt = datetime.strptime(from_date, "%Y-%m-%d")
                # to_dt = datetime.strptime(to_date, "%Y-%m-%d")
                # results = [r for r in results if from_dt <= datetime.strptime(r['date'], "%Y-%m-%d") <= to_dt]
            except ValueError:
                return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400
            
        # conn = sqlite3.connect(DB_FILE)
        # cur = conn.cursor()
        cur.execute(query,params)
        rows = cur.fetchall()
        results = [dict(row) for row in rows]
        conn.close()
        return jsonify(results),200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/delete_all', methods=['GET','POST'])
def delete_all():
    try:
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        cur.execute("DELETE FROM attendance")
        conn.commit()
        conn.close()
        return jsonify({"status": "All attendance records deleted."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/')
def home():
    return "✅ ZKTeco Attendance API is running."

if __name__ == '__main__':
    init_db()
    listener_thread = threading.Thread(target=live_Attendance_Listener, daemon=True)
    listener_thread.start()
    app.run(host='0.0.0.0', port=10000)
