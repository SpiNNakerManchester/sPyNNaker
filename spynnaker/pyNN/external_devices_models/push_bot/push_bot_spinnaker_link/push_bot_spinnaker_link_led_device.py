from pacman.model.graphs.application import ApplicationSpiNNakerLinkVertex

from spynnaker.pyNN.external_devices_models.push_bot.push_bot_ethernet \
    import PushBotEthernetLEDDevice


class PushBotSpiNNakerLinkLEDDevice(
        PushBotEthernetLEDDevice, ApplicationSpiNNakerLinkVertex):
    """ The LED of a PushBot
    """

    default_parameters = {
        'n_neurons': 1, 'label': None, 'board_address': None,
        'start_active_time_front': None, 'start_active_time_back': None,
        'start_total_period': None, 'start_frequency': None}

    def __init__(
            self, led, protocol, spinnaker_link_id,
            n_neurons=default_parameters['n_neurons'],
            label=default_parameters['label'],
            board_address=default_parameters['board_address'],
            start_active_time_front=default_parameters[
                'start_active_time_front'],
            start_active_time_back=default_parameters[
                'start_active_time_back'],
            start_total_period=default_parameters['start_total_period'],
            start_frequency=default_parameters['start_frequency']):
        """

        :param led: The PushBotLED parameter to control
        :param protocol: The protocol instance to get commands from
        :param spinnaker_link_id: The SpiNNakerLink connected to
        :param n_neurons: The number of neurons in the device
        :param label: The label of the device
        :param board_address:\
            The IP address of the board that the device is connected to
        :param start_active_time_front:\
            The "active time" to set for the front LED at the start
        :param start_active_time_back:\
            The "active time" to set for the back LED at the start
        :param start_total_period: The "total period" to set at the start
        :param start_frequency: The "frequency" to set at the start
        """
        PushBotEthernetLEDDevice.__init__(
            self, led, protocol, start_active_time_front,
            start_active_time_back, start_total_period, start_frequency)
        ApplicationSpiNNakerLinkVertex.__init__(
            self, spinnaker_link_id=spinnaker_link_id, n_atoms=n_neurons,
            board_address=board_address, label=label)
