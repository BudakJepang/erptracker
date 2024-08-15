from functools import wraps
from io import BytesIO
from datetime import datetime
# from app import mysql
# from 


def insert_pr_log(no_pr, user_id, status, description, ip_address, today):
    try:
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO pr_logs (no_pr, user_id, status, description, ip_address, created_at) VALUES (%s, %s, %s, %s, %s, %s)",
                    (no_pr, user_id, status, description, ip_address, today))
        mysql.connection.commit()
    except Exception as e:
        print(f'Error: {str(e)}')
    finally:
        cur.close()
    return "Success insert to log"