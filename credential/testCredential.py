# SPDX-License-Identifier: GPL-2.0-only

"""
@file testCredential.py
@brief SSH credential testing tool for Jupiter framework.
@author Security Team
@version 1.0
@date 2026-08-19

@details
Implements a CLI tool for testing SSH credentials against target systems.
Supports both single credential and batch testing with detailed reporting.

@see TestCredential, SshCfg
"""

BANNER = r""" 
████████╗ ███████╗ ███████╗ ████████╗ ██████╗ ██████╗  ███████╗ ██████╗  
╚══██╔══╝ ██╔════╝ ██╔════╝ ╚══██╔══╝ ██╔════╝ ██╔══██╗ ██╔════╝ ██╔══██╗ 
   ██║    █████╗   ███████╗    ██║    ██║      ██████╔╝ █████╗   ██║  ██║ 
   ██║    ██╔══╝   ╚════██║    ██║    ██║      ██╔══██╗ ██╔══╝   ██║  ██║ 
   ██║    ███████╗ ███████║    ██║    ╚██████╗ ██║  ██║ ███████╗ ██████╔╝ 
   ╚═╝    ╚══════╝ ╚══════╝    ╚═╝     ╚═════╝ ╚═╝  ╚═╝ ╚══════╝ ╚═════╝  

"""

TOOL_NAME = "testcred"
HELP = r"""
    Test accounts and credentials against SSH services on target hosts.
"""

from utils.config.netconfig import SshCfg
from utils.config.cliconfig import CommandConfig, OptionConfig
from utils.cli import cliTool, CommandBuilder
from shared import console
import paramiko, socket, click # type: ignore


#TODO: Implement testing with ssh key files 

class TestCredential(cliTool):
    def __init__(self, ssh_cfg: SshCfg):
        self.ssh_cfg = ssh_cfg

    @property
    def ssh_cfg(self):
        return self._ssh_cfg

    @ssh_cfg.setter
    def ssh_cfg(self, value: SshCfg):
        if SshCfg is not None and not isinstance(value, SshCfg):
            raise TypeError("ssh_cfg must be an instance of SshCfg")
        self._ssh_cfg = value

    @staticmethod
    def print_banner():
        return console.print_banner(BANNER)

    @classmethod
    def usage(cls)->CommandConfig:
        return CommandConfig(
            name=TOOL_NAME,
            help=HELP,
            options=[
                OptionConfig(
                    name="host",
                    help="Target host IP or hostname",
                    required=True,
                    type=str
                ),
                OptionConfig(
                    name="port",
                    help="SSH port (default: 22)",
                    required=False,
                    type=int,
                    default=22
                ),
                OptionConfig(
                    name="username",
                    help="Username to test",
                    required=False,
                    type=str
                ),
                OptionConfig(
                    name="password",
                    help="Password to test",
                    required=False,
                    type=str
                ),
                OptionConfig(
                    name="credential_file",
                    help='File containing format : "username password" pairs for batch testing',
                    required=False,
                    type=str
                ),
                OptionConfig(
                    name="timeout",
                    help="Connection timeout in seconds (default: 10)",
                    required=False,
                    type=int,
                    default=10
                )
            ],
        )

    @classmethod
    def cli_behavior(cls,
        host: str,
        dst: str,
        timeout: int,
        verbose: int,
        port: int,
        username: str,
        password: str,
        credential_file: str = None
    ):
        if not credential_file and (not username or not password):
            console.print_error("Either provide a credential file or both username and password.")
            return
        
        cfg = cls(
            SshCfg(
                host=host,
                dst=dst,
                timeout=timeout,
                verbose=verbose,
                port=port,
                username=username,
                password=password,
                file=credential_file
            )
        )

        return cfg.run()

    @classmethod
    def register_cli(cls)->click.Command:
        builder = CommandBuilder(cls.usage(), cls.cli_behavior)
        return builder.build()

    def run(self):
        """
        @brief Run the SSH credential tests.
        @details Attempts to connect to the target SSH service using provided credentials.
        """

        if self.ssh_cfg.file:
            self.__SSH_test_login_with_file()

        # Test with a single username/password if is also or not provided
        if self.ssh_cfg.username and self.ssh_cfg.password:
            self.__SSH_login(
                host=self.ssh_cfg.host,
                port=self.ssh_cfg.port,
                username=self.ssh_cfg.username,
                password=self.ssh_cfg.password,
                timeout=self.ssh_cfg.timeout
            )

    def __SSH_login(host: str, port: int, username: str, password: str, timeout: int):
        """
        @brief Test the provided SSH credentials.
        @details Attempts to authenticate to the SSH service using the provided username and password.
        """

        try:
            client = paramiko.SSHClient()
            except_info = f"{username}@{host}:{port}"

            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(
                hostname=host,
                port=port,
                username=username,
                password=password,
                timeout=timeout
            )

            ssh_session = client.get_transport().is_active()
            if ssh_session.active:
                console.print_green(f"Successful login: {except_info}")
                client.close()
            else:
                console.print_error(f"Failed login: {except_info}")
        except paramiko.AuthenticationException:
            console.print_error(f"Authentication failed for {except_info}")
        except paramiko.SSHException as e:
            console.print_error(f"SSH error for {except_info}: {e}")
        except socket.error as e:
            console.print_error(f"Socket error for {except_info}: {e}") 
        except Exception as e:
            console.print_error(f"Unexpected error for {except_info}: {e}")

    def __SSH_test_login_with_file(self):
        """
        @brief Test SSH credentials from a file.
        @details Reads username:password pairs from the specified file and attempts to authenticate.
        """
        try:
            with open(self.ssh_cfg.file, 'r') as f:
                for line in f:
                    vals = line.split()
                    username = vals[0].strip()
                    password = vals[1].strip() if len(vals) > 1 else ""
                    self.__SSH_login(
                        host=self.ssh_cfg.host,
                        port=self.ssh_cfg.port,
                        username=username,
                        password=password,
                        timeout=self.ssh_cfg.timeout
                    )
        except FileNotFoundError:
            console.print_error(f"Credential file not found: {self.ssh_cfg.file}")
        except Exception as e:
            console.print_error(f"Error reading credential file: {e}")

