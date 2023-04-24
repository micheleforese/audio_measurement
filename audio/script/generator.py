import time
from tkinter import *

import click
import serial

# ==============================================================================
# Define protocol commands
# ==============================================================================
REQUEST_STATUS = b"STATUS?"  # Request actual status.
# 0x40 (Output mode: 1:on, 0:off)
# 0x20 (OVP and/or OCP mode: 1:on, 0:off)
# 0x01 (CV/CC mode: 1:CV, 0:CC)
REQUEST_ID = b"*IDN?"

REQUEST_SET_VOLTAGE = b"VSET1?"  # request the set voltage
REQUEST_ACTUAL_VOLTAGE = b"VOUT1?"  # Request output voltage

REQUEST_SET_CURRENT = b"ISET1?"  # Request the set current
REQUEST_ACTUAL_CURRENT = b"IOUT1?"  # Requst the output current

SET_VOLTAGE = b"VSET1:"  # Set the maximum output voltage
SET_CURRENT = b"ISET1:"  # Set the maximum output current

SET_OUTPUT = b"OUT"  # Enable the power output

SET_OVP = b"OVP"  # Enable(1)/Disable(0) OverVoltageProtection

SET_OCP = b"OCP"  # Enable(1)/Disable(0) OverCurrentProtection

# ==============================================================================
# Methods
# ==============================================================================

DEVICE = "/dev/ttyACM1"


def GetID():
    PS = serial.Serial(
        DEVICE,
        baudrate=9600,
        bytesize=8,
        parity="N",
        stopbits=1,
        timeout=1,
    )
    PS.flushInput()
    PS.write(REQUEST_ID)  # Request the ID from the Power Supply
    PSID = PS.read(16)
    print(b"PSID = " + PSID)
    PS.flushInput()
    return PSID


def Get_I_Set():
    PS = serial.Serial(
        DEVICE,
        baudrate=9600,
        bytesize=8,
        parity="N",
        stopbits=1,
        timeout=1,
    )
    PS.flushInput()
    PS.write(REQUEST_SET_CURRENT)  # Request the target current
    I_set = PS.read(5)
    if I_set == b"":
        I_set = b"0"
    I_set = float(I_set)
    print("Current is set to " + str(I_set))
    PS.flushInput()
    return I_set


def Get_V_Set():
    PS = serial.Serial(
        DEVICE,
        baudrate=9600,
        bytesize=8,
        parity="N",
        stopbits=1,
        timeout=1,
    )
    PS.flushInput()
    PS.write(REQUEST_SET_VOLTAGE)  # Request the target voltage
    V_set = float(PS.read(5))
    print("Voltage is set to " + str(V_set))
    PS.flushInput()
    return V_set


def Get_Status():
    PS = serial.Serial(
        DEVICE,
        baudrate=9600,
        bytesize=8,
        parity="N",
        stopbits=1,
        timeout=1,
    )
    PS.flushInput()
    PS.write(REQUEST_STATUS)  # Request the status of the PS
    Stat = str(PS.read(5))
    print("Status = " + Stat)
    PS.flushInput()
    return Stat


def SetVoltage(Voltage) -> bytes:
    PS = serial.Serial(
        DEVICE,
        baudrate=9600,
        bytesize=8,
        parity="N",
        stopbits=1,
        timeout=1,
    )
    PS.flushInput()
    if float(Voltage) > float(VMAX):
        Voltage = VMAX
    Voltage = f"{float(Voltage):2.2f}"
    Output_string = SET_VOLTAGE + bytes(Voltage, "utf-8")
    PS.write(Output_string)
    print(Output_string)
    PS.flushInput()
    time.sleep(0.2)
    VeriVolt = f"{float(Get_V_Set()):2.2f}"  # Verify PS accepted
    # the setting
    while VeriVolt != Voltage:
        PS.write(Output_string)  # Try one more time
    vEntry.delete(0, 5)
    vEntry.insert(0, f"{float(VeriVolt):2.2f}")
    return Output_string


