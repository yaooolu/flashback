# -*- coding: utf-8 -*-

from .events import *
from .log_event_types import event_types
# import struct


class Event(object):
    def __init__(self, f, offset=None):
        self.file = f
        self.offset = offset
        f.seek(self.offset or 0)

    def parse(self):
        header = EventHeader2.from_file(self.file)
        type_code = int.from_bytes(header.type_code, 'little')
        if event_types[type_code] == "StopEvent":
            return
        body = globals().get(event_types.get(type_code), EventNotDefined).from_file(self.file, length=header.event_length - header.struct_size)

        return (header, body)
        # unpack = struct.unpack('<cIcIIIH', self.file.read(20))
        # self.timestamp = unpack[1]
        # self.event_type = unpack[2]
        # self.server_id = unpack[3]
        # self.event_size = unpack[4]
        # self.log_pos = unpack[5]
        # self.flags = unpack[6]

        # print(self.timestamp)
        # print(self.event_type)
        # print(self.server_id)
        # print(self.log_pos)
        # pass

    def all(self):
        if not self.offset:
            self.seek(4)

        while self.file:
            try:
                # header = EventHeader.from_file(self.file, next_position)
                header = EventHeader.from_file(self.file)
            except Exception:
                return
            next_position = header.next_position
            type_code = int.from_bytes(header.type_code, 'little')
            if event_types[type_code] == "StopEvent":
                return
            body = globals().get(event_types.get(type_code), EventNotDefined).from_file(self.file, length=header.event_length - header.struct_size)
            yield (header, body)

    @classmethod
    def from_file(cls, file, offset=None):
        return cls(file, offset)
