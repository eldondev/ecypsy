import boto.ec2
import logging

logger = logging.getLogger(__name__)
regions = dict([(region.name, region) for region in boto.ec2.regions()])
connections = {}

def get_connection(region):
    if region.name not in connections: 
        logger.debug('Connecting to region %s' % str(region))
        connections[region.name] = region.connect()
    return connections[region.name]
  
        
def setup(region):
    logger.debug('Setting up region %s' % str(region))
    key = get_existing_key(region)
    if key is None:
        logger.debug('Creating key in region %s' % str(region))
        key = setup_key(region)
    security_group = get_security_group(region)
    if not security_group:
        logger.debug('Creating security group in region %s' % str(region))
        initialize_security_group(region)
    return key

def get_existing_key(region):
    import os
    if os.path.isfile('/root/%s.pem' % region.name):
        with open('/root/%s.pem' % region.name) as keyfile:
            logger.debug('Found existing key for region %s' % str(region))
            return keyfile.read()
    return None

def setup_key(region):
    connection = get_connection(region)
    key = connection.get_key_pair('boto-auto')
    if key:
       logger.debug('Deleting unknown existing key for region %s' % str(region))
       key.delete()
    key_pair = connection.create_key_pair('boto_auto')
    with open('/root/%s.pem' % region.name, 'w') as keyfile:
        keyfile.write(key_pair.material)
    return key_pair.material

def get_security_group(region):
    connection = get_connection(region)
    sec_group = [group for group in connection.get_all_security_groups() if group.name == 'boto']
    if sec_group:
        sec_group = sec_group.pop()
        logger.debug('Found security group for region %s' % str(region))
        check_ssh_authorized(sec_group)
    return sec_group

def check_ssh_authorized(sec_group):
    ssh_rule = [rule for rule in sec_group.rules if rule.from_port == '22']
    if ssh_rule:
        ssh_rule = ssh_rule.pop()
        if '0.0.0.0/0' in [str(source) for source in ssh_rule.grants]:
            return
    logger.debug('Authorizing ssh for region %s' % sec_group.region)
    sec_group.authorize('tcp','22','22','0.0.0.0/0')
            
def initialize_security_group(region):
    connection = get_connection(region)
    logger.debug('Creating security group for region %s' % str(region))
    sec_group = connection.create_security_group('boto', 'Security group created by boto')
    check_ssh_authorized(sec_group)


