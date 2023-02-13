# Copyright (c) 2014-2023 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

APP = $(notdir $(CURDIR))

SYNAPSE_DYNAMICS = $(NEURON_DIR)/neuron/plasticity/synapse_dynamics_static_impl.c
SYNAPTOGENESIS_DYNAMICS = $(NEURON_DIR)/neuron/structural_plasticity/synaptogenesis/topographic_map_impl.c
PARTNER_SELECTION = $(NEURON_DIR)/neuron/structural_plasticity/synaptogenesis/partner_selection/last_neuron_selection_impl.c
PARTNER_SELECTION_H = $(NEURON_DIR)/neuron/structural_plasticity/synaptogenesis/partner_selection/last_neuron_selection_impl.h
FORMATION = $(NEURON_DIR)/neuron/structural_plasticity/synaptogenesis/formation/formation_distance_dependent_impl.c
FORMATION_H = $(NEURON_DIR)/neuron/structural_plasticity/synaptogenesis/formation/formation_distance_dependent_impl.h
ELIMINATION = $(NEURON_DIR)/neuron/structural_plasticity/synaptogenesis/elimination/elimination_random_by_weight_impl.c
ELIMINATION_H = $(NEURON_DIR)/neuron/structural_plasticity/synaptogenesis/elimination/elimination_random_by_weight_impl.h

include ../synapse_build.mk
