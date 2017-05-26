#ifndef _NEURON_IMPL_STANDARD_H_
#define _NEURON_IMPL_STANDARD_H_

#include "neuron_impl.h"
//#include "../input_types/input_type.h"

//! neuron_impl_t struct
typedef struct neuron_impl_t {
//
//	// excitatory input value
//	input_t	exc_input_value;
//	// excitatory converted value
//	input_t	exc_input;
//	// excitatory input value
//	input_t	inh_input_value;
//	// excitatory converted value
//	input_t	inh_input;
//
} neuron_impl_t;

input_t exc_input_value=0;
input_t inh_input_value=0;

//! \brief Sets up the conversion of an excitatory input to current
//! \param[in] exc_value The value of the excitatory input before conversion
//! \param[in] input_type The input type pointer to the parameters
//! \param[in] voltage The voltage to use in conversion
//! \return The value of the input after conversion
static input_t neuron_impl_convert_excitatory_input_to_current(
		input_t exc_value,
		input_type_pointer_t input_type, state_t voltage)
{
	//
//    neuron_impl->exc_input_value =
//    		input_type_get_input_value(exc_value, input_type);
//    neuron_impl->exc_input = input_type_convert_excitatory_input_to_current(
//    		neuron_impl->exc_input_value, input_type, voltage);
    exc_input_value =
    		input_type_get_input_value(exc_value, input_type);
    input_t exc_input = input_type_convert_excitatory_input_to_current(
    		exc_input_value, input_type, voltage);

//    return neuron_impl->exc_input;
    return exc_input;
}

//! \brief Sets up the conversion of an inhibittory input to current
//! \param[in] inh_value The value of the inhibitory input before conversion
//! \param[in] input_type The input type pointer to the parameters
//! \param[in] voltage The voltage to use in conversion
//! \return The value of the input after conversion
static input_t neuron_impl_convert_inhibitory_input_to_current(
		input_t inh_value,
		input_type_pointer_t input_type, state_t voltage)
{
	//
//    neuron_impl->inh_input_value =
//    		input_type_get_input_value(inh_value, input_type);
//    neuron_impl->inh_input = input_type_convert_inhibitory_input_to_current(
//    		neuron_impl->inh_input_value, input_type, voltage, 0);
    inh_input_value =
    		input_type_get_input_value(inh_value, input_type);
    input_t inh_input = input_type_convert_inhibitory_input_to_current(
    		inh_input_value, input_type, voltage, 0);

//    return neuron_impl->inh_input;
    return inh_input;
}

//! \brief Gets the value to be recorded as the excitatory value
static input_t neuron_impl_get_recording_excitatory_value()
//		neuron_impl_pointer_t neuron_impl)
{
//	return neuron_impl->exc_input_value;
	return exc_input_value;
}

//! \brief Gets the value to be recorded as the inhibitory value
static input_t neuron_impl_get_recording_inhibitory_value()
//		neuron_impl_pointer_t neuron_impl)
{
//	return neuron_impl->inh_input_value;
	return inh_input_value;
}

#endif // _NEURON_IMPL_STANDARD_H_

