import logging
import logging.config
from datetime import datetime

LOG_STR_LONG = '%(asctime)s [%(levelname)-8s@%(filename)-10s;%(lineno)-4d] %(message)s'
LOG_STR = '%(message)s'


class LithieLogFileHandler(logging.FileHandler):
    def emit(self, record) -> None:
        if record.msg and record.msg.startswith('\u0001'):
            record.msg = record.msg[1:]
            self.terminator = ''
        else:
            self.terminator = '\n'

        return super().emit(record)


class LithieLogStreamHandler(logging.StreamHandler):
    def emit(self, record) -> None:
        if record.msg and record.msg.startswith('\u0001'):
            record.msg = record.msg[1:]
            self.terminator = ''
        else:
            self.terminator = '\n'

        return super().emit(record)


# We keep only one logger as a beginning
logging.basicConfig(format=LOG_STR, datefmt='%Y-%m-%d %H:%M:%S')


def log_setfh():
    sltx_log_file_handler = LithieLogFileHandler(
        'sltx-{:%Y-%m-%d-%H-%M-%S-%f}.sltx-log'.format(datetime.now()))
    formatter = logging.Formatter(LOG_STR)
    sltx_log_file_handler.setFormatter(formatter)
    LOGGER.addHandler(sltx_log_file_handler)


LOGGER = logging.getLogger('sltx')
LOGGER.handlers.clear()
LOGGER.propagate = False
sltx_log_stream_handler = LithieLogStreamHandler()
LOGGER.addHandler(sltx_log_stream_handler)
LOGGER.setLevel(logging.DEBUG)
