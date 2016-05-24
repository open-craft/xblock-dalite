"""Tests for Dalite XBLock."""
from unittest import TestCase

import ddt
import mock

from xblock.core import XBlock
from xblock.field_data import DictFieldData
from xblock.fragment import Fragment

from dalite_xblock import dalite_xblock
from dalite_xblock.dalite_xblock import DaliteXBlock
from dalite_xblock.passport_utils import DaliteLtiPassport
from tests.utils import TestWithPatchesMixin

DEFAULT_LTI_PASSPORTS = [
    "dalite-ng-1:dalite-xblock:aHR0cDovL2ZpcnN0LnVybDo4MDgwO0tFWTtTRUNSRVQ=",
    "dalite-ng-2:dalite-xblock:aHR0cDovL290aGVyLnVybDtPVEhFUktFWTtPVEhFUlNFQ1JFVA==",
    "dalite-ng-3:dalite-xblock:aHR0cHM6Ly8xOTIuMTY4LjMzLjE7YWxwaGE7YmV0YQ==",
    "dalite-ng-4:dalite-xblock:aHR0cHM6Ly9leGFtcGxlLmNvbS87YWxwaGE7YmV0YQ=="
]

PARSED_LTI_PASSPORTS = {
    # This is http with a port.
    "dalite-ng-1": DaliteLtiPassport("dalite-ng-1", "http://first.url:8080", "KEY", "SECRET"),
    # This one is http without a port
    "dalite-ng-2": DaliteLtiPassport("dalite-ng-2", "http://other.url", "OTHERKEY", "OTHERSECRET"),
    # This one is https with IP instead of domain
    "dalite-ng-3": DaliteLtiPassport("dalite-ng-3", "https://192.168.33.1", "alpha", "beta"),
    # This one has a trailing slash
    "dalite-ng-4": DaliteLtiPassport("dalite-ng-3", "https://example.com/", "alpha", "beta")
}


