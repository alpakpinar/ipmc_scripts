#!/usr/bin/env python3

import os
import sys
import re
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
    """Command line parser."""
    parser = argparse.ArgumentParser()
    parser.add_argument('ipmc_ip_addr', type=str, help='IP address of the IPMC to poll.')
    args = parser.parse_args()
    return args


def retrieve_sm_number(stdout):
    """
    From IPMC terminal output, retrieve the Apollo SM number for the IPMC.
    Returns the Apollo SM number as an integer.
    """
    sm_number = None
    # Loop over each line, find the one where the SM number is displayed
    for line in stdout.split('\n'):
        if not (line.startswith('hw') and '#' in line):
            continue
        
        tokens = line.split()
        sm_number = re.findall('#(\d+)', tokens[-1])[0]
    
    if not sm_number:
        raise RuntimeError('Could not retrieve the Apollo SM number.')
    
    return int(sm_number)


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
            
            # Retrieve the Apollo SM number from the output
            sm_number = retrieve_sm_number(output)
            print(sm_number)

        except socket.timeout:
            print('Command timed out.')


if __name__ == '__main__':
    main()
