import logging
import json

from nsdtranslator import NSDTranslator

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger('sfeat.py')


def _load_data_from_file(file_object):
    try:
        json_object = json.load(file_object)
        return json_object
    except Exception as e:
        log.exception('Exception loadJsonFile', e)
        raise


class Sf2heat:

    def __init__(self, descriptors_type='superfluidity', parameters=None, input_file=None, output_file=None,
                 ansible_init=False, output_directory=None):
        log.debug("Constructor %s %s %s ", descriptors_type, input_file, output_file)
        self.descriptors_type = descriptors_type
        self.input_file = input_file
        self.input_data = _load_data_from_file(input_file)
        self.output_file = output_file
        self.output_directory = output_directory
        self.parameters = parameters
        self.ansible_init = ansible_init

        return

    def translate(self):
        log.debug("Starts translation process...")
        if self.ansible_init:
            dest_dir = self.output_directory
            nsd_translator = NSDTranslator(self.input_data, dest_dir, {"app_name": 'app_name', "cloud_config_name": 'app_name'})
        else:
            dest_dir = self.output_file
            nsd_translator = NSDTranslator(self.input_data, dest_dir)

        nsd_translator.translate()
        return

if __name__ == '__main__':
    a_game = Sf2heat()
