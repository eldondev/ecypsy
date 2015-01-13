import logging, itertools
logging.basicConfig()
logger = logging.getLogger("ecypsy")
logger.setLevel(logging.DEBUG)
from ecypsy.region.instances import *
print('\n'.join([str((_.status, _.id)) for _ in itertools.chain(*[h.get_all_spot_instance_requests() for h in regions.values()])]))

