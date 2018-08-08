from datetime import datetime

import iso8601


def convert_events_to_new_format(events):
    formatted_events = {}
    for event in events:
        date_time = iso8601.parse_date(event['timestamp'])
        formatted_events[event['tag']] = {
            "day": date_time.strftime('%A'),
            "date": date_time.strftime('%d %b %Y'),
            "month": date_time.strftime('%m'),
            "time": date_time.strftime('%H:%M GMT'),
            "is_in_future": date_time > iso8601.parse_date(datetime.now().isoformat())
        }
    return formatted_events
