from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Type, Union

import rich

from audio.console import console
from audio.model.file import CacheFile
from audio.plot import CacheCsvData
from audio.decoder.xml import DecoderXML
from audio.procedure.step import DefaultSweepConfig, ProcedureStep


@rich.repr.auto
class Procedure(DecoderXML):

    name: str
    steps: List[ProcedureStep]

    def __init__(
        self,
        name: str,
        steps: List[ProcedureStep] = [],
    ) -> None:
        self.name = name
        self.steps = steps

    def print(self) -> str:
        data = self.__dict__
        console.print(data)

    @classmethod
    def from_xml_file(cls, file: Path) -> Procedure:
        if not file.exists() or not file.is_file() or file.suffix != ".xml":
            return None

        return Procedure.from_xml_string(file.read_text(encoding="utf-8"))

    @classmethod
    def from_xml_string(cls, data: str) -> Procedure:
        tree = ET.ElementTree(ET.fromstring(data))
        procedure = tree.getroot()

        if procedure is None:
            return None

        return Procedure.from_xml_object(procedure)

    @classmethod
    def from_xml_object(cls, xml: ET.Element):
        if not Procedure.xml_is_valid(xml):
            return None

        procedure = xml
        name = procedure.get("name")
        step_nodes: List[ET.Element] = procedure.findall("./steps/*")

        steps: List[ProcedureStep] = []

        for idx, step in enumerate(step_nodes):
            proc_type = step.tag

            console.print(proc_type)
            procedure = ProcedureStep.proc_type_to_procedure(step)
            if procedure is not None:
                steps.append(procedure)
            else:
                console.print(f"procedure idx {idx} is NULL")

        return cls(name, steps)

    @staticmethod
    def xml_is_valid(xml: ET.Element):
        return xml.tag == "procedure"


@dataclass
class DataProcedure:
    name: str
    root: Path
    data: Dict = field(default_factory=lambda: dict())
    cache_csv_data: CacheCsvData = field(default_factory=lambda: CacheCsvData())
    cache_file: CacheFile = field(default_factory=lambda: CacheFile())
    default_sweep_config: DefaultSweepConfig = field(
        default_factory=lambda: DefaultSweepConfig()
    )
