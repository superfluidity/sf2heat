import logging
import yaml
import json

from hotsyntax.hot_template import HotTemplate
from hotsyntax.hot_resource import HotResource

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger('NSDTranslator')


class NSDTranslator(object):
    """ Invokes translation methods. """

    def __init__(self, nsd_data, output_dir=None):
        super(NSDTranslator, self).__init__()
        self.nsd_descriptors = nsd_data
        self.output_dir = output_dir
        self.hot_template = HotTemplate()
        log.debug('Initialized NSDTranslator')

    def translate(self):
        for vnfd_id in self.nsd_descriptors['vnfd']:
            self._translate_vnf(self.nsd_descriptors['vnfd'][vnfd_id])
        # print self.hot_template.json()
        yml_template = self.hot_template.yaml()
        print yml_template

    def _translate_vnf(self, vnf_data):
        log.debug('_translate_vnf id: ' + vnf_data['vnfdId'])
        for vdu in vnf_data['vdu']:
            self._translate_vdu(vdu, vnf_data)

    def _translate_vdu(self, vdu_data, vnf_data):
        log.debug('_translate_vdu id: %s', vdu_data['vduId'])
        resource_type = self._infer_resource_type(vdu_data, vnf_data)
        log.debug('Resource type: %s', resource_type)
        resource_properties = self._get_properties_vdu(resource_type, vdu_data, vnf_data)
        log.debug('Resource prop: %s', resource_properties)
        new_hot_resource = HotResource(vdu_data['vduId'], resource_type, resource_properties)
        self.hot_template.add_resource(vdu_data['vduId'], new_hot_resource)

    def _infer_resource_type(self, vdu_data, vnf_data):
        log.debug('_infer_resource_type from: %s', vdu_data['vduId'])
        try:
            vnf_metadata = vnf_data['modifiableAttributes']['metadata']
            for meta in vnf_metadata:
                if 'types' in meta:
                    for type in meta['types']:
                        if vdu_data['vduId'] in type:
                            return type[vdu_data['vduId']]
        except Exception as e:
            log.exception('_infer_resource_type exception ' + e)
        return None

    def _get_properties_vdu(self, resource_type, vdu_data, vnf_data):
        log.debug('_get_properties_vdu for %s, from %s', resource_type, vdu_data['vduId'])
        result = {}

        if resource_type == 'OS::Nova::Server':
            vdu_sw_img_dsc = vdu_data['swImageDesc']
            result['image'] = vdu_sw_img_dsc['swImage']
            # OS::Nova::Flavor
            flavor_name = 'flavor_' + vdu_data['vduId']
            result['flavor'] = {'get_resource': flavor_name}
            flavor_res = self._get_nova_flavor(flavor_name, vdu_data, vnf_data)
            self.hot_template.add_resource(flavor_name, flavor_res)
            #  OS::Nova::KeyPair
            key_pair_name = 'key_' + vdu_data['vduId']
            result['key_name'] = {'get_resource': key_pair_name}
            key_pair_res = self._get_nova_key_pair(key_pair_name, vdu_data, vnf_data)
            self.hot_template.add_resource(key_pair_name, key_pair_res)
            if 'intCpd' in vdu_data:
                result['networks'] = []
                for intcpd in vdu_data['intCpd']:
                    net = self._get_network_from_cpd(intcpd, vnf_data)
                    result['networks'].append(net)

        elif resource_type == 'OS::Nova::Router':
            metadatalist = vnf_data['modifiableAttributes']['metadata']
            for metadata in metadatalist:
                if 'properties' in metadata:
                    for prop in metadata['properties']:
                        if vdu_data['vduId'] in prop:
                            meta_prop = dict(pair for d in prop[vdu_data['vduId']] for pair in d.items())
                            result.update(meta_prop)
            if 'intCpd' in vdu_data:
                for intcpd in vdu_data['intCpd']:
                    nri = self._get_neutron_router_interface(vdu_data['vduId'], intcpd, vnf_data)
                    self.hot_template.add_resource('interf_' + vdu_data['vduId'], nri)

        return result

    def _get_network_from_cpd(self, intcpd, vnf_data):
        result = {}
        # FIXME generate port resource o full network resource
        neutron_port_name = 'port_' + intcpd['cpdId']
        result['port'] = {'get_resource': neutron_port_name}
        neutron_port_res = self._get_neutron_port(intcpd, vnf_data)
        self.hot_template.add_resource(neutron_port_name, neutron_port_res)
        return result

    def _get_neutron_router_interface(self, router_id, intcpd, vnf_data):
        resource_type = 'OS::Neutron::RouterInterface'
        resource_prop = {}
        resource_prop['router'] = {'get_resource': router_id}
        neutron_port_name = 'port_' + intcpd['cpdId']
        neutron_port_res = self._get_neutron_port(intcpd, vnf_data)
        self.hot_template.add_resource(neutron_port_name, neutron_port_res)
        resource_prop['port'] = {'get_port': neutron_port_name}
        new_hot_resource = HotResource('interf_' + router_id, resource_type, resource_prop)
        return new_hot_resource

    def _get_neutron_port(self, intcpd, vnf_data):
        resource_type = 'OS::Neutron::Port'
        resource_prop = {}
        name = intcpd['cpdId']
        resource_prop['network'] = name
        resource_prop['network_id'] = {'get_resource': 'FIXME'} #FIXME
        resource_prop['fixed_ips'] = []
        metadata_list = vnf_data['modifiableAttributes']['metadata']
        for metadata in metadata_list:
            if 'CPIPv4FixedIP' in metadata:
                for fixed_ip in metadata['CPIPv4FixedIP']:
                    if name in fixed_ip:
                        resource_prop['fixed_ips'].append({'ip_address': fixed_ip[name]})
            if 'properties' in metadata:
                for prop in metadata['properties']:
                    if name in prop:
                        meta_prop = dict(pair for d in prop[name] for pair in d.items())
                        resource_prop.update(meta_prop)
        if 'addressData' in intcpd:
            for addr in intcpd['addressData']:
                if 'l2AddressData' in addr:
                    resource_prop['mac_address'] = addr['l2AddressData']

        new_hot_resource = HotResource(name, resource_type, resource_prop)
        return new_hot_resource

    def _get_nova_flavor(self, name, vdu_data, vnf_data):
        resource_type = 'OS::Nova::Flavor'
        resource_prop = {}
        resource_prop['flavorid'] = vnf_data['deploymentFlavour'][0]['flavourId']
        resource_prop['name'] = name
        resource_prop['is_public'] = False
        # FIXME trovare valori proprieta' seguenti
        resource_prop['disk'] = 40
        resource_prop['ram'] = 8192
        resource_prop['swap'] = 0
        resource_prop['vcusp'] = 4

        new_hot_resource = HotResource(name, resource_type, resource_prop)
        return new_hot_resource

    def _get_nova_key_pair(self, name, vdu_data, vnf_data):
        resource_type = 'OS::Nova::KeyPair'
        resource_prop = {}
        resource_prop['name'] = name
        for prop in vdu_data['configurableProperties']['additionalVnfcConfigurableProperty']:
            if 'SSHPubKey' in prop:
                resource_prop['public_key'] = prop['SSHPubKey']
                break

        new_hot_resource = HotResource(name, resource_type, resource_prop)
        return new_hot_resource
