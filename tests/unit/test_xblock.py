"""Tests for Dalite XBLock."""
from unittest import TestCase

import ddt
import mock
from xblock.core import XBlock
from xblock.field_data import DictFieldData

from dalite_xblock.dalite_xblock import DaliteXBlock
from dalite_xblock.utils import DaliteLtiPassport


DEFAULT_LTI_PASSPORTS = [
    "(dalite-xblock)dalite-ng-1;http://first.url:8080/;KEY;SECRET",
    "(dalite-xblock)dalite-ng-2;https://other.url:8080;OTHERKEY;OTHERSECRET"
]

PARSED_LTI_PASSPORTS = {
    "dalite-ng-1": DaliteLtiPassport("dalite-ng-1", "http://first.url:8080/", "KEY", "SECRET"),
    "dalite-ng-2": DaliteLtiPassport("dalite-ng-2", "https://other.url:8080", "OTHERKEY", "OTHERSECRET"),
}


@ddt.ddt
class DaliteXBlockTests(TestCase):
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

    @ddt.data(
        ([], []),
        (["dalite-ng:QWE:ASD"], []),  # non dalite-xblock pasport ignored
        # correctly parses values for dalite-xblock
        (
            ["(dalite-xblock)dalite-ng;http://qwe.asd/;QWE;ASD"],
            [DaliteLtiPassport("dalite-ng", "http://qwe.asd/", "QWE", "ASD")]
        ),
        # and can ignore non dalite-xblock passport
        (
            ["dalite-ng:QWE:ASD", "(dalite-xblock)dalite-ng-2;https://other.url:8080;KEY;SECRET"],
            [DaliteLtiPassport("dalite-ng-2", "https://other.url:8080", "KEY", "SECRET")]
        ),
        # two dalite-xblock passports
        (
            [
                "dalite-ng:QWE:ASD",
                "(dalite-xblock)dalite-ng-3;https://other.url:8080;KEY;SECRET",
                "(dalite-xblock)dalite-ng-4;;;",
            ],
            [
                DaliteLtiPassport("dalite-ng-3", "https://other.url:8080", "KEY", "SECRET"),
                DaliteLtiPassport("dalite-ng-4", "", "", ""),  # technically, this is valid
            ]
        ),
    )
    @ddt.unpack
    def test_dalite_xblock_lti_passports(self, lti_passports, dalite_passports):
        """Test dalite_xblock_lti_passports property."""
        self.mock_course.lti_passports = lti_passports

        self.assertEqual(self.block.dalite_xblock_lti_passports, dalite_passports)

    def test_malformed_dalite_xblock_lti_passport(self):
        """Test malformed LTI passports does not crash XBlock, and record warnings."""
        lti_passports = [
            "(dalite-xblock)missing-component;KEY;SECRET",
            "(dalite-xblock)extra-component;https://other.url:8080;KEY;SECRET;EXTRA_COMPONENT",
        ]

        self.mock_course.lti_passports = lti_passports

        expected_log_calls = [
            mock.call(DaliteXBlock.MALFORMED_LTI_PASSPORT, lti_passports[0]),
            mock.call(DaliteXBlock.MALFORMED_LTI_PASSPORT, lti_passports[1]),
        ]

        with mock.patch('dalite_xblock.dalite_xblock.logger.warn') as patched_warn:
            self.assertEqual(self.block.dalite_xblock_lti_passports, [])

            self.assertEqual(patched_warn.call_args_list, expected_log_calls)

    @ddt.data(
        ('', None),
        ('missing', None),
        ('dalite-ng-1', PARSED_LTI_PASSPORTS['dalite-ng-1']),
        ('dalite-ng-2', PARSED_LTI_PASSPORTS['dalite-ng-2'])
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
        ('dalite-ng-2', "https://other.url:8080/lti/")
    )
    @ddt.unpack
    def test_launch_url(self, lti_id, launch_url):
        """Test launch_url property."""
        self.block.lti_id = lti_id
        self.assertEqual(self.block.launch_url, launch_url)
