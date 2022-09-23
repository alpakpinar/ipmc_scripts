# IPMC Scripts

A couple of scripts to talk to the IPMC on the Apollo Service Module.

## Requirements

**Supported Python version:** >= 3.6

Please make sure that [PyYAML](https://pypi.org/project/PyYAML/) package is installed before running these scripts.

## Configuring the IPMC EEPROM

To update the EEPROM memory on the Service Module, one can use the `configure_ipmc.py` script, which will read the `config/ipmc_config.yaml` configuration file to figure out which values to set and to what. The script will then contact the IPMC via a TCP/IP socket to execute the commands. The script can be run as follows:

```bash
./configure_ipmc.py <SM serial number> -c /path/to/config
```

Note that the `-c` option defaults to `config/ipmc_config.yaml`.

## Updating IPMC FW

To update the IPMC firmware to a new version, one can use the `update_ipmc_fw.py` file. This script needs a couple of things:

* The IP address of the shelf manager for which the IPMC is located
* Path to the `upgrade.hpm` file, which is a build product of the firmware
* The IPMB address of the slot where the IPMC is located (in hex)

The script can be run as follows:

```bash
./update_ipmc_fw.py -u /path/to/upgrade.hpm -s <IP address of the shelf manager> -i <IPMB address of the slot>
```

The script will go on to upload the firmware to the selected IPMC (via it's IPMB address), and then activate the new firmware.