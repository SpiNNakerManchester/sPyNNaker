from spynnaker.pyNN.utilities.conf import config
from spynnaker.pyNN import exceptions

class FakeHBPPortalMachineProvider(object):

    def __init__(self, n_boards):
        self._ip_addresses = config.get("Machine", "machineName")
        self._bmp_details = config.get("Machine", "bmp_names")
        self._width = 8
        self._height = 8
        if n_boards != 1:
            raise exceptions.InvalidParameterType("Not enough machine size")

    def create(self):
        return

    def wait_until_ready(self):
        return

    def get_machine_info(self):
        connections = {
            "(0, 0)": self._ip_addresses}
        return {'connections': connections,
                'width': self._width,
                'height': self._height,
                'machine_name': "BOB"}

    def destroy(self):
        print "PORTAL DESTROYED!!!!"

    def wait_till_not_ready(self):
        while(True):
            pass
