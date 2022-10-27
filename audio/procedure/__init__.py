from __future__ import annotations
from enum import Enum, auto

import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar, Dict, List, Optional, Type, Union

import rich

from audio.config.sweep import SweepConfig
from audio.console import console
from audio.model.file import CacheFile, File
from audio.plot import CacheCsvData
from audio.type import Dictionary


class ProcedureStep(ABC):
    XML_TAG: str = ""

    @staticmethod
    def proc_type_to_procedure(proc_type: str, xml: ET.Element):
        procedure: Optional[ProcedureStep] = None

        procedure_list_type: Dict[str, Type] = {
            ProcedureText.XML_TAG: ProcedureText,
            ProcedureAsk.XML_TAG: ProcedureAsk,
            ProcedureDefault.XML_TAG: ProcedureDefault,
            ProcedureSetLevel.XML_TAG: ProcedureSetLevel,
            ProcedureSweep.XML_TAG: ProcedureSweep,
            ProcedureSerialNumber.XML_TAG: ProcedureSerialNumber,
            ProcedureInsertionGain.XML_TAG: ProcedureInsertionGain,
            ProcedurePrint.XML_TAG: ProcedurePrint,
            ProcedureMultiPlot.XML_TAG: ProcedureMultiPlot,
            ProcedureFile.XML_TAG: ProcedureFile,
        }

        procedure_type: Optional[Type] = procedure_list_type.get(proc_type)
        if procedure_type is not None:
            procedure = procedure_type.from_xml(xml)

        return procedure


@dataclass
@rich.repr.auto
class ProcedureText(ProcedureStep):
    text: str
    XML_TAG: ClassVar[str] = "text"

    def __init__(self, text: str) -> None:
        self.text = text

    @classmethod
    def from_dict(cls, data: Dictionary):

        text = data.get_property("text", str)
        if text is not None:
            return cls(text)
        else:
            return None

    @classmethod
    def from_xml(cls, xml: ET.Element):
        text = xml.text

        if text is not None:
            return cls(text.strip())


@dataclass
@rich.repr.auto
class ProcedureAsk(ProcedureStep):
    text: Optional[str] = None
    XML_TAG: ClassVar[str] = "ask"

    @classmethod
    def from_xml(cls, xml: ET.Element):
        text = xml.text

        if text is not None:
            text = text.strip()

        return cls(text)


@dataclass
@rich.repr.auto
class ProcedureFile(ProcedureStep):
    key: Optional[str] = None
    path: Optional[str] = None
    XML_TAG: ClassVar[str] = "file"

    @classmethod
    def from_xml(cls, xml: ET.Element):
        Ekey = xml.find("./key")
        Epath = xml.find("./path")

        if Ekey is not None and Epath is not None:
            key = Ekey.text.strip()
            path = Epath.text.strip()

        return cls(key=key, path=path)


@dataclass
class DefaultSweepConfig:
    set_level: Optional[File] = None
    offset: Optional[File] = None
    insertion_gain: Optional[File] = None

    config: Optional[SweepConfig] = None


@dataclass
@rich.repr.auto
class ProcedureDefault(ProcedureStep):
    sweep_file_set_level: Optional[File] = None
    sweep_file_offset: Optional[File] = None
    sweep_file_insertion_gain: Optional[File] = None

    sweep_config: Optional[SweepConfig] = None

    XML_TAG: ClassVar[str] = "default"

    @classmethod
    def from_xml(cls, xml: ET.Element):

        if xml is None:
            return None

        sweep_file_set_level: Optional[File] = None
        sweep_file_offset: Optional[File] = None
        sweep_file_insertion_gain: Optional[File] = None

        sweep_config: Optional[SweepConfig] = None

        Esweep = xml.find("./sweep")
        if Esweep is not None:
            Esweep_config = Esweep.find("./config")
            if Esweep_config is not None:
                sweep_config = SweepConfig.from_xml(ET.ElementTree(Esweep_config))
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
            sweep_file_insertion_gain=sweep_file_insertion_gain,
            sweep_config=sweep_config,
        )


@dataclass
@rich.repr.auto
class ProcedureSetLevel(ProcedureStep):
    dBu: Optional[float] = None
    file_set_level_key: Optional[str] = None
    file_set_level_name: Optional[str] = None
    file_plot_key: Optional[str] = None
    file_plot_name: Optional[str] = None
    config: Optional[SweepConfig] = None
    override: bool = False
    XML_TAG: ClassVar[str] = "set_level"

    @classmethod
    def from_xml(cls, xml: ET.Element):
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
            sweep_config_xml = SweepConfig.from_xml(ET.ElementTree(config))

        return cls(
            dBu=dBu,
            file_set_level_key=file_set_level_key,
            file_set_level_name=file_set_level_name,
            file_plot_key=file_plot_key,
            file_plot_name=file_plot_name,
            config=sweep_config_xml,
            override=override,
        )


