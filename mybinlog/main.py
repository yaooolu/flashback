# -*- coding: utf-8 -*-

from mybinlog.event import Event
from mybinlog.log_event_types import (
    event_types,
    QueryEvent,
    TableMapEvent,
    WriteRowsEvent,
    UpdateRowsEvent,
    DeleteRowsEvent
)
import pymysql
import struct
from io import BytesIO
from pymysql.util import int2byte
from pymysql.constants.COMMAND import COM_BINLOG_DUMP, COM_REGISTER_SLAVE


def _parse_file(file, pos=0):
    event = Event.from_file(file, pos)
    e = event.all()

    for header, body in e:
        type_name = event_types.get(int.from_bytes(header.type_code, 'little'))
        if type_name == 'QueryEvent':
            _event = QueryEvent(header, body)

        elif type_name == 'TableMapEvent':
            _event = TableMapEvent(header, body)
            # print(_event.dumps())

        elif type_name == 'WriteRowsEvent':
            _event = WriteRowsEvent(header, body)
            print(_event.dumps())

        elif type_name == 'UpdateRowsEvent':
            _event = UpdateRowsEvent(header, body)
            print(_event.dumps())

        elif type_name == 'DeleteRowsEvent':
            _event = DeleteRowsEvent(header, body)
            print(_event.dumps())


class MyBinlog(object):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.get('user')
        self.passwd = kwargs.get('passwd')
        self.host = kwargs.get('host')
        self.port = kwargs.get('port')

        self.end_pos = kwargs.get('end_pos')
        self.skip_tables = kwargs.get('skip_tables') or []
        self.start_datetime = kwargs.get('start_datetime')
        self.skip_databases = kwargs.get('skip_databases') or []

        self.start_file = kwargs.get('start_file')
        self.end_datetime = kwargs.get('end_datetime')
        self.skip_pk = kwargs.get('skip_pk')
        self.database = kwargs.get('database')
        self.start_pos = kwargs.get('start_pos')
        self.end_file = kwargs.get('end_file')

        self.type = kwargs.get('type')
        self.table = kwargs.get('table')

        self.server_id = kwargs.get('server_id')
        self.list = kwargs.get('list')
        self.rollback = kwargs.get('rollback')

    def connect_db(self):
        try:
            self.conn = pymysql.connect(host=self.host, password=self.passwd, user=self.user, port=self.port)
            return self.conn
        except Exception as err:
            raise Exception('mysql connect error !! error_code = %s, error_msg = %s' % err.args)

    def __com_binlog_dump(self):
        prelude = struct.pack('<i', len(self.start_file) + 11) + int2byte(COM_BINLOG_DUMP)
        prelude += struct.pack('<I', self.start_pos or 4)
        prelude += struct.pack('<h', 1)
        prelude += struct.pack('<I', self.server_id)
        prelude += self.start_file.encode()

        self.conn._write_bytes(prelude)
        self.conn._next_seq_id = 1

    def __mock_slave(self, server_id, master_id=0):
        lhostname = len(self.host.encode())
        lusername = len(self.user.encode())
        lpassword = len(self.passwd.encode())

        packet_len = (1 +  # command
                      4 +  # server-id
                      1 +  # hostname length
                      lhostname +
                      1 +  # username length
                      lusername +
                      1 +  # password length
                      lpassword +
                      2 +  # slave mysql port
                      4 +  # replication rank
                      4)  # master-id

        MAX_STRING_LEN = 257

        return (struct.pack('<i', packet_len) +
                int2byte(COM_REGISTER_SLAVE) +
                struct.pack('<L', server_id) +
                struct.pack('<%dp' % min(MAX_STRING_LEN, lhostname + 1),
                            self.host.encode()) +
                struct.pack('<%dp' % min(MAX_STRING_LEN, lusername + 1),
                            self.user.encode()) +
                struct.pack('<%dp' % min(MAX_STRING_LEN, lpassword + 1),
                            self.passwd.encode()) +
                struct.pack('<H', 3333) +
                struct.pack('<l', 0) +
                struct.pack('<l', master_id))

    def read_event_from_remote(self):
        self.__mock_slave(self.server_id)
        cur = self.conn.cursor()
        cur.execute("set @master_binlog_checksum= @@global.binlog_checksum")

        if not self.start_file:
            cur.execute("show master status")
            _row = cur.fetchone()
            if _row:
                binlog_file, pos = _row[:2]
                self.start_file = binlog_file
            else:
                raise Exception('remote server binlog not start')

        self.__com_binlog_dump()
        import time

        while True:
            mockdata = BytesIO(self.conn._read_packet().read_all())
            header, body = Event(mockdata).parse()

            type_name = event_types.get(int.from_bytes(header.type_code, 'little'))

            if type_name == 'QueryEvent':
                _event = QueryEvent(header, body)

            elif type_name == 'TableMapEvent':
                _event = TableMapEvent(header, body)
                _event.skip_databases = self.skip_databases
                _event.skip_tables = self.skip_tables
                _event.parse()

            elif type_name == 'WriteRowsEvent':
                _event = WriteRowsEvent(header, body)
                # if _event.tb_name not in self.skip_table:
                    # print(_event.dumps())
                print(_event.rollback_sql())

            elif type_name == 'UpdateRowsEvent':
                _event = UpdateRowsEvent(header, body)
                # if _event.tb_name not in self.skip_table:
                    # print(_event.dumps())
                print(_event.rollback_sql())

            elif type_name == 'DeleteRowsEvent':
                _event = DeleteRowsEvent(header, body)
                # if _event.tb_name not in self.skip_table:
                    # print(_event.dumps())
                print(_event.rollback_sql())

            time.sleep(0.1)


# if __name__ == '__main__':
#     file = open('/usr/local/Cellar/mysql/5.6.26/data/mysql-bin.000002', 'rb')
#     _parse(file)
