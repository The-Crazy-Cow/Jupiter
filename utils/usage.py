# SPDX-License-Identifier: GPL-2.0-only

import argparse
import sys

class Usage:

    def __init__(self, description: str, add_help=True) -> None:
        if not description:
            raise ValueError("empty 'description'")

        self.__parser = argparse.ArgumentParser(
            description=description,
            add_help=add_help
        )

    @property
    def parser(self):
        return self.__parser

    @parser.setter
    def parser(self, parser: argparse.ArgumentParser):
        if not isinstance(parser, argparse.ArgumentParser):
            raise TypeError(
                f"parser must be an ArgumentParser, got {type(parser)}"
            )

        self.__parser = parser

    def parse(self, argv=None):
        if argv is None:
            argv = sys.argv[1:]

        args, _ = self.__parser.parse_known_args(argv)

        if getattr(args, "help", False):
            self.__parser.print_help()
            return None

        return self.__parser.parse_args(argv)