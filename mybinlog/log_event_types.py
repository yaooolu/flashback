# -*- coding: utf-8 -*-

"""
    binlog event types
    source code: mysql-5.7.14/libbinlogevents/include/binlog_event.h
"""

from .helpers import LookupDict
from io import BytesIO
from .helpers import byte2int8, byte2int16, bytes2int, byte2int48, signed, my_decimal_get_binary_size, byte2float, byte2double, get_columns_info_from_db
from . import field_types
import struct
import re
from decimal import Decimal
import time


_event_types = {
    "UNKNOWN_EVENT": 0,
    "START_EVENT_V3": 1,
    "QUERY_EVENT": 2,
    "STOP_EVENT": 3,
    "ROTATE_EVENT": 4,
    "INTVAR_EVENT": 5,
    "LOAD_EVENT": 6,
    "SLAVE_EVENT": 7,
    "CREATE_FILE_EVENT": 8,
    "APPEND_BLOCK_EVENT": 9,
    "EXEC_LOAD_EVENT": 10,
    "DELETE_FILE_EVENT": 11,
    "NEW_LOAD_EVENT": 12,
    "RAND_EVENT": 13,
    "USER_VAR_EVENT": 14,
    "FORMAT_DESCRIPTION_EVENT": 15,
    "XID_EVENT": 16,
    "BEGIN_LOAD_QUERY_EVENT": 17,
    "EXECUTE_LOAD_QUERY_EVENT": 18,
    "TABLE_MAP_EVENT": 19,
    "PRE_GA_WRITE_ROWS_EVENT": 20,
    "PRE_GA_UPDATE_ROWS_EVENT": 21,
    "PRE_GA_DELETE_ROWS_EVENT": 22,
    "WRITE_ROWS_EVENT_V1": 23,
    "UPDATE_ROWS_EVENT_V1": 24,
    "DELETE_ROWS_EVENT_V1": 25,
    "INCIDENT_EVENT": 26,
    "HEARTBEAT_LOG_EVENT": 27,
    "IGNORABLE_LOG_EVENT": 28,
    "ROWS_QUERY_LOG_EVENT": 29,
    "WRITE_ROWS_EVENT": 30,
    "UPDATE_ROWS_EVENT": 31,
    "DELETE_ROWS_EVENT": 32,
    "GTID_LOG_EVENT": 33,
    "ANONYMOUS_GTID_LOG_EVENT": 34,
    "PREVIOUS_GTIDS_LOG_EVENT": 35,
    "TRANSACTION_CONTEXT_EVENT": 36,
    "VIEW_CHANGE_EVENT": 37,
    "XA_PREPARE_LOG_EVENT": 38,
}


class Table(object):
    def __init__(self, table_id, db_name, table_name):
        self.table_id = table_id
        self.charset = None
        self.db_name = db_name
        self.pk = 'id'
        self.table_name = table_name
        self.columns = []

    # @property
    # def table_name(self):
    #     return self.t_name

    # @table_name.setter
    # def table_name(self, value):
    #     if isinstance(value, bytes):
    #         self.t_name = value.decode(self.charset or 'utf-8')
    #     else:
    #         self.t_name = value

    # @property
    # def columns(self):
    #     return self._columns

    # @property
    # def db_name(self):
    #     return self._db_name

    # @db_name.setter
    # def db_name(self, value):
    #     if isinstance(value, bytes):
    #         self._db_name = value.decode(self.charset or 'utf-8')
    #     else:
    #         self._db_name = value

    def __str__(self):
        return """
            db_name = '%s',
            table_name = '%s',
            table_id = %s,
            columns = [%s]
        """ % (self.db_name, self.table_name, self.table_id, "\n".join(self.columns))


