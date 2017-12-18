from pacman.model.graphs.application import ApplicationSpiNNakerLinkVertex
from spynnaker.pyNN.external_devices_models.push_bot.push_bot_ethernet \
    import PushBotEthernetMotorDevice


class PushBotSpiNNakerLinkMotorDevice(
        PushBotEthernetMotorDevice, ApplicationSpiNNakerLinkVertex):
    """ The motor of a PushBot
    """

    default_parameters = {
        'n_neurons': 1,
        'label': None,
        'board_address': None}

    def __init__(
            self, motor, protocol, spinnaker_link_id,
            n_neurons=default_parameters['n_neurons'],
            label=default_parameters['label'],
            board_address=default_parameters['board_address']):
        """

        :param motor: a PushBotMotor value to indicate the motor to control
        :param protocol: The protocol used to control the device
        :param spinnaker_link_id: The SpiNNakerLink connected to
        :param n_neurons: The number of neurons in the device
        :param label: The label of the device
        :param board_address:\
            The IP address of the board that the device is connected to
        """
        # pylint: disable=too-many-arguments
        PushBotEthernetMotorDevice.__init__(self, motor, protocol)
        ApplicationSpiNNakerLinkVertex.__init__(
            self, spinnaker_link_id=spinnaker_link_id, n_atoms=n_neurons,
            board_address=board_address, label=label)
