import logging
import yaml
import json

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger('HotResource')


class HotResource(object):
    """ Representation of a Resource in HOT template
        for the purpose we consider just some fields
    """
    def __init__(self, name, type, properties):
        #self.name = name
        self.type = str(type)
        self.properties = properties or {}

    def yaml(self):
        return yaml.dump(self.__dict__, None, encoding='utf-8', allow_unicode=False, width=float("inf"))