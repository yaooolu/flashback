# -*- coding: utf-8 -*-

from . import event_structs
from .event_base import EventBody
import inspect


def _init_event():
    attrs = [(name, value) for name, value in inspect.getmembers(event_structs) if not name.startswith('_')]
    g = globals()
    for attr, value in attrs:
        name = attr.title().replace('_', '')
        g[name] = type(name, (EventBody,), {'_fields_': value})

    g['EventNotDefined'] = type('', (EventBody,), {'_fields_': []})


_init_event()

__all__ = [name for name in globals() if inspect.isclass(globals().get(name))]
