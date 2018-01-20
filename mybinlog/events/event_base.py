# -*- coding: utf-8 -*-
from ..structure import Structure


class EventHeader(Structure):
    _fields_ = [
        ('<I', 'timestamp'),
        ('<c', 'type_code'),
        ('<I', 'server_id'),
        ('<I', 'event_length'),
        ('<I', 'next_position'),
        ('<H', 'flags'),
    ]


class EventHeader2(Structure):
    _fields_ = [
        ('<c', 'ok_code'),
        ('<I', 'timestamp'),
        ('<c', 'type_code'),
        ('<I', 'server_id'),
        ('<I', 'event_length'),
        ('<I', 'next_position'),
        ('<H', 'flags'),
    ]


class EventBody(Structure):
    """
        Rewritten by specific Event
    """
    _fields_ = []
