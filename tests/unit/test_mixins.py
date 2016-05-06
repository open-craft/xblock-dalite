"""Test for Dalite XBlock mixins."""
from unittest import TestCase

import ddt
import mock
from xblock.runtime import Runtime

from dalite_xblock.mixins import CourseAwareXBlockMixin
from tests.utils import TestWithPatchesMixin


@ddt.ddt
class TestCourseAwareXBlockMixin(TestCase, TestWithPatchesMixin):
    """Tests for CourseAwareXBlockMixin."""

    class CourseAwareXBlockMixinGuineaPig(CourseAwareXBlockMixin):
        """Dummy XBlock to test CourseAwareXBlockMixin."""

        @property
        def runtime(self):
            """Return runtime for the XBlock."""
            pass

    def setUp(self):
        """setUp method - prepares test environment for each test to run."""
        self.block = self.CourseAwareXBlockMixinGuineaPig()
        self.runtime_mock = mock.create_autospec(Runtime)
        self.make_patch(
            self.CourseAwareXBlockMixinGuineaPig, 'runtime',
            mock.PropertyMock(return_value=self.runtime_mock)
        )

    @ddt.data(
        'string_course_id',
        u'unicode_course_id',
    )
    def test_course_id(self, course_id):
        """Test that course_id property returns runtime course_id value."""
        self.runtime_mock.course_id = course_id
        self.assertEqual(self.block.course_id, unicode(course_id))

    def test_course_id_no_attribute(self):
        """Test that course_id property returns 'all' if runtime does not have course_id attribute."""
        del self.runtime_mock.course_id
        self.assertEqual(self.block.course_id, unicode('all'))
