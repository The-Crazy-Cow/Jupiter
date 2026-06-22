#netcat utility implementation


import sys
import socket
import getopt
import threading
import subprocess
import argparse

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
                        required=True,
                        help="-t --target=IP_cible   - target listen port" 
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
    
if __name__ == "__main__":
    main()
