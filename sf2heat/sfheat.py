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


class Sfheat:

    # def __init__(self, descriptors_type='superfluidity', parameters=None, input_data={}, output_file=None):
    #     log.debug("Constructor %s %s %s ", descriptors_type, input_data, output_file)
    #     self.descriptors_type = descriptors_type
    #     self.input_file = None
    #     self.input_data = input_data
    #     self.output_file = output_file
    #     self.parameters = parameters

    def __init__(self, descriptors_type='superfluidity', parameters=None, input_file=None, output_file=None):
        log.debug("Constructor %s %s %s ", descriptors_type, input_file, output_file)
        self.descriptors_type = descriptors_type
        self.input_file = input_file
        self.input_data = _load_data_from_file(input_file)
        self.output_file = output_file
        self.parameters = parameters

        return

    def translate(self):
        log.debug("Starts translation process...")
        nsd_translator = NSDTranslator(self.input_data, self.output_file)
        nsd_translator.translate()
        return

if __name__ == '__main__':
    a_game = Sfheat()
