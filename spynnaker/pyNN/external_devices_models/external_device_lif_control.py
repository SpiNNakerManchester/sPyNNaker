# Copyright (c) 2017 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import Optional, List, Union, Tuple
from spinn_utilities.overrides import overrides
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from spynnaker.pyNN.extra_algorithms.splitter_components import (
    SplitterPopulationVertex)
from spynnaker.pyNN.models.neuron import (
    PopulationVertex, AbstractPyNNNeuronModelStandard)
from spynnaker.pyNN.models.defaults import (
    default_initial_values, default_parameters)
from spynnaker.pyNN.models.neuron.input_types import InputTypeCurrent
from spynnaker.pyNN.models.neuron.implementations import NeuronImplStandard
from spynnaker.pyNN.models.neuron.neuron_models import (
    NeuronModelLeakyIntegrateAndFire)
from spynnaker.pyNN.models.neuron.synapse_types import SynapseTypeExponential
from .abstract_ethernet_translator import AbstractEthernetTranslator
from .abstract_multicast_controllable_device import (
    AbstractMulticastControllableDevice)
from .external_device_lif_control_vertex import ExternalDeviceLifControlVertex
from .threshold_type_multicast_device_control import (
    ThresholdTypeMulticastDeviceControl)


class ExternalDeviceLifControl(AbstractPyNNNeuronModelStandard):
    """
    Abstract control module for the PushBot, based on the LIF neuron, but
    without spikes, and using the voltage as the output to the various devices.
    """
    __slots__ = (
        "_create_edges",
        "_devices",
        "_translator")

    @default_initial_values({"v", "isyn_exc", "isyn_inh"})
    @default_parameters({
        "tau_m", "cm", "v_rest", "v_reset", "tau_syn_E", "tau_syn_I",
        "tau_refrac", "i_offset"})
    def __init__(
            self, devices:  List[AbstractMulticastControllableDevice],
            create_edges: bool,
            translator: Optional[AbstractEthernetTranslator] = None,
            # default params for the neuron model type
            tau_m: float = 20.0, cm: float = 1.0, v_rest: float = 0.0,
            v_reset: float = 0.0, tau_syn_E: float = 5.0,
            tau_syn_I: float = 5.0, tau_refrac: float = 0.1,
            i_offset: float = 0.0, v: float = 0.0, isyn_exc: float = 0.0,
            isyn_inh: float = 0.0):
        """
        :param devices:
            The AbstractMulticastControllableDevice instances to be controlled
            by the population
        :param create_edges:
            True if edges to the devices should be added by this device (set
            to False if using the device over Ethernet using a translator)
        :param translator:
            Translator to be used when used for Ethernet communication.  Must
            be provided if the device is to be controlled over Ethernet.
        :param tau_m: (defaulted LIF neuron parameter)
        :param cm: (defaulted LIF neuron parameter)
        :param v_rest: (defaulted LIF neuron parameter)
        :param v_reset: (defaulted LIF neuron parameter)
        :param tau_syn_E: (defaulted LIF neuron parameter)
        :param tau_syn_I: (defaulted LIF neuron parameter)
        :param tau_refrac: (defaulted LIF neuron parameter)
        :param i_offset: (defaulted LIF neuron parameter)
        :param v: (defaulted LIF neuron state variable initial value)
        :param isyn_exc:
            (defaulted LIF neuron state variable initial value)
        :param isyn_inh:
            (defaulted LIF neuron state variable initial value)
        """
        if not devices:
            raise ConfigurationException("No devices specified")

        neuron_model = NeuronModelLeakyIntegrateAndFire(
            v, v_rest, tau_m, cm, i_offset, v_reset, tau_refrac)
        synapse_type = SynapseTypeExponential(
            tau_syn_E, tau_syn_I, isyn_exc, isyn_inh)
        input_type = InputTypeCurrent()
        threshold_type = ThresholdTypeMulticastDeviceControl(devices)

        self._devices = devices
        self._translator = translator
        self._create_edges = create_edges

        super().__init__(
            model_name="ExternalDeviceLifControl",
            binary="external_device_lif_control.aplx",
            neuron_model=neuron_model, input_type=input_type,
            synapse_type=synapse_type, threshold_type=threshold_type)

    @overrides(AbstractPyNNNeuronModelStandard.create_vertex)
    def create_vertex(
            self, n_neurons: int, label: str, *,
            spikes_per_second: Optional[float] = None,
            ring_buffer_sigma: Optional[float] = None,
            max_expected_summed_weight: Optional[List[float]] = None,
            incoming_spike_buffer_size: Optional[int] = None,
            drop_late_spikes: Optional[bool] = None,
            splitter: Optional[SplitterPopulationVertex] = None,
            seed: Optional[int] = None, n_colour_bits: Optional[int] = None,
            n_steps_per_timestep: int = 1,
            neurons_per_core: Optional[Union[int, Tuple[int, ...]]] = None,
            n_synapse_cores: Optional[int] = None,
            allow_delay_extensions: Optional[bool] = None) -> PopulationVertex:
        if n_neurons != len(self._devices):
            raise ConfigurationException(
                "Number of neurons does not match number of "
                f"devices in {label}")
        model = self._model
        assert isinstance(model, NeuronImplStandard)
        model.n_steps_per_timestep = n_steps_per_timestep
        if neurons_per_core is None:
            neurons_per_core = \
                self.get_model_max_atoms_per_dimension_per_core()
        if n_synapse_cores is None:
            n_synapse_cores = self.get_model_n_synapse_cores()
        if allow_delay_extensions is None:
            allow_delay_extensions = self.get_model_allow_delay_extensions()
        return ExternalDeviceLifControlVertex(
            devices=self._devices, create_edges=self._create_edges,
            max_atoms_per_core=neurons_per_core,
            n_synapse_cores=n_synapse_cores,
            allow_delay_extensions=allow_delay_extensions,
            neuron_impl=model, pynn_model=self, translator=self._translator,
            spikes_per_second=spikes_per_second, label=label,
            ring_buffer_sigma=ring_buffer_sigma,
            max_expected_summed_weight=max_expected_summed_weight,
            incoming_spike_buffer_size=incoming_spike_buffer_size,
            drop_late_spikes=drop_late_spikes, splitter=splitter, seed=seed,
            n_colour_bits=n_colour_bits)
