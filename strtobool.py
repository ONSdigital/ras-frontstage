def strtobool(val):
    val = val.lower()
    if val == "true":
        return True
    elif val == "false":
        return False
    else:
        raise ValueError("invalid truth value %r" % (val,))
