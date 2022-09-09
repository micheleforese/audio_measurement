from __future__ import annotations
from ast import Str
from fileinput import filename

import pathlib
from pydoc import classname
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

        if text is not None and text == "":
            return cls(text)


@rich.repr.auto
class ProcedureSetLevel(ProcedureStep):
    file_key: str
    file_name: str
    config: SweepConfigXML

    def __init__(
        self,
        file_key: str,
        file_name: str,
        config: SweepConfigXML,
    ) -> None:
        self.file_key = file_key
        self.file_name = file_name
        self.config = config

    @classmethod
    def from_xml(cls, xml: ET.Element):
        file_key = xml.find("./file/key")
        file_name = xml.find("./file/name")

        config = xml.find("./config")

        if file_key is not None and file_name is not None and config is not None:
            return cls(
                file_key=file_key.text,
                file_name=file_name.text,
                config=SweepConfigXML.from_xml(ET.ElementTree(config)),
            )
        else:
            return None


@rich.repr.auto
class ProcedureSweep(ProcedureStep):

    name: str
    name_folder: str
    file_set_level_key: str
    file_set_level_name: str
    file_plot_name: str

    config: SweepConfigXML

    def __init__(
        self,
        name: str,
        name_folder: str,
        file_set_level_key: str,
        file_set_level_name: str,
        file_plot_name: str,
        config: SweepConfigXML,
    ) -> None:
        self.name = name
        self.name_folder = name_folder
        self.file_set_level_key = file_set_level_key
        self.file_set_level_name = file_set_level_name
        self.file_plot_name = file_plot_name
        self.config = config

    @classmethod
    def from_xml(cls, xml: Optional[ET.ElementTree]):
        if xml is None:
            return None

        name = xml.find("./").get("name", None)
        name_folder = xml.find("./name_folder")
        file_set_level_key = xml.find("./file_set_level/key")
        file_set_level_name = xml.find("./file_set_level/name")
        file_plot_name = xml.find("./file_plot")

        config = xml.find("./config")

        if (
            name is not None
            and name_folder is not None
            and file_set_level_key is not None
            and file_set_level_name is not None
            and file_plot_name is not None
            and config is not None
        ):
            return cls(
                name=name,
                name_folder=name_folder.text,
                file_set_level_key=file_set_level_key.text,
                file_set_level_name=file_set_level_name.text,
                file_plot_name=file_plot_name.text,
                config=SweepConfigXML.from_xml(ET.ElementTree(config)),
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

    name: str
    set_level: str

    file_calibration_key: str
    file_calibration_name: str
    file_set_level_key: str
    file_set_level_name: str

    def __init__(
        self,
        file_calibration_key: str,
        file_calibration_name: str,
        file_set_level_key: str,
        file_set_level_name: str,
    ) -> None:
        self.file_calibration_key = file_calibration_key
        self.file_calibration_name = file_calibration_name
        self.file_set_level_key = file_set_level_key
        self.file_set_level_name = file_set_level_name

    @classmethod
    def from_xml(cls, xml: Optional[ET.ElementTree]):
        if xml is None:
            return None

        file_calibration_key = xml.find("./file_calibration/key")
        file_calibration_name = xml.find("./file_calibration/name")
        file_set_level_key = xml.find("./file_set_level/key")
        file_set_level_name = xml.find("./file_set_level/name")

        if (
            file_calibration_key is not None
            and file_calibration_name is not None
            and file_set_level_key is not None
            and file_set_level_name is not None
        ):
            return cls(
                file_calibration_key=file_calibration_key.text,
                file_calibration_name=file_calibration_name.text,
                file_set_level_key=file_set_level_key.text,
                file_set_level_name=file_set_level_name.text,
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
    files_csv: List[str]
    config: Optional[SweepConfigXML]

    def __init__(
        self,
        name: str,
        file_plot: str,
        files_csv: List[str],
        config: Optional[SweepConfigXML] = None,
    ) -> None:

        self.name = name
        self.file_plot = file_plot
        self.files_csv = files_csv
        self.config = config

    @classmethod
    def from_xml(cls, xml: Optional[ET.ElementTree]):
        if xml is None:
            return None

        name = xml.find("./").get("name", None)

        file_plot = xml.find("./file_plot")
        files_csv = [
            csv.text for csv in xml.findall("./files_csv/var") if csv.text is not None
        ]

        config = xml.find("./config")

        if name is not None and file_plot is not None:
            return cls(
                name=name,
                file_plot=file_plot,
                files_csv=files_csv,
                config=SweepConfigXML.from_xml(ET.ElementTree(config)),
            )
        else:
            return None


@rich.repr.auto
class Procedure:

    name: str
    steps: List[
        Union[
            ProcedureInsertionGain,
            ProcedureMultiPlot,
            ProcedurePrint,
            ProcedureSerialNumber,
            ProcedureSetLevel,
            ProcedureStep,
            ProcedureSweep,
            ProcedureText,
        ]
    ]

    def __init__(
        self,
        name: str,
        steps: List[
            Union[
                ProcedureInsertionGain,
                ProcedureMultiPlot,
                ProcedurePrint,
                ProcedureSerialNumber,
                ProcedureSetLevel,
                ProcedureStep,
                ProcedureSweep,
                ProcedureText,
            ]
        ],
    ) -> None:
        self.name = name
        self.steps = steps

    @classmethod
    def from_dict(cls, dictionary: Optional[Dictionary]):

        if dictionary is not None:
            procedure = ET.Element("procedure")

            name = ET.SubElement(procedure, "name")
            steps = ET.SubElement(procedure, "steps")

            procedure_data = dictionary.get_property("procedure")
            procedure_data = Dictionary(procedure_data)

            if procedure_data is None:
                raise Exception("procedure_data is NULL")

            procedure_name = procedure_data.get_property("name", str)
            procedure_steps = procedure_data.get_property("steps", List[Dictionary])

            name.text = procedure_name

            steps: List[
                Union[
                    ProcedureInsertionGain,
                    ProcedureMultiPlot,
                    ProcedurePrint,
                    ProcedureSerialNumber,
                    ProcedureSetLevel,
                    ProcedureStep,
                    ProcedureSweep,
                    ProcedureText,
                ]
            ] = []

            if procedure_steps is None:
                raise Exception("procedure_steps is NULL")

            for idx, step in enumerate(procedure_steps):

                step = Dictionary(step)

                procedure_type: Optional[str] = step.get_property("type", str)
                step_dictionary: Optional[Dict] = step.get_property("step", Dict)

                if procedure_type is None:
                    raise Exception(f"procedure_type is NULL at idx: {idx}")

                if step_dictionary is None:
                    raise Exception(f"step_dictionary is NULL at idx: {idx}")

                step_dictionary = Dictionary(step_dictionary)

                procedure: Optional[
                    Union[
                        ProcedureInsertionGain,
                        ProcedureMultiPlot,
                        ProcedurePrint,
                        ProcedureSerialNumber,
                        ProcedureSetLevel,
                        ProcedureStep,
                        ProcedureSweep,
                        ProcedureText,
                    ]
                ] = None

                if procedure_type == "text":
                    procedure = ProcedureText.from_dict(step_dictionary)
                elif procedure_type == "set-level":
                    procedure = ProcedureSetLevel.from_dict(step_dictionary)
                elif procedure_type == "sweep":
                    procedure = ProcedureSweep.from_dict(step_dictionary)
                elif procedure_type == "serial-number":
                    procedure = ProcedureSerialNumber.from_dict(step_dictionary)
                elif procedure_type == "insertion-gain":
                    procedure = ProcedureInsertionGain.from_dict(step_dictionary)
                elif procedure_type == "print":
                    procedure = ProcedurePrint.from_dict(step_dictionary)
                elif procedure_type == "multiplot":
                    procedure = ProcedureMultiPlot.from_dict(step_dictionary)
                else:
                    procedure = ProcedureStep()

                if procedure is not None:
                    steps.append(procedure)
                else:
                    raise Exception

            return cls(procedure_name, steps)
        else:
            return None

    @classmethod
    def from_json5_file(cls, procedure_path: pathlib.Path):
        data: Optional[Dictionary] = Dictionary.from_json5_file(procedure_path)

        return Procedure.from_dict(data)

    @classmethod
    def from_json5_string(cls, data: str):
        data: Optional[Dictionary] = Dictionary.from_json5_string(data)

        return Procedure.from_dict(data)

    @classmethod
    def from_xml_file(cls, file_path: Path):
        if not file_path.exists() or not file_path.is_file():
            return None

        cls.from_xml_string(file_path.read_text(encoding="utf-8"))

    @classmethod
    def from_xml_string(cls, data: str):
        tree = ET.ElementTree(ET.fromstring(data))
        procedure = tree.getroot()

        console.print(procedure)
        if procedure is None:
            return None

        name = procedure.get("name")
        step_nodes: List[ET.Element] = procedure.findall("./steps/*")

        steps: List[
            Union[
                ProcedureInsertionGain,
                ProcedureMultiPlot,
                ProcedurePrint,
                ProcedureSerialNumber,
                ProcedureSetLevel,
                ProcedureStep,
                ProcedureSweep,
                ProcedureText,
            ]
        ] = []

        for idx, step in enumerate(step_nodes):
            console.print(f"{idx}: {step}")
            proc_type = step.tag

            procedure = Procedure.proc_type_to_procedure(proc_type, step)
            if procedure is not None:
                steps.append(procedure)

        return cls(
            name,
            steps,
        )

    @staticmethod
    def proc_type_to_procedure(proc_type: str, xml: ET.Element):
        procedure: Optional[
            Union[
                ProcedureText,
                ProcedureSetLevel,
                ProcedureSweep,
                ProcedureSerialNumber,
                ProcedureInsertionGain,
                ProcedurePrint,
                ProcedureMultiPlot,
                ProcedureStep,
            ]
        ] = None

        if proc_type == "text":
            procedure = ProcedureText.from_xml(xml)
        elif proc_type == "set-level":
            procedure = ProcedureSetLevel.from_xml(xml)
        elif proc_type == "sweep":
            procedure = ProcedureSweep.from_xml(xml)
        elif proc_type == "serial-number":
            procedure = ProcedureSerialNumber.from_xml(xml)
        elif proc_type == "insertion-gain":
            procedure = ProcedureInsertionGain.from_xml(xml)
        elif proc_type == "print":
            procedure = ProcedurePrint.from_xml(xml)
        elif proc_type == "multiplot":
            procedure = ProcedureMultiPlot.from_xml(xml)
        else:
            procedure = ProcedureStep()

        return procedure
