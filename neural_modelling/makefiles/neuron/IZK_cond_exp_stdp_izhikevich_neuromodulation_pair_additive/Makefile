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

NEURON_IMPL_H = $(NEURON_DIR)/neuron/implementations/neuron_impl_standard.h
NEURON_MODEL = $(NEURON_DIR)/neuron/models/neuron_model_izh_impl.c
NEURON_MODEL_H = $(NEURON_DIR)/neuron/models/neuron_model_izh_impl.h
INPUT_TYPE_H = $(NEURON_DIR)/neuron/input_types/input_type_conductance.h
THRESHOLD_TYPE_H = $(NEURON_DIR)/neuron/threshold_types/threshold_type_static.h
SYNAPSE_TYPE_H = $(NEURON_DIR)/neuron/synapse_types/synapse_types_exponential_impl.h
SYNAPSE_DYNAMICS = $(NEURON_DIR)/neuron/plasticity/stdp/synapse_dynamics_stdp_izhikevich_neuromodulation.c
TIMING_DEPENDENCE = $(NEURON_DIR)/neuron/plasticity/stdp/timing_dependence/timing_pair_impl.c
TIMING_DEPENDENCE_H = $(NEURON_DIR)/neuron/plasticity/stdp/timing_dependence/timing_pair_impl.h
WEIGHT_DEPENDENCE = $(NEURON_DIR)/neuron/plasticity/stdp/weight_dependence/weight_additive_one_term_impl.c
WEIGHT_DEPENDENCE_H = $(NEURON_DIR)/neuron/plasticity/stdp/weight_dependence/weight_additive_one_term_impl.h

include ../neural_build.mk
