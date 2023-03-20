from __future__ import annotations

import xml.etree.ElementTree as ET
from abc import ABC
from dataclasses import dataclass
from pathlib import Path
from typing import Self

from rich.repr import auto as rich_repr

from audio.config.sweep import SweepConfig
from audio.console import console
from audio.decoder.xml import DecoderXML
from audio.model.file import File


class ProcedureStep(ABC):
    @staticmethod
    def proc_type_to_procedure(xml: ET.Element):
        procedure: ProcedureStep | None = None

        StepList: list[DecoderXML] = [
            ProcedureText,
            ProcedureAsk,
            ProcedureDefault,
            ProcedureSetLevel,
            ProcedureSweep,
            ProcedureSerialNumber,
            ProcedureInsertionGain,
            ProcedurePrint,
            ProcedureMultiPlot,
            ProcedureFile,
            ProcedureTask,
            ProcedurePhaseSweep,
        ]

        for step in StepList:
            if step.xml_is_valid(xml):
                procedure = step.from_xml_object(xml)

        return procedure


@dataclass
@rich_repr
class ProcedureText(ProcedureStep, DecoderXML):
    text: str

    @classmethod
    def from_xml_file(cls, file: Path):
        return cls.from_xml_string(file.read_text())

    @classmethod
    def from_xml_string(cls, data: str):
        tree = ET.ElementTree(ET.fromstring(data))
        xml = tree.getroot()
        return cls.from_xml_object(xml)

    @classmethod
    def from_xml_object(cls, xml: ET.Element | None):
        if xml is None or not cls.xml_is_valid(xml):
            return None

        text: str | None = xml.text

        if text is not None:
            return cls(text=text.strip())
        return None

    @staticmethod
    def xml_is_valid(xml: ET.Element):
        return xml.tag == "text"


@dataclass
@rich_repr
class ProcedureAsk(ProcedureStep, DecoderXML):
    text: str | None = None

    @classmethod
    def from_xml_file(cls, file: Path):
        return cls.from_xml_string(file.read_text())

    @classmethod
    def from_xml_string(cls, data: str):
        tree = ET.ElementTree(ET.fromstring(data))
        xml = tree.getroot()
        return cls.from_xml_object(xml)

    @classmethod
    def from_xml_object(cls, xml: ET.Element | None):
        if xml is None or not cls.xml_is_valid(xml):
            return None

        text: str | None = xml.text

        if text is not None:
            return cls(text=text.strip())
        return None

    @staticmethod
    def xml_is_valid(xml: ET.Element):
        return xml.tag == "ask"


@dataclass
@rich_repr
class ProcedureFile(ProcedureStep, DecoderXML):
    key: str | None = None
    path: str | None = None

    @classmethod
    def from_xml_file(cls, file: Path):
        return cls.from_xml_string(file.read_text())

    @classmethod
    def from_xml_string(cls, data: str):
        tree = ET.ElementTree(ET.fromstring(data))
        xml = tree.getroot()
        return cls.from_xml_object(xml)

    @classmethod
    def from_xml_object(cls, xml: ET.Element | None):
        if xml is None or not cls.xml_is_valid(xml):
            return None

        Ekey = xml.find("./key")
        Epath = xml.find("./path")

        if Ekey is not None and Epath is not None:
            key = Ekey.text.strip()
            path = Epath.text.strip()

        return cls(key=key, path=path)

    @staticmethod
    def xml_is_valid(xml: ET.Element):
        return xml.tag == "file"


@dataclass
class DefaultSweepConfig:
    set_level: File | None = None
    offset: File | None = None
    offset_sweep: File | None = None
    insertion_gain: File | None = None
    config: SweepConfig | None = None


