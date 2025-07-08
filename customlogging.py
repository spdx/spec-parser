# logging utilities using custom logger(s)

# SPDX-License-Identifier: Apache-2.0

import logging


def error_printed(logger):
    """
    Check if any error has been logged.
    This is a utility function to check the log handler's count of errors.
    """
    return logger.handlers[0].count[logging.ERROR] > 0


class LogCountingHandler(logging.StreamHandler):
    def __init__(self):
        super().__init__()
        self.count = dict.fromkeys((logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL), 0)

    def emit(self, record):
        self.count[record.levelno] += 1
        super().emit(record)

    def num_errors(self):
        return self.count[logging.ERROR]

    def num_warnings(self):
        return self.count[logging.WARNING]


def setup_logging():
    logger = logging.getLogger()
    logger.addHandler(LogCountingHandler())
    return logger

