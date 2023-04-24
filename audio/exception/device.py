from typing import Self


class DeviceNotFoundError(Exception):
    message: str

    def __init__(self: Self, message: str = "UsbTmc devices not found.") -> None:
        self.message = message
        super().__init__(self.message)
