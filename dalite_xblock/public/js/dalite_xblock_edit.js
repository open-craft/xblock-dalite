function DaliteXBlockEdit(runtime, element) {
    StudioEditableXBlockMixin(runtime, element);

    // force changed on LTI ID field - otherwise it is not submitted
    $('#xb-field-edit-lti_id').trigger('change');
}