#ifndef _NEURON_IMPL_H_
#define _NEURON_IMPL_H_

#include "../../common/neuron-typedefs.h"

//! Forward declaration of the neuron impl pointer
typedef struct neuron_impl_t* neuron_impl_pointer_t;

static void neuron_impl_convert_inputs_to_current(
		input_t exc_value, input_t inh_value, input_type_pointer_t input_type,
		state_t voltage);

//! \brief Sets up the conversion of an excitatory input to current
//! \param[in] exc_value The value of the excitatory input before conversion
//! \param[in] input_type The input type pointer to the parameters
//! \param[in] voltage The voltage to use in conversion
//! \return None
static void neuron_impl_convert_excitatory_input_to_current(
		input_t exc_input_value,
		input_type_pointer_t input_type, state_t voltage);

//! \brief Sets up the conversion of an inhibitory input to current
//! \param[in] inh_value The value of the inhibitory input before conversion
//! \param[in] input_type The input type pointer to the parameters
//! \param[in] voltage The voltage to use in conversion
//! \return None
static void neuron_impl_convert_inhibitory_input_to_current(
		input_t inh_input_value,
		input_type_pointer_t input_type, state_t voltage);

//! \return The global excitatory input value
static input_t neuron_impl_get_excitatory_input();

//! \return The global inhibitory input value
static input_t neuron_impl_get_inhibitory_input();

//! \brief Gets the value to be recorded as the excitatory value
//! \return The global excitatory input value
static input_t neuron_impl_get_recording_excitatory_value();

//! \brief Gets the value to be recorded as the inhibitory value
//! \return The global inhibitory input value
static input_t neuron_impl_get_recording_inhibitory_value();

#endif // _NEURON_IMPL_H_
