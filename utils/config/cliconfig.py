# SPDX-License-Identifier: GPL-2.0-only

from dataclasses import dataclass,field
from typing import List

@dataclass
class OptionConfig:
    """command Configuration argument options"""
    name: str         
    is_flag: bool = True
    help_text: str = ""
    options: List[str] = field(default_factory=list)

@dataclass
class CommandConfig:
    name: str                                     
    help_text: str                               
    choices: List[str]                           
