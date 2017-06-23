def file_size_filter(value):
    """
    Filter to format a file size in KB display. This converts the file size that is returned from the service
    tier into the format that is required to be displayed to users in the HTML template
    """
    return split_thousands(value)


def split_thousands(value, sep = ','):
    if len(value) <= 3:
        return value
    else:
        return split_thousands(value[:-3], sep) + sep + value[-3:]