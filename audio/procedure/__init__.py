from __future__ import annotations

import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Type, Union

import rich

from audio.config.sweep import SweepConfigXML
from audio.console import console
from audio.model.file import File
from audio.type import Dictionary


class ProcedureStep(ABC):
    @property
    @abstractmethod
    def xml_tag(self):
        return ""


@rich.repr.auto
class ProcedureText(ProcedureStep):
    text: str

    @property
    def xml_tag(self):
        return "text"

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

    @property
    def xml_tag(self):
        return "ask"

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

    @property
    def xml_tag(self):
        return "file"

    @classmethod
    def from_xml(cls, xml: ET.Element):
        Ekey = xml.find("./key")
        Epath = xml.find("./path")

        if Ekey is not None and Epath is not None:
            key = Ekey.text.strip()
            path = Epath.text.strip()

        return cls(key=key, path=path)


@rich.repr.auto
class ProcedureDefault(ProcedureStep):
    sweep_file_set_level: Optional[File]
    sweep_file_set_level_key: Optional[str]
    sweep_file_set_level_name: Optional[str]

    sweep_file_offset: Optional[File]
    sweep_file_offset_key: Optional[str]
    sweep_file_offset_name: Optional[str]

    sweep_file_insertion_gain: Optional[File]
    sweep_file_insertion_gain_key: Optional[str]
    sweep_file_insertion_gain_name: Optional[str]

    sweep_config: Optional[SweepConfigXML]

    @property
    def xml_tag(self):
        return "default"

    def __init__(
        self,
        sweep_file_set_level: Optional[File] = None,
        sweep_file_set_level_key: Optional[str] = None,
        sweep_file_set_level_name: Optional[str] = None,
        sweep_file_offset: Optional[File] = None,
        sweep_file_offset_key: Optional[str] = None,
        sweep_file_offset_name: Optional[str] = None,
        sweep_file_insertion_gain: Optional[File] = None,
        sweep_file_insertion_gain_key: Optional[str] = None,
        sweep_file_insertion_gain_name: Optional[str] = None,
        sweep_config: Optional[SweepConfigXML] = None,
    ) -> None:
        self.sweep_file_set_level_key = sweep_file_set_level_key
        self.sweep_file_set_level_name = sweep_file_set_level_name
        self.sweep_file_offset_key = sweep_file_offset_key
        self.sweep_file_offset_name = sweep_file_offset_name
        self.sweep_file_insertion_gain_key = sweep_file_insertion_gain_key
        self.sweep_file_insertion_gain_name = sweep_file_insertion_gain_name
        self.sweep_config = sweep_config

    @classmethod
    def from_xml(cls, xml: ET.Element):

        if xml is None:
            return None

        sweep_file_set_level_key: Optional[str] = None
        sweep_file_set_level_name: Optional[str] = None
        sweep_file_offset_key: Optional[str] = None
        sweep_file_offset_name: Optional[str] = None
        sweep_file_insertion_gain_key: Optional[str] = None
        sweep_file_insertion_gain_name: Optional[str] = None
        sweep_config: Optional[SweepConfigXML] = None

        Esweep = xml.find("./sweep")
        if Esweep is not None:
            Esweep_config = Esweep.find("./config")
            if Esweep_config is not None:
                sweep_config = SweepConfigXML.from_xml(ET.ElementTree(Esweep_config))

            Efile_set_level = Esweep.find("./file_set_level")

            if Efile_set_level is not None:
                Efile_set_level_key = Esweep.find("./file_set_level/key")
                Efile_set_level_name = Esweep.find("./file_set_level/name")

                if Efile_set_level_key is not None and Efile_set_level_name is not None:
                    sweep_file_set_level_key = Efile_set_level_key.text
                    sweep_file_set_level_name = Efile_set_level_name.text

                    File(key=sweep_file_set_level_key, path=sweep_file_set_level_name)

            Efile_offset = Esweep.find("./file_offset")
            if Efile_offset is not None:
                Efile_offset_key = Esweep.find("./file_offset/key")
                Efile_offset_name = Esweep.find("./file_offset/name")

                if Efile_offset_key is not None:
                    sweep_file_offset_key = Efile_offset_key.text
                if Efile_offset_name is not None:
                    sweep_file_offset_name = Efile_offset_name.text

            Efile_insertion_gain = Esweep.find("./file_insertion_gain")
            if Efile_insertion_gain is not None:
                Efile_insertion_gain_key = Esweep.find("./file_insertion_gain/key")
                Efile_insertion_gain_name = Esweep.find("./file_insertion_gain/name")

                if Efile_insertion_gain_key is not None:
                    sweep_file_insertion_gain_key = Efile_insertion_gain_key.text
                if Efile_insertion_gain_name is not None:
                    sweep_file_insertion_gain_name = Efile_insertion_gain_name.text

        return cls(
            sweep_file_set_level_key=sweep_file_set_level_key,
            sweep_file_set_level_name=sweep_file_set_level_name,
            sweep_file_offset_key=sweep_file_offset_key,
            sweep_file_offset_name=sweep_file_offset_name,
            sweep_file_insertion_gain_key=sweep_file_insertion_gain_key,
            sweep_file_insertion_gain_name=sweep_file_insertion_gain_name,
            sweep_config=SweepConfigXML.from_xml(ET.ElementTree(sweep_config)),
        )


