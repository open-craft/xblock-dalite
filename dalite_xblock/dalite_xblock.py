"""Dalite XBlock - convenient wrapper for LTIConsumer block tuned to work with dalite-ng."""
import contextlib
import logging

from lazy.lazy import lazy
from lti_consumer import LtiConsumerXBlock
from xblock.core import XBlock
from xblock.fields import String, Scope
from xblockutils.resources import ResourceLoader

from .mixins import CourseAwareXBlockMixin
from .utils import _, FieldValuesContextManager
from .passport_utils import filter_and_parse_passports

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

    NO_LTI_PASSPORTS_OPTION = {"display_name": _("No Dalite-ng LTI Passports configured"), "value": ""}

    ADMIN_URL_SUFFIX = u"admin"
    EDIT_QUESTION_SUFFIX = u"edit-question"

    LMS_ERROR_MESSAGE = _("This question is not configured yet.  Please tell your instructor if you see this error.")
    CMS_NO_PASSPORT_ERROR = _(
        'No valid LTI passport set. Please click Edit and select LTI passport.  '
        'If you see: "No Dalite-ng LTI Passports configured" message, then '
        'please go to Advanced Settings and ensure that the LTI Passport '
        'looks like: "<passport-id>:dalite-xblock:<long hash string>".  '
        'For example: "dalite-ng:dalite-xblock:aHR0cDovLzE5Mi4xNjguMzMuMToxMDEwMDthbHBoYTtiZXRh".  '
        'If you are unsure whether your passport is correct, or don\'t know your passport, please consult '
        'your Dalite provider.'
    )
    CMS_NO_QUESTION_ERROR = _(
        "No question selected. Please click \"Edit\" and enter the assignment ID and question ID."
    )

    # Note used by some bowels of XBlock machinery, if absent after edit will use student_view in studio.
    has_author_view = True

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
        return filter_and_parse_passports(self.course.lti_passports)

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
    def lti_provider_key_secret(self):
        """Obtain client_key and client_secret credentials from current course."""
        if not self.lti_passport:
            return '', ''
        return self.lti_passport.lti_key, self.lti_passport.lti_secret

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
            return [self.NO_LTI_PASSPORTS_OPTION]

        return [
            {"display_name": passport.lti_id, "value": passport.lti_id}
            for passport in self.dalite_xblock_lti_passports
        ]

    @property
    def is_lti_ready(self):
        """Check if this XBlock has all settings so it can connect to the LTI."""
        return all((self.launch_url, self.question_id, self.assignment_id))

    def get_status_message(self, in_studio):
        """
        If this component is ready returns None, else returns an error message.

        :param str in_studio: If true will return message for the Instructor.
        :return: str or None
        """
        if self.is_lti_ready:
            return None

        if not in_studio:
            return self.LMS_ERROR_MESSAGE

        if not self.launch_url:
            return self.CMS_NO_PASSPORT_ERROR

        return self.CMS_NO_QUESTION_ERROR

    def render_student_view(self, context, in_studio):
        """
        Helper method that renders the "student" part of this XBlock both in CMS and in LMS.

        :param dict context: Rendering context.
        :param bool in_studio: If true we are rendering for CMS (displays different error messages)
        :return: Fragment.
        """
        fragment = super(DaliteXBlock, self).student_view(context)
        fragment.add_javascript(loader.load_unicode('public/js/dalite_xblock.js'))
        fragment.initialize_js('DaliteXBlock')

        if not self.is_lti_ready:
            message = self.get_status_message(in_studio)
            fragment.content = u''
            context.update(self._get_context_for_template())
            context.update({
                "message": message
            })
            fragment.add_content(
                loader.render_django_template('/templates/dalite_xblock_data_not_filled.html', context)
            )
            return fragment

        return fragment

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
        return self.render_student_view(context, False)

    @contextlib.contextmanager
    def add_extra_custom_params(self, additional_custom_parameters):
        """
        Temporarily adds custom parameters to this xblock.

        These parameters will be sent to the `lti` provider by any calls made during that time.

        :param list additional_custom_parameters: A list of parameters in a 'key=value` format.
               Eg: ``[u'action=launch-admin']``
        """
        current_params = self.custom_parameters
        self.custom_parameters = list(self.custom_parameters) + additional_custom_parameters
        yield
        self.custom_parameters = current_params

    @XBlock.handler
    def lti_launch_handler(self, request, suffix=u''):
        """
        Override superclass method.

        This method interprets suffix parameter and translates it to
        action LTI parameter, which is then passed to dalite.
        """
        suffix = unicode(suffix)
        custom_params = []
        # By default no action, which means to show the question.
        if suffix == self.ADMIN_URL_SUFFIX:
            # Launch /admin/ url
            custom_params = [u'action=launch-admin']
        elif suffix == self.EDIT_QUESTION_SUFFIX:
            # Launch admin url that allows to edit currently selected question
            custom_params = [u'action=edit-question']

        with self.add_extra_custom_params(custom_params):
            return super(DaliteXBlock, self).lti_launch_handler(request)

    def render_button_launching_admin(self, context, form_url_suffix, button_label, id_specifier):
        """A helper method that renders a button that launches dalite admin in an overlay."""
        admin_context = dict(context)
        admin_context.update(self._get_context_for_template())
        admin_context.update({
            'has_score': False,
            'form_url_suffix': form_url_suffix,
            'dalite_admin_label': button_label,
            'element_id_specifier': id_specifier
        })

        return loader.render_django_template("/templates/dalite_xblock_lti_iframe.html", admin_context)

    def author_view(self, context):
        """XBlock view in studio. It adds admin buttons that allow to launch an overlay displaying admin."""
        fragment = self.render_student_view(context, True)
        if self.launch_url:
            fragment.add_content(self.render_button_launching_admin(
                context=context,
                form_url_suffix=self.ADMIN_URL_SUFFIX,
                button_label=_("Manage peer instruction assignments and questions"),
                id_specifier="admin-main"
            ))
        if self.is_lti_ready:
            fragment.add_content(self.render_button_launching_admin(
                context=context,
                form_url_suffix=self.EDIT_QUESTION_SUFFIX,
                button_label=_("Edit this question"),
                id_specifier="admin-edit-question"
            ))

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

        Use cases: fix capitalization, remove trailing spaces, etc.

        Provides values for fields required by LtiConsumerXBlock, but not exposed in Studio interface.
        Modifies data in place to change/clean/add field values

        :param dict data: Fields data
        """
        assignment_id, question_id = data.get('assignment_id'), data.get('question_id')
        fixed_values = {
            'hide_launch': False,
            'has_score': True,
            'custom_parameters': ["assignment_id=" + str(assignment_id), "question_id=" + str(question_id)],
            'ask_to_send_username': False,
            'ask_to_send_email': False
        }
        data.update(fixed_values)
        logging.info(_(u"Cleaned xblock field values: %s"), data)
