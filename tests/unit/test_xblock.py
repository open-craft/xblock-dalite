from unittest import TestCase

import mock
from xblock.core import XBlock
from xblock.field_data import DictFieldData

from dalite_xblock.dalite_xblock import DaliteXBlock


class DaliteXBlockTests(TestCase):
    DEFAULT_COURSE_ID = 'course-1'

    def setUp(self):
        self.runtime_mock = mock.Mock()
        self.runtime_mock.course_id = self.DEFAULT_COURSE_ID
        self.block = DaliteXBlock(
            self.runtime_mock, DictFieldData({}), scope_ids=mock.Mock()
        )

    def test_course(self):
        mock_course = mock.Mock(spec=XBlock)
        self.runtime_mock.modulestore.get_course = mock.Mock(return_value=mock_course)

        self.assertEqual(self.block.course, mock_course)
        self.runtime_mock.modulestore.get_course.assert_called_once_with(self.DEFAULT_COURSE_ID)