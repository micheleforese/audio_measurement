from pathlib import Path

APP_HOME: Path = Path(__file__).parent.parent
APP_TEST: Path = APP_HOME / "test"
APP_TEST.mkdir(exist_ok=True, parents=True)

APP_AUDIO_TEST: Path = APP_HOME / "audio-test"

APP_LOGGING_FILE: Path = APP_HOME / "logging/app.log"

APP_DB_AUTH_PATH: Path = Path("~/.config/audio_measurement/config.ini").expanduser()

