#!/usr/bin/env python3
"""
ssl_proxy.py — TCP proxy with optional SSL/TLS on client and/or remote side.

Usage:
    python ssl_proxy.py [options] <localhost> <localport> <remotehost> <remoteport>

Examples:
    # Plain proxy (no SSL anywhere):
    python ssl_proxy.py 127.0.0.1 9000 10.0.0.1 9000

    # Wrap both sides in SSL (MITM between two TLS peers):
    python ssl_proxy.py --ssl-client --ssl-remote 127.0.0.1 9443 10.0.0.1 443

    # Only encrypt the upstream leg (client → proxy is plain, proxy → server is SSL):
    python ssl_proxy.py --ssl-remote 127.0.0.1 9000 api.example.com 443

    # Receive remote banner before waiting for client (e.g. FTP, SSH):
    python ssl_proxy.py --receive-first --ssl-remote 127.0.0.1 9021 ftp.example.com 21

Certificate generation (needed for --ssl-client):
    openssl req -x509 -newkey rsa:4096 -keyout proxy.key -out proxy.crt \
        -days 365 -nodes -subj "/CN=localhost"
"""

import sys
import socket
import ssl
import threading
import argparse
import textwrap


# ─────────────────────────────────────────────────────────────────────────────
# Hex dump helper
# ─────────────────────────────────────────────────────────────────────────────

def hexdump(src: bytes, length: int = 16, prefix: str = "") -> None:
    """Print a formatted hex + ASCII dump of *src*."""
    if not src:
        return
    lines = []
    for i in range(0, len(src), length):
        chunk = src[i : i + length]
        hex_part = " ".join(f"{b:02X}" for b in chunk)
        asc_part = "".join(chr(b) if 0x20 <= b < 0x7F else "." for b in chunk)
        lines.append(f"{prefix}{i:04X}  {hex_part:<{length * 3}}  {asc_part}")
    print("\n".join(lines))


# ─────────────────────────────────────────────────────────────────────────────
# Network helpers
# ─────────────────────────────────────────────────────────────────────────────

def receive_from(sock: socket.socket, timeout: float = 2.0) -> bytes:
    """Read all available data from *sock*, returning bytes."""
    buf = b""
    sock.settimeout(timeout)
    try:
        while True:
            data = sock.recv(4096)
            if not data:
                break
            buf += data
    except (socket.timeout, ssl.SSLWantReadError):
        pass
    except Exception as exc:
        print(f"[!!] receive_from error: {exc}")
    return buf


def wrap_client_socket(
    raw_sock: socket.socket,
    certfile: str,
    keyfile: str,
) -> ssl.SSLSocket:
    """Wrap an accepted socket with server-side TLS."""
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(certfile=certfile, keyfile=keyfile)
    # Require at least TLS 1.2
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    return ctx.wrap_socket(raw_sock, server_side=True)


def wrap_remote_socket(
    raw_sock: socket.socket,
    remote_host: str,
    verify: bool = True,
) -> ssl.SSLSocket:
    """Wrap an outgoing socket with client-side TLS."""
    ctx = ssl.create_default_context()
    if not verify:
        # Useful when the remote uses a self-signed cert
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    return ctx.wrap_socket(raw_sock, server_hostname=remote_host)


# ─────────────────────────────────────────────────────────────────────────────
# Packet hooks — customise these
# ─────────────────────────────────────────────────────────────────────────────

def request_handler(buffer: bytes) -> bytes:
    """
    Called for every buffer travelling FROM the local client TO the remote host.
    Modify, log, or drop bytes here.
    """
    # ── Example: log HTTP Host header ────────────────────────────────────────
    # if b"Host:" in buffer:
    #     for line in buffer.split(b"\r\n"):
    #         if line.startswith(b"Host:"):
    #             print(f"[>>] Host header: {line.decode(errors='replace')}")
    # ─────────────────────────────────────────────────────────────────────────
    return buffer


def response_handler(buffer: bytes) -> bytes:
    """
    Called for every buffer travelling FROM the remote host TO the local client.
    Modify, log, or drop bytes here.
    """
    # ── Example: redact a string in server responses ──────────────────────────
    # buffer = buffer.replace(b"secret", b"REDACTED")
    # ─────────────────────────────────────────────────────────────────────────
    return buffer


# ─────────────────────────────────────────────────────────────────────────────
# Core proxy logic
# ─────────────────────────────────────────────────────────────────────────────