@ddt.ddt
class DaliteXBlockTests(TestCase, TestWithPatchesMixin):
    """Tests for Dalite XBlock."""

    DEFAULT_COURSE_ID = "course-1"

    def setUp(self):
        """Obviously, setUP method sets up test environment for each individual test to run."""
        self.runtime_mock = mock.Mock()
        self.runtime_mock.course_id = self.DEFAULT_COURSE_ID
        self.block = DaliteXBlock(
            self.runtime_mock, DictFieldData({}), scope_ids=mock.Mock()
        )

        self.mock_course = mock.Mock(spec=XBlock)
        self.mock_course.lti_passports = DEFAULT_LTI_PASSPORTS
        self.runtime_mock.modulestore.get_course = mock.Mock(return_value=self.mock_course)

    def test_course(self):
        """Test course property."""
        mock_course = mock.Mock(spec=XBlock)
        self.runtime_mock.modulestore.get_course = mock.Mock(return_value=mock_course)

        self.assertEqual(self.block.course, mock_course)
        self.runtime_mock.modulestore.get_course.assert_called_once_with(self.DEFAULT_COURSE_ID)

    def test_dalite_xblock_lti_passports(self):
        """Test dalite_xblock_lti_passports property."""
        with mock.patch.object(dalite_xblock, "filter_and_parse_passports") as filter_passwords:
            passports = ['some:mock:passport']
            self.mock_course.lti_passports = passports
            unused_variable_1 = self.block.dalite_xblock_lti_passports
            unused_variable_2 = self.block.dalite_xblock_lti_passports
            self.assertIs(unused_variable_1, unused_variable_2)
            # Calling property twice to check caching behaviour.
            filter_passwords.assert_called_once_with(passports)

    @ddt.data(
        ('', None),
        ('missing', None),
        ('dalite-ng-1', PARSED_LTI_PASSPORTS['dalite-ng-1']),
        ('dalite-ng-2', PARSED_LTI_PASSPORTS['dalite-ng-2']),
        ('dalite-ng-3', PARSED_LTI_PASSPORTS['dalite-ng-3'])
    )
    @ddt.unpack
    def test_lti_passport(self, lti_id, expected_result):
        """Test lti_passport property."""
        self.block.lti_id = lti_id
        self.assertEqual(self.block.lti_passport, expected_result)

    @ddt.data(
        ('', ''),
        ('missing', ''),
        ('dalite-ng-1', "http://first.url:8080/lti/"),
        ('dalite-ng-2', "http://other.url/lti/"),
        ('dalite-ng-3', "https://192.168.33.1/lti/"),
        ('dalite-ng-4', "https://example.com/lti/")
    )
    @ddt.unpack
    def test_launch_url(self, lti_id, launch_url):
        """Test launch_url property."""
        self.block.lti_id = lti_id
        self.assertEqual(self.block.launch_url, launch_url)

    @ddt.data(
        ('', '', ''),
        ('missing', '', ''),
        ('dalite-ng-1', "KEY", "SECRET"),
        ('dalite-ng-2', "OTHERKEY", "OTHERSECRET")
    )
    @ddt.unpack
    def test_key_secret(self, lti_id, key, secret):
        """Test lti_provider_key_secret property."""
        self.block.lti_id = lti_id
        self.assertEqual(self.block.lti_provider_key_secret, (key, secret))

    @ddt.data(
        ([], [DaliteXBlock.NO_LTI_PASSPORTS_OPTION]),  # no passports at all
        (["dalite-ng:QWE:ASD"], [DaliteXBlock.NO_LTI_PASSPORTS_OPTION]),  # no dalite-xblock passports
        # two dalite and one non-dalite pasport
        (
            [
                "dalite-ng:QWE:ASD",
                "dalite-ng-1:dalite-xblock:aHR0cDovL2ZpcnN0LnVybDo4MDgwO0tFWTtTRUNSRVQ=",
                "dalite-ng-2:dalite-xblock:aHR0cDovL290aGVyLnVybDtPVEhFUktFWTtPVEhFUlNFQ1JFVA=="
            ],
            [
                {"display_name": "dalite-ng-1", "value": "dalite-ng-1"},
                {"display_name": "dalite-ng-2", "value": "dalite-ng-2"},
            ]
        )
    )
    @ddt.unpack
    def test_lti_id_values_provider(self, lti_passports, expected_result):
        """Test lti_id_values_provider."""
        self.mock_course.lti_passports = lti_passports
        self.assertEqual(self.block.lti_id_values_provider(), expected_result)

    @ddt.data(
        ('', 1), ('asgn#1', 1), ('assignment-2', 3), ('almost-irrelevant', 'almost-irrelevenat-too')
    )
    @ddt.unpack
    def test_clean_studio_edits(self, assignment_id, question_id):
        """
        Test clean_studio_edites transforms fields coming from Studio editor.

        Two transforms are applied:
            * Sets values to "fixed" fields: hide_launch, has_score, ask_to_send_username and ask_to_send_email
            * Sets "custom_parameters" from assignment_id and question_id
        """
        initial_data = {'assignment_id': assignment_id, 'question_id': question_id}
        expected_result = {
            'hide_launch': False,
            'has_score': True,
            'custom_parameters': ["assignment_id=" + str(assignment_id), "question_id=" + str(question_id)],
            'ask_to_send_username': False,
            'ask_to_send_email': False
        }
        expected_result.update(initial_data)  # all initial values should still be there
        data = initial_data.copy()

        self.block.clean_studio_edits(data)
        try:
            self.assertEqual(data, expected_result)
        except AssertionError:
            print "Intitial: ", initial_data
            print "Actual: ", data
            print "Expected: ", expected_result
            raise

    def test_is_ready_positive(self):
        """Test is_ready method returns true when has all the data."""
        block = DaliteXBlock(
            self.runtime_mock, DictFieldData({
                'question_id': '4', 'assignment_id': 'foo', 'lti_id': 'dalite-ng-1'
            }),
            scope_ids=mock.Mock()
        )
        self.assertTrue(block.is_lti_ready)

    def test_is_ready_negative(self):
        """Test is_ready method returns false without the data."""
        block = DaliteXBlock(
            self.runtime_mock, DictFieldData({}),
            scope_ids=mock.Mock()
        )
        self.assertFalse(block.is_lti_ready)

    # TODO: should be an integration test - figure out how to do this
    # AS is, this test is extremely fragile - it'll likely break on every code change
    def test_student_view(self):
        """Test that student_view adds JS workaround."""
        mock_fragment = mock.Mock(spec=Fragment)
        context = {}
        load_js_result = "Load JS result"
        with mock.patch("dalite_xblock.dalite_xblock.LtiConsumerXBlock.student_view") as patched_super, \
            mock.patch("dalite_xblock.dalite_xblock.loader.load_unicode") as patched_load_unicode, \
            mock.patch(
                'dalite_xblock.dalite_xblock.DaliteXBlock.is_lti_ready', new_callable=mock.PropertyMock) as is_ready:
            patched_super.return_value = mock_fragment
            patched_load_unicode.return_value = load_js_result
            is_ready.return_value = True

            result = self.block.student_view(context)
            patched_super.assert_called_once_with(context)
            patched_load_unicode.assert_called_once_with('public/js/dalite_xblock.js')

            self.assertEqual(result, mock_fragment)
            mock_fragment.add_javascript.assert_called_once_with(load_js_result)
            mock_fragment.initialize_js.assert_called_once_with('DaliteXBlock')

    # TODO: should be an integration test - figure out how to do this
    # As is, this test is extremely fragile - it'll likely break on every code change
    def test_student_view_error(self):
        """Test that student_view adds JS workaround."""
        with mock.patch('dalite_xblock.dalite_xblock.DaliteXBlock._get_context_for_template') as context, \
            mock.patch(
                'dalite_xblock.dalite_xblock.DaliteXBlock.is_lti_ready', new_callable=mock.PropertyMock) as is_ready:
            context.return_value = {}
            is_ready.return_value = False

            result = self.block.student_view(context)
            self.assertIn(
                'No question selected. Please click "Edit" and enter the assignment ID and question ID.',
                result.body_html()
            )

    # TODO: should be an integration test - figure out how to do this.
    # As is, this test is extremely fragile - it'll likely break on every code change
    def test_studio_view(self):
        """Test that studio adds JS workaround."""
        mock_fragment = mock.Mock(spec=Fragment)
        context = {}
        load_js_result = "Load JS result"
        with mock.patch("dalite_xblock.dalite_xblock.LtiConsumerXBlock.studio_view") as patched_super, \
                mock.patch("dalite_xblock.dalite_xblock.loader.load_unicode") as patched_load_unicode:
            patched_super.return_value = mock_fragment
            patched_load_unicode.return_value = load_js_result

            result = self.block.studio_view(context)
            patched_super.assert_called_once_with(context)
            patched_load_unicode.assert_called_once_with('public/js/dalite_xblock_edit.js')

            self.assertEqual(result, mock_fragment)
            mock_fragment.add_javascript.assert_called_once_with(load_js_result)
            mock_fragment.initialize_js.assert_called_once_with('DaliteXBlockEdit')
