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
    """Wrap an accepted socket with server-side TL"""

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile=certfile,keyfile=keyfile)

    #usage of min TLS 1.2
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    return context.wrap_socket(raw_sock,server_side=True)






if __name__ == "__main__":
    main()