from pathlib import Path

APP_HOME = Path(__file__).parent.parent
APP_TEST = APP_HOME / "test"
APP_TEST.mkdir(exist_ok=True, parents=True)

APP_AUDIO_TEST = APP_HOME / "audio-test"
