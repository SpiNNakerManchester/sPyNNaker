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

import numpy
from spinn_front_end_common.utilities.constants import US_TO_MS
from spinn_front_end_common.utilities.globals_variables import get_simulator
from pyNN.random import NumpyRNG


class SynapseInformation(object):
    """ Contains the synapse information including the connector, synapse type\
        and synapse dynamics
    """
    __slots__ = [
        "__connector",
        "__pre_population",
        "__post_population",
        "__prepop_is_view",
        "__postpop_is_view",
        "__rng",
        "__synapse_dynamics",
        "__synapse_type",
        "__weights",
        "__raw_delays",
        "__rounded_delays"]

    def __init__(self, connector, pre_population, post_population,
                 prepop_is_view, postpop_is_view, rng,
                 synapse_dynamics, synapse_type,
                 weights=None, delays=None):
        self.__connector = connector
        self.__pre_population = pre_population
        self.__post_population = post_population
        self.__prepop_is_view = prepop_is_view
        self.__postpop_is_view = postpop_is_view
        self.__rng = (rng or NumpyRNG())
        self.__synapse_dynamics = synapse_dynamics
        self.__synapse_type = synapse_type
        self.__weights = weights
        self.__raw_delays = delays
        self.__rounded_delays = {}

    @property
    def connector(self):
        return self.__connector

    @property
    def pre_population(self):
        return self.__pre_population

    @property
    def post_population(self):
        return self.__post_population

    @property
    def n_pre_neurons(self):
        return self.__pre_population.size

    @property
    def n_post_neurons(self):
        return self.__post_population.size

    @property
    def prepop_is_view(self):
        return self.__prepop_is_view

    @property
    def postpop_is_view(self):
        return self.__postpop_is_view

    @property
    def rng(self):
        return self.__rng

    @property
    def synapse_dynamics(self):
        return self.__synapse_dynamics

    @property
    def synapse_type(self):
        return self.__synapse_type

    @property
    def weights(self):
        return self.__weights

    @property
    def raw_delays_in_ms(self):
        return self.__raw_delays

    def rounded_delays_in_ms(self, timestep_in_us):
        #  Cache the results to avoid repeated work
        if timestep_in_us not in self.__rounded_delays:
            self.__rounded_delays[timestep_in_us] = self._round_delays(
                timestep_in_us)
        return self.__rounded_delays[timestep_in_us]

    def _round_delays(self, timestep_in_us):
        if timestep_in_us < 50:
            if timestep_in_us <= 0:
                raise ValueError("timestep {} is not possitive!".format(
                    timestep_in_us))
            else:
                # Safety code it timestep < 50 intended reduce as required
                raise NotImplementedError("timestep {} appears to be too low"
                                          "".format(timestep_in_us))
        # Leave randoms as is
        if get_simulator().is_a_pynn_random(self.__raw_delays):
            return self.__raw_delays
        # Concert to timesteps
        delays_in_timesteps = numpy.rint(
            numpy.array(self.__raw_delays) * US_TO_MS / timestep_in_us)
        # make sure delay is at least one timestep
        clipped_in_timesteps = numpy.clip(delays_in_timesteps, 1, float("inf"))
        # convert back to ms
        return clipped_in_timesteps * timestep_in_us / US_TO_MS
