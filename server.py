#!/usr/bin/env python
# Linux setup utility
# Copyright (c) 2024 Jackson Tong, Creekside Networks LLC.

import os
import sys
import re
import time
import logging
import paramiko

def spinner_generator():
    while True:
        for cursor in '|/-\\':
            yield cursor
            
def server_run_cmd(ssh_client, command, echo=False, progress=False, timeout=30):
    # Open a session with a pseudo-terminal
    transport = ssh_client.get_transport()
    channel = transport.open_session()
    channel.get_pty()
    channel.exec_command(command)

    spinner = spinner_generator()
    start_time = time.time()
    last_progress_time = start_time
    if progress:
        print(" ", end='', flush=True)

    output = ""
    try:
        while True:
            if echo:
                if channel.recv_ready():
                    data = channel.recv(1024).decode('utf-8')
                    output += data
                    print(data, end='')
                    # restart timer
                    start_time = time.time()
            elif progress:
                if time.time() - last_progress_time > 0.2:
                    if channel.recv_ready():
                        #if not cursor_hidden:
                        #    print("\033[?25l", end='', flush=True)  # Hide cursor
                        #    cursor_hidden = True
                        #while stdout.channel.recv_ready():
                        data = channel.recv(1024).decode('utf-8') 
                        #print(next(spinner) + "\b", end='', flush=True)
                        print("\b" + next(spinner), end='', flush=True)
                        start_time = time.time()
                    last_progress_time = time.time()
            
            if channel.exit_status_ready():
                break

            time.sleep(0.1)  # Wait for 0.1 seconds

            if timeout > 0 and time.time() - start_time > timeout:
                raise TimeoutError(f"Command {command} timed out after {timeout} seconds")
                
    finally:
        if progress:
            print("\b", end='', flush=True)
        #if cursor_hidden:
        #    print("\033[?25h", end='', flush=True)  # Show cursor

    exit_status = channel.recv_exit_status()
    return exit_status, output