def SetCurrent(Current):
    PS = serial.Serial(
        DEVICE,
        baudrate=9600,
        bytesize=8,
        parity="N",
        stopbits=1,
        timeout=1,
    )
    PS.flushInput()
    if float(Current) > float(IMAX):
        Current = IMAX
    Current = f"{float(Current):2.3f}"
    Output_string = SET_CURRENT + bytes(Current, "utf-8")
    PS.write(Output_string)
    print(Output_string)
    PS.flushInput()
    time.sleep(0.2)
    VeriAmp = f"{float(Get_I_Set()):2.3f}"
    if VeriAmp != Current:
        VeriAmp = 0.00
    iEntry.delete(0, 5)
    iEntry.insert(0, f"{float(VeriAmp):2.3f}")
    return Output_string


def V_Actual():
    PS = serial.Serial(
        DEVICE,
        baudrate=9600,
        bytesize=8,
        parity="N",
        stopbits=1,
        timeout=1,
    )
    PS.flushInput()
    PS.write(REQUEST_ACTUAL_VOLTAGE)  # Request the actual voltage
    time.sleep(0.015)
    V_actual = PS.read(5)
    if V_actual == b"":
        V_actual = b"0"  # deal with the occasional NULL from PS
    V_actual = float(V_actual)
    PS.flushInput()
    return V_actual


def I_Actual():
    PS = serial.Serial(
        DEVICE,
        baudrate=9600,
        bytesize=8,
        parity="N",
        stopbits=1,
        timeout=1,
    )
    PS.flushInput()
    PS.write(REQUEST_ACTUAL_CURRENT)  # Request the actual current
    time.sleep(0.015)
    I_actual = PS.read(5)
    if I_actual == b"":
        I_actual = b"0"  # deal with the occasional NULL from PS
    I_actual = float(I_actual)
    PS.flushInput()
    return I_actual


def SetOP(OnOff):
    PS = serial.Serial(
        DEVICE,
        baudrate=9600,
        bytesize=8,
        parity="N",
        stopbits=1,
        timeout=1,
    )
    PS.flushInput()

    Output_string = SET_OUTPUT + bytes(OnOff, "utf-8")

    PS.write(Output_string)
    print(Output_string)
    PS.flushInput()
    return Output_string


def SetOVP(OnOff):
    PS = serial.Serial(
        DEVICE,
        baudrate=9600,
        bytesize=8,
        parity="N",
        stopbits=1,
        timeout=1,
    )
    PS.flushInput()
    Output_string = SET_OVP + OnOff
    PS.write(Output_string)
    print(Output_string)
    PS.flushInput()
    return Output_string


def SetOCP(OnOff):
    PS = serial.Serial(
        DEVICE,
        baudrate=9600,
        bytesize=8,
        parity="N",
        stopbits=1,
        timeout=1,
    )
    PS.flushInput()

    Output_string = SET_OCP + bytes(OnOff, "utf-8")

    PS.write(Output_string)
    print(Output_string)
    PS.flushInput()
    return Output_string


def Update_VandI():
    V_actual = f"{V_Actual():2.2f}"
    vReadoutLabel.configure(text="{} {}".format(V_actual, "V"))

    I_actual = f"{I_Actual():.3f}"
    iReadoutLabel.configure(text="{} {}".format(I_actual, "A"))


def Application_Loop():
    app.after(75, Update_VandI)
    app.after(100, Application_Loop)


def SetVA():
    Volts = vEntry.get()
    SetVoltage(Volts)

    Amps = iEntry.get()
    if Amps == "":
        Amps = b"0"
        print("changed Amps to 0")
    Amps = f"{float(Amps):.3f}"
    SetCurrent(Amps)


def MemSet(MemNum):
    print(MemNum)


@click.command()
def generator():
    Application_Loop()
    app.mainloop()
