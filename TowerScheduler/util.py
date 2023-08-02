import logging
import sys


__handler = logging.StreamHandler(sys.stdout)
__handler.setLevel(logging.DEBUG)
__formatter = logging.Formatter(
        '%(levelname)s: %(name)s: %(message)s')
__handler.setFormatter(__formatter)
def get_logger(name: str, level: int=logging.INFO) -> logging.Logger:
    '''
    Return a logger with the specified name and logging level, using a
    predefined handler.

    @param name: Name of the logger to return
    @param level: The level at which the set the returned logger
    returns:
        logging.Logger: Logger with the specified name and level
    '''
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(__handler)
    return logger
