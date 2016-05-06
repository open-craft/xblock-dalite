"""Dalite XBlock Mixins."""


class CourseAwareXBlockMixin(object):
    """Provides LMS, Studio and workbench compliant course id attribute for XBlock."""

    @property
    def course_id(self):
        """
        Provide course_id attribute.

        :returns: Course ID
        :rtype: str
        """
        raw_course_id = getattr(self.runtime, 'course_id', 'all')
        return unicode(raw_course_id)