#!/usr/bin/env python
# Linux setup utility
# Copyright (c) 2024 Jackson Tong, Creekside Networks LLC.

import os
import sys
import re
import time
import logging
import paramiko

from redhat import RedhatServer
from server import server_run_cmd

os_supported = {
    "rhel": {
        "versions": ["CentOS Linux 7", "CentOS Linux 8", "Oracle Linux 8", "Oracle Linux 9", "Rocky Linux 8", "Rocky Linux 9"]
    },
    "ubuntu": {
        "versions": ["Ubuntu 18", "Ubuntu 20", "Ubuntu 22", "Ubuntu 24"]
    },
}

def get_server(hostname, port, username, password, verbose=False):
    if verbose:
        # Enable paramiko logging
        logging.basicConfig(level=logging.DEBUG)
        paramiko.util.log_to_file(filename=os.path.expanduser("~/.ssh.log"))

    paramiko.transport.Transport._preferred_pubkeys = (
        "ssh-ed25519",
        "ecdsa-sha2-nistp256",
        "ecdsa-sha2-nistp384",
        "ecdsa-sha2-nistp521",
        "ssh-rsa",
        "rsa-sha2-512",
        "rsa-sha2-256",
        "ssh-dss",
    )        

    # load ssh config under home
    ssh_config_file = os.path.expanduser('~/.ssh/config')
    if os.path.exists(ssh_config_file):
        ssh_config = paramiko.SSHConfig()
        with open(ssh_config_file) as f:
            ssh_config.parse(f)

        # Match the given hostname against the SSH config file
        host_config = ssh_config.lookup(hostname)

        # Apply settings from ~/.ssh/config if they are not explicitly provided
        if 'user' in host_config and not username:
            username = host_config['user']
        if 'port' in host_config and not port:
            port = int(host_config['port'])

    # Set default port if not provided
    if not port:
        port = 22  

    # create ssh client
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # Attempt to connect until successful
    while True:
        try:                
            ssh_client.connect(
                hostname=hostname,
                username=username,
                password=password,
                port=port,
                timeout=10,
                look_for_keys=True,
                allow_agent=True
            )
            print(f"SSH connection established with {hostname}.")
            break
        except Exception as e:
            print(f"Failed to connect to {hostname}: {e}")
            # If connection fails, prompt for new input
            print("\nPlease re-enter the connection details:")
            hostname   = input(f"Hostname (or IP address) [{hostname}]: ") or hostname
            username   = input(f"Username [{username}]): ") or username
            password   = input("Password (Empty to use ssh key): ") or None
            port       = input(f"SSH Port [{port}]: ") or port

    # Detect and verify the supproted OS type
    stdin, stdout, stderr = ssh_client.exec_command("grep '^PRETTY_NAME=' /etc/os-release | cut -d '=' -f 2 | tr -d '\"'")
    os_detected = stdout.read().decode('utf-8')

    def extract_os_version(os_string):
        match = re.match(r"([^\d]*\d+)", os_string)
        return match.group(1) if match else os_string

    os_detected = extract_os_version(os_detected)
    print(f"Detected OS: {os_detected}")

    # enable passwordless sudo
    # Switch to root user if not already
    if username != "root":   
        shell = ssh_client.invoke_shell()
        shell.settimeout(30)
        shell.send('sudo -i\n')
        
        buff = ''
        passowrd_required = False
        while True:
            buff += shell.recv(1024).decode('utf-8')
            if buff.endswith(': ') and 'password for' in buff:
                shell.send(password + '\n')
                passowrd_required = True
            elif buff.endswith('# '):
                break
            time.sleep(0.1)            
        print("Switched to root user")

        if passowrd_required:
            sudo_users = f"{username} ALL=(ALL)       NOPASSWD: ALL\n"
            cmd = f"echo '{sudo_users}' >> /etc/sudoers.d/{username}\n"
            shell.send(cmd)
            time.sleep(0.1)
            print("Passwordless sudo enabled") 
        else:
            print("Passwordless sudo already enabled") 

        shell.close()

    # initlialize the server object
    if os_detected in os_supported["rhel"]["versions"]:
        return RedhatServer(ssh_client, os_detected)
    else:
        print(f"\nUnsupported OS: {os_detected}\n")
        ssh_client.close()
        sys.exit(1)