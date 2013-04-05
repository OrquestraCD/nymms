import json
import time
import logging

from nymms.config import yaml_config
from nymms.channel import Channel

logger = logging.getLogger(__name__)


class YamlNodeBackend(object):
    def __init__(self, path):
        self.path = path

    def get_nodes(self):
        logger.debug("Loading node config from %s" % (self.path))
        return yaml_config.load_config(self.path)


class Scheduler(Channel):
    def __init__(self, node_backend, topic, queue):
        self.node_backend = node_backend
        super(Scheduler, self).__init__(topic, queue)

    def run(self, interval=300):
        while True:
            start = time.time()
            interval = float(interval)
            nodes = self.node_backend.get_nodes()
            for node in nodes:
                task = json.dumps(node)
                logger.debug("Sending task for node '%s'." % (node['name']))
                self.send_task(task)
            real_sleep = interval - (time.time() - start)
            if real_sleep <= 0:
                continue
            logger.debug("Sleeping for %.02f." % (real_sleep))
            time.sleep(real_sleep)
