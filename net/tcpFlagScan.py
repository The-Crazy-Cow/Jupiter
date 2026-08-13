# SPDX-License-Identifier: GPL-2.0-only

import utils.cli as cli
from utils.cli import CommandBuilder, cliTool
from utils.config.cliconfig import CommandConfig, OptionConfig
from utils.config.netconfig import DnsScanCfg, TcpFlag, TcpFlagScanCfg
from shared import console

from scapy.all import IP, TCP, sr
import click
from typing import List

BANNER = r""" 
████████╗ ███████╗ ██████╗ █████╗  ███╗   ██╗ 
╚══██╔══╝ ██╔════╝ ██╔════╝ ██╔══██╗ ████╗  ██║ 
   ██║    ███████╗ ██║      ███████║ ██╔██╗ ██║ 
   ██║    ╚════██║ ██║      ██╔══██║ ██║╚██╗██║ 
   ██║    ███████║ ╚██████╗ ██║  ██║ ██║ ╚████║ 
   ╚═╝    ╚══════╝  ╚═════╝ ╚═╝  ╚═╝ ╚═╝  ╚═══╝ 

"""

TOOL_NAME = "tscan"
HELP = r"""
    Scan TCP ports using different TCP flag combinations
"""


class TcpFlagScan(cliTool):
    def __init__(self, tcp_cfg: TcpFlagScanCfg):
        self.tcp_cfg = tcp_cfg

    @property
    def tcp_cfg(self):
        return self._tcp_cfg

    @tcp_cfg.setter
    def tcp_cfg(self, tcp_cfg: TcpFlagScanCfg):
        if tcp_cfg is not None and not isinstance(tcp_cfg, TcpFlagScanCfg):
            raise TypeError(
                f"'tcp_cfg' must be an <'TcpFlagScanCfg'>, got {type(tcp_cfg)}"
            )

        self._tcp_cfg = tcp_cfg

    @staticmethod
    def print_banner():
        return console.print_banner(BANNER)

    @classmethod
    def usage(cls) -> CommandConfig:
        return CommandConfig(
            name=TOOL_NAME,
            help_text=(HELP),
            options=[
                OptionConfig(
                    name="destination",
                    short_name="d",
                    param_name="dst",
                    required=True,
                    help_text="Destination host or IP address.",
                ),
                OptionConfig(
                    name="ports",
                    short_name="p",
                    param_name="dports",
                    required=True,
                    multiple=True,
                    help_text="Destination TCP ports.",
                ),
                OptionConfig(
                    name="sport",
                    short_name="sp",
                    param_name="sport",
                    help_text="Source TCP port.",
                ),
                OptionConfig(
                    name="timeout",
                    short_name="t",
                    param_name="timeout",
                    help_text="Response timeout in seconds.",
                ),
                OptionConfig(
                    name="verbose",
                    short_name="v",
                    param_name="verbose",
                    is_flag=True,
                    help_text="Enable verbose output.",
                ),
                OptionConfig(
                    name="syn",
                    short_name="s",
                    param_name="scan",
                    is_flag=True,
                    value="syn",
                    help_text="Perform a SYN scan.",
                ),
                OptionConfig(
                    name="ack",
                    short_name="a",
                    param_name="scan",
                    is_flag=True,
                    value="ack",
                    help_text="Perform an ACK scan.",
                ),
                OptionConfig(
                    name="fin",
                    short_name="f",
                    param_name="scan",
                    is_flag=True,
                    value="fin",
                    help_text="Perform a FIN scan.",
                ),
                OptionConfig(
                    name="null",
                    short_name="n",
                    param_name="scan",
                    is_flag=True,
                    value="null",
                    help_text="Perform a NULL scan.",
                ),
                OptionConfig(
                    name="xmas",
                    short_name="x",
                    param_name="scan",
                    is_flag=True,
                    value="xmas",
                    help_text="Perform an Xmas scan.",
                ),
            ],
        )

    @classmethod
    def cli_behavior(
        cls,
        host: str,
        dst: str,
        timeout: int,
        verbose: int,
        dports: List[int],
        sport: int,
        sflags: str,
        rflags: str,
        scan: str,
    ):

        cfg = cls(
            TcpFlagScanCfg(
                host=host,
                dst=dst,
                timeout=timeout,
                verbose=verbose,
                dports=dports,
                sport=sport,
                sflags=sflags,
                rflags=rflags,
                scan=scan,
            )
        )

        return cfg.run()

    @classmethod
    def register_cli(cls) -> click.Command:
        builder = CommandBuilder(cls.usage(), cls.cli_behavior)
        return builder.build()

    def run(self):

        match self.tcp_cfg.scan:
            case "syn":
                return self.__syn_scan()

            case "ack":
                return self.__ack_scan()

            case "fin":
                return self.__fin_scan()

            case "null":
                return self.__null_scan()

            case "xmas":
                return self.__xmas_scan()

            case _:
                raise ValueError(f"unknown TCP scan: {self.tcp_cfg.scan}")

    def __tcp_flag_scan(self):
        cfg = self.tcp_cfg
        packet = IP(dst=cfg.dst) / TCP(
            sport=cfg.sport, dport=cfg.dports, flags=cfg.sflags
        )
        ans, _ = sr(packet, timeout=cfg.timeout, verbose=cfg.verbose)

        if ans:
            console.print_info(f"Open ports on destination [{cfg.host}]:")
            for s, r in ans:
                # Guard: ensure response contains TCP layer
                if TCP not in r or TCP not in s:
                    continue
                if s[TCP].dport == r[TCP].sport and r[TCP].flags == cfg.rflags:
                    console.print_info(s[TCP].dport)
                    return 0
        else:
            console.format_red("no answer")

        return 1

    def __syn_scan(self):
        self.tcp_cfg.sflags = TcpFlag.SYN
        self.tcp_cfg.rflags = TcpFlag.RST
        return self.__tcp_flag_scan()

    def __ack_scan(self):
        self.tcp_cfg.sflags = TcpFlag.ACK
        self.tcp_cfg.rflags = TcpFlag.RST
        return self.__tcp_flag_scan()

    def __fin_scan(self):
        self.tcp_cfg.sflags = TcpFlag.FIN
        self.tcp_cfg.rflags = TcpFlag.RST | TcpFlag.ACK
        return self.__tcp_flag_scan()

    def __null_scan(self):
        self.tcp_cfg.sflags = TcpFlag(0)
        self.tcp_cfg.rflags = TcpFlag.RST | TcpFlag.ACK
        return self.__tcp_flag_scan()

    def __xmas_scan(self):
        self.tcp_cfg.sflags = TcpFlag.FIN | TcpFlag.PSH | TcpFlag.URG
        self.tcp_cfg.rflags = TcpFlag.RST | TcpFlag.ACK
        return self.__tcp_flag_scan()
