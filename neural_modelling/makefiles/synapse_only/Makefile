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
         synapses_stdp_mad_nearest_pair_additive_structural_random_distance_weight\
         synapses_stdp_izhikevich_neuromodulation_pair_additive

ifneq ($(SPYNNAKER_DEBUG), DEBUG)
    MODELS += synapses_stdp_izhikevich_neuromodulation_pair_multiplicative\
              synapses_stdp_izhikevich_neuromodulation_vogels_2011_additive\
              synapses_stdp_izhikevich_neuromodulation_pair_additive_structural_random_distance_weight\
              synapses_stdp_izhikevich_neuromodulation_pair_additive_structural_last_neuron_distance_weight
endif

# Build the optional scheduler without changing the regular binaries.
UPDATE_MODELS = $(foreach model,$(MODELS),\
    $(if $(findstring _stdp_,$(model)),\
        $(if $(findstring _structural_,$(model)),,$(model))))

all:
	for d in $(MODELS); do $(MAKE) -C $$d || exit $$?; done
	for d in $(UPDATE_MODELS); do $(MAKE) -C $$d STDP_UPDATE_BUILD=1 || exit $$?; done

clean:
	for d in $(MODELS); do $(MAKE) -C $$d clean || exit $$?; done
	for d in $(UPDATE_MODELS); do $(MAKE) -C $$d STDP_UPDATE_BUILD=1 clean || exit $$?; done
