from typing import Self

import serial


class ExtechLightMeter:
    device: serial.Serial

    def __init__(self: Self, device_port: str) -> None:
        self.device = serial.Serial(device_port, baudrate=9600)

        if not self.device.is_open:
            self.device.open()

    def __del__(self: Self) -> None:
        if not self.device.closed:
            self.device.close()

    def read(self: Self) -> int:
        read_ok: bool = False

        while not read_ok:
            self.device.reset_input_buffer()
            data: str = self.device.read_until(b"\r").decode()

            lux = int(data[-5:])

            try:
                if data[-6] == "0":
                    lux *= 10
                if data[-7] == "0":
                    lux *= 10
            except Exception:
                read_ok = False
                continue

            read_ok = True

        return lux
