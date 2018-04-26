#ifndef _SYNAPSE_IMPL_H_
#define _SYNAPSE_IMPL_H_

#include <common/neuron-typedefs.h>
#include <neuron/synapse_types/synapse_types.h>

//! \brief Add inputs as required to the implementation
//! \param[in] synapse_type_index the synapse type (exc. or inh.)
//! \param[in] parameter parameters for synapse shaping
//! \param[in] weights_this_timestep Weight inputs to be added
//! \return None
static void synapse_impl_add_inputs(
		index_t synapse_type_index, synapse_param_pointer_t parameter,
		input_t weights_this_timestep);

#endif // _SYNAPSE_IMPL_H_
