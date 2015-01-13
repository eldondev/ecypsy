import boto.ec2
import logging

from ecypsy.region.setup import *

logger = logging.getLogger(__name__)

coreos_url = "http://stable.release.core-os.net/amd64-usr/current/coreos_production_ami_all.json"
image_ids = {}
global_instances = {}
def get_image_ids():
    from urllib.request import urlopen
    from json import loads
    blob = urlopen(coreos_url).readall().decode()[8:]
    for image in loads(blob):
        image_ids[image['name']] = image['pv']
    
get_image_ids()

def ensure_running_set(instance_type='t1.micro', count=3, margin=0.0002):
    current_zones = get_running_zones()
    new_instance_count = count - len(current_zones)
    new_zone_prices = find_cheapest_zones(instance_type,new_instance_count, current_zones) 
    for price in new_zone_prices:
        zone = price.availability_zone
        key, sec_group = setup(zone.region.name)
        launch_instance(zone, key, sec_group, price, margin)

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


def get_most_distributed_zones_for_price(spot_prices, count, running_zones):
    spot_prices.sort(key=lambda spot_price: spot_price.price)
    max_price = spot_prices[count-1].price
    prices_less_than_max_price = list(filter(lambda spot_price: spot_price.price <= max_price, spot_prices))
    logger.info("Found %s prices less than max price %s" % (len(prices_less_than_max_price), max_price))
    running_zones = running_zones + [] # Lazy programmer list copy
    selected = set()
    for price in prices_less_than_max_price:
        if price.availability_zone.region_name not in '\n'.join(running_zones):
            selected.add(price)
            running_zones += [price.availability_zone.name]
    while len(selected) < count: # We didn't have enough different regions, just fill us up
        selected.add(prices_less_than_max_price.pop())
    return list(selected)[:count]
    
def find_cheapest_zones(instance_type, count, running_zones=[]):
    if count < 1:
        return []
    spot_prices = get_candidate_spot_prices(instance_type, running_zones)
    cheap_zone_prices = get_most_distributed_zones_for_price(spot_prices, count, running_zones)
    logger.info("Picking cheap zones for new instances: %s" % str([(price.availability_zone, price.price) for price in cheap_zone_prices]))
    return cheap_zone_prices # Give us zone objects from zone names

def launch_instance(zone, key, sec_group, price, margin):
    logger.info("Launching new instance in zone %s" % str(zone))
    with open(configdir + 'user_data', 'rb') as user_data_file:
        user_data=user_data_file.read()
    regions[zone.region.name].request_spot_instances(instance_type=price.instance_type, price=(price.price + margin), placement = zone.name, security_groups=[sec_group.name], key_name=keypair_name, image_id=image_ids[zone.region.name],user_data=user_data)
    
