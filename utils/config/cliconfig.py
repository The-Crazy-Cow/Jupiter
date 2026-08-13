# SPDX-License-Identifier: GPL-2.0-only

from dataclasses import dataclass,field
from typing import List

@dataclass
class OptionConfig:
    """command CConfiguration argument options"""
    name: str         
    is_flag: bool = True
    help_text: str = ""

@dataclass
class CommandConfig:
    name: str                                     
    help_text: str                               
    choices: List[str]                           
    options: List[OptionConfig] = field(default_factory=list)