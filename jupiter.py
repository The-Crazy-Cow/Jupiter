# SPDX-License-Identifier: GPL-2.0-only

"""
@file jupiter.py
@brief Main entry point for Jupiter security tools framework.
@author Security Team
@version 1.0
@date 2026-08-19

@details
Jupiter is an offensive security tools framework.
"""

from shared import console
from net.tcpFlagScan import TcpFlagScan

if __name__ == "__main__":
    console.add_command(TcpFlagScan.register_cli())

    console.launch()
