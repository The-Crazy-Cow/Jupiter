# SPDX-License-Identifier: GPL-2.0-only

from utils.cli import Console
from utils.config.cliconfig import *
from net.tcpFlagScan import TcpFlagScan

from shared import console

if __name__ == "__main__":
    console.add_command(TcpFlagScan.register_cli())

    console.launch()
