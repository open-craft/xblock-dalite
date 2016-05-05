function DaliteXBlock(runtime, element) {
    LtiConsumerXBlock(runtime, element);

    // hack to make LTI Consumer css applied to Dalite XBlock
    $(element).addClass("xblock-student_view-lti_consumer");
    $(element).children(".xblock-dalite").addClass("lti_consumer");
}