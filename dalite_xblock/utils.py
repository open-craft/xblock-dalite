# -*- coding: utf-8 -*-
"""Dalite XBlock utils."""
import re
from collections import namedtuple

from lazy.lazy import lazy


DALITE_XBLOCK_LIT_PASSPORT_PREFIX = r"(dalite-xblock)"

DaliteLtiPassport = namedtuple("LtiPassport", ["lti_id", "dalite_root_url", "lti_key", "lti_secret"])
DALITE_XBLOCK_LTI_PASSPORT_REGEX = re.compile(
    r"""
    ^                   # together with $ at the end denotes entire LTI passport is analyzed
    \(dalite-xblock\)   # denotes dalite-xblock LTI passport
    ([^;]*);            # first group - passport ID
    ([^;]*);            # second group - Dalite-ng URL
    ([^;]*);            # third group - LTI key
    ([^;]*)             # fourth group - LTI secret
    $
    """,
    re.VERBOSE
)


def _(text):  # pylint: disable=invalid-name
    """
    Make '_' a no-op so we can scrape strings.

    :return text
    """
    return text


# pylint: disable=protected-access
class FieldValuesContextManager(object):
    """
    Allow using bound methods as XBlock field values provider.

    Black wizardy to workaround the fact that field values can be callable, but that callable should be
    parameterless, and we need current XBlock to get a list of values
    """

    def __init__(self, block, field_name, field_values_callback):
        """
        Initialize FieldValuesContextManager.

        :param XBlock block: XBlock containing field to wrap
        :param string field_name: Target field name
        :param () -> list[Any] field_values_callback: Values provider callback (can be bound or unbound method)
        """
        self._block = block
        self._field_name = field_name
        self._callback = field_values_callback
        self._old_values_value = None

    @lazy
    def field(self):
        """
        Return field descriptor to wrap.

        :rtype: xblock.fields.Field
        """
        return self._block.fields[self._field_name]

    def __enter__(self):
        """Enter context managed-section."""
        self._old_values_value = self.field.values
        self.field._values = self._callback

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit from context managed-section.

        :param type|None exc_type: Type of exception thrown or None
        :param Exception|None exc_type: Exception thrown or None
        :param exc_tb: Exception traceback or None

        :rtype: bool
        :returns: True if exception should be suppressed, False otherwise
        """
        self.field._values = self._old_values_value
        return False
