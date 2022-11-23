#!/usr/bin/env python3

import os
import sys
import time
import socket
import argparse

from util import write_command_and_read_output

# Check Python version, need at least 3.6
valid_python = sys.version_info.major >= 3 and sys.version_info.minor >= 6 
assert valid_python, "You need Python version >=3.6 to run this script!"

# The port for the telnet service on the IPMC
PORT = 23

def parse_cli():
    parser = argparse.ArgumentParser()
    parser.add_argument('ipmc_ip_addr', type=str, help='IP address of the IPMC to poll.')
    args = parser.parse_args()
    return args


def main():
    args = parse_cli()
    HOST = args.ipmc_ip_addr

    # Timeout value (s) for socket connection
    timeout = 5

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # Make the connection
        s.connect((HOST, PORT))
        s.settimeout(timeout)

        try:
            output = write_command_and_read_output(s, 'eepromrd\r\n')
            print(output)
        except socket.timeout:
            print('Command timed out.')


if __name__ == '__main__':
    main()
