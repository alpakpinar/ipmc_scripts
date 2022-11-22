#!/usr/bin/env python3

import os
import sys
import time
import socket
import argparse
import subprocess


# Check Python version, need at least 3.6
valid_python = sys.version_info.major >= 3 and sys.version_info.minor >= 6 
assert valid_python, "You need Python version >=3.6 to run this script!"


# IPMC information we want to check before any firmware upgrade
IPMC_INFO = {
    "FRU Device Description" : "Builtin FRU Device (ID 0)",
}


def parse_cli():
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--upgrade-file', required=True, help='Path to the .hpm file to be used to update IPMC firmware.')
    parser.add_argument('-s', '--shelf', required=True, help='The shelf IP address where the blades to do the update are located.')
    parser.add_argument('-i', '--ipmb', nargs='*', required=True, help='List of slot IPMB addresses representing the IPMCs to update.')
    args = parser.parse_args()

    # Check that the upgrade file exists
    if not os.path.exists(args.upgrade_file):
        raise IOError(f'Could not find the upgrade file: {args.upgrade_file}')

    # Check if the shelf IP address is valid
    try:
        socket.inet_aton(args.shelf)
    except socket.error:
        raise IOError(f'Invalid IP address for the shelf: {args.shelf}')

    # The slot adresses must be in hex format, i.e. it must start with 0x
    for ipmb in args.ipmb:
        if not ipmb.startswith('0x'):
            raise IOError(f'Invalid slot address given: {ipmb}')

    return args


def get_ipmc_info(shelf_address: str, ipmb_address: str) -> str:
    """Function to retrieve the IPMC information via ipmitool fru command.

    Args:
        shelf_address (str): IP address of the shelf.
        ipmb_address (str): IPMB address for the slot where the IPMC is located.

    Returns:
        Optional[str]: The output of the fru command.
    """
    command = f'ipmitool -H {shelf_address} -P "" -t {ipmb_address} fru'

    # Run the ipmitool fru command to retrieve information
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    stdout, _ = proc.communicate()

    return stdout.decode('latin-1')


def validate_ipmc_info(shelf_address: str, ipmb_address: str) -> bool:
    """Parses the output of fru command and compares it with the IPMC_INFO.

    Args:
        shelf_address (str): IP address of the shelf.
        ipmb_address (str): IPMB address for the slot where the IPMC is located.

    Returns:
        bool: If all values are the same as IPMC_INFO, returns True. Otherwise, returns False.
    """
    # Retrieve the IPMC information using helper function
    try:
        input = get_ipmc_info(shelf_address, ipmb_address)
    except subprocess.SubprocessError as e: 
        print(f'\nFailed to retrieve information from slot: {ipmb_address}, skipping.')
        print(f'Error message: {e.output}')
        return False    

    rows = input.split('\n')

    # Go through the information list and check
    for row in rows:
        temp = row.split(':')
        if len(temp) < 2:
            continue
        field_name = temp[0].strip()
        field_value = temp[1].strip()

        if field_name not in IPMC_INFO:
            continue

        # Check if this information matches the one we're expecting
        if field_value != IPMC_INFO[field_name]:
            print(f'\nWrong information for slot {ipmb_address}')
            print(f'Field name   :  {field_name}')
            print(f'Field value  :  {field_value} (expected {IPMC_INFO[field_name]})')
            print(f'Skipping {ipmb_address}\n')
            return False

    return True


def update_ipmc_firmware(shelf_address: str, ipmb_address: str, upgrade_file: str) -> bool:
    """Function that updates the IPMC firmware.

    Args:
        shelf_address (str): IP address of the shelf.
        ipmb_address (str): IPMB address for the slot where the IPMC is located.
        upgrade_file (str): Path to the upgrade file to be used.
    
    Returns:
        bool: Specifies success or failure for the update operation.
    """
    command = f'ipmitool -H {shelf_address} -P "" -t {ipmb_address} hpm upgrade {upgrade_file}'
    try:
        subprocess.run(command, shell=True, stdout=sys.stdout, stderr=sys.stderr)
    except subprocess.SubprocessError as e: 
        print(f'Failed to update IPMC firmware for slot: {ipmb_address}, skipping.')
        print(f'Error message: {e.output}')
        return False
    
    return True


def activate_ipmc_firmware(shelf_address: str, ipmb_address: str) -> bool:
    """Function that activates the newly installed IPMC firmware.

    Args:
        shelf_address (str): IP address of the shelf.
        ipmb_address (str): IPMB address for the slot where the IPMC is located.
    
    Returns:
        bool: Specifies success or failure for the activation operation.
    """
    command = f'ipmitool -H {shelf_address} -P "" -t {ipmb_address} hpm activate'
    try:
        subprocess.run(command, shell=True, stdout=sys.stdout, stderr=sys.stderr)
    except subprocess.SubprocessError as e: 
        print(f'Failed to activate IPMC firmware for slot: {ipmb_address}, skipping.')
        print(f'Error message: {e.output}')
        return False
    
    return True


def main():
    args = parse_cli()

    for ipmb in args.ipmb:
        # First, check if the information on the IPMC makes sense
        print(f'\nValidating IPMC information for slot: {ipmb}...', end=' ')
        if not validate_ipmc_info(args.shelf, ipmb):
            continue
        print('OK')

        # Then, move on to updating and activating the IPMC firmware for the slot
        print('\nUpdating and activating the IPMC firmware\n')
        print(f'Shelf         : {args.shelf}')
        print(f'Slot          : {ipmb}')
        print(f'Upgrade file  : {os.path.abspath(args.upgrade_file)}')

        if not update_ipmc_firmware(args.shelf, ipmb, args.upgrade_file):
            continue
        
        # Wait 1s between update and activate commands
        time.sleep(1)

        if not activate_ipmc_firmware(args.shelf, ipmb):
            continue


if __name__ == '__main__':
    main()
