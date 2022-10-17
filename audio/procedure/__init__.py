from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Union

import rich

from audio.config.sweep import SweepConfigXML
from audio.console import console
from audio.type import Dictionary


class ProcedureStep:
    pass


@rich.repr.auto
class ProcedureText(ProcedureStep):
    text: str

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


@rich.repr.auto
class ProcedureSetLevel(ProcedureStep):
    dBu: Optional[float]
    file_set_level_key: str
    file_set_level_name: str
    file_plot_key: str
    file_plot_name: str
    config: SweepConfigXML
    override: bool

    def __init__(
        self,
        dBu: Optional[float],
        file_set_level_key: str,
        file_set_level_name: str,
        file_plot_key: str,
        file_plot_name: str,
        config: SweepConfigXML,
        override: bool = False,
    ) -> None:
        self.dBu = dBu
        self.file_set_level_key = file_set_level_key
        self.file_set_level_name = file_set_level_name
        self.file_plot_key = file_plot_key
        self.file_plot_name = file_plot_name
        self.config = config
        self.override = override

    @classmethod
    def from_xml(cls, xml: ET.Element):
        EdBu = xml.find("./dBu")
        file_set_level_key = xml.find("./file_set_level/key")
        file_set_level_name = xml.find("./file_set_level/name")
        file_plot_key = xml.find("./file_set_level_plot/key")
        file_plot_name = xml.find("./file_set_level_plot/name")

        override_elem = xml.get("override", None)
        override = override_elem is not None

        config = xml.find("./config")
        sweep_config_xml = SweepConfigXML.from_xml(ET.ElementTree(config))

        dBu: Optional[float] = None

        if EdBu is not None:
            dBu = float(EdBu.text)

        if (
            file_set_level_key is not None
            and file_set_level_name is not None
            and file_plot_key is not None
            and file_plot_name is not None
            and sweep_config_xml is not None
        ):
            return cls(
                dBu=dBu,
                file_set_level_key=file_set_level_key.text,
                file_set_level_name=file_set_level_name.text,
                file_plot_key=file_plot_key.text,
                file_plot_name=file_plot_name.text,
                config=sweep_config_xml,
                override=override,
            )
        else:
            return None


@rich.repr.auto
class ProcedureSweep(ProcedureStep):

    name_folder: str
    file_set_level_key: str
    file_set_level_name: str
    file_offset_key: str
    file_offset_name: str
    file_insertion_gain_key: str
    file_insertion_gain_name: str
    override: bool

    config: SweepConfigXML

    def __init__(
        self,
        name_folder: str,
        file_set_level_key: str,
        file_set_level_name: str,
        file_offset_key: str,
        file_offset_name: str,
        file_insertion_gain_key: str,
        file_insertion_gain_name: str,
        # file_plot_name: str,
        config: SweepConfigXML,
        override: bool = False,
    ) -> None:
        self.name_folder = name_folder
        self.file_set_level_key = file_set_level_key
        self.file_set_level_name = file_set_level_name
        self.file_offset_key = file_offset_key
        self.file_offset_name = file_offset_name
        self.file_insertion_gain_key = file_insertion_gain_key
        self.file_insertion_gain_name = file_insertion_gain_name
        # self.file_plot_name = file_plot_name
        self.config = config
        self.override = override

    @classmethod
    def from_xml(cls, xml: Optional[ET.ElementTree]):
        if xml is None:
            return None

        name_folder = xml.find("./name_folder")
        file_set_level_key = xml.find("./file_set_level/key")
        file_set_level_name = xml.find("./file_set_level/name")
        file_offset_key = xml.find("./file_offset/key")
        file_offset_name = xml.find("./file_offset/name")
        file_insertion_gain_key = xml.find("./file_insertion_gain/key")
        file_insertion_gain_name = xml.find("./file_insertion_gain/name")

        config = xml.find("./config")

        override_elem = xml.get("override", None)
        override = override_elem is not None

        if (
            name_folder is not None
            and file_set_level_key is not None
            and file_set_level_name is not None
            and file_offset_key is not None
            and file_offset_name is not None
            and file_insertion_gain_key is not None
            and file_insertion_gain_name is not None
            # and file_plot_name is not None
            and config is not None
        ):
            return cls(
                name_folder=name_folder.text,
                file_set_level_key=file_set_level_key.text,
                file_set_level_name=file_set_level_name.text,
                file_offset_key=file_offset_key.text,
                file_offset_name=file_offset_name.text,
                file_insertion_gain_key=file_insertion_gain_key.text,
                file_insertion_gain_name=file_insertion_gain_name.text,
                # file_plot_name=file_plot_name.text,
                config=SweepConfigXML.from_xml(ET.ElementTree(config)),
                override=override,
            )
        else:
            return None


