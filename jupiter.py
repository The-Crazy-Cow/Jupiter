# SPDX-License-Identifier: GPL-2.0-only

from shared import console
from net.tcpFlagScan import TcpFlagScan

if __name__ == "__main__":
    console.add_command(TcpFlagScan.register_cli())

    console.launch()
