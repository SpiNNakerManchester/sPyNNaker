#ifndef _FORMATION_H_
#define _FORMATION_H_

#include <neuron/structural_plasticity/synaptogenesis/sp_structs.h>

//! \brief Read and return an formation parameter data structure from the
//!        data stream
//! \param[in/out] The data stream to read from, updated to the new position
//!                after the read is done
//! \return the read parameters data structure
struct formation_params *synaptogenesis_formation_init(uint8_t **data);

//! \brief Formation rule for synaptogenesis
//! \param[in] rewiring_data Pointer to rewiring data
//! \param[in] current_state Pointer to current state
//! \param[in] time Time of formation
//! \param[in] row The row to form within
//! \return if row was modified
static inline bool synaptogenesis_formation_rule(
        current_state_t *current_state, struct formation_params *params,
        uint32_t time, address_t row);

#endif // _FORMATION_H_