@dataclass
@rich_repr
class ProcedureDefault(ProcedureStep, DecoderXML):
    sweep_file_set_level: File | None = None
    sweep_file_offset: File | None = None
    sweep_file_offset_sweep: File | None = None
    sweep_file_insertion_gain: File | None = None

    sweep_config: SweepConfig | None = None

    @classmethod
    def from_xml_file(cls, file: Path):
        return ProcedureText.from_xml_string(file.read_text())

    @classmethod
    def from_xml_string(cls, data: str):
        tree = ET.ElementTree(ET.fromstring(data))
        xml = tree.getroot()
        return ProcedureText.from_xml_object(xml)

    @classmethod
    def from_xml_object(cls, xml: ET.Element | None):
        if not ProcedureText.xml_is_valid(xml):
            return None

        sweep_file_set_level: File | None = None
        sweep_file_offset: File | None = None
        sweep_file_offset_sweep: File | None = None
        sweep_file_insertion_gain: File | None = None

        sweep_config: SweepConfig | None = None

        Esweep = xml.find("./sweep")
        if Esweep is not None:
            Esweep_config = Esweep.find("./config")
            if Esweep_config is not None:
                sweep_config = SweepConfig.from_xml_object(
                    ET.ElementTree(Esweep_config),
                )
                if sweep_config is not None:
                    sweep_config.print_object()

            Efile_set_level = Esweep.find("./file_set_level")
            if Efile_set_level is not None:
                sweep_file_set_level_key = Efile_set_level.get("key")
                sweep_file_set_level_path = Efile_set_level.find("path")
                sweep_file_set_level = File(
                    sweep_file_set_level_key,
                    sweep_file_set_level_path,
                )

            Efile_offset = Esweep.find("./file_offset")
            if Efile_offset is not None:
                sweep_file_offset_key = Efile_offset.get("key")
                sweep_file_offset_path = Efile_offset.find("path")
                sweep_file_offset = File(sweep_file_offset_key, sweep_file_offset_path)

            Efile_offset_sweep = Esweep.find("./file_offset_sweep")
            if Efile_offset_sweep is not None:
                sweep_file_offset_sweep_key = Efile_offset_sweep.get("key")
                sweep_file_offset_sweep_path = Efile_offset_sweep.find("path")
                sweep_file_offset_sweep = File(
                    sweep_file_offset_sweep_key,
                    sweep_file_offset_sweep_path,
                )

            Efile_insertion_gain = Esweep.find("./file_insertion_gain")
            if Efile_insertion_gain is not None:
                sweep_file_insertion_gain_key = Efile_insertion_gain.get("key")
                sweep_file_insertion_gain_path = Efile_insertion_gain.find("path")
                sweep_file_insertion_gain = File(
                    sweep_file_insertion_gain_key,
                    sweep_file_insertion_gain_path,
                )

        return cls(
            sweep_file_set_level=sweep_file_set_level,
            sweep_file_offset=sweep_file_offset,
            sweep_file_offset_sweep=sweep_file_offset_sweep,
            sweep_file_insertion_gain=sweep_file_insertion_gain,
            sweep_config=sweep_config,
        )

    @staticmethod
    def xml_is_valid(xml: ET.Element):
        return xml.tag == "default"


@dataclass
@rich_repr
class ProcedureSetLevel(ProcedureStep, DecoderXML):
    name: str
    comment: str | None = None
    dBu: float | None = None
    dBu_modifier: bool = False
    config: SweepConfig | None = None

    @classmethod
    def from_xml_file(cls: type[Self], file: Path):
        return cls.from_xml_string(file.read_text())

    @classmethod
    def from_xml_string(cls, data: str):
        tree = ET.ElementTree(ET.fromstring(data))
        xml = tree.getroot()
        return cls.from_xml_object(xml)

    @classmethod
    def from_xml_object(cls, xml: ET.Element | None):
        if xml is None or not cls.xml_is_valid(xml):
            return None

        dBu: float | None = None
        dBu_modifier: bool = False
        sweep_config_xml: SweepConfig | None = None

        name = xml.get("name")
        comment = xml.get("comment")

        EdBu = xml.find("./dBu")
        if EdBu is not None:
            dBu = float(EdBu.text)

            modifier: str | None = EdBu.get("modifier")
            if modifier is not None and modifier == "yes":
                dBu_modifier = True

        # if Efile_set_level is not None:

        # if Efile_plot is not None:

        config = xml.find("./config")
        if config is not None:
            sweep_config_xml = SweepConfig.from_xml_object(ET.ElementTree(config))

        return cls(
            name=name,
            comment=comment,
            dBu=dBu,
            dBu_modifier=dBu_modifier,
            config=sweep_config_xml,
        )

    @staticmethod
    def xml_is_valid(xml: ET.Element):
        return xml.tag == "set_level"


