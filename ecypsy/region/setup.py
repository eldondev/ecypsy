import boto.ec2
import logging

logger = logging.getLogger(__name__)

import os

from ecypsy.region.inspect import *

username = 'core'

def cancel_existing_spot_requests(connection):
    connection.get_all_zones()
    sec_group = connection.get_all_security_groups(filters={'group-name':'ecypsy'}) 
    if sec_group:
        group_id = sec_group.pop().id
        requests = connection.get_all_spot_instance_requests(filters={'launch.group-id':group_id}) # Errors out if no permissions to connect
        for spot_instance_request in requests:
            spot_instance_request.cancel()

def setup(region):
    logger.debug('Setting up region %s' % str(region))
    key = get_existing_key(region)
    if key is None:
        logger.debug('Creating key in region %s' % str(region))
        setup_key(region)
    security_group = get_security_group(region)
    if not security_group:
        logger.debug('Creating security group in region %s' % str(region))
        initialize_security_group(region)
    else:
        if security_group:
            security_group = security_group.pop()
            logger.debug('Found security group for region %s' % str(region))
            check_port_authorized(security_group)
            check_port_authorized(security_group,'2200')
    return (key, security_group)

def setup_key(region):
    connection = regions[region]
    key = connection.get_key_pair(keypair_name)
    if key:
       logger.warn('Deleting unknown existing key for region %s' % str(region))
       key.delete()
    key_pair = connection.create_key_pair(keypair_name)
    with open(configdir + '%s.pem' % region, 'w') as keyfile:
        keyfile.write(key_pair.material)
    return key_pair.material

def check_port_authorized(sec_group, port='22'):
    ssh_rule = [rule for rule in sec_group.rules if rule.from_port == port]
    if ssh_rule:
        ssh_rule = ssh_rule.pop()
        if '0.0.0.0/0' in [str(source) for source in ssh_rule.grants]:
            return
    logger.debug('Authorizing ssh for region %s' % sec_group.region)
    sec_group.authorize('tcp',port,port,'0.0.0.0/0')

def initialize_security_group(region):
    connection = regions[region]
    logger.debug('Creating security group for region %s' % str(region))
    sec_group = connection.create_security_group('ecypsy', 'Security group created by ecypsy')
    check_port_authorized(sec_group)

def write_ssh_config(instances):
    with open(configdir + 'config', 'w') as keyfile:
        for host, instance in instances.items():
            keyfile.write("Host %s\n" % instance.placement)
            keyfile.write("    IdentityFile %s%s.pem\n" % (configdir, instance.region.name))
            os.chmod("%s%s.pem" % (configdir, instance.region.name), 0o600)
            keyfile.write("    Hostname %s\n" % instance.public_dns_name)
            keyfile.write("    User %s\n\n" % username)

    
