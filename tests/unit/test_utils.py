"""Tests for Dalite XBlock utilities"""
from unittest import TestCase

import ddt
import mock
from xblock.core import XBlock
from xblock.field_data import DictFieldData
from xblock.fields import String

from dalite_xblock.utils import _, FieldValuesContextManager


class DummyXBlock(XBlock):
    """Dummy XBlock."""
    field = String(values=[10, 15, 20])


@ddt.ddt
class GetTextTests(TestCase):
    """Tests for gettext (aka _) method"""

    @ddt.data(None, '', "qwerty", u"azerty")
    def test_gettext(self, argument):
        """Tests that this particular implementation we use is a no-op (or, better put, identity function)."""
        self.assertEqual(_(argument), argument)


@ddt.ddt
class FieldValuesContextManagerTests(TestCase):
    """Tests for FieldValuesContextManager."""
    def setUp(self):
        """Obviously, setUp method prepares test environment for each test to run."""
        self.runtime_mock = mock.Mock()
        self.block = DummyXBlock(self.runtime_mock, field_data=DictFieldData({}), scope_ids=mock.Mock())

    @ddt.data([], [1, 2, 3], range(5))
    def test_context_manager(self, values):
        """
        Test that FieldValuesContextManager works correctly.

        Correctly means that it replaces field's values with value arising from values_generator for a duration of
        context scope, and restores them to initial value after exiting the scope.
        """
        values_generator = mock.Mock(return_value=values)
        initial_values = self.block.fields['field'].values

        with FieldValuesContextManager(self.block, 'field', values_generator):
            available_values = self.block.fields['field'].values

            self.assertTrue(values_generator.called)
            self.assertEqual(available_values, values)

        self.assertEqual(self.block.fields['field'].values, initial_values)
