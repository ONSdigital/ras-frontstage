import itertools

from frontstage.support.util import flatten_keys


class ValidatorBase:
    """
    Base class for performing validation of a dictionary against a specific criteria, for example checking
    existence of specific keys, format of specific values, etc.

    Each subclass must be a callable, i.e. must implement dunder method __call__, which accepts the
    dictionary to be validated and returns True if the dictionary is deemed valid. The member property
    _errors should also be set, this is a list of string values, where each string value is an error
    message (where errors exist). I.e. multiple errors may be found for any given dictionary, thus
    multiple error messages can be set.
    """

    def __init__(self):
        self._errors = []

    @property
    def errors(self):
        return self._errors


class Exists(ValidatorBase):

    ERROR_MESSAGE = "Required key '{}' is missing."

    def __init__(self, *keys):
        super().__init__()
        self._keys = set(keys)
        self._diff = []

    def __call__(self, data):
        keys = flatten_keys(data)
        self._diff = self._keys.difference(keys)
        self._errors = [self.ERROR_MESSAGE.format(d) for d in self._diff]
        return len(self._diff) == 0


class Validator:
    def __init__(self, *rules):
        self._rules = list(rules)
        self.valid = True

    def add_rule(self, r):
        self._rules.append(r)

    def validate(self, d):
        self.valid = all([r(d) for r in self._rules])
        return self.valid

    @property
    def errors(self):
        return list(itertools.chain(*[r.errors for r in self._rules]))
