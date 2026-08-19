# SPDX-License-Identifier: GPL-2.0-only

"""
@file shared.py
@brief Global shared variables and singleton instances.
@author Security Team
@version 1.0
@date 2026-08-19

@details
This module provides global instances that are shared across the Jupiter framework.
Most notably, it exports the singleton Console instance used for all CLI operations.

@code
    from shared import console
    console.print_info("Starting scan...")
@endcode
"""

# shared variables

from utils.cli import Console

console = Console()
