"""Utility that allows to generate passports encoded for this xblock."""
import argparse
from dalite_xblock.passport_utils import DaliteLtiPassport, prepare_passport


def main():
    """Entrypoint for this script."""
    parser = argparse.ArgumentParser(description='Create dalite passport')
    parser.add_argument('--passport-id', help='Passports are identified in studio using this value', required=True)
    parser.add_argument('--dalite-url', help='Base url for dalite, eg. http://localhost:1234', required=True)
    parser.add_argument('--lti-key', help='Value for LTI_CLITEN_KEY', required=True)
    parser.add_argument('--lti-secret', help='Value for LTI_CLIENT_SECRET', required=True)

    args = parser.parse_args()

    passport = DaliteLtiPassport(
        dalite_root_url=args.dalite_url,
        lti_key=args.lti_key,
        lti_secret=args.lti_secret,
        lti_id=args.passport_id
    )

    print '"{}"'.format(prepare_passport(passport))

if __name__ == "__main__":
    main()
