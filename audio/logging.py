import logging

from audio.constant import APP_LOGGING_FILE

log = logging.getLogger("audio")
log.setLevel(logging.DEBUG)

file_handler = logging.FileHandler(APP_LOGGING_FILE, mode="w")
formatter = logging.Formatter("[%(asctime)s] - %(levelname)s: %(message)s")
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.DEBUG)

log.addHandler(file_handler)
