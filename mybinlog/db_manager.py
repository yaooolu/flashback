
import pymysql
import time


# _conn = pymysql.connect(
#     host='127.0.0.1',
#     user='yaolu',
#     password='yaolu',
#     db='jupiter',
#     charset='utf8mb4',
#     cursorclass=pymysql.cursors.DictCursor
# )


class ConnectionPool():
    _pool = []

    def __init__(self, host, user, password, port, database='', pool_size=10, charset='utf8mb4'):
        for i in range(0, pool_size):
            conn = pymysql.connect(host=host, user=user, password=password, port=port, db=database, charset=charset)
            conn.autocommit(1)
            self._pool.append(conn)

    def execute(self, sql):
        try:
            conn = self._pool.pop()
        except IndexError:
            time.sleep(0.2)
            self.execute(sql)

        _cursor = conn.cursor()
        _cursor.execute(sql)
        res = _cursor.fetchall()
        _cursor.close()
        self._pool.append(conn)
        return res

    def get_conn(self):
        conn = self._pool.pop()
        yield conn
        self._pool.append(conn)
