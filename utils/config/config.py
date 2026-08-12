# SPDX-License-Identifier: GPL-2.0-only

from utils.usage import Usage
from dataclasses import dataclass

@dataclass
class Config:
    usage    :Usage