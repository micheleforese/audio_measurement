import os
import serial
import usb.core
import usb.util
from cDAQ.console import console


class usbtmc_instr:
    """Simple implementation of a USBTMC device driver, in the style of visa.h"""

    def __init__(self, device: os.path):
        self.device = device
        self.FILE = os.open(device, os.O_RDWR)
        # self.serial = serial.Serial(device)
        console.log(usb.core.show_devices(verbose=True), style="info")

    # def __del__(self):
    #     self.serial.close()

    def write(self, command: str):
        command += '\0'
        # self.serial.write(bytes(command, "utf-8"))
        console.log(bytes(command, "utf-8"), style="info")
        os.write(self.FILE, bytes(command, "utf-8"))

    def read(self, length=4000) -> bytes:
        # return self.serial.read(length)
        return os.read(self.FILE, length)

    def getName(self) -> str:
        # self.serial.write("*IDN?")
        self.write("*IDN?")
        return str(self.read()).strip()

    def sendReset(self):
        self.write("*RST")
