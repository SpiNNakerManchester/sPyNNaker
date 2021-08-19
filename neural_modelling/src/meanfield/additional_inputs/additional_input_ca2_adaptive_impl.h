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

//----------------------------------------------------------------------------
//! \file
//! \brief Implementation of adaptive calcium ion additional input
//!
//! Model from Liu, Y. H., & Wang, X. J. (2001). Spike-frequency adaptation of
//! a generalized leaky integrate-and-fire model neuron. _Journal of
//! Computational Neuroscience,_ 10(1), 25-45. doi:10.1023/A:1008916026143
//----------------------------------------------------------------------------
#ifndef _ADDITIONAL_INPUT_CA2_ADAPTIVE_H_
#define _ADDITIONAL_INPUT_CA2_ADAPTIVE_H_

#include "../../meanfield/additional_inputs/additional_input.h"

//! The additional input is due to calcium ions
struct additional_input_t {
    //! exp(-(machine time step in ms) / (TauCa))
    REAL    exp_TauCa;
    //! Calcium current
    REAL    I_Ca2;
    //! Influx of CA2 caused by each spike
    REAL    I_alpha;
};

//! \brief Gets the value of current provided by the additional input this
//!     timestep
//! \param[in] additional_input: The additional input type pointer to the
//!     parameters
//! \param[in] membrane_voltage: The membrane voltage of the neuron
//! \return The value of the input after scaling
static inline input_t additional_input_get_input_value_as_current(
        struct additional_input_t *additional_input,
        UNUSED state_t membrane_voltage) {
    // Decay Ca2 trace
    additional_input->I_Ca2 *= additional_input->exp_TauCa;

    // Return the Ca2
    return -additional_input->I_Ca2;
}

//! \brief Notifies the additional input type that the neuron has spiked
//! \param[in] additional_input: The additional input type pointer to the
//!     parameters
static inline void additional_input_has_spiked(
        struct additional_input_t *additional_input) {
    // Apply influx of calcium to trace
    additional_input->I_Ca2 += additional_input->I_alpha;
}

#endif // _ADDITIONAL_INPUT_CA2_ADAPTIVE_H_
