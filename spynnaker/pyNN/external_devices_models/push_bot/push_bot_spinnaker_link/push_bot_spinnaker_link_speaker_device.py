from pacman.model.graphs.application import ApplicationSpiNNakerLinkVertex
from spynnaker.pyNN.external_devices_models.push_bot.push_bot_ethernet import (
    PushBotEthernetSpeakerDevice)


class PushBotSpiNNakerLinkSpeakerDevice(
        PushBotEthernetSpeakerDevice, ApplicationSpiNNakerLinkVertex):
    """ The speaker of a PushBot
    """
    __slots__ = []

    default_parameters = {
        'n_neurons': 1, 'label': None,
        'board_address': None,
        'start_active_time': 50,
        'start_total_period': 100,
        'start_frequency': None,
        'start_melody': None}

    def __init__(
            self, speaker, protocol, spinnaker_link_id,
            n_neurons=default_parameters['n_neurons'],
            label=default_parameters['label'],
            board_address=default_parameters['board_address'],
            start_active_time=default_parameters['start_active_time'],
            start_total_period=default_parameters['start_total_period'],
            start_frequency=default_parameters['start_frequency'],
            start_melody=default_parameters['start_melody']):
        """

        :param speaker: The PushBotSpeaker value to control
        :param protocol: The protocol instance to get commands from
        :param spinnaker_link_id: The SpiNNakerLink connected to
        :param n_neurons: The number of neurons in the device
        :param label: The label of the device
        :param board_address:\
            The IP address of the board that the device is connected to
        :param start_active_time: The "active time" to set at the start
        :param start_total_period: The "total period" to set at the start
        :param start_frequency: The "frequency" to set at the start
        :param start_melody: The "melody" to set at the start
        """
        # pylint: disable=too-many-arguments
        PushBotEthernetSpeakerDevice.__init__(
            self, speaker, protocol, start_active_time,
            start_total_period, start_frequency, start_melody)
        ApplicationSpiNNakerLinkVertex.__init__(
            self, spinnaker_link_id=spinnaker_link_id, n_atoms=n_neurons,
            board_address=board_address, label=label)
