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
//! \brief meanfield types
#ifndef _MEANFIELD_MODEL_IMPL_H_
#define _MEANFIELD_MODEL_IMPL_H_

#include "../../meanfield/models/meanfield_model.h"
//#include <sqrt.h>

typedef struct meanfield_t {
    // TODO: Parameters - make sure these match with the Python code,
    // including the order of the variables when returned by
    // get_neural_parameters.

    // 
    REAL a;
    REAL b;
    REAL tauw;
    REAL Trefrac;
    REAL Vthre;
    REAL Vreset;
    REAL delta_v;
    REAL ampnoise;
    REAL Timescale_inv;
    
    REAL Ve; // will be used as a vector !!! OR Ve and Vi
    //REAL Vi;
    
    //vector V = {Ve, Vi};
    
    REAL this_h;
        
    
} meanfield_t;

typedef struct global_neuron_params_t {
    // TODO: Add any parameters that apply to the whole model here (i.e. not
    // just to a single neuron)

    // Note: often these are not user supplied, but computed parameters

    //uint32_t machine_time_step;
    REAL machine_timestep_ms;
} global_neuron_params_t;

#endif // _NEURON_MODEL_MY_IMPL_H_
