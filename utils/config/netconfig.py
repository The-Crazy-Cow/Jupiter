# SPDX-License-Identifier: GPL-2.0-only

"""
@file netconfig.py
@brief Network configuration dataclasses for Jupiter tools.
@author Security Team
@version 1.0
@date 2026-08-19

@details
Defines configuration dataclasses for network-based tools including:
- TCP flag scanning
- DNS scanning
- Honeypot monitoring
- SSH operations

@see NetCfg, TcpFlagScanCfg, DnsScanCfg, HoneyPotCfg
"""

from utils.config.config import Config, LoginCfg
from dataclasses import dataclass
from typing import List
from typing import Callable, Any
from enum import IntFlag


class TcpFlag(IntFlag):
    """
    @enum TcpFlag
    @brief TCP packet flags.
    @details Defines standard TCP header flags as bit values.
    """

    FIN = 0x01
    SYN = 0x02
    RST = 0x04
    PSH = 0x08
    ACK = 0x10
    URG = 0x20
    ECE = 0x40
    CWR = 0x80


@dataclass(kw_only=True)
class NetCfg(Config):
    """
    @class NetCfg
    @brief Base network configuration.
    @details Contains common parameters for all network operations.
    """

    host: str = "localhost"
    dst: str = "localhost"
    timeout: int = 2
    verbose: int = 0


@dataclass(kw_only=True)
class sniffCfg(NetCfg):
    """
    @class sniffCfg
    @brief Configuration for packet sniffing.
    @details Extends NetCfg with packet capture parameters.
    """

    prn: Callable[[Any], None]
    store: bool = True
    count: int = 25
    filter: str = "f"
    iface: str = "eth0"


# Inherits from sniffCfg through NetCfg
@dataclass(kw_only=True)
class HoneyPotCfg(sniffCfg):
    """
    @class HoneyPotCfg
    @brief Configuration for honeypot monitoring.
    @details Inherits from sniffCfg to monitor specific ports and services.
    """

    ports: tuple
    honeys: tuple


@dataclass(kw_only=True)
class TcpFlagScanCfg(NetCfg):
    """
    @class TcpFlagScanCfg
    @brief Configuration for TCP flag scanning.
    @details Defines parameters for advanced TCP flag-based port scanning.
    """

    dports: List[int]
    sport: int = 33333
    sflags: str
    rflags: str
    scan: str


@dataclass(kw_only=True)
class DnsScanCfg(NetCfg):
    """
    @class DnsScanCfg
    @brief Configuration for DNS scanning/enumeration.
    @details Parameters for DNS-based reconnaissance.
    """

    qname: str
    rd: int = 1  # recursion desired
    dport: int = 53


@dataclass(kw_only=True)
class SshCfg(NetCfg):
    login: LoginCfg
    sshport: int = 22
    file: str = None
