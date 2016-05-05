import logging
import re
from collections import namedtuple

from lazy.lazy import lazy
from lti_consumer import LtiConsumerXBlock
from xblock.fields import String, Scope
from xblockutils.resources import ResourceLoader

from .utils import _, field_values_context_manager


logger = logging.getLogger(__name__)
loader = ResourceLoader(__name__)

DALITE_XBLOCK_LTI_PASSPORT_REGEX = re.compile(
    r"""
    ^                   # together with $ at the end denotes entire LTI passport is analyzed
    \(dalite-xblock\)   # denotes dalite-xblock LTI passport
    ([^;]+);            # first group - passport ID
    ([^;]+);            # second group - Dalite-ng URL
    ([^;]+);            # third group - LTI key
    ([^;]+)             # fourth group - LTI secret
    $
    """,
    re.VERBOSE
)


DaliteLtiPassport = namedtuple("LtiPassport", ["lti_id", "dalite_root_url", "lti_key", "lti_secret"])


class DaliteXBlock(LtiConsumerXBlock):
    """
    Dalite XBlock
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

    @property
    def course(self):
        """
        Return course by course id.
        """
        return self.runtime.modulestore.get_course(self.course_id)  # pylint: disable=no-member

    @lazy
    def _dalite_xblock_lti_passports(self):
        result = []
        for lti_passport in self.course.lti_passports:
            lti_passport_analyzed = DALITE_XBLOCK_LTI_PASSPORT_REGEX.search(lti_passport)
            if lti_passport_analyzed and lti_passport_analyzed.group(0):   # prevents zero-length matches
                lti_id, dalite_root_url, lti_key, lti_secret = lti_passport_analyzed.group(1, 2, 3, 4)
                passport = DaliteLtiPassport(lti_id, dalite_root_url, lti_key, lti_secret)
                result.append(passport)

        return result

    @lazy
    def lti_passport(self):
        for lti_passport in self._dalite_xblock_lti_passports:
            if lti_passport.lti_id == self.lti_id.strip():
                logging.warn(
                    _(u"LTI passport found for LTI ID %s: dalite URL is %s"), self.lti_id, lti_passport.dalite_root_url
                )
                return lti_passport

        logging.warn(_(u"No matching LTI passport found for LTI ID %s"), self.lti_id)
        return None

    @property
    def launch_url(self):
        if not self.lti_passport:
            return ''
        return self.lti_passport.dalite_root_url.rstrip('/') + '/lti/'

    def get_fixed_values(self, assignment_id, question_id):
        custom_parameters = ["assignment_id="+str(assignment_id), "question_id="+str(question_id)]
        return {
            'hide_launch': False,
            'has_score': True,
            'custom_parameters': custom_parameters,
            'ask_to_send_username': False,
            'ask_to_send_email': False
        }

    def _get_context_for_template(self):
        """
        Returns the context dict for LTI templates.

        Arguments:
            None

        Returns:
            dict: Context variables for templates
        """
        result = super(DaliteXBlock, self)._get_context_for_template()
        result['launch_url'] = self.launch_url
        return result

    def lti_id_values_provider(self):
        if not self._dalite_xblock_lti_passports:
            return [{"display_name": _("No Dalite-ng LTI Passports configured"), "value": ""}]

        return [
            {"display_name": passport.lti_id, "value": passport.lti_id}
            for passport in self._dalite_xblock_lti_passports
        ]

    def student_view(self, context):
        fragment = super(DaliteXBlock, self).student_view(context)
        fragment.add_javascript(loader.load_unicode('public/js/dalite_xblock.js'))
        fragment.initialize_js('DaliteXBlock')
        return fragment

    def studio_view(self, context):
        # can't use values_provider as we need it to be bound to current block instance
        with field_values_context_manager(self, 'lti_id', self.lti_id_values_provider):
            fragment = super(DaliteXBlock, self).studio_view(context)
            fragment.add_javascript(loader.load_unicode('public/js/dalite_xblock_edit.js'))
            fragment.initialize_js('DaliteXBlockEdit')
            return fragment

    def clean_studio_edits(self, data):
        """
        Given POST data dictionary 'data', clean the data before validating it.
        e.g. fix capitalization, remove trailing spaces, etc.

        Provides values for fields required by LtiConsumerXBlock, but not exposed in Studio interface
        """
        fixed_values = self.get_fixed_values(data['assignment_id'], data['question_id'])
        data.update(fixed_values)
        logging.info(_(u"Cleaned xblock field values: %s"), data)