@dataclass
@rich.repr.auto
class ProcedureSweep(ProcedureStep):

    name_folder: Optional[str] = None
    file_set_level_key: Optional[str] = None
    file_set_level_path: Optional[str] = None
    file_offset_key: Optional[str] = None
    file_offset_path: Optional[str] = None
    file_insertion_gain_key: Optional[str] = None
    file_insertion_gain_path: Optional[str] = None
    config: Optional[SweepConfig] = None
    override: bool = False
    XML_TAG: ClassVar[str] = "sweep"

    @classmethod
    def from_xml(cls, xml: Optional[ET.Element]):
        if xml is None:
            return None

        name_folder: str
        file_set_level_key: Optional[str] = None
        file_set_level_path: Optional[str] = None
        file_offset_key: Optional[str] = None
        file_offset_path: Optional[str] = None
        file_insertion_gain_key: Optional[str] = None
        file_insertion_gain_path: Optional[str] = None
        override: bool = False

        config: Optional[SweepConfig] = None

        Ename_folder = xml.find("./name_folder")
        if Ename_folder is None:
            return None
        name_folder = Ename_folder.text

        Efile_set_level = xml.find("./file_set_level")
        if Efile_set_level is not None:
            file_set_level_key = Efile_set_level.get("key")
            file_set_level_path = Efile_set_level.get("path")

            if not (file_set_level_key is not None or file_set_level_path is not None):
                return None

        Efile_offset = xml.find("./file_offset")
        if Efile_offset is not None:
            file_offset_key = Efile_offset.get("key")
            file_offset_path = Efile_offset.get("path")

            if not (file_offset_key is not None or file_offset_path is not None):
                return None

        Efile_insertion_gain = xml.find("./file_insertion_gain")
        if Efile_insertion_gain is not None:
            file_insertion_gain_key = Efile_insertion_gain.get("key")
            file_insertion_gain_path = Efile_insertion_gain.get("path")

            if not (
                file_insertion_gain_key is not None
                or file_insertion_gain_path is not None
            ):
                return None

        Econfig = xml.find("./config")
        if Econfig is not None:
            config = SweepConfig.from_xml(ET.ElementTree(Econfig))

        override_elem = xml.get("override", None)
        override = override_elem is not None

        return cls(
            name_folder=name_folder,
            file_set_level_key=file_set_level_key,
            file_set_level_path=file_set_level_path,
            file_offset_key=file_offset_key,
            file_offset_path=file_offset_path,
            file_insertion_gain_key=file_insertion_gain_key,
            file_insertion_gain_path=file_insertion_gain_path,
            config=config,
            override=override,
        )


@dataclass
@rich.repr.auto
class ProcedureSerialNumber(ProcedureStep):

    text: Optional[str] = None
    XML_TAG: ClassVar[str] = "serial_number"

    @classmethod
    def from_xml(cls, xml: ET.Element):
        if xml is None:
            return None

        text = xml.find("./text")

        if text is not None:
            return cls(
                text=text.text,
            )
        else:
            return None


@dataclass
@rich.repr.auto
class ProcedureInsertionGain(ProcedureStep):

    file_calibration_key: Optional[str] = None
    file_calibration_path: Optional[str] = None

    file_set_level_key: Optional[str] = None
    file_set_level_path: Optional[str] = None

    file_gain_key: Optional[str] = None
    file_gain_path: Optional[str] = None
    XML_TAG: ClassVar[str] = "insertion_gain"

    @classmethod
    def from_xml(cls, xml: Optional[ET.Element]):
        if xml is None:
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


@dataclass
@rich.repr.auto
class ProcedureTask(ProcedureStep):

    text: Optional[str] = None
    steps: List[ProcedureStep] = field(default_factory=[])
    XML_TAG: ClassVar[str] = "task"

    @classmethod
    def from_xml(cls, xml: Optional[ET.Element]):
        if xml is None:
            return None

        text: Optional[str] = None

        text = xml.find(".").get("text")

        step_nodes: List[ET.Element] = xml.findall("./*")

        steps: List[ProcedureStep] = []

        for idx, step in enumerate(step_nodes):
            proc_type = step.tag

            console.print(proc_type)
            procedure = ProcedureStep.proc_type_to_procedure(proc_type, step)
            if procedure is not None:
                steps.append(procedure)
            else:
                console.print(f"procedure idx {idx} is NULL")

        return cls(
            text=text,
            steps=steps,
        )


