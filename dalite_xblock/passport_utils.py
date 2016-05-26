"""
Module that handles passport parsing and generation.

Separate module so I know no XBlock related imports are used from here, and
it can be launched locally on vanilla python, just to generate passports.
"""
import base64
from collections import namedtuple
import logging

logger = logging.getLogger(__name__)

DaliteLtiPassport = namedtuple("DaliteLtiPassport", ["lti_id", "dalite_root_url", "lti_key", "lti_secret"])

DALITE_PASSPORT_MARKER = "dalite-xblock"

MALFORMED_LTI_PASSPORT_MESSAGE = u"Malformed Dalite-XBlock LTI Passport: %s - skipping"


def prepare_passport(passport_data):
    """
    Create passport in a dalite-xblock format.

    :param  DalitePassportData passport_data:
    :returns: Dalite passport that can be pasted into studio
    :rtype: str
    """
    decoded_data = ";".join((passport_data.dalite_root_url, passport_data.lti_key, passport_data.lti_secret))
    encoded_part = base64.b64encode(decoded_data)
    return ":".join((passport_data.lti_id, DALITE_PASSPORT_MARKER, encoded_part))


def parse_passport(passport_str):
    """
    Parse passport.

    :param str passport_str: A passport string.
    :rtype: DaliteLtiPassport or None if parsing failed
    """
    passport_parts = passport_str.split(":")
    if len(passport_parts) != 3 or passport_parts[1] != DALITE_PASSPORT_MARKER:
        return None
    lti_id = passport_parts[0]
    encoded_passport = passport_parts[2]
    try:
        decoded_passport = base64.b64decode(encoded_passport)
    except TypeError:
        logger.warn(MALFORMED_LTI_PASSPORT_MESSAGE, passport_str)
        return None
    encoded_part_parts = decoded_passport.split(";")
    if len(encoded_part_parts) != 3:
        logger.warn(MALFORMED_LTI_PASSPORT_MESSAGE, passport_str)
        return None
    dalite_root_url, lti_key, lti_secret = decoded_passport.split(";")
    return DaliteLtiPassport(
        lti_id=lti_id, lti_key=lti_key, lti_secret=lti_secret, dalite_root_url=dalite_root_url
    )


def filter_and_parse_passports(passports):
    """
    Return parsed passports for dalite-xblock.

    :param Iterable[str] passports: List of strings that contain passports for this xblock and for normal LTI modules
    :return: list[DaliteLtiPassport]
    """
    return [
        passport
        for passport in (parse_passport(passport_str) for passport_str in passports)
        if passport is not None
    ]
