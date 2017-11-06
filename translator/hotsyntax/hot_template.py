import logging
import yaml
import json

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger('HotTemplate')


class HotTemplate(object):
    """ Representation of a HOT template"""
    def __init__(self):
        self.resources = {}
        self.outputs = {}
        self.parameters = {}
        self.description = ''
        log.debug('Initialized HotTemplate')

    def add_resource(self, res_id, new_resource):
        log.debug('Add new resource '+ res_id)
        self.resources[res_id] = new_resource

    def add_parameter(self, param_id, new_parameter):
        self.parameters[param_id] = new_parameter

    def set_description(self, description):
        self.description = description

    def yaml(self):
        return yaml.dump(self.__dict__, None, encoding='utf-8', allow_unicode=False )

