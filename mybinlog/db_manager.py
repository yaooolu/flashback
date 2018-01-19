
import pymysql


_conn = pymysql.connect(
    host='127.0.0.1',
    user='yaolu',
    password='yaolu',
    db='jupiter',
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)


def get_conn():
    return _conn
