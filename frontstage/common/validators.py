from wtforms.validators import InputRequired as IR
from wtforms.validators import DataRequired as DR

"""
A collection of validators for use with WTForms forms
"""


class InputRequired(IR):
    """
    WTForms validator replacement that requires input, but doesn't add 'required' attribute to rendered html

    Example sage: element = StringField('name', [ FrontstageInputRequired(message="Error message to show") ]
    """
    def __init__(self, message=None):
        super().__init__(message=message)
        self.field_flags = remove_required(self.field_flags)


class DataRequired(DR):
    """
    WTForms validator replacement that requires data, but doesn't add 'required' attribute to rendered html
    """
    def __init__(self, message=None):
        super().__init__(message=message)
        self.field_flags = remove_required(self.field_flags)


def remove_required(flags):
    if 'required' in flags:
        n = flags.index('required')
        return flags[: n] + flags[n + 1:]

    return flags