@dataclass
@rich_repr
class ProcedureSweep(ProcedureStep, DecoderXML):
    name: str | None = None
    comment: str | None = None
    config: SweepConfig | None = None

    @classmethod
    def from_xml_file(cls, file: Path):
        return cls.from_xml_string(file.read_text())

    @classmethod
    def from_xml_string(cls, data: str):
        tree = ET.ElementTree(ET.fromstring(data))
        xml = tree.getroot()
        return cls.from_xml_object(xml)

    @classmethod
    def from_xml_object(cls, xml: ET.Element | None):
        if xml is None or not cls.xml_is_valid(xml):
            return None

        config: SweepConfig | None = None

        name = xml.get("name")
        comment = xml.get("comment")

        Econfig = xml.find("./config")
        if Econfig is not None:
            config = SweepConfig.from_xml_object(ET.ElementTree(Econfig))

        return cls(name=name, comment=comment, config=config)

    @staticmethod
    def xml_is_valid(xml: ET.Element):
        return xml.tag == "sweep"


@dataclass
@rich_repr
class ProcedureSerialNumber(ProcedureStep, DecoderXML):
    text: str

    @classmethod
    def from_xml_file(cls, file: Path):
        return cls.from_xml_string(file.read_text())

    @classmethod
    def from_xml_string(cls, data: str):
        tree = ET.ElementTree(ET.fromstring(data))
        xml = tree.getroot()
        return cls.from_xml_object(xml)

    @classmethod
    def from_xml_object(cls, xml: ET.Element | None):
        if xml is None or not cls.xml_is_valid(xml):
            return None

        text = xml.find("./text")

        if text is None:
            return None

        return cls(
            text=text.text,
        )

    @staticmethod
    def xml_is_valid(xml: ET.Element):
        return xml.tag == "serial_number"


@dataclass
@rich_repr
class ProcedureInsertionGain(ProcedureStep, DecoderXML):
    file_calibration_key: str | None = None
    file_calibration_path: str | None = None

    file_set_level_key: str | None = None
    file_set_level_path: str | None = None

    file_gain_key: str | None = None
    file_gain_path: str | None = None

    @classmethod
    def from_xml_file(cls, file: Path):
        return cls.from_xml_string(file.read_text())

    @classmethod
    def from_xml_string(cls, data: str):
        tree = ET.ElementTree(ET.fromstring(data))
        xml = tree.getroot()
        return cls.from_xml_object(xml)

    @classmethod
    def from_xml_object(cls, xml: ET.Element | None):
        if xml is None or not cls.xml_is_valid(xml):
            return None

        file_calibration_key: str | None = None
        file_calibration_path: str | None = None
        file_set_level_key: str | None = None
        file_set_level_path: str | None = None
        file_gain_key: str | None = None
        file_gain_path: str | None = None

        Efile_file_calibration = xml.find("./file_calibration")
        if Efile_file_calibration is not None:
            file_calibration_key = Efile_file_calibration.get("key")
            file_calibration_path = Efile_file_calibration.get("path")

            if not (
                file_calibration_key is not None or file_calibration_path is not None
            ):
                return None

        Efile_set_level = xml.find("./file_set_level")
        if Efile_set_level is not None:
            file_set_level_key = Efile_set_level.get("key")
            file_set_level_path = Efile_set_level.get("path")

            if not (file_set_level_key is not None or file_set_level_path is not None):
                return None

        Efile_gain = xml.find("./file_gain")
        if Efile_gain is not None:
            file_gain_key = Efile_gain.get("key")
            file_gain_path = Efile_gain.get("path")

            if not (file_gain_key is not None or file_gain_path is not None):
                return None

        return cls(
            file_calibration_key=file_calibration_key,
            file_calibration_path=file_calibration_path,
            file_set_level_key=file_set_level_key,
            file_set_level_path=file_set_level_path,
            file_gain_key=file_gain_key,
            file_gain_path=file_gain_path,
        )

    @staticmethod
    def xml_is_valid(xml: ET.Element):
        return xml.tag == "insertion_gain"


