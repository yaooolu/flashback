# -*- coding: utf-8 -*-

"""
    document url: https://dev.mysql.com/doc/internals/en/event-data-for-specific-event-types.html
"""

format_description_event = [
    ('<h', 'binlog_version'),
    ('<50s', 'server_version'),
    ('<i', 'create_timestamp'),
    ('<c', 'header_length'),
]


query_event = [
    ('<i', 'thread_id'),
    ('<i', 'execute_time'),
    ('<c', 'db_name_len'),
    ('<h', 'error_code'),
    ('<h', 'status_block_len'),
]


rotate_event = [
    ('<Q', 'first_event_pos')
]


load_event = [
    ('<i', 'thread_id'),
    ('<i', 'execute_time'),
    ('<i', 'skip_lines_num'),
    ('<c', 'tb_name_len'),
    ('<c', 'db_name_len'),
    ('<i', 'columns_num'),
]


new_load_event = [
    ('<i', 'thread_id'),
    ('<i', 'execute_time'),
    ('<i', 'skip_lines_num'),
    ('<c', 'tb_name_len'),
    ('<c', 'db_name_len'),
    ('<i', 'columns_num'),
]


create_file_event = [
    ('<i', 'thread_id'),
]


table_map_event = [
    ('<6s', 'table_id'),
    ('<2s', 'future_use'),
]


write_rows_event = [
    ('<6s', 'table_id'),
    ('<2s', 'future_use'),
    ('<2s', 'not_desc'),
]


update_rows_event = [
    ('<6s', 'table_id'),
    ('<2s', 'future_use'),
    ('<2s', 'not_desc'),
]


delete_rows_event = [
    ('<6s', 'table_id'),
    ('<2s', 'future_use'),
    ('<2s', 'not_desc'),
]

xid_event = []
stop_event = []
intvar_event = []
