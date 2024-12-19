#!/usr/bin/env python
# Linux setup utility
# Copyright (c) 2024 Jackson Tong, Creekside Networks LLC.

import  os
import  sys
import  argparse
import  paramiko
from    simple_term_menu                import TerminalMenu
from    getpass                         import getpass

from    get_server                      import get_server

TITLE_COPYRIGHT="""
***************************************************************************
*                      Linux Setup Utility v1.0                           *
*          (c) 2024-2024 Jackson Tong, Creekside Networks LLC             *
***************************************************************************

"""

# Function to connect to the Linux server
def connect_ssh(hostname, port, username, passwd):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    while True:
        try:
            if passwd is None:
                passwd = getpass(f"Password: ")
            client.connect(hostname, port=port, username=username, password=passwd)
            print(f"Connected to {hostname} on port {port}")
            return client
        except Exception as sshException:
            print(f"\n{sshException}, please try again\n")
            hostname = input(f"Hostname/IP [{hostname}]: ") or hostname
            port     = input(f"Port [{port}]: ")
            port     = int(port) if port else 22
            username = input(f"Username [{username}]: ") or username
            passwd   = None

# main function
def main():
    # print copyright information
    print(TITLE_COPYRIGHT)

    # parse command line arguments
    parser = argparse.ArgumentParser(description='Connect to a Linux server')
    parser.add_argument('hostname', help='The hostname or IP address of the server (optionally with username@hostname)')
    parser.add_argument('-p', type=int, default=22, help='Specify a port other than the default port 22')
    parser.add_argument('-w', type=str, default=None, help='Password for the user')

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args  = parser.parse_args()

    # Extract username and hostname
    if '@' in args.hostname:
        username, hostname = args.hostname.split('@', 1)
    else:
        username = "root"
        hostname = args.hostname

    # Use default password "ubnt" if username is "ubnt"
    port  = args.p if args.p is not None else 22
    passwd = args.w if args.w is not None else None

    server = get_server(hostname, port, username, passwd)

    title="\no Main menu"
    options = [
        "[0] Exit",
        "[1] Initlial setup", 
        "[2] Install applications", 
    ]

    while True:
        terminal_menu       = TerminalMenu(options, title=title)
        menu_entry_index    = terminal_menu.show()

        match menu_entry_index:
            case 0:
                break
            case 1:
                server.os_initialization()
            case _:
                print("\n*** This feature is not implemented yet")

    server.close()
    print("\n*** Thank you for using this script ***\n\n")

if __name__ == "__main__":
    main()