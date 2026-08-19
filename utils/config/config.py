# SPDX-License-Identifier: GPL-2.0-only

from utils.usage import Usage
from dataclasses import dataclass

# all Configuration class inherit of 'Config'


@dataclass(kw_only=True)
class Config:
    usage: Usage


@dataclass(kw_only=True)
class LoginCfg(Config):
    username: str
    password: str
