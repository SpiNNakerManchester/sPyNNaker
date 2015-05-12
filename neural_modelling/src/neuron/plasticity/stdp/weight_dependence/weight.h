/*!
 * \file
 * \brief interface for different weight implementations for the weight half of
 *  a STDP rule.
 *
 *  \details the API interface contains:
 *  - weight_initialise(address, ring_buffer_to_input_buffer_left_shifts):
 *        initialised the weight aspect of a STDP rule.
 *  - weight_get_initial(weight, synapse_type):
 *
 *  - weight_get_final(new_state):
 *
 *
 */

#ifndef _WEIGHT_H_
#define _WEIGHT_H_

#include "../../../../common/neuron-typedefs.h"
#include "../../../synapse_row.h"

/*! \brief initialised the weight aspect of a STDP rule.
 * \param[in] address: the absolute address in SRAM where the weight parameters
 *  are stored.
 * \param[in] ring_buffer_to_input_buffer_left_shifts: how much a value needs
 * to be shifted in the left direction to support comprises with fixed point
 * arithmetic
 * \param[in] weight_dependence_magic_number the magic number which represents
 * which weight dedependence component this model is expected to use.
 * \return address_t: returns the end of the weight region as an absolute
 * SDRAM memory address, or NULL if the init failed.
 */
address_t weight_initialise(
        address_t address, uint32_t *ring_buffer_to_input_buffer_left_shifts,
        uint32_t weight_dependence_magic_number);

/*!
 * \brief
 */
static weight_state_t weight_get_initial(weight_t weight, index_t synapse_type);

static weight_t weight_get_final(weight_state_t new_state);

#endif // _WEIGHT_H_
