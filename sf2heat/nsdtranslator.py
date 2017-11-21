import logging
import yaml
from hotsyntax.hot_template import HotTemplate
from hotsyntax.hot_resource import HotResource
import os

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
        if self.output_dir is not None:
            dstfile = open(self.output_dir, 'w') if isinstance(self.output_dir, str) else self.output_dir
            yaml.dump(self.hot_template, dstfile, default_flow_style=False, explicit_start=True)
        else:
            print yaml.dump(self.hot_template, default_flow_style=False, explicit_start=True)

    def _translate_vnf(self, vnf_data):
        log.debug('_translate_vnf id: ' + vnf_data['vnfdId'])
        for vdu in vnf_data['vdu']:
            self._translate_vdu(vdu, vnf_data)
        for intVl in vnf_data['intVirtualLinkDesc']:
            self._translate_intVl(intVl, vnf_data)

    def _translate_vdu(self, vdu_data, vnf_data):
        log.debug('_translate_vdu id: %s', vdu_data['vduId'])
        resource_type = self._infer_resource_type(vdu_data['vduId'], vnf_data)
        log.debug('Resource type: %s', resource_type)
        resource_properties = self._get_properties_vdu(resource_type, vdu_data, vnf_data)
        log.debug('Resource prop: %s', resource_properties)
        new_hot_resource = HotResource(vdu_data['vduId'], resource_type, resource_properties)
        self.hot_template.add_resource(vdu_data['vduId'], new_hot_resource)

    def _translate_vnfExtCpd(self, extCpd, vnf_data):
        log.debug('_translate_vnfExtCpd id: %s', extCpd['cpdId'])
        resource_type = self._infer_resource_type(extCpd['cpdId'], vnf_data)
        log.debug('Resource type: %s', resource_type)
        new_hot_resource = self._get_neutron_provider_net(extCpd, vnf_data)
        return new_hot_resource

    def _translate_intVl(self, intVl, vnf_data):
        log.debug('_translate_intVl id: %s', intVl['virtualLinkDescId'])
        # find and get properties for subnet
        metadata_list = vnf_data['modifiableAttributes']['metadata']
        for metadata in metadata_list:
            if 'CPIPv4CIDR' in metadata:
                for prop in metadata['CPIPv4CIDR']:
                    if intVl['virtualLinkDescId'] in prop:
                        for k, cidr in enumerate(prop[intVl['virtualLinkDescId']]):
                            subnet_name = 'subnet_'+intVl['virtualLinkDescId']+'_' + str(k)
                            sub_pro = {'cidr': cidr['cidr'], 'network': intVl['virtualLinkDescId']}
                            neutron_subnet = self._get_subnet(subnet_name, sub_pro, vnf_data)
                            self.hot_template.add_resource(subnet_name, neutron_subnet)

    @staticmethod
    def _infer_resource_type(element_id, vnf_data):
        log.debug('_infer_resource_type from: %s', element_id)
        try:
            vnf_metadata = vnf_data['modifiableAttributes']['metadata']
            for meta in vnf_metadata:
                if 'types' in meta:
                    for type in meta['types']:
                        if element_id in type:
                            return type[element_id]
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

        elif resource_type == 'OS::Neutron::Router':
            meta_prop = self._get_properties_from_metadata(vdu_data['vduId'], 'properties', vnf_data)
            result.update(meta_prop)
            if 'intCpd' in vdu_data:
                for intcpd in vdu_data['intCpd']:
                    nri = self._get_neutron_router_interface(vdu_data['vduId'], intcpd, vnf_data)
                    self.hot_template.add_resource('interf_' + intcpd['cpdId'], nri)

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
        resource_prop = {'router': {'get_resource': router_id}}
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
        network_name = intcpd['intVirtualLinkDesc']

        extCpd = self._isIntCpd_conn_extCpd(intcpd, vnf_data)
        if extCpd:
            neutron_elem = self._translate_vnfExtCpd(extCpd, vnf_data)
        else:
            neutron_elem = self._get_neutron_net(network_name, vnf_data)
        self.hot_template.add_resource(network_name, neutron_elem)
        resource_prop['network'] = {'get_resource': network_name}
        metadata_list = vnf_data['modifiableAttributes']['metadata']
        for metadata in metadata_list:
            if 'CPIPv4FixedIP' in metadata:
                for index, fixed_ip in enumerate(metadata['CPIPv4FixedIP']):

                    if name in fixed_ip:
                        if 'fixed_ips' not in resource_prop:
                            resource_prop['fixed_ips'] = []
                        resource_prop['fixed_ips'].append({'ip_address': fixed_ip[name]})
                        #print "SUBNET for cpid:", name, network_name
                        subnet_name = 'subnet_' + name + '_' + str(index)
                        #neutron_subnet = self._get_port_subnet(subnet_name, intcpd, vnf_data)
                        #self.hot_template.add_resource(subnet_name, neutron_subnet)
            if 'properties' in metadata:
                for prop in metadata['properties']:
                    if name in prop:
                        meta_prop = dict(pair for d in prop[name] for pair in d.items())
                        resource_prop.update(meta_prop)
        if 'addressData' in intcpd:
            for addr in intcpd['addressData']:
                if 'l2AddressData' in addr:
                    resource_prop['mac_address'] = addr['l2AddressData']
                if 'l3AddressData' in addr and addr['l3AddressData']['floatingIpActivated']:
                    float_name = name + "_floating_ip"
                    neutron_floating_ip = self. _get_floating_ip(float_name, intcpd, vnf_data)
                    self.hot_template.add_resource(float_name, neutron_floating_ip)

        new_hot_resource = HotResource(name, resource_type, resource_prop)
        return new_hot_resource

    def _get_floating_ip(self, float_name, intcpd, vnf_data):
        resource_type = 'OS::Nova::FloatingIP'
        resource_prop = {'port_id': {'get_resource': intcpd['cpdId']}}
        meta_float_ip = self._get_properties_from_metadata(intcpd['cpdId'], 'CPIPv4FloatingIP', vnf_data)
        resource_prop.update({'floating_ip_address': meta_float_ip['CPIPv4FloatingIP']})
        meta_prop = self._get_properties_from_metadata(intcpd['cpdId'], 'properties', vnf_data)
        resource_prop.update(meta_prop)
        new_hot_resource = HotResource(float_name, resource_type, resource_prop)
        return new_hot_resource

    def _get_nova_flavor(self, name, vdu_data, vnf_data):
        resource_type = 'OS::Nova::Flavor'
        resource_prop = {'flavorid': vnf_data['deploymentFlavour'][0]['flavourId'], 'name': name, 'is_public': False}
        # virtualMemory and virtualCpu properties
        if 'virtualComputeDesc' in vdu_data and vdu_data['virtualComputeDesc'] is not None:
            for vcd in vnf_data['virtualComputeDesc']:
                if vcd['virtualComputeDescId'] == vdu_data['virtualComputeDesc']:
                    resource_prop['ram'] = vcd['virtualMemory']['virtualMemSize']
                    resource_prop['vcpus'] = vcd['virtualCpu']['numVirtualCpu']
        # virtualStorageDesc
        if 'virtualStorageDesc' in vdu_data and vdu_data['virtualStorageDesc'] is not None:
            for vsd in vnf_data['virtualStorageDesc']:
                if vsd['id'] == vdu_data['virtualStorageDesc']:
                    resource_prop['disk'] = vsd['sizeOfStorage']
                    resource_prop['swap'] = 0
        new_hot_resource = HotResource(name, resource_type, resource_prop)
        return new_hot_resource

    def _get_nova_key_pair(self, name, vdu_data, vnf_data):
        resource_type = 'OS::Nova::KeyPair'
        resource_prop = {'name': name}
        for prop in vdu_data['configurableProperties']['additionalVnfcConfigurableProperty']:
            if 'SSHPubKey' in prop:
                resource_prop['public_key'] = prop['SSHPubKey']
                break
        new_hot_resource = HotResource(name, resource_type, resource_prop)
        return new_hot_resource

    def _get_subnet(self, subnet_name, prop, vnf_data):
        resource_type = 'OS::Neutron::Subnet'
        resource_prop = {'name': subnet_name, 'network': {'get_resource': prop['network']}, 'cidr': prop['cidr']}
        new_hot_resource = HotResource(subnet_name, resource_type, resource_prop)
        return new_hot_resource

    def _get_neutron_net(self, name, vnf_data):
        resource_type = 'OS::Neutron::Net'
        resource_prop = {'name': name}
        new_hot_resource = HotResource(name, resource_type, resource_prop)
        return new_hot_resource

    def _get_neutron_provider_net(self, ext_cpd, vnf_data):
        resource_type = 'OS::Neutron::ProviderNet'
        resource_prop = {'name': ext_cpd['intVirtualLinkDesc']}
        meta_pro = self._get_properties_from_metadata(ext_cpd['cpdId'], 'properties', vnf_data)
        resource_prop.update(meta_pro)
        new_hot_resource = HotResource(ext_cpd['intVirtualLinkDesc'], resource_type, resource_prop)
        return new_hot_resource

    @staticmethod
    def _get_properties_from_metadata(element_id, meta_name, vnf_data):
        metadata_list = vnf_data['modifiableAttributes']['metadata']
        for metadata in metadata_list:
            if meta_name in metadata:
                for prop in metadata[meta_name]:
                    if element_id in prop:
                        if isinstance(prop[element_id], list):
                            meta_prop = dict(pair for d in prop[element_id] for pair in d.items())
                            return meta_prop
                        else:
                            return {meta_name: prop[element_id]}
        return {}

    @staticmethod
    def _isIntCpd_conn_extCpd(intcpd, vnf_data):
        intVirtualLinkDesc = intcpd['intVirtualLinkDesc']
        for extCpd in vnf_data['vnfExtCpd']:
            if extCpd['intVirtualLinkDesc'] == intVirtualLinkDesc:
                return extCpd
        return None

    @staticmethod
    def makedir_p(directory):
        """makedir_p(path)

        Works like mkdirs, except that check if the leaf exist.

        """
        if not os.path.isdir(directory):
            os.makedirs(directory)
