from datetime import datetime

from iso8601 import parse_date, ParseError


def convert_events_to_new_format(events):
    formatted_events = {}
    for event in events:
        try:
            date_time = parse_date(event['timestamp'])
        except ParseError:
            raise ParseError

        formatted_events[event['tag']] = {
            "day": date_time.strftime('%A'),
            "date": date_time.strftime('%d %b %Y'),
            "month": date_time.strftime('%m'),
            "time": date_time.strftime('%H:%M GMT'),
            "is_in_future": date_time > parse_date(datetime.now().isoformat())
        }
    return formatted_events