@dataclass
@rich.repr.auto
class ProcedureSetLevel(ProcedureStep):
    dBu: Optional[float]
    file_set_level_key: Optional[str]
    file_set_level_name: Optional[str]
    file_plot_key: Optional[str]
    file_plot_name: Optional[str]
    config: Optional[SweepConfigXML]
    override: bool = False

    @property
    def xml_tag(self):
        return "set_level"

    @classmethod
    def from_xml(cls, xml: ET.Element):
        dBu: Optional[float] = None
        file_set_level_key: Optional[str] = None
        file_set_level_name: Optional[str] = None
        file_plot_key: Optional[str] = None
        file_plot_name: Optional[str] = None
        override: bool = False
        sweep_config_xml: Optional[SweepConfigXML] = None

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
            sweep_config_xml = SweepConfigXML.from_xml(ET.ElementTree(config))

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

    name_folder: str
    file_set_level_key: Optional[str] = None
    file_set_level_path: Optional[str] = None
    file_offset_key: Optional[str] = None
    file_offset_path: Optional[str] = None
    file_insertion_gain_key: Optional[str] = None
    file_insertion_gain_path: Optional[str] = None
    config: Optional[SweepConfigXML] = None
    override: bool = False

    @property
    def xml_tag(self):
        return "sweep"

    @classmethod
    def from_xml(cls, xml: Optional[ET.ElementTree]):
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

        config: SweepConfigXML

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

        Efile_insertion_gain = xml.find("./file_set_level_plot")
        if Efile_insertion_gain is not None:
            file_insertion_gain_key = Efile_insertion_gain.get("key")
            file_insertion_gain_path = Efile_insertion_gain.get("path")

            if not (
                file_insertion_gain_key is not None
                or file_insertion_gain_path is not None
            ):
                return None

        Econfig = xml.find("./config")
        config = SweepConfigXML.from_xml(ET.ElementTree(Econfig))

        override_elem = xml.getroot().get("override", None)
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


@rich.repr.auto
class ProcedureSerialNumber(ProcedureStep):

    text: str

    @property
    def xml_tag(self):
        return "serial_number"

    def __init__(self, text: str) -> None:
        self.text = text

    @classmethod
    def from_xml(cls, xml: ET.ElementTree):
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

    @property
    def xml_tag(self):
        return "insertion_gain"

    @classmethod
    def from_xml(cls, xml: Optional[ET.ElementTree]):
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


@rich.repr.auto
class ProcedurePrint(ProcedureStep):

    variables: List[str] = []

    @property
    def xml_tag(self):
        return "print"

    def __init__(self, variables: List[str]) -> None:
        self.variables = variables

    @classmethod
    def from_xml(cls, xml: Optional[ET.ElementTree]):
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
    config: Optional[SweepConfigXML]

    @property
    def xml_tag(self):
        return "multiplot"

    def __init__(
        self,
        name: str,
        file_plot: str,
        folder_sweep: List[str],
        config: Optional[SweepConfigXML] = None,
    ) -> None:

        self.name = name
        self.file_plot = file_plot
        self.folder_sweep = folder_sweep
        self.config = config

    @classmethod
    def from_xml(cls, xml: Optional[ET.ElementTree]):
        if xml is None:
            return None

        name = xml.find(".").get("name", None)

        file_plot = xml.find("./file_plot")
        folder_sweep = [
            csv.text
            for csv in xml.findall("./folder_sweep/var")
            if csv.text is not None
        ]

        config = xml.find("./config")

        sweep_config_xml: SweepConfigXML

        if config is not None:
            sweep_config_xml = SweepConfigXML.from_xml(ET.ElementTree(config))
        else:
            sweep_config_xml = SweepConfigXML()

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

            procedure = Procedure.proc_type_to_procedure(proc_type, step)
            if procedure is not None:
                steps.append(procedure)
            else:
                console.print(f"procedure idx {idx} is NULL")

        return cls(
            name,
            steps,
        )

    @staticmethod
    def proc_type_to_procedure(proc_type: str, xml: ET.Element):
        procedure: Optional[ProcedureStep] = None

        procedure_list_type: List[Type] = [
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
        ]

        for proc_type_class in procedure_list_type:
            if proc_type == proc_type_class.xml_tag:
                procedure = proc_type_class.from_xml(xml)
                break

        return procedure
