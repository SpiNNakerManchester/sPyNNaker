import logging

from spynnaker.pyNN.utilities.conf import config
from spynnaker.pyNN.utilities import constants


from spinn_front_end_common.utilities import exceptions
import math


logger = logging.getLogger(__name__)


class SpynnakerConfigurationFunctions(object):

    def __init__(self):
        pass

    def _set_up_machine_specifics(self, timestep, min_delay, max_delay,
                                  hostname):
        self._machine_time_step = config.getint("Machine", "machineTimeStep")

        # deal with params allowed via the setup optimals
        if timestep is not None:
            timestep *= 1000  # convert into ms from microseconds
            config.set("Machine", "machineTimeStep", timestep)
            self._machine_time_step = timestep

        if min_delay is not None and float(min_delay * 1000) < 1.0 * timestep:
            raise exceptions.ConfigurationException(
                "Pacman does not support min delays below {} ms with the "
                "current machine time step".format(1.0 * timestep))

        natively_supported_delay_for_models = \
            constants.MAX_SUPPORTED_DELAY_TICS
        delay_extention_max_supported_delay = \
            constants.MAX_DELAY_BLOCKS \
            * constants.MAX_TIMER_TICS_SUPPORTED_PER_BLOCK

        max_delay_tics_supported = \
            natively_supported_delay_for_models + \
            delay_extention_max_supported_delay

        if max_delay is not None\
           and float(max_delay * 1000) > max_delay_tics_supported * timestep:
            raise exceptions.ConfigurationException(
                "Pacman does not support max delays above {} ms with the "
                "current machine time step".format(0.144 * timestep))
        if min_delay is not None:
            if not config.has_section("Model"):
                config.add_section("Model")
            config.set("Model", "min_delay", (min_delay * 1000) / timestep)

        if max_delay is not None:
            if not config.has_section("Model"):
                config.add_section("Model")
            config.set("Model", "max_delay", (max_delay * 1000) / timestep)

        if (config.has_option("Machine", "timeScaleFactor") and
                config.get("Machine", "timeScaleFactor") != "None"):
            self._time_scale_factor = \
                config.getint("Machine", "timeScaleFactor")
            if timestep * self._time_scale_factor < 1000:
                logger.warn("the combination of machine time step and the "
                            "machine time scale factor results in a real "
                            "timer tick that is currently not reliably "
                            "supported by the spinnaker machine.")
        else:
            self._time_scale_factor = max(1,
                                          math.ceil(1000.0 / float(timestep)))
            if self._time_scale_factor > 1:
                logger.warn("A timestep was entered that has forced pacman103 "
                            "to automatically slow the simulation down from "
                            "real time by a factor of {}. To remove this "
                            "automatic behaviour, please enter a "
                            "timescaleFactor value in your .pacman.cfg"
                            .format(self._time_scale_factor))

        if hostname is not None:
            self._hostname = hostname
            logger.warn("The machine name from PYNN setup is overriding the "
                        "machine name defined in the spynnaker.cfg file")
        elif config.has_option("Machine", "machineName"):
            self._hostname = config.get("Machine", "machineName")
        else:
            raise Exception("A SpiNNaker machine must be specified in "
                            "spynnaker.cfg.")
        use_virtual_board = config.getboolean("Machine", "virtual_board")
        if self._hostname == 'None' and not use_virtual_board:
            raise Exception("A SpiNNaker machine must be specified in "
                            "spynnaker.cfg.")
