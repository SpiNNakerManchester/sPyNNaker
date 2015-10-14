#ifndef _ADDITIONAL_INPUT_TYPE_H_
#define _ADDITIONAL_INPUT_TYPE_H_

#include "../../common/neuron-typedefs.h"

//! Forward declaration of the additional input pointer
typedef struct additional_input_t* additional_input_pointer_t;

//! \brief Gets the value of current provided by the additional input this
//!     timestep
//! \param[in] additional_input The additional input type pointer to the
//!     parameters
//! \param[in] membrane_voltage The membrane voltage of the neuron
//! \return The value of the input after scaling
static input_t additional_input_get_input_value_as_current(
    additional_input_pointer_t additional_input,
    state_t membrane_voltage);

//! \brief Notifies the additional input type that the neuron has spiked
//! \param[in] additional_input The additional input type pointer to the
//!     parameters
static void additional_input_has_spiked(
    additional_input_pointer_t additional_input);

#endif // _ADDITIONAL_INPUT_TYPE_H_
