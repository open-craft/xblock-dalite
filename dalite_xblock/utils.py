# -*- coding: utf-8 -*-
"""
Dalite XBlock utils
"""
from lazy.lazy import lazy


def _(text):
    """
    Make '_' a no-op so we can scrape strings
    :return text
    """
    return text


# pylint: disable=protected-access
class field_values_context_manager(object):
    """
    Black wizardy to workaround the fact that field values can be callable, but that callable should be
    parameterless, and we need current XBlock to get a list of values
    """
    def __init__(self, block, field_name, field_values_callback):
        self._block = block
        self._field_name = field_name
        self._callback = field_values_callback
        self._old_values_value = None

    @lazy
    def field(self):
        return self._block.fields[self._field_name]

    def __enter__(self):
        self._old_values_value = self.field.values
        self.field._values = self._callback

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.field._values = self._old_values_value
        return False