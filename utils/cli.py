# SPDX-License-Identifier: GPL-2.0-only

"""
@file cli.py
@brief CLI framework and console management for Jupiter.
@author Security Team
@version 1.0
@date 2026-08-19

@details
Provides the Console singleton class for managing CLI operations, command registration,
and terminal formatting. Uses Click framework for command-line interface.

@see Console, CommandBuilder, cliTool
"""

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
    """
    @class Console
    @brief Singleton CLI console manager for Jupiter framework.
    @details Manages CLI IO operations, formatting, and command registration.
    Implements the Singleton pattern to ensure a single CLI instance globally.

    @code
    from shared import console
    console.print_info("Scanning target...")
    @endcode
    """

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
        """
        @brief Initialize the Console singleton.
        @param title Title of the CLI application (default: TOOL_NAME)
        @param synopsis Help text synopsis (default: HELP)
        @details Initializes the Click CLI group and banner.
        Only initializes once due to singleton pattern.
        """
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
        """
        @brief Print a banner in green to terminal.
        @param banner Banner text to display
        @details Prints the banner with green color and bold formatting.
        """
        click.echo(click.style(banner, fg="green", bold=True))
        click.get_text_stream("stdout").flush()

    def print_error(self, string: str):
        """
        @brief Print error message in red.
        @param string Error message text
        @details Prints a critical error message in bold red to stderr.
        """
        click.echo(click.style(f"{string}", fg="red", bold=True))
        click.get_text_stream("stderr").flush()

    def print_info(self, string: str):
        """
        @brief Print informational message in cyan.
        @param string Info message text
        @details Prints an informational message with [*] prefix in cyan color.
        """
        click.echo(click.style(f"[*] INFO: {string}", fg="cyan"))

    def format_green(self, string: str) -> str:
        """
        @brief Format string in bold green.
        @param string Text to format
        @return Formatted string
        @details Returns a string formatted in bold green (e.g., for success statuses).
        """
        return click.style(string, fg="green", bold=True)

    def format_red(self, string: str) -> str:
        """
        @brief Format string in bold red.
        @param string Text to format
        @return Formatted string
        @details Returns a string formatted in bold red (e.g., for error statuses).
        """
        return click.style(string, fg="red", bold=True)

    def add_command(self, cli_register: click.Command):
        """
        @brief Register a command to the CLI.
        @param cli_register Click command object to register
        @details Adds a command to the console's command group.
        """
        self._cli.add_command(cli_register)

    def repl(self):
        """
        @brief Start interactive REPL mode.
        @details Implements a Read-Eval-Print loop for interactive command execution.
        Supports "exit", "quit", and "help" commands.
        @todo Complete REPL implementation with history and autocomplete.
        """
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
        """
        @brief Launch the CLI application.
        @details Starts the Click CLI group and processes commands.
        Blocks until the user exits the application.
        """
        self._cli()


class CommandBuilder:
    """
    @class CommandBuilder
    @brief Builds Click commands from CommandConfig objects.
    @details Constructs Click command objects with options from a declarative configuration.
    """

    def __init__(self, config: CommandConfig, behavior: Callable):
        """
        @brief Initialize the CommandBuilder.
        @param config CommandConfig object defining the command structure
        @param behavior Callable that implements the command logic
        """
        self.config = config
        self.behavior = behavior

    def build(self) -> click.Command:
        """
        @brief Build and return a Click command.
        @return Fully constructed Click command object
        @details Constructs a Click command with all options from the config.
        """

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
    """
    @class cliTool
    @brief Abstract base class for CLI tools in Jupiter framework.
    @details Defines the interface that all CLI tools must implement.

    @code
    class MyTool(cliTool):
        @staticmethod
        def print_banner():
            console.print_banner("My Tool Banner")
    @endcode
    """

    @staticmethod
    @abstractmethod
    def print_banner():
        """
        @brief Print tool-specific banner.
        @details Must be implemented by subclasses to display a custom banner.
        """
        pass

    @classmethod
    @abstractmethod
    def usage(cls) -> str:
        """
        @brief Return usage information.
        @return CommandConfig object describing the tool's usage
        @details Must be implemented to provide CLI configuration.
        """
        pass

    @classmethod
    @abstractmethod
    def cli_behavior(cls, **kwargs):
        """
        @brief Implement the tool's CLI behavior.
        @param kwargs Command-line arguments
        @details Must be implemented to define what the tool does when invoked.
        """
        pass

    @abstractmethod
    def run(self):
        """
        @brief Run the tool in background.
        @details Must be implemented to define background execution behavior.
        """
        pass

    @classmethod
    def register_cli(cls) -> click.Command:
        """
        @brief Register the tool as a CLI command.
        @return Click command object
        @details Builds and returns a Click command from the tool's configuration.
        """
        builder = CommandBuilder(cls.__usage(), cls.__cli_behavior)
        return builder.build()
