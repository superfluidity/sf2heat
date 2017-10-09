import logging

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger('sfeat.py')


class Sfheat:

    def __init__(self, descriptors_type='superfluidity', parameters=None, input_file=None, output_file=None):
        log.debug("Constructor %s %s %s ", descriptors_type, input_file, output_file)
        self.descriptors_type = descriptors_type
        self.input_file = input_file
        self.output_file = output_file

        self.parameters = parameters

        pass

    def translate(self):
        return

if __name__ == '__main__':
    a_game = Sfheat()
