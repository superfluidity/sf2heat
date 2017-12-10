import logging
import yaml
import json

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger('HotTemplate')


class HotTemplate(object):
    """ Representation of a HOT template"""
    def __init__(self):
        self.heat_template_version = '2017-02-24'
        self.resources = {}
        self.outputs = {}
        self.parameters = {}
        self.description = ''
        log.debug('Initialized HotTemplate')

    def add_resource(self, res_id, new_resource):
        log.debug('Add new resource '+ res_id)
        self.resources[str(res_id)] = new_resource

    def add_parameter(self, param_id, new_parameter):
        self.parameters[str(param_id)] = new_parameter

    def set_description(self, description):
        self.description = str(description)

    def export_yaml(self, dstfile):
        str_json = self.toJSON()
        yaml.safe_dump(json.loads(str_json), dstfile, default_flow_style=False)

    def toYaml(self):
        str_json = self.toJSON()
        return yaml.safe_dump(json.loads(str_json), default_flow_style=False)

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__,
                          sort_keys=True, indent=4)
