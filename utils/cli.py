# SPDX-License-Identifier: GPL-2.0-only

import click, shlex
from typing import Callable
from utils.config.cliconfig import *
from abc import abstractmethod, ABC

BANNER = r"""

     ██╗ ██╗   ██╗ ██████╗  ██╗ ████████╗ ███████╗ ██████╗  
     ██║ ██║   ██║ ██╔══██╗ ██║ ╚══██╔══╝ ██╔════╝ ██╔══██╗ 
     ██║ ██║   ██║ ██████╔╝ ██║    ██║    █████╗   ██████╔╝ 
██   ██║ ██║   ██║ ██╔═══╝  ██║    ██║    ██╔══╝   ██╔══██╗ 
╚█████╔╝ ╚██████╔╝ ██║      ██║    ██║    ███████╗ ██║  ██║ 
 ╚════╝   ╚═════╝  ╚═╝      ╚═╝    ╚═╝    ╚══════╝ ╚═╝  ╚═╝ 
"""

TOOL_NAME = "JUPITER"
HELP = """
  Security offensive tools framework for Linux
"""


class Console:
    """Manages the CLI IO operations, formatting, and command registration."""
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        title: str = TOOL_NAME,
        synopsis: str = HELP,
    ):
        if Console._initialized:
            return
        
        @click.group(
            name=title,
            help=f"{title}  -{synopsis}.",
            invoke_without_command=True,
        )
        @click.pass_context
        def cli(ctx):
            if ctx.invoked_subcommand is None:
                # TODO: uncomment this after implement the REPL
                self.print_banner(BANNER)
                click.secho(ctx.get_help(), bold=True)

        self._cli = cli
        Console._initialized = True

    def print_banner(self, banner):
        click.echo(click.style(banner, fg="green", bold=True))
        click.get_text_stream("stdout").flush()

    def print_error(self, string: str):
        """Prints a critical error message in bold red."""
        click.echo(click.style(f"{string}", fg="red", bold=True))
        click.get_text_stream("stderr").flush()

    def print_info(self, string: str):
        click.echo(click.style(f"[*] INFO: {string}", fg="cyan"))

    def format_green(self, string: str) -> str:
        """Returns a string formatted in bold green (e.g., for success statuses)."""
        return click.style(string, fg="green", bold=True)

    def format_red(self, string: str) -> str:
        return click.style(string, fg="red", bold=True)

    def add_command(self, cli_register: click.Command):
        """Builds a command from a configuration and registers it into the console."""

        self._cli.add_command(cli_register)

    # TODO: implement repl system
    def repl(self):
        while True:
            try:
                line = input(self.format_green("jupiter> ")).strip()

                if not line:
                    continue

                if line in ("exit", "quit"):
                    return

                if line == "help":
                    self._cli.main(
                        args=["--help"],
                        standalone_mode=False,
                    )
                    continue

                args = shlex.split(line)

                self._cli.main(
                    args=args,
                    standalone_mode=False,
                )

            except KeyboardInterrupt:
                print()

            except EOFError:
                print()
                return

            except Exception as e:
                self.print_error(e)

    def launch(self):
        self._cli()


class CommandBuilder:
    """Build a specific Click command."""

    def __init__(self, config: CommandConfig, behavior: Callable):
        self.config = config
        self.behavior = behavior

    def build(self) -> click.Command:

        cmd_callback = click.command(
            name=self.config.name, help=self.config.help_text
        )(self.behavior)

        for opt in self.config.options:
            option_type = click.Choice(opt.choices) if opt.choices else None

            cmd_callback = click.option(
                f"--{opt.name}",
                f"-{opt.short_name}",
                opt.param_name,
                is_flag=opt.is_flag,
                required=opt.required,
                multiple=opt.multiple,
                type=option_type,
                help=opt.help_text,
            )(cmd_callback)

        return cmd_callback


class cliTool(ABC):
    @staticmethod
    @abstractmethod
    def print_banner():
        pass

    @classmethod
    @abstractmethod
    def usage(cls) -> str:
        pass

    @classmethod
    @abstractmethod
    def cli_behavior(cls, **kwargs):
        pass

    @abstractmethod
    def run(self):
        pass

    @abstractmethod
    def runfg(self):
        pass

    @classmethod
    def register_cli(cls) -> click.Command:
        builder = CommandBuilder(cls.__usage(), cls.__cli_behavior)
        return builder.build()
