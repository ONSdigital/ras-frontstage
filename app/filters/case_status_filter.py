def case_status_filter(value):
    """
    Filter to format a case status for display. This converts the status that is returned from the service
    tier into the format that is required to be displayed to users in the HTML template
    """
    if value == 'not started':
        formatted_value = 'Not started'
    elif value == 'in progress':
        formatted_value = 'In Progress'
    elif value == 'complete':
        formatted_value = 'Complete'

    return formatted_value
