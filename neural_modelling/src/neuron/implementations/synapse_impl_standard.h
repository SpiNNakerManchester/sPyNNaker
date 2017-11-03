#ifndef _SYNAPSE_IMPL_STANDARD_H_
#define _SYNAPSE_IMPL_STANDARD_H_

#include "synapse_impl.h"

//! synapse_impl_t struct (empty at the moment...)
typedef struct synapse_impl_t {
} synapse_impl_t;

//! \brief Add inputs as required to the implementation
//! \param[in] synapse_type_index the synapse type (exc. or inh.)
//! \param[in] parameter parameters for synapse shaping
//! \param[in] weights_this_timestep Weight inputs to be added
static void synapse_impl_add_inputs(
		index_t synapse_type_index, synapse_param_pointer_t parameter,
		input_t weights_this_timestep)
{
	// simple wrapper to synapse type input function
	synapse_types_add_neuron_input(synapse_type_index,
			parameter, weights_this_timestep);
}

#endif // _SYNAPSE_IMPL_STANDARD_H_
