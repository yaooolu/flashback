# -*- coding: utf-8 -*-
import struct
from mybinlog.db_manager import get_conn


class LookupDict(dict):
    """Dictionary lookup object."""

    def __init__(self, name=None):
        self.name = name
        super(LookupDict, self).__init__()

    def __repr__(self):
        return '<lookup \'%s\'>' % (self.name)

    def __getitem__(self, key):
        return self.__dict__.get(key, None)

    def __setitem__(self, key, value):
        self.__dict__[key] = value

    def get(self, key, default=None):
        return self.__dict__.get(key, default)


def byte2int8(byte):
    return struct.unpack("<B", byte)[0]


def byte2int16(byte):
    return struct.unpack("<H", byte)[0]


def byte2int48(byte):
    _res = struct.unpack("<HHH", byte)
    return _res[0] + (_res[1] << 16) + (_res[2] << 32)


def bytes2int(byte, end="little"):
    return int.from_bytes(byte, end)


def byte2float(byte):
    return struct.unpack("f", byte)[0]


def byte2double(byte):
    return struct.unpack("d", byte)[0]


def signed(unsigned_num, size):
    if unsigned_num & int('0x8' + '0' * (size * 2 - 1), 16) != 0:
        _ = int('0x' + 'f' * (size * 2), 16)
        return ((unsigned_num ^ _) + 1) * -1
    else:
        return unsigned_num


def get_columns_info_from_db(db_name, table_name):
    conn = get_conn()
    res = {}
    try:
        with conn.cursor() as cursor:
            sql = "select column_name, ordinal_position, character_set_name, column_key from information_schema.`columns` where table_schema = '%s' and table_name = '%s'" % (db_name, table_name)
            cursor.execute(sql)
            result = cursor.fetchall()
            for _res in result:
                res['column_' + str(_res['ordinal_position'])] = [_res.get('column_name'), _res.get('character_set_name'), _res.get('column_key')]
    except Exception as e:
        print(e)

    return res


def my_decimal_get_binary_size(precision, decimals):
    compress_bytes = [0, 1, 1, 2, 2, 3, 3, 4, 4, 4]
    integer_length = decimals - precision
    return (integer_length // 9) * 4 + \
        compress_bytes[integer_length % 9] + \
        compress_bytes[precision]
