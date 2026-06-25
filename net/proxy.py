#tcp procy

import sys
import socket
import ssl
import threading
import  argparse
import  textwrap

#const
MAX_PROXY_LISTEN=5

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
    server.listen(MAX_PROXY_LISTEN)

    while True:
        client_raw,addr =  server.accept()
        print(f"\n[*] Connection from {addr[0]}:{addr[1]}")

        client_sock: socket.socket = client_raw

        if ssl_client:
            try:
                client_sock = wrap_client_socket(client_raw,certfile=certfile,keyfile=keyfile)
                print(f"[SSL] Client TLS established — cipher: {client_sock.cipher()}")
            except ssl.SSLError as exc:
                print(f"[!] SSL handshake with client failed" : {exc})
                client_raw.close()
                continue
        
        t = threading.Thread(
            target=proxy_handler,
            args=(client_sock, remote_host, remote_port, receive_first, ssl_remote, no_verify),
            daemon=True,
        )
        t.start()


def wrap_client_socket(
    raw_sock: socket.socket,
    certfile: str,
    keyfile: str,
) -> ssl.SSLSocket:
    """Wrap an accepted socket with server-side TLS"""

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile=certfile,keyfile=keyfile)

    #usage of min TLS 1.2
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    return context.wrap_socket(raw_sock,server_side=True)

def build_parser()-> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=textwrap.dedent("""\
            TCP proxy with optional SSL/TLS on the client and/or remote side.
        """),
        add_help=False
    )

    parser.add_argument("local_host", 
                        help="Interface to listen")

    parser.add_argument("local_port", type=int)

    parser.add_argument("remote_host", 
                        help="Target host to forward traffic to")

    parser.add_argument("remote_port", 
                        type=int)

    parser.add_argument(
        "--receive-first", 
        action="store_true",
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
        "--no-verify",
        action="store_true",
        help="Skip certificate verification on the remote leg",
    )

    parser.add_argument(
        "--cert", 
        default="proxy.crt",
        help="Path to PEM certificate for server-side TLS",
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