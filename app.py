import re
import credentials
from netmiko import ConnectHandler
from netmiko.ssh_exception import AuthenticationException
# mac = ":".join(["%s" % (mac[i:i+2]) for i in range(0, 12, 2)])

# ON SMALL BUSSIONES SWITCHES SET LENGTH TO 0
#
# net_connect.send_command('set length 0')
#
device = {
    'device_type': 'cisco_ios',
    'host': credentials.core,
    'username': credentials.username,
    'password': credentials.password,
    'port': 22,
    'secret': credentials.secret,
}

# Cisco IOS Switches
IOS = ['CISCO', 'CISCO2921/K9', 'WS-C2960-24TC-S'] # Add Your Models
# Cisco Small Bussiness Switches
SG = ['SG300-10MP', 'SF300-48PP', 'SF300-24PP'] # Add Your Models


def core_switch(device, ip):
    port = 'Port not found'
    net_connect = ConnectHandler(**device)
    net_connect.enable()
    arp = net_connect.send_command('sh ip arp | i {}'.format(ip))

    match = re.search('[0-9A-Fa-f]{4}.[0-9A-Fa-f]{4}.[0-9A-Fa-f]{4}', arp)
    # print(match)
    if match:
        mac = match.group()
        print('Computer Mac addres: {}'.format(mac))
        table = net_connect.send_command(
            'sh mac address-table address {}'.format(mac))
        # print(table)
        interface = re.search('DYNAMIC\s+(\S+)', table).groups()[0]
        print('Core Switch Interface: {}'.format(interface))
        print('Serching CDP Neighbours on Interface: {}'.format(interface))
        cdp = net_connect.send_command(
            'sh cdp neighbors {} detail'.format(interface))
        print(cdp)
        # check if device is on Core Switch
        if cdp:
            switch_ip = re.search('IP address: (\S+)', cdp).groups()[0]
            print(switch_ip)
            # Finding Cisco Model for connection type
            switch_model = re.search('PLATFORM: CISCO (\S+)', cdp.upper()).groups()[0]
            print(switch_model)
            if switch_model in IOS:  # ამ ტიპის მოდელები
                device['device_type'] = 'cisco_ios'
            elif switch_model in SG:  # ამ ტიპის მოდელები
                device['device_type'] = 'cisco_s300'
            print('Switch Found\nIP Address: {}\nmodel: {}'.format(
                switch_ip, switch_model))
            device['host'] = switch_ip
            port = switch(device, ip, mac)
            # print('{} Found on Port: {}'.format(ip, pc))

        else:
            print('Device is on Core Switch Port: ' + interface)
            port = interface
    else:
        print('IP address not found')
    print('Disconnecting from Core Switch')
    net_connect.disconnect()
    
    return port


def switch(device, ip, mac):
    print('Connecting to switch: {}\nConnection Type: {}'.format(
        device['host'], device['device_type']))
    try:
        net_connect = ConnectHandler(**device)
    except AuthenticationException as auth:
        print('-'*20)
        print(str(auth))
        print('-'*20)
        username = input('Enter Username:')
        password = input('Enter Password:')
        enable = input('Enter Enable if Required:')
        device['username'] = username
        device['password'] = password
        device['secret'] = enable
        net_connect = ConnectHandler(**device)
    # enable
    net_connect.enable()
    prompt = net_connect.find_prompt()
    hostname = prompt.rstrip('>#')
    print("Searching For {} on {}".format(ip, hostname))
    interface = net_connect.send_command(
        'sh mac address-table address {}'.format(mac))
    port = 'Not Found'
    if device['device_type'] == 'cisco_ios':
        port = re.search('DYNAMIC\s+(\S+)', interface).groups()[0]
    elif device['device_type'] == 'cisco_s300':
        port = re.search('(\S+)\s+dynamic', interface).groups()[0]
    print('{} Found on Port: {}'.format(ip, port))
    print('Disconnecting from: ' + hostname)
    net_connect.disconnect()

    return port


def main():
    ip = input('Enter Computer IP:')
    # print('Enter Core Switch Information')
    # sw_ip = input('Enter IP:')
    # username = input('Enter Username:')
    # password = input('Enter Password:')
    # enable = input('Enter Enable:')
    # device['username'] = sw_ip
    # device['username'] = username
    # device['password'] = password
    # device['secret'] = enable

    port = core_switch(device, ip)
    # Next Chapter
    print('What to do with this PORT: ' + port)

main()
