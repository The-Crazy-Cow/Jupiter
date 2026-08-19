# SPDX-License-Identifier: GPL-2.0-only

# !! deprecated: This module is deprecated and will be removed in future versions.

"""
@file usage.py
@brief Command-line argument parsing utility for Jupiter framework.
@author Security Team
@version 1.0
@date 2026-08-20

@details
Provides a wrapper around argparse.ArgumentParser for consistent CLI argument
parsing across Jupiter tools. Handles help text, argument validation, and
graceful error handling.

@see Usage, argparse.ArgumentParser
"""

import argparse
import sys


class Usage:
    """
    @class Usage
    @brief Wrapper for argparse-based command-line argument parsing.
    @details Provides a cleaner interface to argparse with validation and error handling.

    @code
    usage = Usage("My Tool - Does something awesome")
    usage.parser.add_argument("--target", required=True, help="Target host")
    usage.parser.add_argument("--port", type=int, default=22)

    args = usage.parse(sys.argv[1:])
    if args:
        print(f"Target: {args.target}:{args.port}")
    @endcode
    """

    def __init__(self, description: str, add_help=True) -> None:
        """
        @brief Initialize the Usage parser.
        @param description Help text describing the tool/command
        @param add_help Whether to automatically add --help option (default: True)
        @throw ValueError if description is empty

        @details Creates an ArgumentParser with the given description.
        """
        if not description:
            raise ValueError("empty 'description'")

        self.__parser = argparse.ArgumentParser(
            description=description, add_help=add_help
        )

    @property
    def parser(self):
        """
        @brief Get the underlying ArgumentParser instance.
        @return argparse.ArgumentParser object
        @details Access the parser to add arguments:
                 usage.parser.add_argument(...)
        """
        return self.__parser

    @parser.setter
    def parser(self, parser: argparse.ArgumentParser):
        """
        @brief Set and validate the ArgumentParser instance.
        @param parser ArgumentParser object to set
        @throw TypeError if parser is not an ArgumentParser instance
        """
        if not isinstance(parser, argparse.ArgumentParser):
            raise TypeError(
                f"parser must be an ArgumentParser, got {type(parser)}"
            )

        self.__parser = parser

    def parse(self, argv=None):
        """
        @brief Parse command-line arguments.
        @param argv List of argument strings (default: sys.argv[1:])
        @return Namespace object with parsed arguments, or None if --help was invoked
        @details Parses arguments with unknown argument forwarding.
                 Returns None if --help flag is detected.

        @code
        args = usage.parse(["-t", "localhost", "-p", "22"])
        if args:
            print(f"Parsed: target={args.t}, port={args.p}")
        @endcode
        """
        if argv is None:
            argv = sys.argv[1:]

        args, _ = self.__parser.parse_known_args(argv)

        if getattr(args, "help", False):
            self.__parser.print_help()
            return None

        return self.__parser.parse_args(argv)
