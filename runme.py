import logging
logging.basicConfig()
logger = logging.getLogger("ecypsy")
logger.setLevel(logging.DEBUG)
from ecypsy.region.instances import *
import time
while True:
    ensure_running_set()
    write_ssh_config(global_instances)
    for dns, _ in global_instances.items():
        logger.info("Host %s up" % dns)
    time.sleep(600)

