import logging
import sys

DEBUG = True

DB_ENGINE = 'sqlite:///db.sqlite3'
COUNT_PERSONS_TO_WRITE_IN_DB_FOR_ONE_QUERY = 100000
DATETIME_FORMAT = '%d-%m-%Y %H:%M:%S'

log = logging.getLogger(__name__)
log.level = logging.DEBUG if DEBUG else logging.ERROR
log.addHandler(logging.StreamHandler(sys.stderr))
log.debug('ATTENTION!!! YOU USE DEBUG-MODE')