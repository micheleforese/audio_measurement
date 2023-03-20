from enum import Enum, auto
from math import log10, sqrt


def Vrms_to_Vpp(Vrms: float) -> float:
    return Vrms * 2 * sqrt(2)


def Vrms_to_VdBu(Vrms: float) -> float:
    return 20 * log10(Vrms / 0.77459667)


def Vpp_to_Vrms(Vpp: float) -> float:
    return Vpp / (2 * sqrt(2))


def Vpp_to_VdBu(Vpp: float) -> float:
    return Vrms_to_VdBu(Vpp_to_Vrms(Vpp))


def VdBu_to_Vrms(VdBu: float) -> float:
    return pow(10, VdBu / 20) * 0.77459667


class VoltageMode(Enum):
    Vpp = auto()
    Vrms = auto()
    VdBu = auto()


def VdBu_to_Vpp(VdBu: float) -> float:
    return Vrms_to_Vpp(VdBu_to_Vrms(VdBu))


def voltage_converter(
    voltage: float,
    frm: VoltageMode,
    to: VoltageMode,
) -> float | None:
    if frm == to:
        return voltage

    if frm == VoltageMode.Vpp:
        if to == VoltageMode.Vrms:
            return Vpp_to_Vrms(voltage)
        elif to == VoltageMode.VdBu:
            return Vpp_to_VdBu(voltage)
    elif frm == VoltageMode.Vrms:
        if to == VoltageMode.Vpp:
            return Vrms_to_Vpp(voltage)
        elif to == VoltageMode.VdBu:
            return Vrms_to_VdBu(voltage)
    elif frm == VoltageMode.VdBu:
        if to == VoltageMode.Vrms:
            return VdBu_to_Vrms(voltage)
        elif to == VoltageMode.Vpp:
            return VdBu_to_Vpp(voltage)
    return None


def calculate_gain_dB(Vin: float, Vout: float) -> float:
    return 20 * log10(Vout / Vin)
