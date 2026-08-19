# SPDX-License-Identifier: GPL-2.0-only

"""
@file cliconfig.py
@brief CLI configuration dataclasses for Jupiter framework.
@author Security Team
@version 1.0
@date 2026-08-19

@details
Defines dataclasses for declaratively configuring CLI commands and options.
Used by CommandBuilder to automatically generate Click commands.

@see OptionConfig, CommandConfig
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class OptionConfig:
    """
    @class OptionConfig
    @brief Configuration for a single CLI command option.
    @details Defines a command-line option including name, type, help text, and behavior.
    """

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
    """
    @class CommandConfig
    @brief Configuration for a complete CLI command.
    @details Defines a command's name, help text, and all available options.
    """

    name: str
    help_text: str
    options: List[OptionConfig]
