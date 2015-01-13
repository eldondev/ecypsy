import logging, os

logger = logging.getLogger(__name__)

import boto.ec2

configdir = os.path.sep.join([os.path.expanduser("~"), '.ecypsy', ''])
if not os.path.isdir(configdir):
    os.mkdir(configdir)

keypair_name = 'ecypsy_auto'
regions = {}

for region in boto.ec2.regions():
    try:
        if region.name not in regions and region.name not in ['cn-north-1', 'us-gov-west-1']: 
            logger.debug('Connecting to region %s' % region)
            conn =  region.connect()
            regions[region.name] = conn
    except Exception as e:
        logger.warn("Failed to connect to region %s, error %s" % (region, e))

def get_existing_key(region):
    import os
    if os.path.isfile(configdir + '%s.pem' % region):
        with open(configdir + '%s.pem' % region) as keyfile:
            logger.debug('Found existing key for region %s' % str(region))
            return keyfile.read()
    return None

def get_security_group(region):
    connection = regions[region]
    sec_group = connection.get_all_security_groups(filters={'group-name':'ecypsy'}) 
    return sec_group

def get_running_zones():
    zones = []
    for region in regions.keys():
        sec_group = get_security_group(region)
        if sec_group:
            instances = sec_group.pop().instances()
            for instance in instances:
                if not instance.state == 'terminated':
                    global_instances[instance.public_dns_name] = instance 
                    zones += [instance.placement]
    logger.info("Zones that already have instances: %s" % str(zones))
    return zones

def get_running_instances():
    instances = []
    for region in regions.keys():
        sec_group = get_security_group(region)
        if sec_group:
            instances += [instance for instance in sec_group.pop().instances() if not instance.state == 'terminated']
    return instances

def get_candidate_spot_prices(instance_type, exclude_zones):
    spot_prices = []
    zones = {}
    for region in regions.values():
        for zone in region.get_all_zones():
            zones[zone.name] = zone
            if not zone.name in exclude_zones:
                spot_prices += region.get_spot_price_history(instance_type=instance_type, availability_zone=zone.name, max_results=1)
    for spot_price in spot_prices:
        spot_price.availability_zone = zones[spot_price.availability_zone] # Get the real zone instead of just the name
    return spot_prices



