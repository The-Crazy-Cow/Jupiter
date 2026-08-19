# SPDX-License-Identifier: GPL-2.0-only

ROOT=$(CURDIR)
MAIN := main.py

all:
	python3 $(MAIN)

clean:
	find . -name "__pycache__" -type d -exec rm -rf {} +
	rm -rf .ruff_cache
