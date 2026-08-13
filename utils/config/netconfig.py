# SPDX-License-Identifier: GPL-2.0-only

from utils.config.config import Config
from dataclasses import dataclass
from typing import List
from typing import Callable,Any

@dataclass 
class NetCfg(Config):
    host   : str = "localhost"
    dst    : str = "localhost"
    timeout: int = 2
    verbose: int = 0 

@dataclass
class sniffCfg(NetCfg):
    count  : int = 25
    filter : str = 'f'
    iface  : str = 'eth0'
    prn    : Callable[[Any], None] 
    store  : bool = True

# you will notice that HoneyConfig not inehrit of network basic config class
# 'netConfig'obivisiouly it's done by inheritence NetConfig --> sniffCfg
@dataclass
class HoneyPotCfg(sniffCfg):
    ports   : tuple
    honeys  : tuple

@dataclass
class TcpFlagScanConfig(NetCfg):
    dports: List[int]
    sport : int = 33333 

@dataclass
class DnsScanConfig(NetCfg):
    qname  : str
    rd     : int = 1  # recursion desired
    dport  : int = 53