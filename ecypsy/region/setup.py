import boto.ec2
import logging

logger = logging.getLogger(__name__)

import os
configdir = os.path.sep.join([os.path.expanduser("~"), '.ecypsy', ''])
if not os.path.isdir(configdir):
    os.mkdir(configdir)

keypair_name = 'ecypsy_auto'

def cancel_existing_spot_requests(connection):
    connection.get_all_zones()
    sec_group = connection.get_all_security_groups(filters={'group-name':'ecypsy'}) 
    if sec_group:
        group_id = sec_group.pop().id
        requests = connection.get_all_spot_instance_requests(filters={'launch.group-id':group_id}) # Errors out if no permissions to connect
        for spot_instance_request in requests:
            spot_instance_request.cancel()


regions = {}
for region in boto.ec2.regions():
    try:
        if region.name not in regions and region.name not in ['cn-north-1', 'us-gov-west-1']: 
            logger.debug('Connecting to region %s' % region)
            conn =  region.connect()
            cancel_existing_spot_requests(conn) # errors out if no permissions to connect
            regions[region.name] = conn
    except Exception as e:
        logger.warn("Failed to connect to region %s, error %s" % (region, e))
        
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
    return (key, security_group)

def get_existing_key(region):
    import os
    if os.path.isfile(configdir + '%s.pem' % region):
        with open(configdir + '%s.pem' % region) as keyfile:
            logger.debug('Found existing key for region %s' % str(region))
            return keyfile.read()
    return None

def setup_key(region):
    connection = regions[region]
    key = connection.get_key_pair(keypair_name)
    if key:
       logger.warn('Deleting unknown existing key for region %s' % str(region))
       key.delete()
    key_pair = connection.create_key_pair(keypair_name)
    with open(configdir + '%s.pem' % region, 'w') as keyfile:
        keyfile.write(key_pair.material)
    return key.material

def get_security_group(region, authorize=True):
    connection = regions[region]
    sec_group = connection.get_all_security_groups(filters={'group-name':'ecypsy'}) 
    if sec_group and authorize:
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
    connection = regions[region]
    logger.debug('Creating security group for region %s' % str(region))
    sec_group = connection.create_security_group('ecypsy', 'Security group created by ecypsy')
    check_ssh_authorized(sec_group)


