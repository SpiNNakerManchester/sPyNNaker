from pacman.model.decorators import overrides

from spynnaker.pyNN.external_devices_models import AbstractEthernetSensor
from .push_bot_translator import PushBotTranslator
from .push_bot_wifi_connection import get_pushbot_wifi_connection
from .push_bot_retina_connection import PushBotRetinaConnection
from spynnaker.pyNN.external_devices_models.push_bot \
    import AbstractPushBotRetinaDevice


class PushBotEthernetRetinaDevice(
        AbstractPushBotRetinaDevice, AbstractEthernetSensor):

    def __init__(
            self, protocol, resolution, pushbot_ip_address, pushbot_port=56000,
            injector_port=None, local_host=None, local_port=None,
            retina_injector_label="PushBotRetinaInjector"):
        # pylint: disable=too-many-arguments
        AbstractPushBotRetinaDevice.__init__(self, protocol, resolution)
        pushbot_wifi_connection = get_pushbot_wifi_connection(
            pushbot_ip_address, pushbot_port)
        self._translator = PushBotTranslator(protocol, pushbot_wifi_connection)
        self._injector_port = injector_port
        self._retina_injector_label = retina_injector_label

        self._database_connection = PushBotRetinaConnection(
            self._retina_injector_label, pushbot_wifi_connection, resolution,
            local_host, local_port)

    @overrides(AbstractEthernetSensor.get_n_neurons)
    def get_n_neurons(self):
        return self._resolution.value.n_neurons

    @overrides(AbstractEthernetSensor.get_injector_parameters)
    def get_injector_parameters(self):
        return {"port": self._injector_port}

    @overrides(AbstractEthernetSensor.get_injector_label)
    def get_injector_label(self):
        return self._retina_injector_label

    @overrides(AbstractEthernetSensor.get_translator)
    def get_translator(self):
        return self._translator

    @overrides(AbstractEthernetSensor.get_database_connection)
    def get_database_connection(self):
        return self._database_connection
