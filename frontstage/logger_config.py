import logging
import sys

from structlog import configure
from structlog.processors import JSONRenderer, TimeStamper, format_exc_info
from structlog.stdlib import LoggerFactory, add_log_level, filter_by_level
from structlog.threadlocal import wrap_dict


def logger_initial_config(log_level="INFO", logger_format="%(message)s", logger_date_format="%Y-%m-%dT%H:%M%s"):
    def add_service(logger, method_name, event_dict):
        """
        Add the service name to the event dict.
        This adds `service: 'ras-frontstage'` to all log lines.
        """
        event_dict["service"] = "ras-frontstage"
        return event_dict

    logging.basicConfig(stream=sys.stdout, level=log_level, format=logger_format)
    auth_log = logging.getLogger(__name__)
    auth_log.addHandler(logging.NullHandler())
    auth_log.propagate = False

    def add_severity_level(logger, method_name, event_dict):
        """
        Add the log level to the event dict.
        """
        if method_name == "warn":
            # The stdlib has an alias
            method_name = "warning"

        event_dict["severity"] = method_name
        return event_dict

    def parse_exception(_, __, event_dict):
        exception = event_dict.get("exception")
        if exception:
            event_dict["exception"] = exception.replace('"', "'").split("\n")
        return event_dict

    # setup file logging
    renderer_processor = JSONRenderer(indent=None)

    processors = [
        add_severity_level,
        add_log_level,
        filter_by_level,
        add_service,
        format_exc_info,
        TimeStamper(fmt=logger_date_format, utc=True, key="created_at"),
        parse_exception,
        renderer_processor,
    ]
    configure(
        context_class=wrap_dict(dict),
        logger_factory=LoggerFactory(),
        processors=processors,
        cache_logger_on_first_use=True,
    )
