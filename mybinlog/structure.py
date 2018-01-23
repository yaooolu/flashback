# -*- coding: utf-8 -*-

"""
    define structure
"""

import struct
import re


class StructField:
    def __init__(self, format, offset=None):
        self.format = format
        self.offset = offset

    def __get__(self, instance, cls):
        if instance is None:
            return self
        else:
            r = struct.unpack_from(self.format, instance._buffer, self.offset)
        return r[0] if len(r) == 1 else r


class StructureMeta(type):
    def __init__(self, cls, bases, clsdict):
        fields = getattr(self, '_fields_', [])
        offset = 0
        for (format, fieldname) in fields:
            setattr(self, fieldname, StructField(format, offset))
            offset += struct.calcsize(format)
        setattr(self, 'struct_size', offset)


class Structure(metaclass=StructureMeta):
    def __init__(self, bytedata):
        self._buffer = memoryview(bytedata)
        self.variable_part = self._buffer[self.struct_size:]
        self.variable_part_len = len(self.variable_part)

    @classmethod
    def from_file(cls, f, offset=None, length=None):
        if offset:
            f.seek(offset)

        _data = f.read(length or cls.struct_size)
        if _data:
            return cls(_data)
        else:
            raise Exception('file data is None')
