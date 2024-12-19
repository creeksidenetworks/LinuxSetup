#!/usr/bin/env python
# Linux setup utility
# Copyright (c) 2024 Jackson Tong, Creekside Networks LLC.

import  os
import  json
import  time
import  pytz
import  requests

from    global_config       import GlobalConfig
from    server              import server_run_cmd
from    sshkey              import retrieve_ssh_key

def print_status(msg, status=None):
    if status == None:
        print(f"   - {msg:<40} : ", end="")
    else:
        print(f"   - {msg:<40} : {status}")

def get_ip_info(ip_address):

    response = requests.get(f"https://ipinfo.io/{ip_address}/json")
    if response.status_code == 200:
        info = response.json()
        city = info.get('city')
        region = info.get('region')
        country = info.get('country')
        timezone = info.get('timezone')
        return timezone, city, region, country
    else:
        return None

#
class RedhatServer:
    def __init__(self, ssh_client, os_name):
        self.ssh_client = ssh_client
        self.os         = os_name

    def run_cmd(self, command):
        stdin, stdout, stderr = self.ssh_client.exec_command(command)
        return stdout.read().decode('utf-8')

    def run_interactive_cmd(self, command, echo=False, progress=False, timeout=30):
        return server_run_cmd(self.ssh_client, command, echo=echo, progress=progress, timeout=timeout)

    def is_package_installed(self, package):
        stdin, stdout, stderr = self.ssh_client.exec_command(f"rpm -q {package}")
        output = stdout.read().decode('utf-8')
        return "is not installed" not in output

    def install_package(self, package):
        if self.is_package_installed(package):
            print_status(f"Installing {package}", "done")
        else:
            print_status(f"Installing {package}")
            self.run_interactive_cmd(f"sudo yum install -y {package}", echo=False, progress=True, timeout=0)
            print("done")

    def os_initialization(self):
        print (f"\nInitializing the server for Red Hat based OS - {self.os}")
        print("------------------------------------------------------------")
        """
        print(" o Installing required packages")
        # check CentOS-Base.repo
        if self.os == "CentOS Linux 7":
            print_status("Updating CentOS-Base.repo")
            file="/etc/yum.repos.d/CentOS-Base.repo"
            cmds = [f"sudo sed -i 's/^mirrorlist=/#mirrorlist=/' {file}",
                    f"sudo sed -i 's|^#baseurl=http://mirror.centos.org/|baseurl=http://vault.centos.org/|' {file}",
                    f"sudo sed -i 's|^baseurl=http://mirror.centos.org/|baseurl=http://vault.centos.org/|' {file}",
                    ]
            for cmd in cmds:
                self.run_interactive_cmd(cmd)
            print("done")
        
        # install epel-release
        self.install_package("epel-release")
        print_status("Updating the server")
        self.run_interactive_cmd("sudo yum update -y", echo=False, progress=True, timeout=0)
        print("done")

        # and other tools
        if self.os == "CentOS Linux 7":

            self.install_package("kernel-devel")
        elif self.os in ["Oracle Linux 8", "Rocky Linux 8"]:
            self.run_interactive_cmd("sudo yum config-manager --set-enabled powertools")
            self.install_package("libnsl")  
        elif os in ["Oracle Linux 9", "Rocky Linux 9"]:
            self.run_interactive_cmd("sudo yum config-manager --set-enabled crb")
            self.install_package("libnsl")   

        # install all default packages
        for package in ["yum-utils","rsync","util-linux","curl","firewalld","bind-utils","telnet","jq","nano",
                    "ed","tcpdump","wget","nfs-utils","cifs-utils","samba-client","tree","xterm","net-tools",
                    "openldap-clients","sssd","realmd","oddjob","oddjob-mkhomedir","adcli",
                    "samba-common","samba-common-tools","krb5-workstation","openldap-clients","iperf3","rsnapshot","zip",
                    "unzip","ftp","autofs","zsh","ksh","tcsh","ansible","cabextract","fontconfig",
                    "nedit","htop","tar","traceroute","mtr","pwgen","ipa-admintools"]:
            self.install_package(package)

        """

        print(" o Detecting regional information")
        stdin, stdout, stderr = self.ssh_client.exec_command("curl -s -m 30 checkip.dyndns.com")
        output = stdout.read().decode('utf-8')
        ip_address = output.split(': ')[1].split('<')[0].strip()
        print_status("Public IP address", ip_address)

        timezone, city, region, country = get_ip_info(ip_address)
        # Get current hostname
        stdin, stdout, stderr = self.ssh_client.exec_command("hostname")
        hostname = stdout.read().decode('utf-8').strip()

        print_status("Hostname", hostname)        
        if timezone:
            print_status("Timezone", timezone)
            print_status("Location", f"{city}, {region}, {country}")
        else:
            print_status("Timezone", "unknown")
            print_status("Location", "unknown")

        # get users confirmation
        while True:
            print(" o Please confirm the following settings:")
            hostname = input(f"   - Enter the hostname [{hostname}] : ") or hostname

            while True:
                timezone = input(f"   - Enter the timezone [{timezone}] : ") or timezone
                try:
                    pytz.timezone(timezone)
                except pytz.UnknownTimeZoneError:
                    print(f"   - The timezone '{timezone}' is not valid. Please enter a valid timezone.")
                    continue
                break

            confirm  = input(f"   - Add ssh pubic key to current account? [Y/N] [Y] : ") or "Y"
            if confirm.lower() == "y":
                ssh_key_names = retrieve_ssh_key()

            confirm  = input(f"   - Disable SELinux? (Y/N) [Y] : ") or "Y"
            disable_SELinux  = confirm.lower() == "y"

            confirm  = input(f"\n   - Accept above settings? (Y/N) [N] : ") or "N"
            if confirm.lower() == "y":
                break
            else:
                confirm = input(f"   - Return to main menu? (Y/N) [N] : ") or "N"
                if confirm.lower() == "y":
                    return None

        print("\n o Updating the server")     

        # update the hostname
        print_status(f"Updating hostname to {hostname}")
        self.run_interactive_cmd(f"sudo hostnamectl set-hostname {hostname}")
        print("done")

        print_status(f"Set time zone and enable ntp")
        self.run_interactive_cmd(f"sudo  timedatectl set-timezone {timezone} && sudo  timedatectl set-ntp true")
        print("done")

        print_status(f"Disable dns lookup in SSH")
        self.run_interactive_cmd(f"sudo sed -i.bak -e 's/^#UseDNS.*/UseDNS no/' -e 's/^UseDNS.*/UseDNS no/' /etc/ssh/sshd_config")
        print("done")

        if ssh_key_names:
            print_status(f"Add ssh public keys", "")
            global_config = GlobalConfig()
            keys = global_config.get("ssh_keys")    
            self.run_cmd(f"mkdir -p ~/.ssh && chmod 700 ~/.ssh && touch ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys")

            # Retrieve existing keys from the remote server
            existing_keys = self.run_cmd("cat ~/.ssh/authorized_keys").splitlines()

            for key_name in ssh_key_names:
                key = keys.get(key_name)
                new_key_entry = f"{key['type']} {key['key']}"

                # Check if the key already exists
                duplicated_key = False
                for existing_key in existing_keys:
                    if key['key'] in existing_key:
                        print(f"     > Key '{key_name}' already exists on the remote server. Skipping.")
                        duplicated_key = True
                        break

                if not duplicated_key:
                    # Add the new key to the authorized_keys file
                    self.run_cmd(f"echo '{new_key_entry}' >> ~/.ssh/authorized_keys")
                    print(f"     > Key '{key_name}' added to the remote server.")
            
            print("     > done")


        return True


    def close(self):
        self.ssh_client.close()
 