class Column(object):
    def __init__(self, column_name=None):
        self.column_name = column_name
        self.data_type = None
        self.charset = None

    def __str__(self):
        return """
            column_name = %s,
            data_type = %s,
            charset = %s
        """ % (
            self.column_name,
            field_types.fields[self.data_type],
            self.charset
        )

    def parse(self, data):
        _field = ''
        if self.data_type == field_types.LONG:
            _field = signed(bytes2int(data.read(4)), 4)

        elif self.data_type == field_types.FLOAT:
            _field = byte2float(data.read(self.meta_len))

        elif self.data_type == field_types.DOUBLE:
            _field = byte2double(data.read(self.meta_len))

        elif self.data_type == field_types.SHORT:
            _field = signed(bytes2int(data.read(self.meta_len)), self.meta_len)

        elif self.data_type == field_types.TINY:
            _field = signed(bytes2int(data.read(1)), 1)

        elif self.data_type == field_types.BLOB:
            field_len = bytes2int(data.read(self.meta_len))
            _field = data.read(field_len).decode(self.charset)

        elif self.data_type == field_types.INT24:
            _field = signed(bytes2int(data.read(3)), 3)

        elif self.data_type == field_types.VARCHAR:
            if self.meta_len <= 0xff:
                field_len = byte2int8(data.read(1))
            else:
                field_len = byte2int16(data.read(2))
            _field = data.read(field_len).decode(self.charset)

        elif self.data_type == field_types.JSON:
            field_len = byte2int8(data.read(1))
            _field = data.read(field_len)

        elif self.data_type == field_types.DATE:
            # Date
            _date = bytes2int(data.read(3))
            _year = _date // 32 // 16
            _month = _date // 32 % 16
            _day = _date % 32
            _field = "%s-%02d-%02d" % (_year, _month, _day)

        elif self.data_type == field_types.LONGLONG:
            # bigint
            _field = signed(bytes2int(data.read(8)), 8)

        elif self.data_type == field_types.TIME2:
            _time = data.read(3).hex()
            _time_bin_str = bin(int(_date, 16))[2:]
            _h = int(_time_bin_str[2:12], 2)
            _m = int(_time_bin_str[12:18], 2)
            _s = int(_time_bin_str[18:24], 2)

            if self.fsp != 0:
                fsp_storage = [0, 1, 1, 2, 2, 3, 3]
                _fsp = data.read(fsp_storage[self.fsp])

            _field = "%02d:%02d:%02d" % (_h, _m, _s)

        elif self.data_type == field_types.TIMESTAMP2:
            _timestamp = bytes2int(data.read(4), 'big')

            if self.fsp != 0:
                fsp_storage = [0, 1, 1, 2, 2, 3, 3]
                _fsp = data.read(fsp_storage[self.fsp])

            _field = _timestamp

        elif self.data_type == field_types.DATETIME2:
            """DATETIME
                https://dev.mysql.com/doc/internals/en/date-and-time-data-type-representation.html
            """
            _date = data.read(5).hex()
            _date_bin_str = bin(int(_date, 16))[2:]
            # _date_bin_str = bin(_date)[2:]
            y_m = int(_date_bin_str[1:18], 2)
            _year = y_m // 13
            _month = y_m % 13
            _day = int(_date_bin_str[18:23], 2)
            _h = int(_date_bin_str[23:28], 2)
            _m = int(_date_bin_str[28:34], 2)
            _s = int(_date_bin_str[34:40], 2)

            if self.fsp != 0:
                fsp_storage = [0, 1, 1, 2, 2, 3, 3]
                _fsp = data.read(fsp_storage[self.fsp])

            _field = "%s-%02d-%02d %02d:%02d:%02d" % (_year, _month, _day, _h, _m, _s)

        elif self.data_type == field_types.NEWDECIMAL:
            # Decimal support negative
            _decimals = self.meta_len >> 8
            _precision = self.meta_len & 0xff
            bin_size = my_decimal_get_binary_size(_decimals, _precision)

            compress_bytes = [0, 1, 1, 2, 2, 3, 3, 4, 4, 4]
            integer_length = _precision - _decimals
            integer_size = integer_length // 9
            decimal_size = _decimals // 9
            left_integer = integer_length - integer_size * 9
            left_decimal = _decimals - decimal_size * 9
            val = byte2int8(data.read(1))
            if val & 0x80 != 0:
                mask = 0
                res = ''
            else:
                mask = -1
                res = '-'

            data.seek(-1, 1)
            data.write(struct.pack('<B', val ^ 0x80))
            data.seek(-1, 1)

            _res = ''
            data = list(data.read(bin_size))
            data.reverse()
            data = BytesIO(bytes(data))
            if left_decimal > 0:
                val = signed(bytes2int(data.read(compress_bytes[left_decimal])), compress_bytes[left_decimal]) ^ mask
                _res = str(val)

            for i in range(0, decimal_size):
                val = signed(bytes2int(data.read(4)), 4) ^ mask
                _res = str(val) + _res

            _res = '.' + _res

            for i in range(0, integer_size):
                val = signed(bytes2int(data.read(4)), 4) ^ mask
                _res = str(val) + _res

            if left_integer > 0:
                val = signed(bytes2int(data.read(compress_bytes[left_integer])), compress_bytes[left_integer]) ^ mask
                _res = str(val) + _res

            _field = Decimal(res + _res)

            # _int_size = integer_size * 4 + compress_bytes[left_integer]
            # integer_part = signed(bytes2int(data.read(_int_size), 'big'), _int_size) ^ mask
            # _decimal_size = decimal_size * 4 + compress_bytes[left_decimal]
            # decimal_part = signed(bytes2int(data.read(_decimal_size), 'big'), _decimal_size) ^ mask

            # _field = Decimal("%s%s.%s" % (res, integer_part, str(decimal_part).rjust(_decimals, '0')))

        return _field


