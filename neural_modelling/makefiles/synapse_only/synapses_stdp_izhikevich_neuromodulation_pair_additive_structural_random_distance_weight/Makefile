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

APP = $(notdir $(CURDIR))

SYNAPSE_DYNAMICS = $(NEURON_DIR)/neuron/plasticity/stdp/synapse_dynamics_stdp_izhikevich_neuromodulation.c
TIMING_DEPENDENCE = $(NEURON_DIR)/neuron/plasticity/stdp/timing_dependence/timing_pair_impl.c
TIMING_DEPENDENCE_H = $(NEURON_DIR)/neuron/plasticity/stdp/timing_dependence/timing_pair_impl.h
WEIGHT_DEPENDENCE = $(NEURON_DIR)/neuron/plasticity/stdp/weight_dependence/weight_additive_one_term_impl.c
WEIGHT_DEPENDENCE_H = $(NEURON_DIR)/neuron/plasticity/stdp/weight_dependence/weight_additive_one_term_impl.h
SYNAPTOGENESIS_DYNAMICS = $(NEURON_DIR)/neuron/structural_plasticity/synaptogenesis/topographic_map_impl.c
PARTNER_SELECTION = $(NEURON_DIR)/neuron/structural_plasticity/synaptogenesis/partner_selection/random_selection_impl.c
PARTNER_SELECTION_H = $(NEURON_DIR)/neuron/structural_plasticity/synaptogenesis/partner_selection/random_selection_impl.h
FORMATION = $(NEURON_DIR)/neuron/structural_plasticity/synaptogenesis/formation/formation_distance_dependent_impl.c
FORMATION_H = $(NEURON_DIR)/neuron/structural_plasticity/synaptogenesis/formation/formation_distance_dependent_impl.h
ELIMINATION = $(NEURON_DIR)/neuron/structural_plasticity/synaptogenesis/elimination/elimination_random_by_weight_impl.c
ELIMINATION_H = $(NEURON_DIR)/neuron/structural_plasticity/synaptogenesis/elimination/elimination_random_by_weight_impl.h

include ../synapse_build.mk
