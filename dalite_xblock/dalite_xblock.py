"""Dalite XBlock - convenient wrapper for LTIConsumer block tuned to work with dalite-ng."""
import logging

from lazy.lazy import lazy
from lti_consumer import LtiConsumerXBlock
from xblock.fields import String, Scope
from xblockutils.resources import ResourceLoader

from .mixins import CourseAwareXBlockMixin
from .utils import _, FieldValuesContextManager, DaliteLtiPassport, DALITE_XBLOCK_LTI_PASSPORT_REGEX, \
    DALITE_XBLOCK_LIT_PASSPORT_PREFIX

logger = logging.getLogger(__name__)
loader = ResourceLoader(__name__)


class DaliteXBlock(LtiConsumerXBlock, CourseAwareXBlockMixin):
    """
    This XBlock provides an LTI consumer interface for integrating Dalite-NG tools using the LTI specification.

    This is a wrapper around LtiConsumerXBlock, providing sensible defaults and fixed values to some
    fields, so course authors must only edit two fields: Assignment ID and Question ID - other fields
    are either automatically populated, or have default values suit most common cases.

    See LtiConsumerXBlock docstring for more detailed information
    """

    display_name = String(
        display_name=_("Display Name"),
        help=_(
            "Enter the name that students see for this component. "
            "Analytics reports may also use the display name to identify this component."
        ),
        scope=Scope.settings,
        default=_("Dalite XBlock"),
    )
    assignment_id = String(
        display_name=_("Assignment ID"),
        help=_("Assignment ID"),
        scope=Scope.settings,
    )
    question_id = String(
        display_name=_("Question ID"),
        help=_("Question ID"),
        scope=Scope.settings,
    )

    editable_fields = [
        # must edit
        "display_name", "assignment_id", "question_id",
        # Reads from course LTI passports, defaults to first dalite-ng
        "lti_id",
        # defaults are fine
        "weight", "launch_target", "inline_height", "modal_width", "modal_height", "accept_grades_past_due",
        "button_text",

        # Base class fields that should not be editable
        # 'launch_url', - obtained from LTI passport
        # 'custom_parameters', - generated automatically from assignment_id and question_id
        # 'has_score', - always True
        # 'hide_launch', - always False
        # 'ask_to_send_username', - dalite-ng defined
        # 'ask_to_send_email' - dalite-ng defined
    ]

    MALFORMED_LTI_PASSPORT = _(u"Malformed DAlite-XBlock LTI Passport: %s - skipping")

    @property
    def course(self):
        """
        Return course by course id.

        :returns: Course XBlock for current course
        :rtype: XBlock
        """
        return self.runtime.modulestore.get_course(self.course_id)

    @lazy
    def dalite_xblock_lti_passports(self):
        """
        Return all xblock-dalite LTI passports.

        :returns: list of all Dalite-xblock LTI Passports
        :rtype: list[DaliteLtiPassport]
        """
        result = []
        for lti_passport in self.course.lti_passports:
            if DALITE_XBLOCK_LIT_PASSPORT_PREFIX in lti_passport:
                lti_passport_analyzed = DALITE_XBLOCK_LTI_PASSPORT_REGEX.search(lti_passport)
                if lti_passport_analyzed and lti_passport_analyzed.group(0):   # prevents zero-length matches
                    lti_id, dalite_root_url, lti_key, lti_secret = lti_passport_analyzed.group(1, 2, 3, 4)
                    passport = DaliteLtiPassport(lti_id, dalite_root_url, lti_key, lti_secret)
                    result.append(passport)
                else:
                    logger.warn(self.MALFORMED_LTI_PASSPORT, lti_passport)

        return result

    @lazy
    def lti_passport(self):
        """
        Return selected LTI passport.

        :returns: LTI passport matching selected LTI ID
        :rtype: DaliteLtiPassport|None
        """
        for lti_passport in self.dalite_xblock_lti_passports:
            if lti_passport.lti_id == self.lti_id.strip():
                logging.warn(
                    _(u"LTI passport found for LTI ID %s: dalite URL is %s"), self.lti_id, lti_passport.dalite_root_url
                )
                return lti_passport

        logging.warn(_(u"No matching LTI passport found for LTI ID %s"), self.lti_id)
        return None

    @property
    def launch_url(self):
        """
        Return LTI launch URL for selected LTI passport.

        :returns: launch URL for selected Dalite-ng instance
        :rtype: string
        """
        if not self.lti_passport:
            return ''
        return self.lti_passport.dalite_root_url.rstrip('/') + '/lti/'

    def lti_id_values_provider(self):
        """
        Provide values for LTI ID field at runtime.

        :returns: List of Dalite-xblock LTI passports IDs.
        :rtype: [dict[str, str]]
        """
        if not self.dalite_xblock_lti_passports:
            return [{"display_name": _("No Dalite-ng LTI Passports configured"), "value": ""}]

        return [
            {"display_name": passport.lti_id, "value": passport.lti_id}
            for passport in self.dalite_xblock_lti_passports
        ]

    def student_view(self, context):
        """
        XBlock student view of this component.

        Makes a request to `lti_launch_handler` either
        in an iframe or in a new window depending on the
        configuration of the instance of this XBlock

        :param dict context: XBlock context

        :returns: XBlock HTML fragment
        :rtype: xblock.fragment.Fragment
        """
        fragment = super(DaliteXBlock, self).student_view(context)
        fragment.add_javascript(loader.load_unicode('public/js/dalite_xblock.js'))
        fragment.initialize_js('DaliteXBlock')
        return fragment

    def studio_view(self, context):
        """
        XBlock studio edit view of this component.

        :param dict context: XBlock context

        :returns: XBlock HTML fragment
        :rtype: xblock.fragment.Fragment
        """
        # can't use values_provider as we need it to be bound to current block instance
        with FieldValuesContextManager(self, 'lti_id', self.lti_id_values_provider):
            fragment = super(DaliteXBlock, self).studio_view(context)
            fragment.add_javascript(loader.load_unicode('public/js/dalite_xblock_edit.js'))
            fragment.initialize_js('DaliteXBlockEdit')
            return fragment

    def clean_studio_edits(self, data):  # pylint: disable=no-self-use
        """
        Given POST data dictionary 'data', clean the data before validating it.

        USe cases: fix capitalization, remove trailing spaces, etc.

        Provides values for fields required by LtiConsumerXBlock, but not exposed in Studio interface.
        Modifies data in place to change/clean/add field values

        :param dict data: Fields data
        """
        assignment_id, question_id = data['assignment_id'], data['question_id']
        fixed_values = {
            'hide_launch': False,
            'has_score': True,
            'custom_parameters': ["assignment_id=" + str(assignment_id), "question_id=" + str(question_id)],
            'ask_to_send_username': False,
            'ask_to_send_email': False
        }
        data.update(fixed_values)
        logging.info(_(u"Cleaned xblock field values: %s"), data)
