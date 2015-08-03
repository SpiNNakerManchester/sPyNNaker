/*! \file
 *
 *  \brief a interface
 */

#ifndef _NEURON_MODEL_H_
#define _NEURON_MODEL_H_

#include "../../common/neuron-typedefs.h"

//! Forward declaration of neuron type (creates a definition for a pointer to a
//   Neuron parameter struct
typedef struct neuron_t* neuron_pointer_t;

//! Forward declaration of global neuron parameters
typedef struct global_neuron_params_t* global_neuron_params_pointer_t;

//! \brief set the global neuron parameters
//! \param[in] params The parameters to set
void neuron_model_set_global_neuron_params(
    global_neuron_params_pointer_t params);

//! \brief setup function which needs to be called in main program before any
//! neuron code executes currently minimum 100, then in 100 steps...  if not
//! called then defaults to 1ms time step
//! \param[in] microsecs the amount of time between timer ticks in microseconds
//! \return This method does not return anything
void neuron_model_set_machine_timestep(timer_t microsecs);

//! \brief Function that converts an input into the real value to be used by the
//! neuron; Allows e.g. scaling of the neuron inputs for better precision
//! \param[in] input a pointer to the array of inputs received this timer tick
//! which can have an effect on the neuron in terms of stimulation.
//! \return a new pointer to the converted/scaled inputs which are now
//! usable by the neural model.
static input_t neuron_model_convert_input(input_t input);

//! \brief primary function called in timer loop after synaptic updates
//! \param[in] exc_input The inputs received this timer tick that produces
//! a positive reaction within the neuron in terms of stimulation.
//! \param[in] inh_input The inputs received this timer tick that produces
//! a negative reaction within the neuron in terms of stimulation.
//! \param[in] external_bias This is the intrinsic plasticity which could be
//! used for ac, noisy input etc etc. (general purpose input)
//! \param[in] neuron the pointer to a neuron parameter struct which contains
//! all the parameters for a specific neuron
//! \return bool which states if the neuron model was successful in updating
//! its state
bool neuron_model_state_update(input_t exc_input, input_t inh_input,
                               input_t external_bias, neuron_pointer_t neuron);

//! \brief get the neuron membrane voltage for a given neuron parameter set
//! \param[in] neuron a pointer to a neuron parameter struct which contains
//! all the parameters for a specific neuron
//! \return state_t the voltage membrane for a given neuron with the neuron
//! parameters specified in neuron
state_t neuron_model_get_membrane_voltage(restrict neuron_pointer_t neuron);

//! \brief printout of neuron definition and state variables
//! \param[in] neuron a pointer to a neuron parameter struct which contains all
//! the parameters for a specific neuron
//! \return None, this method does not return anything
void neuron_model_print(restrict neuron_pointer_t neuron);

#endif // _NEURON_MODEL_H_