class BinlogEvent(object):
    tables_map = {}
    crc_len = 4

    def __init__(self, header, body):
        self.header = header
        self.body = body


class QueryEvent(BinlogEvent):
    def __init__(self, header, body):
        super(QueryEvent, self).__init__(header, body)
        status_block_len = body.status_block_len
        len_variable_data = len(body.variable_part)
        variable_data = BytesIO(body.variable_part)
        self.status_block = variable_data.read(status_block_len)
        db_name_len = byte2int8(body.db_name_len)
        self.db_name = variable_data.read(db_name_len)
        variable_data.read(1)
        self.query = variable_data.read(len_variable_data - status_block_len - db_name_len - self.crc_len)
        _query = self.query.decode('utf-8')
        _query_re = re.search(r'alter +table +(.*?) .*', _query)
        if _query_re:
            table_name = _query_re.group(1)
            for table_id, table_obj in self.tables_map.items():
                # print('table_id = ', table_id, ' db_name = ', table_obj.db_name, ' table_name = ', table_obj.table_name)
                if table_obj.db_name == self.db_name and table_obj.table_name == table_name.encode():
                    del self.tables_map[table_id]
                    break

    def __str__(self):
        return "db_name = %s, query = %s" % (self.db_name, self.query)


class TableMapEvent(BinlogEvent):
    def __init__(self, header, body):
        super(TableMapEvent, self).__init__(header, body)
        self.table_id = int.from_bytes(body.table_id, 'little')
        self.variable_data = BytesIO(body.variable_part)
        db_name_len = byte2int8(self.variable_data.read(1))
        self.db_name = self.variable_data.read(db_name_len)
        self.variable_data.read(1)
        tb_name_len = byte2int8(self.variable_data.read(1))
        self.tb_name = self.variable_data.read(tb_name_len)
        self.variable_data.read(1)
        self.columns_len = byte2int8(self.variable_data.read(1))
        self.skip_databases = []
        self.skip_tables = []
        self.conn = None

    def parse(self):
        variable_data = self.variable_data
        db_columns_info = get_columns_info_from_db(self.db_name.decode(), self.tb_name.decode(), self.conn)
        field_list = list(variable_data.read(self.columns_len))
        self.metadata_len = byte2int8(variable_data.read(1))

        if not self.tables_map.get(self.table_id) and \
            self.db_name.decode() not in self.skip_databases and \
            self.tb_name.decode() not in self.skip_tables:

            _table = Table(self.table_id, self.db_name, self.tb_name)

            for i, val in enumerate(field_list):
                _col = 'column_' + str(i + 1)
                _column_name, _charset, is_pk = db_columns_info.get(_col, (_col, None, None))
                _column = Column(_column_name)
                _column.data_type = val
                _column.charset = _charset

                if is_pk:
                    _table.pk = _column_name

                if val == field_types.VARCHAR:
                    _column.meta_len = byte2int16(variable_data.read(2))
                elif val == field_types.JSON:
                    _column.meta_len = byte2int8(variable_data.read(1))
                elif val == field_types.DATETIME2:
                    _column.fsp = byte2int8(variable_data.read(1))
                elif val == field_types.TIME2:
                    _column.fsp = byte2int8(variable_data.read(1))
                elif val == field_types.TIMESTAMP2:
                    _column.fsp = byte2int8(variable_data.read(1))
                elif val == field_types.NEWDECIMAL:
                    _column.meta_len = byte2int16(variable_data.read(2))
                elif val == field_types.BLOB:
                    _column.meta_len = byte2int8(variable_data.read(1))
                elif val == field_types.TINY:
                    _column.is_bool = True
                elif val == field_types.FLOAT:
                    _column.meta_len = byte2int8(variable_data.read(1))
                elif val == field_types.DOUBLE:
                    _column.meta_len = byte2int8(variable_data.read(1))
                else:
                    pass

                _table.columns.append(_column)

            self.tables_map[self.table_id] = _table

    def __str__(self):
        return "table_id = %s, table = [%s]" % (self.table_id, self.tables_map.get(self.table_id))