def proxy_handler(
    client_sock: socket.socket,
    remote_host: str,
    remote_port: int,
    receive_first: bool,
    ssl_remote: bool,
    no_verify: bool,
) -> None:
    """Handle one client connection in its own thread."""
    # Connect to remote
    raw_remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        raw_remote.connect((remote_host, remote_port))
    except Exception as exc:
        print(f"[!!] Cannot connect to {remote_host}:{remote_port} — {exc}")
        client_sock.close()
        return

    remote_sock: socket.socket = raw_remote
    if ssl_remote:
        try:
            remote_sock = wrap_remote_socket(raw_remote, remote_host, verify=not no_verify)
            print(f"[SSL] Remote TLS established — cipher: {remote_sock.cipher()}")
        except ssl.SSLError as exc:
            print(f"[!!] SSL handshake with remote failed: {exc}")
            raw_remote.close()
            client_sock.close()
            return

    # Optionally grab a banner from remote before client speaks
    if receive_first:
        remote_buf = receive_from(remote_sock)
        if remote_buf:
            print(f"[<==] Remote banner ({len(remote_buf)} bytes):")
            hexdump(remote_buf)
            remote_buf = response_handler(remote_buf)
            client_sock.send(remote_buf)

    # Relay loop
    while True:
        # Client → remote
        local_buf = receive_from(client_sock)
        if local_buf:
            print(f"[==>] Client → proxy: {len(local_buf)} bytes")
            hexdump(local_buf, prefix="    ")
            local_buf = request_handler(local_buf)
            remote_sock.send(local_buf)
            print(f"[==>] Forwarded to remote.")

        # Remote → client
        remote_buf = receive_from(remote_sock)
        if remote_buf:
            print(f"[<==] Remote → proxy: {len(remote_buf)} bytes")
            hexdump(remote_buf, prefix="    ")
            remote_buf = response_handler(remote_buf)
            client_sock.send(remote_buf)
            print(f"[<==] Forwarded to client.")

        # Close when both sides go silent
        if not local_buf and not remote_buf:
            print("[*] No more data — closing connection.")
            break

    client_sock.close()
    remote_sock.close()


def server_loop(
    local_host: str,
    local_port: int,
    remote_host: str,
    remote_port: int,
    receive_first: bool,
    ssl_client: bool,
    ssl_remote: bool,
    no_verify: bool,
    certfile: str,
    keyfile: str,
) -> None:
    """Bind, listen, and dispatch one thread per connection."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server.bind((local_host, local_port))
    except OSError as exc:
        print(f"[!!] Failed to bind {local_host}:{local_port} — {exc}")
        sys.exit(1)

    print(f"[*] Listening on {local_host}:{local_port}")
    print(f"[*] Forwarding to {remote_host}:{remote_port}")
    print(f"[*] Client-side SSL : {'ON' if ssl_client else 'off'}")
    print(f"[*] Remote-side SSL : {'ON' if ssl_remote else 'off'}")
    server.listen(5)

    while True:
        client_raw, addr = server.accept()
        print(f"\n[==>] Connection from {addr[0]}:{addr[1]}")

        client_sock: socket.socket = client_raw
        if ssl_client:
            try:
                client_sock = wrap_client_socket(client_raw, certfile, keyfile)
                print(f"[SSL] Client TLS established — cipher: {client_sock.cipher()}")
            except ssl.SSLError as exc:
                print(f"[!!] SSL handshake with client failed: {exc}")
                client_raw.close()
                continue

        t = threading.Thread(
            target=proxy_handler,
            args=(client_sock, remote_host, remote_port, receive_first, ssl_remote, no_verify),
            daemon=True,
        )
        t.start()


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="ssl_proxy.py",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent("""\
            TCP proxy with optional SSL/TLS on the client and/or remote side.
        """),
    )
    parser.add_argument("local_host", help="Interface to listen on (e.g. 0.0.0.0)")
    parser.add_argument("local_port", type=int)
    parser.add_argument("remote_host", help="Target host to forward traffic to")
    parser.add_argument("remote_port", type=int)

    parser.add_argument(
        "--receive-first", action="store_true",
        help="Pull a banner from remote before waiting for client data",
    )
    parser.add_argument(
        "--ssl-client", action="store_true",
        help="Wrap the client ↔ proxy leg with TLS (requires --cert and --key)",
    )
    parser.add_argument(
        "--ssl-remote", action="store_true",
        help="Wrap the proxy ↔ remote leg with TLS",
    )
    parser.add_argument(
        "--no-verify", action="store_true",
        help="Skip certificate verification on the remote leg (for self-signed certs)",
    )
    parser.add_argument(
        "--cert", default="proxy.crt",
        help="Path to PEM certificate for server-side TLS (default: proxy.crt)",
    )
    parser.add_argument(
        "--key", default="proxy.key",
        help="Path to PEM private key for server-side TLS (default: proxy.key)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.ssl_client and not (args.cert and args.key):
        print("[!!] --ssl-client requires --cert and --key")
        sys.exit(1)

    server_loop(
        local_host=args.local_host,
        local_port=args.local_port,
        remote_host=args.remote_host,
        remote_port=args.remote_port,
        receive_first=args.receive_first,
        ssl_client=args.ssl_client,
        ssl_remote=args.ssl_remote,
        no_verify=args.no_verify,
        certfile=args.cert,
        keyfile=args.key,
    )


if __name__ == "__main__":
    main()