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


def _parse(file, pos=0):
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
            # pass
            _event = DeleteRowsEvent(header, body)
            print(_event.dumps())


class MyBinlog(object):
    pass

if __name__ == '__main__':
    file = open('/usr/local/Cellar/mysql/5.6.26/data/mysql-bin.000002', 'rb')
    _parse(file)
