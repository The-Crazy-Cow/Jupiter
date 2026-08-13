# SPDX-License-Identifier: GPL-2.0-only

import utils.io as io
import argparse
from utils.config.netconfig import TcpFlagScanCfg,DnsScanCfg,TcpFlag
from utils.usage import Usage
from scapy.all import IP,TCP,sr

def parse_tcp_scan_args(argv=None) -> TcpFlagScanCfg:
    usg = Usage(
        "Scan TCP ports using different TCP flag combinations."
    )

    parser = usg.parser

    parser.add_argument(
        "-d", "--destination",
        dest="dst",
        required=True,
        help="destination host or IP address"
    )

    parser.add_argument(
        "-p", "--ports",
        dest="dports",
        required=True,
        nargs="+",
        type=int,
        help="destination TCP ports"
    )

    parser.add_argument(
        "--sport",
        type=int,
        default=argparse.SUPPRESS,
        help="source TCP port"
    )

    parser.add_argument(
        "-t", "--timeout",
        type=int,
        default=argparse.SUPPRESS,
        help="response timeout in seconds"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_const",
        const=1,
        default=argparse.SUPPRESS,
        help="enable verbose output"
    )

    scan = parser.add_mutually_exclusive_group(required=True)

    scan.add_argument(
        "--syn",
        dest="scan",
        action="store_const",
        const="syn",
        help="perform a SYN scan"
    )

    scan.add_argument(
        "--ack",
        dest="scan",
        action="store_const",
        const="ack",
        help="perform an ACK scan"
    )

    scan.add_argument(
        "--fin",
        dest="scan",
        action="store_const",
        const="fin",
        help="perform a FIN scan"
    )

    scan.add_argument(
        "--null",
        dest="scan",
        action="store_const",
        const="null",
        help="perform a NULL scan"
    )

    scan.add_argument(
        "--xmas",
        dest="scan",
        action="store_const",
        const="xmas",
        help="perform an Xmas scan"
    )

    args = usg.parse(argv)

    return TcpFlagScanCfg(**vars(args))

def parse_dns_scan_args(argv=None) -> DnsScanCfg:
    usg = Usage(
        "Check for a DNS service by sending a DNS query."
    )

    parser = usg.parser

    parser.add_argument(
        "-d", "--destination",
        dest="dst",
        required=True,
        help="DNS server address"
    )

    parser.add_argument(
        "-q", "--query",
        dest="qname",
        required=True,
        help="DNS name to query"
    )

    parser.add_argument(
        "-p", "--port",
        dest="dport",
        type=int,
        default=argparse.SUPPRESS,
        help="DNS server port"
    )

    parser.add_argument(
        "-t", "--timeout",
        type=int,
        default=argparse.SUPPRESS,
        help="response timeout in seconds"
    )

    parser.add_argument(
        "--no-recursion",
        dest="rd",
        action="store_false",
        default=argparse.SUPPRESS,
        help="disable recursion desired"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_const",
        const=1,
        default=argparse.SUPPRESS,
        help="enable verbose output"
    )

    args = usg.parse(argv)

    return DnsScanCfg(**vars(args))


class NetScan:
    def __init__(self,tcp_cfg:TcpFlagScanCfg|None=None,dns_cfg:DnsScanCfg|None=None):
        if tcp_cfg is None and dns_cfg is None:
                raise ValueError(
                    "at least one of 'tcp_cfg' or 'dns_cfg' must be provided"
                )
        self.tcp_cfg = tcp_cfg
        self.dns_cfg = dns_cfg

    @property
    def tcp_cfg(self):
        return self._tcp_cfg

    @tcp_cfg.setter
    def tcp_cfg(self,tcp_cfg:TcpFlagScanCfg):
        if tcp_cfg is not None and not isinstance (tcp_cfg,TcpFlagScanCfg):
            raise TypeError(
                    f"'tcp_cfg' must be an <'TcpFlagScanCfg'>, got {type(tcp_cfg)}"
                )
        self._tcp_cfg  = tcp_cfg

    @property
    def dns_cfg(self):
        return self._dns_cfg

    @dns_cfg.setter
    def dns_cfg(self,dns_cfg:DnsScanCfg):
        if dns_cfg is not None and not isinstance (dns_cfg,DnsScanCfg):
            raise TypeError(
                    f"'dns_cfg' must be a <'DnsScanCfg'>, got {type(dns_cfg)}"
                )
        self._dns_cfg  = dns_cfg

    def tcp_scan(self):
        if self.tcp_cfg is None:
                raise RuntimeError("TCP scan configuration is not set")
        
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
                raise ValueError(
                    f"unknown TCP scan: {self.tcp_cfg.scan}"
                )

    def __tcp_flag_scan(self):
        cfg = self.tcp_cfg
        packet = IP(dst=cfg.dst)/TCP(sport=cfg.sport,
                                        dport=cfg.dports,
                                        flags=cfg.sflags
                                    )
        ans,_ = sr(packet,
                   timeout=cfg.timeout,
                   verbose=cfg.verbose
                   )

        if ans:
            io.print_info(f"Open ports on destination [{cfg.host}]:")
            for (s,r) in ans:
                if s[TCP].dport == r[TCP].sport and r[TCP].flags==cfg.rflags:
                    io.print_info(s[TCP].dport)
        else: 
            io.print_info("no answer")

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
        self.tcp_cfg.sflags = (
            TcpFlag.FIN |
            TcpFlag.PSH |
            TcpFlag.URG
        )
        self.tcp_cfg.rflags = TcpFlag.RST | TcpFlag.ACK
        return self.__tcp_flag_scan()

    def scan(self):
        results = []

        if self.tcp_cfg is not None:
            results.append(self.tcp_scan())

        if self.dns_cfg is not None:
            results.append(self.dns_scan())

        return results

    def dns_scan(self)->int:
        cfg = self.dns_cfg
        packet =  IP(dst=cfg.dst)/\
                UDP(dport=cfg.dport)/\
                DNS(rd=cfg.rd,qd=DNSQR(qname=cfg.qname))

        ans,_ = sr(packet,
                    timeout=cfg.timeout,
                    verbose=cfg.verbose)

        if ans and ans[UDP]:
            io.print_info(f"DNS Service found at {cfg.host} ")
            return 0
        
        return 1