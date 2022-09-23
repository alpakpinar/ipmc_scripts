#!/usr/bin/env python3

import os
import sys
import time
import yaml
import socket
import argparse

from pprint import pprint

# Check Python version, need at least 3.6
valid_python = sys.version_info.major >= 3 and sys.version_info.minor >= 6 
assert valid_python, "You need Python version >=3.6 to run this script!"

# The port for the telnet service on the IPMC
PORT = 23

# A mapping of Service Module serial numbers to the IPMC numbers
SM_TO_IPMC = {
    'SM207': 32
}

# A mapping of configuration fields -> commands to set them
CONFIG_TO_COMMANDS = {
    'board' : {
        'serial' : 'idwr',
        'rev'    : 'revwr',
    },
    'eeprom' : {
        'version' : 'verwr',
    },
    'mac' : {
        'eth0' : 'ethmacwr 0',
        'eth1' : 'ethmacwr 1',
    },
}

def parse_cli():
    parser = argparse.ArgumentParser()
    parser.add_argument('board_number', type=int, help='The serial number of the Apollo SM.')
    parser.add_argument('-c', '--config-path', default='config/ipmc_config.yaml', help='Path to the IPMC config file.')
    args = parser.parse_args()
    return args


def read_config(filepath: str):
    """Reads the YAML configuration file from the given file path."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Could not find IPMC configuration file: {filepath}")
    
    with open(filepath, 'r') as f:
        data = yaml.safe_load(f)
    
    return data


def validate_config(config):
    """Make sure that all the required keys are in place for the configuration."""
    for key, item in CONFIG_TO_COMMANDS.items():
        assert key in config, f"Key cannot be found: {key}"

        for subkey in item.keys():
            assert subkey in config[key], f"Sub-key cannot be found: {subkey} (under {key})"


def get_commands(config):
    """
    Given the configuration of IPMC fields, generate the set of commands necessary to set them in EEPROM.
    """
    commands = []

    for key, item in CONFIG_TO_COMMANDS.items():
        for subkey, commandbase in item.items():
            # Read the value from the config and figure out the command
            # Some minor pre-processing for MAC address values 
            value = str(config[key][subkey]).replace(':', ' ')
            commands.append(f"{commandbase} {value}\r\n")

    # Do a final eepromrd
    commands.append("eepromrd\r\n")

    return commands


def write_command_and_read_output(
    sock: socket.socket, 
    command: str,
    max_size: int=2048,
    read_until: bytes=b">",
    ) -> str:
    """
    Given the socket interface, writes a command to IPMC TelNet interface 
    and returns the data echoed back.

    The maximum message size to expect is specified via the max_size argument.
    """
    counter = 0
    data = b""

    # Send the command one byte at a time
    for ch in command:
        sock.send(bytes(ch, 'utf-8'))
        # Read back the command
        _ = sock.recv(1)

    # Recieve the echoed message one byte at a time
    while counter < max_size:
        rcv = sock.recv(1)
        if rcv == read_until:
            if counter != 0:
                break
            else:
                continue
        data += rcv
        counter += 1

    # Get the leftover ">" and " " characters before exiting
    for i in range(2):
        _ = sock.recv(1)

    return data.decode('ascii')


def main():
    args = parse_cli()

    board = f'SM{args.board_number}'

    # Check board serial
    if board not in SM_TO_IPMC:
        raise ValueError(f'Invalid Apollo serial number: {board}')

    # IP address of the IPMC
    HOST=f"192.168.22.{SM_TO_IPMC[board]}"

    # Retrieve and validate the configuration
    config = read_config(args.config_path)
    validate_config(config)
    
    commands = get_commands(config)
    pprint(commands)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # Make the connection
        s.connect((HOST, PORT))
        
        for command in commands:
            print(command)
            output = write_command_and_read_output(s, command)
            print(output)

if __name__ == '__main__':
    main()