@rich_repr
class ProcedureTask(ProcedureStep, DecoderXML):
    text: str | None
    steps: list[ProcedureStep]

    def __init__(
        self,
        text: str | None = None,
        steps: list[ProcedureStep] = [],
    ) -> None:
        self.text = text
        self.steps = steps

    @classmethod
    def from_xml_file(cls, file: Path):
        return cls.from_xml_string(file.read_text())

    @classmethod
    def from_xml_string(cls, data: str):
        tree = ET.ElementTree(ET.fromstring(data))
        xml = tree.getroot()
        return cls.from_xml_object(xml)

    @classmethod
    def from_xml_object(cls, xml: ET.Element | None):
        if xml is None or not cls.xml_is_valid(xml):
            return None

        text: str | None = None

        text = xml.find(".").get("text")

        step_nodes: list[ET.Element] = xml.findall("./*")

        steps: list[ProcedureStep] = []

        for idx, step in enumerate(step_nodes):
            proc_type = step.tag

            console.print(proc_type)
            procedure = ProcedureStep.proc_type_to_procedure(step)
            if procedure is not None:
                steps.append(procedure)
            else:
                console.print(f"procedure idx {idx} is NULL")

        return cls(
            text=text,
            steps=steps,
        )

    @staticmethod
    def xml_is_valid(xml: ET.Element):
        return xml.tag == "task"


@rich_repr
class ProcedurePrint(ProcedureStep, DecoderXML):
    variables: list[str]

    def __init__(self, variables: list[str] = []) -> None:
        self.variables = variables

    @classmethod
    def from_xml_file(cls, file: Path):
        return cls.from_xml_string(file.read_text())

    @classmethod
    def from_xml_string(cls, data: str):
        tree = ET.ElementTree(ET.fromstring(data))
        xml = tree.getroot()
        return cls.from_xml_object(xml)

    @classmethod
    def from_xml_object(cls, xml: ET.Element | None):
        if xml is None or not cls.xml_is_valid(xml):
            return None

        variables: list[str] = [
            var.text for var in xml.findall("./var") if var.text is not None
        ]

        return cls(variables=variables)

    @staticmethod
    def xml_is_valid(xml: ET.Element):
        return xml.tag == "print"


@dataclass
@rich_repr
class ProcedureMultiPlot(ProcedureStep, DecoderXML):
    name: str
    file_plot: str
    folder_sweep: list[str]
    config: SweepConfig | None = None

    @classmethod
    def from_xml_file(cls, file: Path):
        return cls.from_xml_string(file.read_text())

    @classmethod
    def from_xml_string(cls, data: str):
        tree = ET.ElementTree(ET.fromstring(data))
        xml = tree.getroot()
        return cls.from_xml_object(xml)

    @classmethod
    def from_xml_object(cls, xml: ET.Element | None):
        if xml is None or not cls.xml_is_valid(xml):
            return None

        name = xml.find(".").get("name", None)

        file_plot = xml.find("./file_plot")

        folder_sweep: list[str] = []

        Efolders = xml.findall("./folder_sweep/var")

        for Efolder in Efolders:
            if Efolder.text is None:
                continue

            text = Efolder.text
            if Efolder.get("balanced") is not None:
                folder_sweep.append(f"{text}/{text}.balanced.csv")
            else:
                folder_sweep.append(f"{text}/{text}.csv")

        console.print(folder_sweep)

        Econfig = xml.find("./config")

        sweep_config_xml: SweepConfig | None = None

        if Econfig is not None:
            sweep_config_xml = SweepConfig.from_xml_object(ET.ElementTree(Econfig))

        if name is not None and file_plot is not None:
            return cls(
                name=name,
                file_plot=file_plot.text,
                folder_sweep=folder_sweep,
                config=sweep_config_xml,
            )
        else:
            return None

    @staticmethod
    def xml_is_valid(xml: ET.Element):
        return xml.tag == "multiplot"


@dataclass
@rich_repr
class ProcedurePhaseSweepData:
    name: str | None = None
    folder_path: str | None = None
    graph_path: str | None = None
    config: SweepConfig | None = None


@rich_repr
class ProcedurePhaseSweep(ProcedureStep, DecoderXML):
    data: ProcedurePhaseSweepData

    def __init__(
        self,
        data: ProcedurePhaseSweepData = ProcedurePhaseSweepData(),
    ) -> None:
        self.data = data

    @classmethod
    def from_xml_file(cls, file: Path):
        return cls.from_xml_string(file.read_text())

    @classmethod
    def from_xml_string(cls, data: str):
        tree = ET.ElementTree(ET.fromstring(data))
        xml = tree.getroot()
        return cls.from_xml_object(xml)

    @classmethod
    def from_xml_object(cls, xml: ET.Element | None):
        if xml is None or not cls.xml_is_valid(xml):
            return None

        name: str | None = None
        folder_path: str | None = None
        graph_path: str | None = None

        Ename = xml.find(".")
        if Ename is not None:
            name = Ename.get("name", None)

        Efolder = xml.find("./folder_path")
        if Efolder is not None:
            folder_path = Efolder.text

        Egraph_path = xml.find("./graph_path")
        if Egraph_path is not None:
            graph_path = Egraph_path.text

        Econfig = xml.find("./config")

        sweep_config_xml: SweepConfig | None = None

        if Econfig is not None:
            sweep_config_xml = SweepConfig.from_xml_object(ET.ElementTree(Econfig))

        data = ProcedurePhaseSweepData(
            name=name,
            folder_path=folder_path,
            graph_path=graph_path,
            config=sweep_config_xml,
        )

        return cls(data=data)

    @staticmethod
    def xml_is_valid(xml: ET.Element):
        return xml.tag == "phase_sweep"


