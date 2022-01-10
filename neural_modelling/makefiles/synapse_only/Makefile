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

MODELS = synapses\
         synapses_stdp_mad_pair_additive\
         synapses_stdp_mad_pair_multiplicative\
         synapses_stdp_mad_nearest_pair_additive\
         synapses_stdp_mad_nearest_pair_multiplicative\
         synapses_stdp_mad_recurrent_dual_fsm_multiplicative\
         synapses_stdp_mad_pfister_triplet_additive\
         synapses_stdp_mad_vogels_2011_additive\
         synapses_structural_random_distance_weight\
         synapses_structural_last_neuron_distance_weight\
         synapses_stdp_mad_pair_additive_structural_random_distance_weight\
         synapses_stdp_mad_pair_additive_structural_last_neuron_distance_weight\
         synapses_stdp_izhikevich_neuromodulation_pair_additive
         
ifneq ($(SPYNNAKER_DEBUG), DEBUG)
    MODELS += synapses_stdp_izhikevich_neuromodulation_pair_additive_structural_random_distance_weight\
              synapses_stdp_izhikevich_neuromodulation_pair_additive_structural_last_neuron_distance_weight
endif

all:
	for d in $(MODELS); do $(MAKE) -C $$d || exit $$?; done

clean:
	for d in $(MODELS); do $(MAKE) -C $$d clean || exit $$?; done
