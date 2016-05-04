from lti_consumer import LtiConsumerXBlock
from xblock.fields import String, Scope

from .utils import _


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

    editable_fields = ["display_name", "assignment_id", "question_id", "weight"]

    def get_fixed_values(self):
        return {}

    def clean_studio_edits(self, data):
        """
        Given POST data dictionary 'data', clean the data before validating it.
        e.g. fix capitalization, remove trailing spaces, etc.

        Provides values for fields required by LtiConsumerXBlock, but not exposed in Studio interface
        """
        fixed_values = self.get_fixed_values()
        data.update(fixed_values)
