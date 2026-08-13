
# netcat utility implementation

import sys
import socket
import threading
import subprocess
import argparse
from dataclasses import dataclass, field
from typing import Optional

SERVER_LISTEN_BACKLOG = 5
RECV_BYTES            = 4096
SHELL_PROMPT          = b"<BHP:#> "

@dataclass(frozen=True)
class Config:
    target:str  = "0.0.0.0"
    port:int = 0
    listen:bool= False
    command:bool = False
    execute: Optional[str]  = None
    upload_destination: Optional[str]  = None

def build_parser():

    parser = argparse.ArgumentParser(description='netcat implementation', add_help=True)

    parser.add_argument("-l",
                        "--listen",
                        action="store_true",
                        help="-l --listen   - Listen on [host]:[port] for incoming connection"
    )

    parser.add_argument("-c",
                        "--command",
                        action="store_true",
                        help="initialize a command shell"
    )

    # options with values

    parser.add_argument("-e",
                        "--execute",
                        type=str,
                        help="-e --execute=file_to_run  - execute the given file upon receiving a connection"
    )

    parser.add_argument("-u",
                        "--upload",
                        metavar="DESTINATION",
                        type=str,
                        help="-u --upload=destination   - upload a file and write to [destination] upon receiving connection"
    )

    parser.add_argument("-t",
                        "--target",
                        default='0.0.0.0',
                        type=str,
                        help="-t --target=target_ip   - target listen host (default: 0.0.0.0)"
    )

    parser.add_argument("-p",
                        "--port",
                        type=int,
                        required=True,
                        help="-p --port   - host network port"
    )

    return parser

def parser_config() -> Config:
    parser = build_parser()

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()

    if not (1 <= args.port <= 65535):
        parser.error(f"Port {args.port} is invalid.")

    return Config(
        target             = args.target,
        port               = args.port,
        listen             = args.listen,
        command            = args.command,
        execute            = args.execute,
        upload_destination = args.upload,
    )


def run_shell(cmd: str) -> bytes:

    cmd = cmd.strip()
    if not cmd:
        return b""

    try:
        # NOTE: This executes the command using the system shell. Keep in mind this has
        # security implications if untrusted input is passed. The behavior is preserved
        # for compatibility with the original tool.
        output = subprocess.check_output(
            cmd,
            stderr=subprocess.STDOUT,
            shell=True,
        )
        return output
    except subprocess.CalledProcessError as e:
        return e.output or f"[!] error: return_code={e.returncode}\r\n".encode()
    except Exception as e:
        return f"[!] error: cannot execute command: {e}\r\n".encode()



def client_handler(sock: socket.socket, cfg: Config) -> None:
    """handle client connection"""

    try:
        if cfg.upload_destination:
            _handle_upload(sock, cfg.upload_destination)

        if cfg.execute:
            output = run_shell(cfg.execute)
            sock.sendall(output)

        if cfg.command:
            _handle_shell(sock)

    except (ConnectionResetError, BrokenPipeError):
        print("[*] Disconnected client")
    finally:
        sock.close()

def _handle_upload(sock: socket.socket, destination: str) -> None:
    """handle uploading of files (streaming write to avoid buffering entire file in memory)"""

    print(f"[*] File reception -> {destination}")
    total = 0

    sock.settimeout(3.0)
    try:
        # write to file as data arrives to avoid OOM for large uploads
        with open(destination, "wb") as f:
            while True:
                try:
                    chunk = sock.recv(RECV_BYTES)
                except socket.timeout:
                    # timeout likely means end of upload
                    break
                if not chunk:
                    break
                f.write(chunk)
                total += len(chunk)
    finally:
        sock.settimeout(None)

    try:
        msg = f"[ok] {total} bytes written to {destination}\r\n"
        print(msg.strip())
        sock.sendall(msg.encode())
    except OSError as e:
        msg = f"[!] error: cannot write {destination}: {e}\r\n"
        print(msg.strip())
        try:
            sock.sendall(msg.encode())
        except Exception:
            pass

def _handle_shell(sock: socket.socket) -> None:
    """Open shell"""

    sock.sendall(SHELL_PROMPT)

    while True:
        cmd_buffer = b""
        while b"\n" not in cmd_buffer:
            chunk = sock.recv(1024)
            if not chunk:
                return  # disconnect client
            cmd_buffer += chunk

        response = run_shell(cmd_buffer.decode("utf-8", errors="ignore"))
        sock.sendall(response + SHELL_PROMPT)



def server_mode(cfg: Config) -> None:

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((cfg.target, cfg.port))
        srv.listen(SERVER_LISTEN_BACKLOG)
        print(f"[*] Server listening on {cfg.target}:{cfg.port}")

        while True:
            try:
                client_sock, client_addr = srv.accept()
                print(f"[+] Connection : {client_addr[0]}:{client_addr[1]}")
                t = threading.Thread(
                    target=client_handler,
                    args=(client_sock, cfg),
                    daemon=True,
                )
                t.start()
            except KeyboardInterrupt:
                print("\n[*] Server down!")
                break


def client_mode(cfg: Config, initial_buffer: str = "") -> None:

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.connect((cfg.target, cfg.port))
            print(f"[*] Connected to {cfg.target}:{cfg.port}")
        except ConnectionRefusedError:
            print(f"[!] Connection refused: {cfg.target}:{cfg.port}")
            sys.exit(1)

        try:
            if initial_buffer:
                sock.sendall(initial_buffer.encode("utf-8"))

            while True:
                response = b""
                sock.settimeout(1.0)
                try:
                    while True:
                        chunk = sock.recv(RECV_BYTES)
                        if not chunk:
                            break
                        response += chunk
                        if len(chunk) < RECV_BYTES:
                            break
                except socket.timeout:
                    pass
                finally:
                    sock.settimeout(None)

                if response:
                    print(response.decode("utf-8", errors="ignore"), end="", flush=True)

                try:
                    user_input = input() + "\n"
                    sock.sendall(user_input.encode("utf-8"))
                except EOFError:
                    break  # CTRL+D

        except (ConnectionResetError, BrokenPipeError):
            print("\n[*] Connection closed by the server")
        except KeyboardInterrupt:
            print("\n[*] Keyboard interruption")


def main() -> None:
    cfg = parser_config()

    print(f"[+] Config — target: {cfg.target}  port: {cfg.port}")

    if cfg.listen:
        server_mode(cfg)
    else:
        initial = ""
        if not sys.stdin.isatty():
            initial = sys.stdin.read()
        client_mode(cfg, initial)

if __name__ == "__main__":
    main()
