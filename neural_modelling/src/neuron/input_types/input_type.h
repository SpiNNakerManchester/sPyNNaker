#ifndef _INPUT_TYPE_H_
#define _INPUT_TYPE_H_

#include "../../common/neuron-typedefs.h"

//! Forward declaration of the input type pointer
typedef struct input_type_t* input_type_pointer_t;

//! \brief Gets the actual input value - allows any scaling to take place
//! \param[in/out] value The array of the recepor-based values of the input
//!  before scaling
//! \param[in] input_type The input type pointer to the parameters
//! \return Pointer to array of values of the receptor-based input after
//!  scaling
static input_t* input_type_get_input_value(
    input_t* value, input_type_pointer_t input_type,
	uint16_t num_receptors);

//! \brief Converts an excitatory input into an excitatory current
//! \param[in/out] exc_input Pointer to array of excitatory inputs from
//! different receptors this timestep - note that this will already have been
//! scaled by input_type_get_input_value
//! \param[in] input_type The input type pointer to the parameters
//! \param[in] membrane_voltage The membrane voltage to use for the input
//! \return void
static void input_type_convert_excitatory_input_to_current(
    input_t* exc_input, input_type_pointer_t input_type,
    state_t membrane_voltage);

//! \brief Converts an inhibitory input into an inhibitory current
//! \param[in/out] inh_input Pointer to array of inhibitory inputs from
//! different receptors this timestep - note that this will already have been
//! scaled by input_type_get_input_value
//! \param[in] input_type The input type pointer to the parameters
//! \param[in] membrane_voltage The membrane voltage to use for the input
//! \return void
static void input_type_convert_inhibitory_input_to_current(
    input_t* inh_input, input_type_pointer_t input_type,
    state_t membrane_voltage);

#endif // _INPUT_TYPE_H_
