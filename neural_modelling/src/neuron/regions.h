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

#pragma once

typedef enum regions_e {
    SYSTEM_REGION,            // 0
    NEURON_PARAMS_REGION,     // 1
    SYNAPSE_PARAMS_REGION,    // 2
    POPULATION_TABLE_REGION,  // 3
    SYNAPTIC_MATRIX_REGION,   // 4
    SYNAPSE_DYNAMICS_REGION,  // 5
    NEURON_RECORDING_REGION,  // 6
    PROVENANCE_DATA_REGION,   // 7
    PROFILER_REGION,          // 8
    CONNECTOR_BUILDER_REGION, // 9
    DIRECT_MATRIX_REGION      // 10
} regions_e;
