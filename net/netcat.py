#netcat utility implementation

import sys
import socket
import getopt
import threading
import subprocess
import argparse
import ssl

#server mode 
SERVER_MODE_LISTEN_MAX = 5

#client mode
RECV_BYTES = 4096

#args vars
LISTEN=False
COMMAND=False
UPLOAD=False
EXECUTE=""
TARGET=""
UPLOAD_DESTINATION=""
PORT=""

#define prompt help
def arguments_parser():

    parser = argparse.ArgumentParser(description='netcat impl.',add_help=False)

    parser.add_argument("-h",
                        "--help",
                        action="store_true",
                        help="""implementation of netcat tool:\n
                            Usage: netcat.py -t <target host> -p <port>\n"""
    )

    parser.add_argument("-l",
                        "--listen",
                        action="store_true",
                        help="-l --listen   - Listen on [host]:[port] for incoming connection" 
    )

    parser.add_argument("-c",
                        "--command",
                        help="initialize a command shell" 
    )

    #options with values

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
                        help="-t --target=IP_cible   - target listen port by default on 0.0.0.0" 
    )

    parser.add_argument("-p",
                        "--port",
                        type=int,
                        required=True,
                        help="-p --port   - host network port" 
    )

    return parser

def usage():
    #help print
    pass

def server_mode():

    server_sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    server_sock.bind((TARGET,PORT))
    server_sock.listen(SERVER_MODE_LISTEN_MAX)

    while True:
        client_sock,client_addr = server_sock.accept()
        client_thread = threading.Thread(target=client_handler,args=(client_sock,))
        client_thread.start()

def run_shell(cmd):
    #delete space and \n ... caract
    COMMAND = COMMAND.rstrip()

    try:
        client_shell = subprocess.check_output(
            COMMAND,
            stderr=subprocess.STDOUT,
            shell=True
        )
    except:
        client_shell = "failed to execute command.\r\n"
    return client_shell

def client_handler(client_sock):

    global UPLOAD
    global EXECUTE
    global COMMAND

    #check for any upload
    if len(UPLOAD_DESTINATION):

        file_buffer=""

        if True:
            data = client_sock.recv()


def client_mode(buffer):
    
    client_sock  = socket.socket (socket.AF_INET,socket.SOCK_STREAM)

    try:
        #connection to the target host
        client_sock.connect((TARGET,PORT))

        #TODO : implement with ssl encryption 
        #use fernet to secure backdoor

        if len(buffer):
            client_sock.sendall(buffer)

        while True:
            recv_len = 1
            response = ""

            while recv_len:
                data=client_sock.recv(RECV_BYTES)
                recv_len=len(data)
                response+=data

                if recv_len <RECV_BYTES:
                    break

            print(f"[*] server response : < {response.decode('utf-8',errors='ignore')} >")

            buffer = input("")
            buffer += "\n"
            client_sock.sendall(buffer.encode(''))
    except:
        print("[*] Exception! Exciting.")

        client_sock.close()

def main ():

    global LISTEN
    global COMMAND
    global UPLOAD
    global EXECUTE
    global TARGET
    global UPLOAD_DESTINATION
    global PORT

    #handle the user prompt
    parser = arguments_parser()

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()

    print(f"[+] Conf - Target: {args.target}, Port: {args.port}")

    LISTEN      = args.listen
    COMMAND     = args.command
    EXECUTE     = args.execute
    DESTINATION = args.upload  
    TARGET      = args.target  
    PORT        = args.port

    assert 1<= PORT <= 65535,f"Port {PORT} is invalid."

    if not LISTEN:
        #if we are not listen we are client (send data)
        print("[*] Client mode - Enter data")
        buffer = sys.stdin.read()
        client_mode(buffer)

    else: server_mode()

if __name__ == "__main__":
    main()