class ProcedureCalculation(ProcedureStep, DecoderXML):
    steps: list[ProcedureStep]

    def __init__(
        self,
        steps: list[ProcedureStep] = [],
    ) -> None:
        self.steps = steps

    @classmethod
    def from_xml_file(cls, file: Path):
        return cls.from_xml_string(file.read_text())

    @classmethod
    def from_xml_string(cls, data: str):
        tree = ET.ElementTree(ET.fromstring(data))
        xml = tree.getroot()
        return cls.from_xml_object(xml)

    @classmethod
    def from_xml_object(cls, xml: ET.Element | None):
        if xml is None or not cls.xml_is_valid(xml):
            return None

        step_nodes: list[ET.Element] = xml.findall("./*")

        steps: list[ProcedureStep] = []

        for idx, step in enumerate(step_nodes):
            proc_type = step.tag

            console.print(proc_type)
            procedure = ProcedureStep.proc_type_to_procedure(step)
            if procedure is not None:
                steps.append(procedure)
            else:
                console.print(f"procedure idx {idx} is NULL")

        return cls(steps=steps)

    @staticmethod
    def xml_is_valid(xml: ET.Element):
        return xml.tag == "calculation"


class ProcedureCalculation_sweepVoltageDb(ProcedureStep, DecoderXML):
    key: str
    idx: int

    def __init__(
        self,
        key: str,
        idx: int,
    ) -> None:
        self.key = key
        self.idx = idx

    @classmethod
    def from_xml_file(cls, file: Path):
        return cls.from_xml_string(file.read_text())

    @classmethod
    def from_xml_string(cls, data: str):
        tree = ET.ElementTree(ET.fromstring(data))
        xml = tree.getroot()
        return cls.from_xml_object(xml)

    @classmethod
    def from_xml_object(cls, xml: ET.Element | None):
        if xml is None or not cls.xml_is_valid(xml):
            return None

        key = xml.get("key")
        idx = xml.get("idx")

        return cls(key=key, idx=idx)

    @staticmethod
    def xml_is_valid(xml: ET.Element):
        return xml.tag == "sweepVoltageDb"


class ProcedureCalculation_sweepVoltageLocal(ProcedureStep, DecoderXML):
    key: str

    def __init__(
        self,
        key: str,
    ) -> None:
        self.key = key

    @classmethod
    def from_xml_file(cls, file: Path):
        return cls.from_xml_string(file.read_text())

    @classmethod
    def from_xml_string(cls, data: str):
        tree = ET.ElementTree(ET.fromstring(data))
        xml = tree.getroot()
        return cls.from_xml_object(xml)

    @classmethod
    def from_xml_object(cls, xml: ET.Element | None):
        if xml is None or not cls.xml_is_valid(xml):
            return None

        key = xml.get("key")

        return cls(key=key)

    @staticmethod
    def xml_is_valid(xml: ET.Element):
        return xml.tag == "sweepVoltageLocal"


class ProcedurePlot(ProcedureStep, DecoderXML):
    key: str

    def __init__(
        self,
        key: str,
    ) -> None:
        self.key = key

    @classmethod
    def from_xml_file(cls, file: Path):
        return cls.from_xml_string(file.read_text())

    @classmethod
    def from_xml_string(cls, data: str):
        tree = ET.ElementTree(ET.fromstring(data))
        xml = tree.getroot()
        return cls.from_xml_object(xml)

    @classmethod
    def from_xml_object(cls, xml: ET.Element | None):
        if xml is None or not cls.xml_is_valid(xml):
            return None

        key = xml.get("key")

        return cls(key=key)

    @staticmethod
    def xml_is_valid(xml: ET.Element):
        return xml.tag == "plot"
