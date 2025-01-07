def strtobool(val):
    """This directly replaces the distutils function strtobool. All the redundant checks that were carried out
    originally by the function are no longer needed. We either need a true or false value. We don't need to compare if
    there is a I/O, 1/0, Yes/No, Y/N or t/f etc.
    """
    val = val.lower()
    if val == "true":
        return True
    elif val == "false":
        return False
    else:
        raise ValueError("invalid truth value %r" % (val,))
