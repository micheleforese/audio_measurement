from __future__ import annotations

import xml.etree.ElementTree as ET
from abc import ABC
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import ClassVar, Dict, List, Optional, Type, Union

import rich
from rich.repr import auto as rich_repr

from audio.config.sweep import SweepConfig
from audio.console import console
from audio.model.file import CacheFile, File
from audio.plot import CacheCsvData
from audio.decoder.xml import DecoderXML


class ProcedureStep(ABC):
    @staticmethod
    def proc_type_to_procedure(xml: ET.Element):
        procedure: Optional[ProcedureStep] = None

        StepList: List[DecoderXML] = [
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
            ProcedureCheck,
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
    def from_xml_object(cls, xml: Optional[ET.Element]):
        if xml is None or not cls.xml_is_valid(xml):
            return None

        text: Optional[str] = xml.text

        if text is not None:
            return cls(text=text.strip())

    @staticmethod
    def xml_is_valid(xml: ET.Element):
        return xml.tag == "text"


@dataclass
@rich_repr
class ProcedureAsk(ProcedureStep, DecoderXML):
    text: Optional[str] = None

    @classmethod
    def from_xml_file(cls, file: Path):
        return cls.from_xml_string(file.read_text())

    @classmethod
    def from_xml_string(cls, data: str):
        tree = ET.ElementTree(ET.fromstring(data))
        xml = tree.getroot()
        return cls.from_xml_object(xml)

    @classmethod
    def from_xml_object(cls, xml: Optional[ET.Element]):
        if xml is None or not cls.xml_is_valid(xml):
            return None

        text: Optional[str] = xml.text

        if text is not None:
            return cls(text=text.strip())

    @staticmethod
    def xml_is_valid(xml: ET.Element):
        return xml.tag == "ask"


@dataclass
@rich_repr
class ProcedureFile(ProcedureStep, DecoderXML):
    key: Optional[str] = None
    path: Optional[str] = None

    @classmethod
    def from_xml_file(cls, file: Path):
        return cls.from_xml_string(file.read_text())

    @classmethod
    def from_xml_string(cls, data: str):
        tree = ET.ElementTree(ET.fromstring(data))
        xml = tree.getroot()
        return cls.from_xml_object(xml)

    @classmethod
    def from_xml_object(cls, xml: Optional[ET.Element]):
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
    set_level: Optional[File] = None
    offset: Optional[File] = None
    offset_sweep: Optional[File] = None
    insertion_gain: Optional[File] = None
    config: Optional[SweepConfig] = None


@dataclass
@rich_repr
class ProcedureDefault(ProcedureStep, DecoderXML):
    sweep_file_set_level: Optional[File] = None
    sweep_file_offset: Optional[File] = None
    sweep_file_offset_sweep: Optional[File] = None
    sweep_file_insertion_gain: Optional[File] = None

    sweep_config: Optional[SweepConfig] = None

    @classmethod
    def from_xml_file(cls, file: Path):
        return ProcedureText.from_xml_string(file.read_text())

    @classmethod
    def from_xml_string(cls, data: str):
        tree = ET.ElementTree(ET.fromstring(data))
        xml = tree.getroot()
        return ProcedureText.from_xml_object(xml)

    @classmethod
    def from_xml_object(cls, xml: Optional[ET.Element]):
        if not ProcedureText.xml_is_valid(xml):
            return None

        sweep_file_set_level: Optional[File] = None
        sweep_file_offset: Optional[File] = None
        sweep_file_offset_sweep: Optional[File] = None
        sweep_file_insertion_gain: Optional[File] = None

        sweep_config: Optional[SweepConfig] = None

        Esweep = xml.find("./sweep")
        if Esweep is not None:
            Esweep_config = Esweep.find("./config")
            if Esweep_config is not None:
                sweep_config = SweepConfig.from_xml_object(
                    ET.ElementTree(Esweep_config)
                )
                if sweep_config is not None:
                    sweep_config.print()

            Efile_set_level = Esweep.find("./file_set_level")
            if Efile_set_level is not None:
                sweep_file_set_level_key = Efile_set_level.get("key")
                sweep_file_set_level_path = Efile_set_level.find("path")
                sweep_file_set_level = File(
                    sweep_file_set_level_key, sweep_file_set_level_path
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
                    sweep_file_offset_sweep_key, sweep_file_offset_sweep_path
                )

            Efile_insertion_gain = Esweep.find("./file_insertion_gain")
            if Efile_insertion_gain is not None:
                sweep_file_insertion_gain_key = Efile_insertion_gain.get("key")
                sweep_file_insertion_gain_path = Efile_insertion_gain.find("path")
                sweep_file_insertion_gain = File(
                    sweep_file_insertion_gain_key, sweep_file_insertion_gain_path
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
    dBu: Optional[float] = None
    file_set_level_key: Optional[str] = None
    file_set_level_name: Optional[str] = None
    file_plot_key: Optional[str] = None
    file_plot_name: Optional[str] = None
    config: Optional[SweepConfig] = None
    override: bool = False

    @classmethod
    def from_xml_file(cls, file: Path):
        return cls.from_xml_string(file.read_text())

    @classmethod
    def from_xml_string(cls, data: str):
        tree = ET.ElementTree(ET.fromstring(data))
        xml = tree.getroot()
        return cls.from_xml_object(xml)

    @classmethod
    def from_xml_object(cls, xml: Optional[ET.Element]):
        if xml is None or not cls.xml_is_valid(xml):
            return None

        dBu: Optional[float] = None
        file_set_level_key: Optional[str] = None
        file_set_level_name: Optional[str] = None
        file_plot_key: Optional[str] = None
        file_plot_name: Optional[str] = None
        override: bool = False
        sweep_config_xml: Optional[SweepConfig] = None

        EdBu = xml.find("./dBu")
        if EdBu is not None:
            dBu = float(EdBu.text)

        Efile_set_level = xml.find("./file_set_level")
        if Efile_set_level is not None:
            file_set_level_key = Efile_set_level.get("key")
            file_set_level_name = Efile_set_level.get("path")

        Efile_plot = xml.find("./file_set_level_plot")
        if Efile_plot is not None:
            file_plot_key = Efile_plot.get("key")
            file_plot_name = Efile_plot.get("path")

        override_elem = xml.get("override")
        override = override_elem is not None

        config = xml.find("./config")
        if config is not None:
            sweep_config_xml = SweepConfig.from_xml_object(ET.ElementTree(config))

        return cls(
            dBu=dBu,
            file_set_level_key=file_set_level_key,
            file_set_level_name=file_set_level_name,
            file_plot_key=file_plot_key,
            file_plot_name=file_plot_name,
            config=sweep_config_xml,
            override=override,
        )

    @staticmethod
    def xml_is_valid(xml: ET.Element):
        return xml.tag == "set_level"


@dataclass
@rich_repr
class ProcedureSweep(ProcedureStep, DecoderXML):

    name_folder: Optional[str] = None
    file_set_level: Optional[File] = None
    file_offset: Optional[File] = None
    file_offset_sweep: Optional[File] = None
    file_insertion_gain: Optional[File] = None
    config: Optional[SweepConfig] = None
    override: bool = False

    @classmethod
    def from_xml_file(cls, file: Path):
        return cls.from_xml_string(file.read_text())

    @classmethod
    def from_xml_string(cls, data: str):
        tree = ET.ElementTree(ET.fromstring(data))
        xml = tree.getroot()
        return cls.from_xml_object(xml)

    @classmethod
    def from_xml_object(cls, xml: Optional[ET.Element]):
        if xml is None or not cls.xml_is_valid(xml):
            return None

        name_folder: str

        file_set_level: Optional[File] = None
        file_offset: Optional[File] = None
        file_offset_sweep: Optional[File] = None
        file_insertion_gain: Optional[File] = None
        override: bool = False

        config: Optional[SweepConfig] = None

        Ename_folder = xml.find("./name_folder")
        if Ename_folder is None:
            return None
        name_folder = Ename_folder.text

        Efile_set_level = xml.find("./file_set_level")
        if Efile_set_level is not None:
            file_set_level = File(
                key=Efile_set_level.get("key"), path=Efile_set_level.get("path")
            )

            if file_set_level.is_null():
                return None

        Efile_offset = xml.find("./file_offset")
        if Efile_offset is not None:
            file_offset = File(
                key=Efile_offset.get("key"), path=Efile_offset.get("path")
            )

            if file_offset.is_null():
                return None

        Efile_offset_sweep = xml.find("./file_offset_sweep")
        if Efile_offset_sweep is not None:
            file_offset_sweep = File(
                key=Efile_offset_sweep.get("key"), path=Efile_offset_sweep.get("path")
            )

            if file_offset_sweep.is_null():
                return None

        Efile_insertion_gain = xml.find("./file_insertion_gain")
        if Efile_insertion_gain is not None:
            file_insertion_gain = File(
                key=Efile_insertion_gain.get("key"),
                path=Efile_insertion_gain.get("path"),
            )

            if file_insertion_gain.is_null():
                return None

        Econfig = xml.find("./config")
        if Econfig is not None:
            config = SweepConfig.from_xml_object(ET.ElementTree(Econfig))

        override_elem = xml.get("override", None)
        override = override_elem is not None

        return cls(
            name_folder=name_folder,
            file_set_level=file_set_level,
            file_offset=file_offset,
            file_offset_sweep=file_offset_sweep,
            file_insertion_gain=file_insertion_gain,
            config=config,
            override=override,
        )

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
    def from_xml_object(cls, xml: Optional[ET.Element]):
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

    file_calibration_key: Optional[str] = None
    file_calibration_path: Optional[str] = None

    file_set_level_key: Optional[str] = None
    file_set_level_path: Optional[str] = None

    file_gain_key: Optional[str] = None
    file_gain_path: Optional[str] = None

    @classmethod
    def from_xml_file(cls, file: Path):
        return cls.from_xml_string(file.read_text())

    @classmethod
    def from_xml_string(cls, data: str):
        tree = ET.ElementTree(ET.fromstring(data))
        xml = tree.getroot()
        return cls.from_xml_object(xml)

    @classmethod
    def from_xml_object(cls, xml: Optional[ET.Element]):
        if xml is None or not cls.xml_is_valid(xml):
            return None

        file_calibration_key: Optional[str] = None
        file_calibration_path: Optional[str] = None
        file_set_level_key: Optional[str] = None
        file_set_level_path: Optional[str] = None
        file_gain_key: Optional[str] = None
        file_gain_path: Optional[str] = None

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

    text: Optional[str]
    steps: List[ProcedureStep]

    def __init__(
        self,
        text: Optional[str] = None,
        steps: List[ProcedureStep] = [],
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
    def from_xml_object(cls, xml: Optional[ET.Element]):
        if xml is None or not cls.xml_is_valid(xml):
            return None

        text: Optional[str] = None

        text = xml.find(".").get("text")

        step_nodes: List[ET.Element] = xml.findall("./*")

        steps: List[ProcedureStep] = []

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


class ProcedureCheckCondition(Enum):
    NOT_EXISTS = "not exists"

    @staticmethod
    def from_str(label: Optional[str]) -> Optional[ProcedureCheckCondition]:
        if label is None:
            return None

        if label == ProcedureCheckCondition.NOT_EXISTS.value:
            return ProcedureCheckCondition.NOT_EXISTS
        else:
            return None


class ProcedureCheckAction(Enum):
    BREAK_TASK = "break"

    @staticmethod
    def from_str(
        label: Optional[str],
    ) -> Optional[ProcedureCheckAction]:

        if label is None:
            return None

        if label == ProcedureCheckAction.BREAK_TASK.value:
            return ProcedureCheckAction.BREAK_TASK
        else:
            return None


@rich_repr
class ProcedureCheck(ProcedureStep, DecoderXML):

    condition: ProcedureCheckCondition
    action: ProcedureCheckAction
    file: Optional[File]

    def __init__(
        self,
        condition: ProcedureCheckCondition = ProcedureCheckCondition.NOT_EXISTS,
        action: ProcedureCheckAction = ProcedureCheckAction.BREAK_TASK,
        file: Optional[File] = None,
    ) -> None:
        self.condition = condition
        self.action = action
        self.file = file

    @classmethod
    def from_xml_file(cls, file: Path):
        return cls.from_xml_string(file.read_text())

    @classmethod
    def from_xml_string(cls, data: str):
        tree = ET.ElementTree(ET.fromstring(data))
        xml = tree.getroot()
        return cls.from_xml_object(xml)

    @classmethod
    def from_xml_object(cls, xml: Optional[ET.Element]):
        if xml is None or not cls.xml_is_valid(xml):
            return None

        condition: Optional[ProcedureCheckCondition] = None
        action: Optional[ProcedureCheckAction] = None
        file: Optional[File] = None

        condition = ProcedureCheckCondition.from_str(xml.find(".").get("condition"))
        action = ProcedureCheckAction.from_str(xml.find(".").get("action"))

        Efile = xml.find("./file")
        if Efile is not None:
            file = File(key=Efile.get("key"), path=Efile.get("path"))

        return cls(
            condition=condition,
            action=action,
            file=file,
        )

    @staticmethod
    def xml_is_valid(xml: ET.Element):
        return xml.tag == "check"


@rich_repr
class ProcedurePrint(ProcedureStep, DecoderXML):

    variables: List[str]

    def __init__(self, variables: List[str] = []) -> None:
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
    def from_xml_object(cls, xml: Optional[ET.Element]):
        if xml is None or not cls.xml_is_valid(xml):
            return None

        variables: List[str] = [
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
    folder_sweep: List[str]
    config: Optional[SweepConfig] = None

    @classmethod
    def from_xml_file(cls, file: Path):
        return cls.from_xml_string(file.read_text())

    @classmethod
    def from_xml_string(cls, data: str):
        tree = ET.ElementTree(ET.fromstring(data))
        xml = tree.getroot()
        return cls.from_xml_object(xml)

    @classmethod
    def from_xml_object(cls, xml: Optional[ET.Element]):
        if xml is None or not cls.xml_is_valid(xml):
            return None

        name = xml.find(".").get("name", None)

        file_plot = xml.find("./file_plot")

        folder_sweep: List[str] = []

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

        sweep_config_xml: Optional[SweepConfig] = None

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
    name: Optional[str] = None
    folder_path: Optional[str] = None
    graph_path: Optional[str] = None
    config: Optional[SweepConfig] = None


@rich_repr
class ProcedurePhaseSweep(ProcedureStep, DecoderXML):

    data: ProcedurePhaseSweepData

    def __init__(
        self, data: ProcedurePhaseSweepData = ProcedurePhaseSweepData()
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
    def from_xml_object(cls, xml: Optional[ET.Element]):
        if xml is None or not cls.xml_is_valid(xml):
            return None

        name: Optional[str] = None
        folder_path: Optional[str] = None
        graph_path: Optional[str] = None

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

        sweep_config_xml: Optional[SweepConfig] = None

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