@rich.repr.auto
class ProcedureSerialNumber(ProcedureStep):

    text: str

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


@rich.repr.auto
class ProcedureInsertionGain(ProcedureStep):

    file_calibration_key: str
    file_calibration_name: str

    file_set_level_key: str
    file_set_level_name: str

    file_gain_key: str
    file_gain_name: str

    def __init__(
        self,
        file_calibration_key: str,
        file_calibration_name: str,
        file_set_level_key: str,
        file_set_level_name: str,
        file_gain_key: str,
        file_gain_name: str,
    ) -> None:
        self.file_calibration_key = file_calibration_key
        self.file_calibration_name = file_calibration_name
        self.file_set_level_key = file_set_level_key
        self.file_set_level_name = file_set_level_name
        self.file_gain_key = file_gain_key
        self.file_gain_name = file_gain_name

    @classmethod
    def from_xml(cls, xml: Optional[ET.ElementTree]):
        if xml is None:
            return None

        file_calibration_key = xml.find("./file_calibration/key")
        file_calibration_name = xml.find("./file_calibration/name")
        file_set_level_key = xml.find("./file_set_level/key")
        file_set_level_name = xml.find("./file_set_level/name")
        file_gain_key = xml.find("./file_gain/key")
        file_gain_name = xml.find("./file_gain/name")
        if (
            file_calibration_key is not None
            and file_calibration_name is not None
            and file_set_level_key is not None
            and file_set_level_name is not None
            and file_gain_key is not None
            and file_gain_name is not None
        ):
            return cls(
                file_calibration_key=file_calibration_key.text,
                file_calibration_name=file_calibration_name.text,
                file_set_level_key=file_set_level_key.text,
                file_set_level_name=file_set_level_name.text,
                file_gain_key=file_gain_key.text,
                file_gain_name=file_gain_name.text,
            )
        else:
            return None


@rich.repr.auto
class ProcedurePrint(ProcedureStep):

    variables: List[str] = []

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
        console.print(name)

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

    @classmethod
    def from_xml_file(cls, file_path: Path):
        if not file_path.exists() or not file_path.is_file():
            return None

        return cls.from_xml_string(file_path.read_text(encoding="utf-8"))

    @classmethod
    def from_xml_string(cls, data: str):
        tree = ET.ElementTree(ET.fromstring(data))
        procedure = tree.getroot()

        # DEBUG PRINT
        from rich.syntax import Syntax

        ET.indent(procedure)
        console.print("\n")
        console.print(
            Syntax(ET.tostring(procedure, encoding="unicode"), "xml", theme="one-dark")
        )

        if procedure is None:
            return None

        name = procedure.get("name")
        step_nodes: List[ET.Element] = procedure.findall("./steps/*")

        steps: List[ProcedureStep] = []

        for idx, step in enumerate(step_nodes):
            proc_type = step.tag
            console.print(f"Procedure idx: {idx} with tag {proc_type}")

            procedure = Procedure.proc_type_to_procedure(proc_type, step)
            if procedure is not None:
                steps.append(procedure)
            else:
                console.print(f"procedure idx {idx} is NULL")

        for idx, step in enumerate(steps):
            console.print(f"{idx}: {step}")

        return cls(
            name,
            steps,
        )

    @staticmethod
    def proc_type_to_procedure(proc_type: str, xml: ET.Element):
        procedure: Optional[ProcedureStep] = None

        if proc_type == "text":
            procedure = ProcedureText.from_xml(xml)
        elif proc_type == "set_level":
            procedure = ProcedureSetLevel.from_xml(xml)
        elif proc_type == "sweep":
            procedure = ProcedureSweep.from_xml(xml)
        elif proc_type == "serial_number":
            procedure = ProcedureSerialNumber.from_xml(xml)
        elif proc_type == "insertion_gain":
            procedure = ProcedureInsertionGain.from_xml(xml)
        elif proc_type == "print":
            procedure = ProcedurePrint.from_xml(xml)
        elif proc_type == "multiplot":
            procedure = ProcedureMultiPlot.from_xml(xml)
        else:
            procedure = ProcedureStep()

        return procedure