class WriteRowsEvent(BinlogEvent):
    def __init__(self, header, body):
        super(WriteRowsEvent, self).__init__(header, body)
        # self.body = body
        table_id = byte2int48(body.table_id)
        self._table = self.tables_map.get(table_id)
        self.skip = False

        if self._table:
            self.tb_name = self._table.table_name.decode()
            self.db_name = self._table.db_name.decode()
            self.row_data = {}
        else:
            self.skip = True

    def _dump_variable(self):
        variable_data = BytesIO(self.body.variable_part)
        columns_len = byte2int8(variable_data.read(1))
        columns_is_used = bytes2int(variable_data.read((columns_len + 7) // 8))
        columns_is_null = bytes2int(variable_data.read((columns_len + 7) // 8))
        columns = self._table.columns

        index = 0
        fields = []
        field_list_len = len(columns)
        while columns_is_null >= 0 and index < field_list_len:
            if columns_is_null % 2 == 0:
                fields.append(columns[index])
            columns_is_null //= 2
            index += 1

        for _index, field in enumerate(fields):
            _field = field.parse(variable_data)
            self.row_data[field.column_name] = _field

    def dumps(self):
        if not self.skip:
            self._dump_variable()
            return [self.db_name, self.tb_name, 'insert', self.row_data]
        return []

    def excute_info(self):
        if not self.skip:
            self._dump_variable()
            _keys = self.row_data.keys()
            _values = self.row_data.values()

            _keys_str = ','.join(map(lambda x: '`{}`'.format(x), _keys))
            _values_str = []
            for val in _values:
                if isinstance(val, Decimal):
                    _values_str.append(str(val))
                elif isinstance(val, str):
                    _values_str.append('"{}"'.format(str(val)))
                else:
                    _values_str.append(str(val))
            _values_str = ','.join(_values_str)

            sql = 'insert into `%s`.`%s`(%s) values (%s)' % (self.db_name, self.tb_name, _keys_str, _values_str)

            _timestamp = time.strftime('%Y-%m-%d %H:%M', time.localtime(self.header.timestamp))
            return {
                "timestamp": _timestamp,
                # "next_position": self.header.next_position,
                # "event_length": self.header.event_length,
                "position": self.header.next_position - self.header.event_length,
                "sql": sql
            }
        return {}

    def rollback_sql(self):
        if not self.skip:
            self._dump_variable()
            _pk = self.row_data.get(self._table.pk)
            if isinstance(_pk, str):
                _pk = '"{}"'.format(_pk)
            sql = 'delete from `%s`.`%s` where %s = %s' % (self.db_name, self.tb_name, self._table.pk, _pk)
            return sql
        return ''


class DeleteRowsEvent(BinlogEvent):
    def __init__(self, header, body):
        super(DeleteRowsEvent, self).__init__(header, body)
        # self.body = body
        table_id = byte2int48(self.body.table_id)
        self._table = self.tables_map.get(table_id)
        self.skip = False

        if self._table:
            self.tb_name = self._table.table_name.decode()
            self.db_name = self._table.db_name.decode()
            self.row_data = {}
        else:
            self.skip = True

    def _dump_variable(self):
        variable_data = BytesIO(self.body.variable_part)
        columns_len = byte2int8(variable_data.read(1))
        columns_is_used = bytes2int(variable_data.read((columns_len + 7) // 8))
        columns_is_null = bytes2int(variable_data.read((columns_len + 7) // 8))

        columns = self._table.columns

        index = 0
        fields = []
        field_list_len = len(columns)
        while columns_is_null >= 0 and index < field_list_len:
            if columns_is_null % 2 == 0:
                fields.append(columns[index])
            columns_is_null //= 2
            index += 1

        for _index, field in enumerate(fields):
            _field = field.parse(variable_data)
            self.row_data[field.column_name] = _field

    def dumps(self):
        if not self.skip:
            self._dump_variable()
            return [self.db_name, self.tb_name, 'delete', self.row_data]
        return []

    def excute_info(self):
        if not self.skip:
            self._dump_variable()
            _pk = self.row_data.get(self._table.pk)
            if isinstance(_pk, str):
                _pk = '"{}"'.format(_pk)
            sql = 'delete from `%s`.`%s` where %s = %s' % (self.db_name, self.tb_name, self._table.pk, _pk)
            _timestamp = time.strftime('%Y-%m-%d %H:%M', time.localtime(self.header.timestamp))
            return {
                "timestamp": _timestamp,
                "next_position": self.header.next_position,
                "event_length": self.header.event_length,
                "position": self.header.next_position - self.header.event_length,
                "sql": sql
            }
        return {}

    def rollback_sql(self):
        if not self.skip:
            self._dump_variable()
            _keys = self.row_data.keys()
            _values = self.row_data.values()

            _keys_str = ','.join(map(lambda x: '`{}`'.format(x), _keys))
            _values_str = []
            for val in _values:
                if isinstance(val, Decimal):
                    _values_str.append(str(val))
                elif isinstance(val, str):
                    _values_str.append('"{}"'.format(str(val)))
                else:
                    _values_str.append(str(val))
            _values_str = ','.join(_values_str)

            sql = 'insert into `%s`.`%s`(%s) values (%s)' % (self.db_name, self.tb_name, _keys_str, _values_str)
            return sql
        return ''


class UpdateRowsEvent(BinlogEvent):
    def __init__(self, header, body):
        super(UpdateRowsEvent, self).__init__(header, body)
        # self.body = body
        table_id = byte2int48(self.body.table_id)
        self._table = self.tables_map.get(table_id)
        self.skip = False

        if self._table:
            self.tb_name = self._table.table_name.decode()
            self.db_name = self._table.db_name.decode()

            self.before_row_data = {}
            self.row_data = {}
        else:
            self.skip = True

    def _dump_variable(self):
        variable_data = BytesIO(self.body.variable_part)
        columns_len = byte2int8(variable_data.read(1))
        columns_is_used = bytes2int(variable_data.read((columns_len + 7) // 8))
        columns_is_used_update = bytes2int(variable_data.read((columns_len + 7) // 8))
        columns_is_null = bytes2int(variable_data.read((columns_len + 7) // 8))

        columns = self._table.columns
        index = 0
        fields = []
        field_list_len = len(columns)
        while columns_is_null >= 0 and index < field_list_len:
            if columns_is_null % 2 == 0:
                fields.append(columns[index])
            columns_is_null //= 2
            index += 1

        for _index, field in enumerate(fields):
            _field = field.parse(variable_data)
            self.before_row_data[field.column_name] = _field

        columns_is_null = bytes2int(variable_data.read((columns_len + 7) // 8))
        index = 0
        fields = []
        field_list_len = len(columns)

        while columns_is_null >= 0 and index < field_list_len:
            if columns_is_null % 2 == 0:
                fields.append(columns[index])
            columns_is_null //= 2
            index += 1

        for _index, field in enumerate(fields):
            _field = field.parse(variable_data)
            self.row_data[field.column_name] = _field

    def dumps(self):
        if not self.skip:
            self._dump_variable()
            return [self.db_name, self.tb_name, 'update', self.before_row_data, self.row_data]
        return []

    def excute_info(self):
        if not self.skip:
            self._dump_variable()
            val_sql = []
            for key, val in self.row_data.items():
                if isinstance(val, str):
                    val_sql.append('%s = "%s"' % (key, val))
                # elif isinstance(val, Decimal):
                else:
                    val_sql.append('%s = %s' % (key, str(val)))

            val_sql = ', '.join(val_sql)
            _pk = self.before_row_data.get(self._table.pk)
            if isinstance(_pk, str):
                _pk = '"{}"'.format(_pk)
            # print(val_sql)

            sql = 'update table `%s`.`%s` set %s where %s = %s' % (self.db_name, self.tb_name, val_sql, self._table.pk, _pk)
            _timestamp = time.strftime('%Y-%m-%d %H:%M', time.localtime(self.header.timestamp))
            return {
                "timestamp": _timestamp,
                # "next_position": self.header.next_position,
                # "event_length": self.header.event_length,
                "position": self.header.next_position - self.header.event_length,
                "sql": sql
            }
        return {}

    def rollback_sql(self):
        if not self.skip:
            self._dump_variable()
            val_sql = []
            for key, val in self.before_row_data.items():
                if isinstance(val, str):
                    val_sql.append('%s = "%s"' % (key, val))
                # elif isinstance(val, Decimal):
                else:
                    val_sql.append('%s = %s' % (key, str(val)))

            val_sql = ', '.join(val_sql)
            _pk = self.row_data.get(self._table.pk)
            if isinstance(_pk, str):
                _pk = '"{}"'.format(_pk)

            sql = 'update table `%s`.`%s` set %s where %s = %s' % (self.db_name, self.tb_name, val_sql, self._table.pk, _pk)
            return sql
        return ''


event_types = LookupDict(name="event_types")


def _init():
    for type_name, code in _event_types.items():
        event_types[code] = type_name.title().replace('_', '')


_init()
