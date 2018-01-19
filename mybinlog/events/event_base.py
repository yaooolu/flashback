# -*- coding: utf-8 -*-
from ..structure import Structure


class EventHeader(Structure):
    """
        v4 event header
        +=====================================+
        | event  | timestamp         0 : 4    |
        | header +----------------------------+
        |        | type_code         4 : 1    |
        |        +----------------------------+
        |        | server_id         5 : 4    |
        |        +----------------------------+
        |        | event_length      9 : 4    |
        |        +----------------------------+
        |        | next_position    13 : 4    |
        |        +----------------------------+
        |        | flags            17 : 2    |
        +=====================================+
    """
    _fields_ = [
        ('<i', 'timestamp'),
        ('<c', 'type_code'),
        ('<i', 'server_id'),
        ('<i', 'event_length'),
        ('<i', 'next_position'),
        ('<h', 'flags'),
    ]


class EventBody(Structure):
    """
        Rewritten by specific Event
    """
    _fields_ = []
