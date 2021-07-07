def file_size_filter(value):
    """
    Filter to format a file size in KB display. This converts the file size that is returned from the service
    tier into the format that is required to be displayed to users in the HTML template
    """

    # Divide by 1024 to convert from bytes to KB, round and then convert into a string
    return split_thousands(str(round(value / 1024)))


def split_thousands(value, sep=","):
    if len(value) <= 3:
        return value
    else:
        return split_thousands(value[:-3], sep) + sep + value[-3:]
