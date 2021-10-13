#  AUTHOR: Brad Atkinson
#    DATE: 10/6/2020
# PURPOSE: Configuration file info containing username, password, and IPs

# CONNECTIVITY CONFIGURATIONS
# Update the panorama_ip section with the primary and secondary Panorama 
# IP addresses.

paloalto = {
    'username': '<USERNAME>',
    'password': '<PASSWORD>',
    'key': '<API_KEY>',
    'panorama_ip': ['<IP_ADDRESS1>', '<IP_ADDRESS2>']
    }

# FIREWALL SERIAL NUMBER(S)
# Enter the firewall serial number(s) to be added to Panorama.
#
# Single Serial Number: ['<SERIAL_NUMBER>']
# Multiple Serial Numbers: ['<SERIAL_NUMBER1>', '<SERIAL_NUMBER2>']

serial_number = ['<SERIAL_NUMBER>']