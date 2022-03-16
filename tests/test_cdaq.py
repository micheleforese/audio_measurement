from cDAQ.console import console

from cDAQ.utility import cDAQ


def test_print_device_and_version(self):
    # 192.168.1.52 cDAQ
    cdaq: cDAQ = cDAQ()

    console.print("ciaos")

    cdaq.print_driver_version()
    cdaq.print_list_devices()
