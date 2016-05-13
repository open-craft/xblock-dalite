#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Run tests for the Dalite XBlock.

This script is required to run our selenium tests inside the xblock-sdk workbench
because the workbench SDK's settings file is not inside any python module.
"""

import os
import sys

import logging


def main():
    """Main entry point."""
    noisy_logger_overrides = {
        'workbench.views': logging.ERROR,
        'django.request': logging.ERROR,
        'workbench.runtime': logging.ERROR,
    }

    # Use the workbench settings file:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "workbench.settings")
    # Configure a range of ports in case the default port of 8081 is in use
    os.environ.setdefault("DJANGO_LIVE_TEST_SERVER_ADDRESS", "localhost:8081-8099")

    for noisy_logger, log_level in noisy_logger_overrides.iteritems():
        logging.getLogger(noisy_logger).setLevel(log_level)

    from django.core.management import execute_from_command_line
    args = sys.argv[1:]
    paths = [arg for arg in args if arg[0] != '-']
    if not paths:
        paths = ["tests/"]
    options = [arg for arg in args if arg not in paths]
    execute_from_command_line([sys.argv[0], "test"] + paths + options)

if __name__ == "__main__":
    main()
