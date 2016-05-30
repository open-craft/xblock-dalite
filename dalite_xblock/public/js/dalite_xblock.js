function DaliteXBlock(runtime, element) {
    LtiConsumerXBlock(runtime, element);

    // hack to make LTI Consumer css applied to Dalite XBlock
    $(element).addClass("xblock-student_view-lti_consumer xblock-student_view");
    $(element).children(".xblock-dalite").addClass("lti_consumer");

    $('.btn-lti-modal-dalite-admin').each(function (index, element) {
        var $element = $(element);
        $element.iframeModal({
            top: 200,
            closeButton: '.close-modal'
        });
        var modal_selector = $element.data("target");
        var overlay_selector = (modal_selector + '_lean-overlay');
        var onClose = function () { runtime.refreshXBlock($element.data("data-xblock-id")); };
        $(overlay_selector).on("click", onClose);
        $(modal_selector).on("click", ".close-modal", onClose);
    });
}
