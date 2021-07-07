def subject_filter(subject):
    """
    Filter to format subject if subject is empty or has only spaces.
    """
    if subject is None or len(subject.strip()) < 1:
        subject = "[no subject]"

    return subject
