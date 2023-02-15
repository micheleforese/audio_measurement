import logging

from audio.console import console, log


def test_logging():
    log.debug("This is a debug message")
    log.info("This is an info message")
    log.warning("This is a warning message")
    log.error("This is an error message")
    log.critical("This is a critical message")
    console.log("ciao")


if __name__ == "__main__":
    test_logging()
