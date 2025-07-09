from zk import ZK
zk = ZK('192.168.30.10', port=4370, timeout=5)

try: 
    conn = zk.connect()
    print("Connected to ZK Teco")
    print("Disabling Device")
    conn.disable_device()
    print('fetching data')
    attendance = conn.get_attendance()
    print(f"Total records fetched: {len(attendance)}")
    Emp_id = '16'
    # filtered_data = [a for a in attendance if str(a.user_id) == str(Emp_id)]
    filtered_data = [a for a in attendance if (a.timestamp.month == 6 or a.timestamp.month == 7) and (a.timestamp.year == 2025) ]
    print({len(filtered_data)})
    for record in filtered_data:
        print(f"Time: {record}")
        # print(f"UserID: {record.user_id} | Time: {record.timestamp}")
    print('Enabling Device')
    print(f"Total records fetched: {len(attendance)}")
    print({len(filtered_data)})
    conn.enable_device()
    print("Disconnecting")
    conn.disconnect()
    print("Done fetching and disconnected.")

except Exception as e:
    print(f"Error:{e}")