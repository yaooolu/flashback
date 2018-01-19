# -*- coding: utf-8 -*-

from .events import *
from .log_event_types import event_types


class Event(object):
    def __init__(self, f, offset):
        self.file = f
        if offset:
            f.seek(offset)
        else:
            f.seek(0)
            self.magic_num = f.read(4)

    def all(self):
        # next_position = 4
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
