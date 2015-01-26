import math

from spynnaker.pyNN.models.neural_properties.synapse_dynamics.abstract_rules.\
    abstract_time_dependency import AbstractTimeDependency
from spynnaker.pyNN import exceptions
from spynnaker.pyNN.models.neural_properties.synapse_dynamics.abstract_rules.\
    abstract_voltage_dependency import AbstractVoltageDependency
from spynnaker.pyNN.models.neural_properties.synapse_dynamics.abstract_rules.\
    abstract_weight_dependency import AbstractWeightDependency

# How large are the time-stamps stored with each event
TIME_STAMP_BYTES = 4

# When not using the MAD scheme, how many pre-synaptic events are buffered
NUM_PRE_SYNAPTIC_EVENTS = 4


class STDPMechanism(object):

    def __init__(self, timing_dependence=None, weight_dependence=None,
                 voltage_dependence=None, dendritic_delay_fraction=1.0,
                 mad=False):
        if timing_dependence is not None and \
                not isinstance(timing_dependence, AbstractTimeDependency):
            raise exceptions.ConfigurationException(
                "The timing dependency handed is not a supported time "
                "dependency. Please rectify and try again")
        if weight_dependence is not None and \
                not isinstance(weight_dependence, AbstractWeightDependency):
            raise exceptions.ConfigurationException(
                "The weight dependency handed is not a supported weight "
                "dependency. Please rectify and try again")
        if voltage_dependence is not None and \
                not isinstance(voltage_dependence, AbstractVoltageDependency):
            raise exceptions.ConfigurationException(
                "The voltage dependency handed is not a supported voltage "
                "dependency. Please rectify and try again")

        self._timing_dependence = timing_dependence
        self._weight_dependence = weight_dependence
        self._voltage_dependence = voltage_dependence
        self._dendritic_delay_fraction = dendritic_delay_fraction
        self._mad = mad

        if (self._dendritic_delay_fraction < 0.5
                or self._dendritic_delay_fraction > 1.0):
            raise NotImplementedError("SpiNNaker only supports dendritic delay"
                                      " fractions in the interval [0.5, 1.0]")

        if self.voltage_dependence is not None:
            raise NotImplementedError("voltage_dependence not implemented")

        self._weight_scale = 1.0

    @property
    def weight_scale(self):
        return self._weight_scale

    @weight_scale.setter
    def weight_scale(self, weight_scale):
        self._weight_scale = weight_scale

    @property
    def timing_dependence(self):
        return self._timing_dependence

    @property
    def weight_dependence(self):
        return self._weight_dependence

    @property
    def voltage_dependence(self):
        return self._voltage_dependence

    @property
    def dentritic_delay_fraction(self):
        return self._dendritic_delay_fraction

    def __eq__(self, other):
        if (other is None) or (not isinstance(other, self.__class__)):
            return False

        return ((self._timing_dependence == other.timing_dependence)
                and (self._weight_dependence == other.weight_dependence)
                and (self._voltage_dependence == other.voltage_dependence)
                and (self._dendritic_delay_fraction
                     == other.dendritic_delay_fraction)

                and self.equals(other))

    def get_synapse_row_io(self):
        if self.timing_dependence is not None:
            # If we're using MAD, the header contains a single timestamp and
            # pre-trace
            if self._mad:
                synaptic_row_header_bytes = (
                    TIME_STAMP_BYTES
                    + self.timing_dependence.pre_trace_size_bytes)
            # Otherwise, headers consist of a counter followed by
            # NUM_PRE_SYNAPTIC_EVENTS timestamps and pre-traces
            else:
                synaptic_row_header_bytes = (
                    4 + (NUM_PRE_SYNAPTIC_EVENTS
                         * (TIME_STAMP_BYTES
                            + self.timing_dependence.pre_trace_size_bytes)))

            # Convert to words, rounding up to take into account word
            # alignement
            synaptic_row_header_words = int(
                math.ceil(float(synaptic_row_header_bytes) / 4.0))

            # Create a suitable synapse row io object
            return self._timing_dependence.create_synapse_row_io(
                synaptic_row_header_words, self._dendritic_delay_fraction)
        else:
            return None

    def equals(self, other):
        """
        Determines if an object is equal to this object
        """
        raise NotImplementedError

    # **TODO** make property
    def are_weights_signed(self):
        return False

    # **TODO** make property
    def get_params_size(self, num_synapse_types):
        """
        Gets the size of the STDP parameters in bytes for a range of atoms
        """
        size = 0
        num_terms = 1
        if self._timing_dependence is not None:
            size += self._timing_dependence.get_params_size_bytes()
            num_terms = self._timing_dependence.num_terms

        if self._weight_dependence is not None:
            size += self._weight_dependence.get_params_size_bytes(
                num_synapse_types, num_terms)

        return size

    def write_plastic_params(self, spec, region, machine_time_step,
                             weight_scales):
        spec.comment("Writing Plastic Parameters")

        # Switch focus to the region:
        spec.switch_write_focus(region)

        # Write timing dependence parameters to region and get number of weight
        # terms it requires
        num_terms = 1
        if self.timing_dependence is not None:
            self.timing_dependence.write_plastic_params(
                spec, machine_time_step, weight_scales, self._weight_scale)
            num_terms = self.timing_dependence.num_terms

        # Write weight dependence information to region
        if self.weight_dependence is not None:
            self.weight_dependence.write_plastic_params(
                spec, machine_time_step, weight_scales, self._weight_scale,
                num_terms)

    # **TODO** make property
    def get_vertex_executable_suffix(self):
        name = "stdp_mad" if self._mad else "stdp"
        if self.timing_dependence is not None:
            name += "_" + self.timing_dependence.vertex_executable_suffix
        if self.weight_dependence is not None:
            name += "_" + self.weight_dependence.vertex_executable_suffix
        return name

    # **TODO** make property
    def get_max_weight(self):
        if self.weight_dependence is not None:
            return self.weight_dependence.w_max
        else:
            return 0.0
