"""Tests for passport utils."""
import unittest

import mock
import ddt
from dalite_xblock.passport_utils import (
    DaliteLtiPassport, prepare_passport, parse_passport, filter_and_parse_passports, MALFORMED_LTI_PASSPORT_MESSAGE
)


@ddt.ddt
class TestPassportUtils(unittest.TestCase):
    """Test class for passport_utils module."""

    def test_passport_generation(self):
        """Test passport generation."""
        decoded_passport = DaliteLtiPassport(
            lti_id="test-dalite",
            lti_key="beta",
            lti_secret="gamma",
            dalite_root_url="https://dalite.com"
        )
        expected_passport = "test-dalite:dalite-xblock:aHR0cHM6Ly9kYWxpdGUuY29tO2JldGE7Z2FtbWE="
        actual_passport = prepare_passport(decoded_passport)
        self.assertEqual(expected_passport, actual_passport)

    def test_passport_parsing(self):
        """Test passport parsing."""
        expected_passport = DaliteLtiPassport(
            lti_id="test-dalite",
            lti_key="beta",
            lti_secret="gamma",
            dalite_root_url="https://dalite.com"
        )
        encoded_passport = "test-dalite:dalite-xblock:aHR0cHM6Ly9kYWxpdGUuY29tO2JldGE7Z2FtbWE="
        actual_passport = parse_passport(encoded_passport)
        self.assertEqual(expected_passport, actual_passport)

    @ddt.data(
        ("::::::", True),  # This one is ignored as we assume it is not meant for us
        ("test-dalite:dalite-xblock:p", False),  # Not base64 encoded data
        ("test-dalite-2:dalite-xblock:Zm9vYmFyCg==", False),  # Does not contain ;
        ("test-dalite-3:dalite-xblock:Ozs7Ozs7Ozs7Owo=", False)  # Contains too many ;
    )
    @ddt.unpack
    def test_malformed_passports(self, passport, is_failure_silent):
        """Test handling of malformed passports."""
        with mock.patch('dalite_xblock.passport_utils.logger.warn') as patched_warn:
            self.assertEqual(filter_and_parse_passports([passport]), [])
            if not is_failure_silent:
                patched_warn.assert_called_once_with(MALFORMED_LTI_PASSPORT_MESSAGE, passport)

    @ddt.data(
        # Handles emtpy collections
        ([], []),
        # Handles single dalite passport
        (
            ['test-dalite:dalite-xblock:aHR0cHM6Ly9kYWxpdGUuY29tO2JldGE7Z2FtbWE='],
            [DaliteLtiPassport(lti_id="test-dalite", lti_key="beta", lti_secret="gamma",
                               dalite_root_url="https://dalite.com")]
        ),
        # Ignores passports for non dalite xblocks
        (
            [
                'another-lti:edx:aHR0cHM6Ly9kYWxpdGUuY29tO2JldGE7Z2FtbWE=',
                'test-dalite:dalite-xblock:aHR0cHM6Ly9kYWxpdGUuY29tO2JldGE7Z2FtbWE=',
                'yet-another-lti:edx:aHR0cHM6Ly9kYWxpdGUuY29tO2JldGE7Z2FtbWE=',
            ],
            [DaliteLtiPassport(lti_id="test-dalite", lti_key="beta", lti_secret="gamma",
                               dalite_root_url="https://dalite.com")]
        ),
        # Handles more than single passport
        (
            [
                'another-lti:edx:aHR0cHM6Ly9kYWxpdGUuY29tO2JldGE7Z2FtbWE=',
                'test-dalite:dalite-xblock:aHR0cHM6Ly9kYWxpdGUuY29tO2JldGE7Z2FtbWE=',
                "dalite-local:dalite-xblock:aHR0cDovLzE5Mi4xNjguMzMuMToxMDEwMDtiZXRhO2dhbW1h",
                'yet-another-lti:edx:aHR0cHM6Ly9kYWxpdGUuY29tO2JldGE7Z2FtbWE=',
            ],
            [
                DaliteLtiPassport(
                    lti_id="test-dalite", lti_key="beta", lti_secret="gamma", dalite_root_url="https://dalite.com"
                ),
                DaliteLtiPassport(
                    lti_id="dalite-local", lti_key="beta", lti_secret="gamma",
                    dalite_root_url="http://192.168.33.1:10100"
                ),
            ]
        ),
    )
    @ddt.unpack
    def test_passport_filtering(self, passports, expected_output):
        """Test for function that filters dalite passports."""
        actual_output = filter_and_parse_passports(passports)
        self.assertEqual(actual_output, expected_output)
