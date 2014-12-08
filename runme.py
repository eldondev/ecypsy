import logging
logging.basicConfig()
logger = logging.getLogger("ecypsy")
logger.setLevel(logging.INFO)
from ecypsy.region.instances import *
import time
while True:
    ensure_running_set()
    time.sleep(300)

