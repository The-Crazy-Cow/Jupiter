#!/bin/bash

# SPDX-License-Identifier: GPL-2.0-only

##
# @file starter.sh
# @brief Simple script to replace Makefile for Jupiter framework.
# @usage
#   ./starter.sh         # Run jupiter.py
#   ./starter.sh clean   # Clean cache
##

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

case "${1:-run}" in
    clean)
        find "$ROOT" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
        rm -rf "$ROOT/.ruff_cache"
        echo "[✓] Cache cleaned"
        ;;
    *)
        python3 "$ROOT/jupiter.py" "$@"
        ;;
esac