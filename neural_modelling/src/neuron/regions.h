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

//! \file
//! \brief Standard layout of DSG regions in neuron code.
//!
//! Note that not all models use all of these regions, but they all use the same
//! region identifier mapping.
#pragma once

//! DSG region identifiers
typedef enum neuron_regions_e {
    SYSTEM_REGION,                //!< simulation system; 0
    NEURON_PARAMS_REGION,         //!< neuron parameters; 1
    CURRENT_SOURCE_PARAMS_REGION, //!< current source parameters; 2
    SYNAPSE_PARAMS_REGION,        //!< synapse parameters; 3
    POPULATION_TABLE_REGION,      //!< master population table; 4
    SYNAPTIC_MATRIX_REGION,       //!< synaptic matrix; 5
    SYNAPSE_DYNAMICS_REGION,      //!< synapse dynamics; 6
    STRUCTURAL_DYNAMICS_REGION,   //!< structural dynamics; 7
    NEURON_RECORDING_REGION,      //!< recording; 8
    PROVENANCE_DATA_REGION,       //!< provenance; 9
    PROFILER_REGION,              //!< profiling; 10
    CONNECTOR_BUILDER_REGION,     //!< connection building; 11
    DIRECT_MATRIX_REGION,         //!< direct synaptic matrix; 12
    BIT_FIELD_FILTER_REGION,      //!< bitfield filter; 13
    BIT_FIELD_BUILDER,            //!< bitfield builder parameters; 14
    BIT_FIELD_KEY_MAP,            //!< bitfield key map; 15
    RECORDING_REGION              //!< general recording data; 16
} regions_e;
