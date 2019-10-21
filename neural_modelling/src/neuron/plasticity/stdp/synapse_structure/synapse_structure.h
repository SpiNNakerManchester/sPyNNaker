/*
 * Copyright (c) 2017-2019 The University of Manchester
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

#ifndef _SYNAPSE_STRUCTURE_H_
#define _SYNAPSE_STRUCTURE_H_

#include <neuron/plasticity/stdp/weight_dependence/weight.h>

static update_state_t synapse_structure_get_update_state(
        plastic_synapse_t synaptic_word, index_t synapse_type);

static final_state_t synapse_structure_get_final_state(
        update_state_t state);

static weight_t synapse_structure_get_final_weight(
        final_state_t final_state);

static plastic_synapse_t synapse_structure_get_final_synaptic_word(
        final_state_t final_state);

static plastic_synapse_t synapse_structure_create_synapse(weight_t weight);

static weight_t synapse_structure_get_weight(plastic_synapse_t synaptic_word);

#endif // _SYNAPSE_STRUCTURE_H_
