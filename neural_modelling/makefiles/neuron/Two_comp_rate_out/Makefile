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

OTHER_SOURCES = $(NEURON_DIR)/neuron/models/neuron_model_lif_two_comp_rate_out.c
NEURON_IMPL_H = $(NEURON_DIR)/neuron/implementations/neuron_impl_two_comp_rate.h
SYNAPSE_DYNAMICS = $(NEURON_DIR)/synapse/plasticity/synapse_dynamics_static_impl.c

COMPARTMENT_TYPE_H = $(NEURON_DIR)/synapse/compartment_type/compartment_type_US_model.h

include ../neural_build.mk