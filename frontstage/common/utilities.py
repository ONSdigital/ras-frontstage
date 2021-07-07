def obfuscate_email(email):
    """Takes an email address and returns an obfuscated version of it.
    For example: test@example.com would turn into t**t@e*********m
    """
    if email is None:
        return None
    splitmail = email.split("@")
    # If the prefix is 1 character, then we can't obfuscate it
    if len(splitmail[0]) <= 1:
        prefix = splitmail[0]
    else:
        prefix = f'{splitmail[0][0]}{"*"*(len(splitmail[0])-2)}{splitmail[0][-1]}'
    # If the domain is missing or 1 character, then we can't obfuscate it
    if len(splitmail) <= 1 or len(splitmail[1]) <= 1:
        return f"{prefix}"
    else:
        domain = f'{splitmail[1][0]}{"*"*(len(splitmail[1])-2)}{splitmail[1][-1]}'
        return f"{prefix}@{domain}"
