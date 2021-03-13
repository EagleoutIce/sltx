import logging
import logging.config
import re
from datetime import datetime

from sltxpkg.util import create_multiple_replacer

LOG_STR_LONG = '%(asctime)s [%(levelname)-8s@%(filename)-10s;%(lineno)-4d] %(message)s'
LOG_STR = '%(message)s'
LOG_STR = '%(level_color)s%(message)s%(color_reset)s'

RESET_SEQ = "\033[0m"
ENCAPSULE_SEQ = "\033[%dm%s" + RESET_SEQ

COLORS = {
    'WARNING': '\033[33m',
    'INFO': '',
    'DEBUG': '\033[35m',
    'CRITICAL': '\033[95m',
    'ERROR': '\033[31m'
}


__log__replacer = create_multiple_replacer({
    'True': ENCAPSULE_SEQ % (92, 'True'),
    'False': ENCAPSULE_SEQ % (91, 'False')
})


def log_color_format(message: str) -> str:
    return __log__replacer(message)


class LithieColoredStreamFormatter(logging.Formatter):
    def __init__(self, msg, use_color=True):
        logging.Formatter.__init__(self, msg)
        self.use_color = use_color

    def format(self, record):

        if self.use_color and record.levelname in COLORS:
            record.level_color = COLORS[record.levelname]
        else:
            record.level_color = ""
        record.color_reset = RESET_SEQ
        msg = logging.Formatter.format(self, record)
        return log_color_format(msg)


class LithieLogFileHandler(logging.FileHandler):
    """Just like the default logger, but it suppresses a line break if the msg starts with \\u1
    """

    def emit(self, record) -> None:
        if record.msg and record.msg.startswith('\u0001'):
            record.msg = record.msg[1:]
            self.terminator = ''
        else:
            self.terminator = '\n'

        return super().emit(record)


class LithieLogStreamHandler(logging.StreamHandler):
    """Just like the default logger, but it suppresses a line break if the msg starts with \\u1
    """

    def emit(self, record) -> None:
        if record.msg and record.msg.startswith('\u0001'):
            record.msg = record.msg[1:]
            self.terminator = ''
        else:
            self.terminator = '\n'
        return super().emit(record)


# We keep only one logger as a beginning
logging.basicConfig(format=LOG_STR, datefmt='%Y-%m-%d %H:%M:%S')


def log_set_file_handler():
    """Update the file handler of the main 'LOGGER' to mirror outputs to a file
    """
    sltx_log_file_handler = LithieLogFileHandler(
        'sltx-{:%Y-%m-%d-%H-%M-%S-%f}.sltx-log'.format(datetime.now()))
    formatter = logging.Formatter(LOG_STR)
    sltx_log_file_handler.setFormatter(formatter)
    LOGGER.addHandler(sltx_log_file_handler)


LOGGER = logging.getLogger('sltx')
LOGGER.handlers.clear()
LOGGER.propagate = False
sltx_log_stream_handler = LithieLogStreamHandler()
sltx_log_stream_handler.setFormatter(LithieColoredStreamFormatter(LOG_STR))
LOGGER.addHandler(sltx_log_stream_handler)
LOGGER.setLevel(logging.DEBUG)
