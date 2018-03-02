# -*- coding: utf-8 -*-
###
# (C) Copyright (2012-2017) Hewlett Packard Enterprise Development LP
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
###

from pprint import pprint
import re
from hpOneView.oneview_client import OneViewClient
from hpOneView.exceptions import HPOneViewException
from config_loader import try_load_from_file

config = {
    "ip": "<oneview_ip>",
    "credentials": {
        "userName": "<username>",
        "password": "<password>"
    }
}

# Try load config from a file (if there is a config file)
config = try_load_from_file(config)

options = {
    "hostname": config['storage_system_hostname'],
    "username": config['storage_system_username'],
    "password": config['storage_system_password'],
    "family": "StoreServ"
}

oneview_client = OneViewClient(config)

# Add and update storage system for management
storage_system = oneview_client.storage_systems.add(options)
print("\nAdded storage system '%s'.\n   uri = '%s'" %
      (storage_system['name'], storage_system['uri']))         
storage_system['deviceSpecificAttributes']['managedDomain'] = storage_system['deviceSpecificAttributes']['discoveredDomains'][0]
storage_system = oneview_client.storage_systems.update(storage_system)
print("\nUpdated 'managedDomain' to '{}' so storage system can be managed".format(
storage_system['deviceSpecificAttributes']['managedDomain']))       

# Add storage pool to be managed
try:
    print("\nAdd first storage pool from unmanaged storage pools to be managed")
    if storage_system['deviceSpecificAttributes']['discoveredPools'] != None:
        for pool in storage_system['deviceSpecificAttributes']['discoveredPools']:        
            if pool['domain'] == storage_system['deviceSpecificAttributes']['managedDomain']:
                pool_to_manage = pool                
            storage_system['deviceSpecificAttributes']['managedPools'] = [{
                "type": pool_to_manage['type'],
                "domain": pool_to_manage['type'],
                "name": pool_to_manage['name'],
                "deviceType": pool_to_manage['deviceType']
            }]
            storage_system = oneview_client.storage_systems.update(storage_system)              
            print("\nManaged storage pool '{}' at uri: '{}'".format(storage_system['deviceSpecificAttributes'][
                'managedPools'][0]['name'], storage_system['deviceSpecificAttributes']['managedPools'][0]['uri']))
            break                  
except HPOneViewException as e:
    print(e.msg)        

# Get all managed storage systems
print("\nGet all managed storage systems")
storage_systems_all = oneview_client.storage_systems.get_all()
for ss in storage_systems_all:
    print("   '{}' at uri: '{}'".format(ss['name'], ss['uri']))

# Get maximum of 5 storage systems which belong to model of type 'HP_3PAR
# 7200', sorted by freeCapacity in descending order.
print(
    "Get maximum of 5 storage systems which belong to model of type 'HP_3PAR 7200,' sorted by freeCapacity in "
    "descending order.")
filter = 'model=HP_3PAR 7200'
storage_systems_filtered = oneview_client.storage_systems.get_all(
    0, 5, filter="\"'name'='ThreePAR-2'\"", sort='freeCapacity:desc')
for ss in storage_systems_filtered:
    print("   '{}' at uri: '{}'".format(ss['name'], ss['uri']))
if not storage_systems_filtered:
    print("   No storage systems matching parameters")

# Get the list of supported host types
print("\nGet supported host types")
support_host_types = oneview_client.storage_systems.get_host_types()
pprint(support_host_types)

# Get a list of storage pools
print("\nGet a list of storage pools managed by storage system")
storage_pools = oneview_client.storage_systems.get_storage_pools(
    storage_system['uri'])
pprint(storage_pools)

# Get a specified storage system by id
try:
    storage_system_by_id = oneview_client.storage_systems.get('TXQ1010307')
    print("\nGot storage system by id 'TXQ1010307' at uri '{}'".format(
        storage_system_by_id['uri']))
except HPOneViewException as e:
    print(e.msg)

# Add managed ports
ports_to_manage = []
for port in storage_system['ports']:
    if port['actualSanUri'] != "unknown":        
        port_to_manage = {
            "type": port['type'],
            "name": port['name'],           
            "expectedNetworkUri": '/rest/fc-networks/5c942011-c7bc-42f2-a52a-3d471f01f2c6',            
            "actualSanUri": port['actualSanUri'],
            "expectedSanUri": port['expectedSanUri'],
            "mode": 'Managed',
            "groupName": port['groupName'],
            "deviceSpecificAttributes": port['deviceSpecificAttributes'],
            "protocolType": port['protocolType'],
            "label": port['label'],
            "id": port['id']
        }
        ports_to_manage.append(port_to_manage)
storage_system['ports'] = ports_to_manage
storage_system = oneview_client.storage_systems.update(storage_system)
print("\nSuccessfully added ports to be managed")

if oneview_client.api_version <= 300:
    # Get managed ports for specified storage system
    print("\nGet all managed ports for storage system at uri '{}'".format(
        storage_system['uri']))
    managed_ports = oneview_client.storage_systems.get_managed_ports(
        storage_system['uri'])
    for port in managed_ports['members']:
        print("   '{}' at uri: {}".format(port['name'], port['uri']))

    # Get managed target port for specified storage system
    print("\nGet managed port by uri")
    managed_port_by_uri = oneview_client.storage_systems.get_managed_ports(
        storage_system['uri'], storage_system['managedPorts'][0]['uri'])
    print("   '{}' at uri: {}".format(
        managed_port_by_uri['name'], managed_port_by_uri['uri']))

    # Get managed target port for specified storage system by id
    try:
        port_id = re.sub("/rest/storage-systems/TXQ1010307/managedPorts/",
                         '', storage_system['managedPorts'][0]['uri'])
        print("\nGet managed port by id: '{}'".format(port_id))
        managed_port_by_id = oneview_client.storage_systems.get_managed_ports(
            'TXQ1010307', port_id)
        print("   '{}' at uri: {}".format(
            managed_port_by_id['name'], managed_port_by_id['uri']))
    except HPOneViewException as e:
        print(e.msg)

if oneview_client.api_version >= 500:
    # Get managed target port for specified storage system
    print("\nGet all reachable port managed by the appliance")
    reachable_port = oneview_client.storage_systems.get_reachable_ports(
       storage_system['uri'])
    print("   '{}' at uri: {}".format(
        reachable_port['members'][0]['name'], reachable_port['members'][0]['expectedNetworkUri']))

    # Get all reachable storage ports connected to the set of expected network URIs
    print("\nGet reachable_port by uri")
    reachable_port_by_uri = oneview_client.storage_systems.get_reachable_ports(
       storage_system['uri'], networks=reachable_port['members'][0]['reachableNetworks'])
    print("   '{}' at uri: {}".format(
        reachable_port_by_uri['members'][0]['reachableNetworks'], reachable_port_by_uri['uri']))

    print("\nGet templates related to a storage systems")
    templates = oneview_client.storage_systems.get_templates(
       storage_system['uri'])
    print("   '{}' at uri: {}".format(
        templates['members'][0]['name'], templates['members'][0]['uri']))

# Remove storage system
print("\nRemove storage system")
oneview_client.storage_systems.remove(storage_system)
print("   Done.")
