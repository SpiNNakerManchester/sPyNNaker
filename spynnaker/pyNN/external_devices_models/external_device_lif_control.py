# Copyright (c) 2017-2019 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
from spinn_utilities.overrides import overrides
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from spynnaker.pyNN.models.neuron import AbstractPyNNNeuronModelStandard
from spynnaker.pyNN.models.defaults import default_initial_values
from spynnaker.pyNN.models.neuron.input_types import InputTypeCurrent
from spynnaker.pyNN.models.neuron.neuron_models import (
    NeuronModelLeakyIntegrateAndFire)
from spynnaker.pyNN.models.neuron.synapse_types import SynapseTypeExponential
from .external_device_lif_control_vertex import ExternalDeviceLifControlVertex
from .threshold_type_multicast_device_control import (
    ThresholdTypeMulticastDeviceControl)

logger = logging.getLogger(__name__)


class ExternalDeviceLifControl(AbstractPyNNNeuronModelStandard):
    """ Abstract control module for the PushBot, based on the LIF neuron,\
        but without spikes, and using the voltage as the output to the various\
        devices
    """
    __slots__ = [
        "_create_edges",
        "_devices",
        "_translator"]

    @default_initial_values({"v", "isyn_exc", "isyn_inh"})
    def __init__(
            self, devices, create_edges, translator=None,

            # default params for the neuron model type
            tau_m=20.0, cm=1.0, v_rest=0.0, v_reset=0.0, tau_syn_E=5.0,
            tau_syn_I=5.0, tau_refrac=0.1, i_offset=0.0, v=0.0,
            isyn_inh=0.0, isyn_exc=0.0):
        """
        :param devices:\
            The AbstractMulticastControllableDevice instances to be controlled\
            by the population
        :param create_edges:\
            True if edges to the devices should be added by this device (set\
            to False if using the device over Ethernet using a translator)
        :param translator:\
            Translator to be used when used for Ethernet communication.  Must\
            be provided if the device is to be controlled over Ethernet.
        """
        # pylint: disable=too-many-arguments, too-many-locals

        if not devices:
            raise ConfigurationException("No devices specified")

        neuron_model = NeuronModelLeakyIntegrateAndFire(
            v, v_rest, tau_m, cm, i_offset, v_reset, tau_refrac)
        synapse_type = SynapseTypeExponential(
            tau_syn_E, tau_syn_I, isyn_inh, isyn_exc)
        input_type = InputTypeCurrent()
        threshold_type = ThresholdTypeMulticastDeviceControl(devices)

        self._devices = devices
        self._translator = translator
        self._create_edges = create_edges

        super(ExternalDeviceLifControl, self).__init__(
            model_name="ExternalDeviceLifControl",
            binary="external_device_lif_control.aplx",
            neuron_model=neuron_model, input_type=input_type,
            synapse_type=synapse_type, threshold_type=threshold_type)

    @overrides(AbstractPyNNNeuronModelStandard.create_vertex)
    def create_vertex(
            self, n_neurons, label, constraints, spikes_per_second,
            ring_buffer_sigma, incoming_spike_buffer_size,
            in_partitions, out_partitions, packet_compressor,
            atoms_per_core, input_pop):
        if n_neurons != len(self._devices):
            raise ConfigurationException(
                "Number of neurons does not match number of devices in {}"
                .format(label))
        max_atoms = self.get_max_atoms_per_core()
        return ExternalDeviceLifControlVertex(
            self._devices, self._create_edges, max_atoms, self._model, self,
            self._translator, spikes_per_second, label, ring_buffer_sigma,
            incoming_spike_buffer_size, constraints)
