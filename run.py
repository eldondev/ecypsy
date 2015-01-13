import logging
logging.basicConfig()
logger = logging.getLogger("ecypsy")
logger.setLevel(logging.DEBUG)
from ecypsy.region.instances import *
import time
for dns, _ in global_instances.items():
    logger.info("Host %s up" % dns)

