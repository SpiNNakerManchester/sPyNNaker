from pacman.model.graphs.application import ApplicationSpiNNakerLinkVertex
from spynnaker.pyNN.external_devices_models.push_bot.push_bot_ethernet import (
    PushBotEthernetLaserDevice)


class PushBotSpiNNakerLinkLaserDevice(
        PushBotEthernetLaserDevice, ApplicationSpiNNakerLinkVertex):
    """ The Laser of a PushBot
    """
    __slots__ = []

    default_parameters = {
        'n_neurons': 1, 'label': None, 'board_address': None,
        'start_active_time': 0, 'start_total_period': 0, 'start_frequency': 0}

    def __init__(
            self, laser, protocol, spinnaker_link_id,
            n_neurons=default_parameters['n_neurons'],
            label=default_parameters['label'],
            board_address=default_parameters['board_address'],
            start_active_time=default_parameters['start_active_time'],
            start_total_period=default_parameters['start_total_period'],
            start_frequency=default_parameters['start_frequency']):
        """

        :param laser: The PushBotLaser value to control
        :param protocol: The protocol instance to get commands from
        :param spinnaker_link_id:\
            The SpiNNakerLink that the PushBot is connected to
        :param n_neurons: The number of neurons in the device
        :param label: A label for the device
        :param board_address:\
            The IP address of the board that the device is connected to
        :param start_active_time: The "active time" value to send at the start
        :param start_total_period:\
            The "total period" value to send at the start
        :param start_frequency: The "frequency" to send at the start
        """
        # pylint: disable=too-many-arguments
        PushBotEthernetLaserDevice.__init__(
            self, laser, protocol, start_active_time,
            start_total_period, start_frequency)
        ApplicationSpiNNakerLinkVertex.__init__(
            self, spinnaker_link_id=spinnaker_link_id, n_atoms=n_neurons,
            board_address=board_address, label=label)
