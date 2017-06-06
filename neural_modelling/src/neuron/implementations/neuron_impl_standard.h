#ifndef _NEURON_IMPL_STANDARD_H_
#define _NEURON_IMPL_STANDARD_H_

#include "neuron_impl.h"

//! neuron_impl_t struct
typedef struct neuron_impl_t {
} neuron_impl_t;

input_t gl_exc_input=0;
input_t exc_input_value=0;
input_t gl_inh_input=0;
input_t inh_input_value=0;

//! \brief Sets up the conversion of (voltage) input to current
//! \param[in] exc_value The value of the excitatory input before conversion
//! \param[in] inh_value The value of the inhibitory input before conversion
//! \param[in] input_type The input type pointer to the parameters
//! \param[in] voltage The voltage to use in conversion
//! \return None
static void neuron_impl_convert_inputs_to_current(
		input_t exc_value, input_t inh_value, input_type_pointer_t input_type,
		state_t voltage)
{
	exc_input_value = input_type_get_input_value(exc_value, input_type);
	inh_input_value = input_type_get_input_value(inh_value, input_type);

	neuron_impl_convert_excitatory_input_to_current(
			exc_input_value, input_type, voltage);
	neuron_impl_convert_inhibitory_input_to_current(
			inh_input_value, input_type, voltage);
}

//! \brief Sets up the conversion of an excitatory input to current
//! \param[in] exc_value The value of the excitatory input before conversion
//! \param[in] input_type The input type pointer to the parameters
//! \param[in] voltage The voltage to use in conversion
//! \return None
static void neuron_impl_convert_excitatory_input_to_current(
		input_t exc_input_value,
		input_type_pointer_t input_type, state_t voltage)
{
    gl_exc_input = input_type_convert_excitatory_input_to_current(
    		exc_input_value, input_type, voltage);
}

//! \brief Sets up the conversion of an inhibittory input to current
//! \param[in] inh_value The value of the inhibitory input before conversion
//! \param[in] input_type The input type pointer to the parameters
//! \param[in] voltage The voltage to use in conversion
//! \return The value of the input after conversion
static void neuron_impl_convert_inhibitory_input_to_current(
		input_t inh_value,
		input_type_pointer_t input_type, state_t voltage)
{
    gl_inh_input = input_type_convert_inhibitory_input_to_current(
    		inh_input_value, input_type, voltage);
}

//! \brief Gets excitatory input value
//! \return The excitatory input value
static input_t neuron_impl_get_excitatory_input()
{
	return gl_exc_input;
}

//! \brief Gets inhibitory input value
//! \return The inhibitory input value
static input_t neuron_impl_get_inhibitory_input()
{
	return gl_inh_input;
}

//! \brief Gets the value to be recorded as the excitatory value
//! \return The excitatory recording value
static input_t neuron_impl_get_recording_excitatory_value()
{
	return exc_input_value;
}

//! \brief Gets the value to be recorded as the inhibitory value
//! \return The inhibitory recording value
static input_t neuron_impl_get_recording_inhibitory_value()
{
	return inh_input_value;
}

#endif // _NEURON_IMPL_STANDARD_H_
