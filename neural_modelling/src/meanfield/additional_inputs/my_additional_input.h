#ifndef _ADDITIONAL_INPUT_H_
#define _ADDITIONAL_INPUT_H_

#include <neuron/additional_inputs/additional_input.h>

typedef struct additional_input_t {
    //REAL my_parameter;
    //REAL input_current;
} additional_input_t;


//! \brief Gets the value of current provided by the additional input this
//!     timestep
//! \param[in] additional_input The additional input type pointer to the
//!     parameters
//! \param[in] membrane_voltage The membrane voltage of the neuron
//! \return The value of the input after scaling
static input_t additional_input_get_input_value_as_current(
        additional_input_t *additional_input,
        state_t membrane_voltage) {
    use(membrane_voltage);
    additional_input->input_current += additional_input->my_parameter;
    return additional_input->input_current;
}

//! \brief Notifies the additional input type that the neuron has spiked
//! \param[in] additional_input The additional input type pointer to the
//!     parameters
static void additional_input_has_spiked(
        additional_input_t *additional_input) {
    additional_input->input_current = 0;
}


#endif // _MY_ADDITIONAL_INPUT_H_
