from spynnaker.pyNN.exceptions import InvalidParameterType


class FakeHBPPortalMachineProvider(object):
    __slots__ = ["__bmp_details", "__height", "__ip_addresses", "__width"]

    def __init__(self, n_boards, config):
        self.__ip_addresses = config.get("Machine", "machineName")
        self.__bmp_details = config.get("Machine", "bmp_names")
        self.__width = 8
        self.__height = 8
        if n_boards != 1:
            raise InvalidParameterType("Not enough machine size")

    def create(self):
        return

    def wait_until_ready(self):
        return

    def get_machine_info(self):
        connections = {"(0, 0)": self.__ip_addresses}
        return {'connections': connections,
                'width': self.__width,
                'height': self.__height,
                'machine_name': "BOB"}

    def destroy(self):
        print("PORTAL DESTROYED!")

    def wait_till_not_ready(self):
        while True:
            pass
