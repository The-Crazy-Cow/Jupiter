# SPDX-License-Identifier: GPL-2.0-only

from dataclasses import dataclass, field
from typing import List


@dataclass
class OptionConfig:
    """Command configuration argument option."""

    name: str
    short_name: str | None = None
    param_name: str | None = None
    is_flag: bool = False
    required: bool = False
    multiple: bool = False
    value: str = ""
    help_text: str = ""
    choices: List[str] = field(default_factory=list)


@dataclass
class CommandConfig:
    name: str
    help_text: str
    options: List[OptionConfig]
