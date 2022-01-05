#!/usr/bin/env python3
#
#  AUTHOR: Brad Atkinson
#    DATE: 5/11/2021
# PURPOSE: To perform initial onboarding tasks for new firewall(s)

import sys
import config
from panos import base


def find_active_device():
    """Find Active Device

    Returns:
        pano_ip (str): The IP address of the active Panorama
    """
    print('Finding the active Panorama...')
    pano1_ip = config.paloalto['panorama_ip'][0]
    pano1_conn = connect_device(pano1_ip)
    pano1_results = check_ha_status(pano1_conn)
    pano1_state = process_ha_status(pano1_results)

    pano2_ip = config.paloalto['panorama_ip'][1]
    pano2_conn = connect_device(pano2_ip)
    pano2_results = check_ha_status(pano2_conn)
    pano2_state = process_ha_status(pano2_results)

    active_tuple = ('active', 'active-primary', 'primary-active')
    if pano1_state in active_tuple:
        pano_ip = pano1_ip
        pano_conn = pano1_conn
    elif pano2_state in active_tuple:
        pano_ip = pano2_ip
        pano_conn = pano2_conn
    else:
        print("-- Couldn't find the active Panorama.\n", file=sys.stderr)
        sys.exit(1)

    pano_conn = connect_device(pano_ip)
    results = get_system_info(pano_conn)
    hostname = get_hostname(results)
    print('-- Connected to the active Panorama: {}\n'.format(hostname))
    return pano_conn


def check_ha_status(pano_conn):
    """Check HA Status

    Args:
        pano_conn (PanDevice): A panos object for device

    Returns:
        results (Element): XML results from firewall
    """
    command = ('<show><high-availability><state>'
               '</state></high-availability></show>')
    results = pano_conn.op(cmd=command, cmd_xml=False)
    return results


def process_ha_status(results):
    """Process HA Status

    Args:
        results (Element): XML results from firewall

    Returns:
        ha_status (str): A string containing the HA state
    """
    ha_status = results.find('./result/local-info/state').text
    return ha_status


def connect_device(pano_ip):
    """Connect To Device

    Args:
        pano_ip (str): A string containing the Panorama IP address

    Returns:
        pano_conn (PanDevice): A panos object for device
    """
    username = config.paloalto['username']
    password = config.paloalto['password']
    pano_conn = base.PanDevice.create_from_device(
        hostname=pano_ip,
        api_username=username,
        api_password=password)
    return pano_conn


def get_system_info(pano_conn):
    """Get Show System Info

    Args:
        pano_conn (PanDevice): A panos object for device

    Returns:
        results (Element): XML results from firewall
    """
    results = pano_conn.op(cmd='show system info')
    return results


def get_hostname(results):
    """Get Hostname

    Args:
        results (Element): XML results from firewall

    Returns:
        hostname (str): A string containing the hostname
    """
    hostname = results.find('./result/system/hostname').text
    return hostname


def get_device_serialnum(pano_conn, serial_number):
    """Get Device Serial Number

    Args:
        pano_conn (PanDevice): A panos object for device
        serial_number (str): A string of the firewall serial number

    Returns:
        results (Element): XML results from firewall
    """
    base_xpath = ("/config/mgt-config/devices/entry[@name='{}']"
                  .format(serial_number))
    results = pano_conn.xapi.get(xpath=base_xpath)
    return results


def process_device_serialnum(results):
    """Process Device Serial Number

    Args:
        results (Element): XML results from firewall

    Returns:
        (bool): True if serial number found otherwise False
    """
    try:
        results.find('./result/entry').attrib
        return True
    except AttributeError:
        return False


def add_device_serialnum(pano_conn, serial_number):
    """Add Device Serial Number

    Args:
        pano_conn (PanDevice): A panos object for device
        serial_number (str): A string of the firewall serial number

    Returns:
        results (Element): XML results from firewall
    """
    base_xpath = "/config/mgt-config/devices"
    entry_element = ("<entry name='{}'/>".format(serial_number))
    results = pano_conn.xapi.set(xpath=base_xpath, element=entry_element)
    return results


def process_device_add(results):
    """Process Device Add

    Args:
        results (Element): XML results from firewall

    Returns:
        message (str): A string of commit message(s)
    """
    message = results.find('./msg').text
    return message


def commit_config(pano_conn):
    """Commit Config

    Args:
        pano_conn (PanDevice): A panos object for device
    """
    print('Committing config...')

    admin = config.paloalto['username']
    command = ("<commit><partial><admin><member>{}</member></admin>"
               "<no-template/><no-template-stack/>"
               "<no-log-collector-group/><no-log-collector/>"
               "<shared-object>excluded</shared-object></partial>"
               "<description>Add Firewall Serial Numbers</description>"
               "</commit>".format(admin))
    results = pano_conn.commit(sync=True, cmd=command)

    print('-- Commit Status:\n')
    messages = results.get('messages')
    if isinstance(messages, list):
        for message in messages:
            print('{}\n'.format(message))
    else:
        print(messages)


def main():
    """Function Calls
    """
    pano_conn = find_active_device()
    needs_commit = False

    for serial_number in config.serial_number:
        print('Checking if serial number already entered in Panorama...')
        get_results = get_device_serialnum(pano_conn, serial_number)
        has_serialnum = process_device_serialnum(get_results)

        if has_serialnum:
            print('-- Serial number {} already entered in Panorama\n')
        else:
            print('-- Adding serial number {} to Panorama\n'.format(serial_number))
            add_results = add_device_serialnum(pano_conn, serial_number)
            message = process_device_add(add_results)
            print(message)
            print('\n')
            needs_commit = True

    if needs_commit:
        commit_config(pano_conn)


if __name__ == '__main__':
    main()
