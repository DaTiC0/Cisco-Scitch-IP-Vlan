import re
import config
from getpass import getpass
from netmiko import ConnectHandler
from netmiko.ssh_exception import AuthenticationException
# mac = ":".join(["%s" % (mac[i:i+2]) for i in range(0, 12, 2)])

# ON SMALL BUSSIONES SWITCHES SET LENGTH TO 0
# net_connect.send_command('set length 0')

device = {
    'device_type': 'cisco_ios',
    'host': config.core,
    'username': config.username,
    'password': config.password,
    'port': 22,
    'secret': config.secret,
}

def cisco_decorator(func):
    def wrapper(*args, **kwargs):
        print('\nConnecting to switch: {}\nConnection Type: {}'.format(device['host'], device['device_type']))
        try:
            net_connect = ConnectHandler(**device)
        except AuthenticationException as auth:
            print('-'*20)
            print(str(auth))
            print('-'*20)
            device['username'] = input('Enter Username:')
            device['password'] = getpass('Enter Password:')
            device['secret'] = getpass('Enter Enable if Required:')
            net_connect = ConnectHandler(**device)
        # enable
        net_connect.enable()
        prompt = net_connect.find_prompt()
        hostname = prompt.rstrip('>#')
        # print("Searching For {} on {}".format(ip, hostname))

        result = func(net_connect, *args, **kwargs)

        print('Disconnecting from: ' + hostname)
        net_connect.disconnect()

        return result
    
    return wrapper

@cisco_decorator
def core_switch(net_connect, device, ip):
    port = 'Port not found'
    # net_connect = ConnectHandler(**device)
    # net_connect.enable()
    arp = net_connect.send_command('sh ip arp | i {}'.format(ip))

    match = re.search('[0-9A-Fa-f]{4}.[0-9A-Fa-f]{4}.[0-9A-Fa-f]{4}', arp)
    # print(match)
    if match:
        mac = match.group()
        print('Mac addres found: {}'.format(mac))
        table = net_connect.send_command(
            'sh mac address-table address {}'.format(mac))
        # print(table)
        interface = re.search('DYNAMIC\s+(\S+)', table).groups()[0]
        print('On Core Switch Interface: {}'.format(interface))
        print('Serching CDP Neighbours on Interface: {}'.format(interface))
        cdp = net_connect.send_command('sh cdp neighbors {} detail'.format(interface))
        # print(cdp)
        # check if device is on Core Switch
        if cdp:
            device_id = re.search('Device ID: (\S+)', cdp).groups()[0]
            # print(device_id)
            #first find platform
            platform = re.search('PLATFORM: (\S+)', cdp.upper()).groups()[0]
            if platform == 'VMWARE':
                print('PC or server is on ESXI Server')
                # return 0
            elif platform == 'CISCO':
                # Finding Cisco Model for connection type
                switch_model = re.search('PLATFORM: CISCO (\S+)', cdp.upper()).groups()[0]
                # print(switch_model)
                # Get Device Config By model
                if switch_model in config.IOS:
                    device['device_type'] = 'cisco_ios'
                elif switch_model in config.SG:
                    device['device_type'] = 'cisco_s300'

                switch_ip = re.search('IP address: (\S+)', cdp).groups()[0]
                # print(switch_ip)
                print('\nSwitch Found\nIP Address: {}\nmodel: {}\nDevice ID: {}'.format(
                    switch_ip, switch_model, device_id))
                device['host'] = switch_ip
                port = switch(device, ip, mac)
                # print('{} Found on Port: {}'.format(ip, pc))
            else:
                print('Not supported platform')
        else:
            print('Device is on Core Switch Port: ' + interface)
            port = interface
    else:
        print('IP address not found')
    # print('Disconnecting from Core Switch')
    # net_connect.disconnect()

    return port

@cisco_decorator
def switch(net_connect, device, ip, mac):
    # print('Connecting to switch: {}\nConnection Type: {}'.format(
    #     device['host'], device['device_type']))
    # try:
    #     net_connect = ConnectHandler(**device)
    # except AuthenticationException as auth:
    #     print('-'*20)
    #     print(str(auth))
    #     print('-'*20)
    #     username = input('Enter Username:')
    #     password = getpass('Enter Password:')
    #     enable = getpass('Enter Enable if Required:')
    #     device['username'] = username
    #     device['password'] = password
    #     device['secret'] = enable
    #     net_connect = ConnectHandler(**device)
    # # enable
    # net_connect.enable()
    # prompt = net_connect.find_prompt()
    # hostname = prompt.rstrip('>#')
    # print("Searching For {} on {}".format(ip, hostname))
    interface = net_connect.send_command('sh mac address-table address {}'.format(mac))
    port = 'Not Found'
    if device['device_type'] == 'cisco_ios':
        port = re.search('DYNAMIC\s+(\S+)', interface).groups()[0]
    elif device['device_type'] == 'cisco_s300':
        port = re.search('(\S+)\s+dynamic', interface).groups()[0]
    print('{} Found on Port: {}'.format(ip, port))
    # print('Disconnecting from: ' + hostname)
    # net_connect.disconnect()

    return port


def main():
    ip = input('Enter Computer IP:')
    # Get Info 
    port = core_switch(device, ip)
    # Next Chapter

    print('What to do with this PORT: ' + port)

main()