class ProcedureCheckCondition(Enum):
    NOT_EXISTS = "not exists"

    @staticmethod
    def from_str(label: Optional[str]) -> Optional[ProcedureCheckCondition]:
        if label is None:
            return None

        if label in ProcedureCheckCondition:
            return ProcedureCheckCondition[label]
        else:
            return None


class ProcedureCheckAction(Enum):
    BREAK_TASK = "break"

    @staticmethod
    def from_str(label: Optional[str]) -> Optional[ProcedureCheckAction]:
        if label is None:
            return None

        if label in ProcedureCheckAction:
            return ProcedureCheckAction[label]
        else:
            return None


@dataclass
@rich.repr.auto
class ProcedureCheck(ProcedureStep):

    condition: ProcedureCheckCondition = field(
        default_factory=ProcedureCheckCondition.NOT_EXISTS
    )
    action: ProcedureCheckAction = field(
        default_factory=ProcedureCheckAction.BREAK_TASK
    )
    file: Optional[File] = None

    XML_TAG: ClassVar[str] = "check"
    example = """
    <check condition="not exists" action="break">
        <file key="file_key"/>
    </check>

    <check>
        <file key="file_key"/>
    </check>
    """

    @classmethod
    def from_xml(cls, xml: Optional[ET.Element]):
        if xml is None:
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


@rich.repr.auto
class ProcedurePrint(ProcedureStep):

    variables: List[str] = field(default_factory=lambda: [])
    XML_TAG: ClassVar[str] = "print"

    def __init__(self, variables: List[str]) -> None:
        self.variables = variables

    @classmethod
    def from_xml(cls, xml: Optional[ET.Element]):
        if xml is None:
            return None

        variables: List[str] = [
            var.text for var in xml.findall("./var") if var.text is not None
        ]

        return cls(variables=variables)


@rich.repr.auto
class ProcedureMultiPlot(ProcedureStep):

    name: str
    file_plot: str
    folder_sweep: List[str]
    config: Optional[SweepConfig]
    XML_TAG: ClassVar[str] = "multiplot"

    def __init__(
        self,
        name: str,
        file_plot: str,
        folder_sweep: List[str],
        config: Optional[SweepConfig] = None,
    ) -> None:

        self.name = name
        self.file_plot = file_plot
        self.folder_sweep = folder_sweep
        self.config = config

    @classmethod
    def from_xml(cls, xml: Optional[ET.Element]):
        if xml is None:
            return None

        name = xml.find(".").get("name", None)

        file_plot = xml.find("./file_plot")
        folder_sweep = [
            csv.text
            for csv in xml.findall("./folder_sweep/var")
            if csv.text is not None
        ]

        Econfig = xml.find("./config")

        sweep_config_xml: Optional[SweepConfig] = None

        if Econfig is not None:
            sweep_config_xml = SweepConfig.from_xml(ET.ElementTree(Econfig))

        if name is not None and file_plot is not None:
            return cls(
                name=name,
                file_plot=file_plot.text,
                folder_sweep=folder_sweep,
                config=sweep_config_xml,
            )
        else:
            return None


@rich.repr.auto
class Procedure:

    name: str
    steps: List[ProcedureStep]

    def __init__(
        self,
        name: str,
        steps: List[ProcedureStep],
    ) -> None:
        self.name = name
        self.steps = steps

    def print(self, procedure: ET.Element) -> str:
        from rich.syntax import Syntax

        ET.indent(procedure)
        console.print("\n")
        console.print(
            Syntax(ET.tostring(procedure, encoding="unicode"), "xml", theme="one-dark")
        )

    @classmethod
    def from_xml_file(cls, file_path: Path):
        if not file_path.exists() or not file_path.is_file():
            return None

        return cls.from_xml_string(file_path.read_text(encoding="utf-8"))

    @classmethod
    def from_xml_string(cls, data: str):
        tree = ET.ElementTree(ET.fromstring(data))
        procedure = tree.getroot()

        if procedure is None:
            return None

        name = procedure.get("name")
        step_nodes: List[ET.Element] = procedure.findall("./steps/*")

        steps: List[ProcedureStep] = []

        for idx, step in enumerate(step_nodes):
            proc_type = step.tag

            console.print(proc_type)
            procedure = ProcedureStep.proc_type_to_procedure(proc_type, step)
            if procedure is not None:
                steps.append(procedure)
            else:
                console.print(f"procedure idx {idx} is NULL")

        return cls(
            name,
            steps,
        )


@dataclass
class DataProcedure:
    procedure: Procedure
    root: Path
    data: Dict = field(default_factory=dict())
    cache_csv_data: CacheCsvData = field(default_factory=CacheCsvData())
    cache_file: CacheFile = field(default_factory=CacheFile())
    default_sweep_config: DefaultSweepConfig = field(
        default_factory=DefaultSweepConfig()
    )
