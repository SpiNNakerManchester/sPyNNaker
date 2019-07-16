#ifndef _FORMATION_H_
#define _FORMATION_H_

#include <neuron/structural_plasticity/sp_structs.h>

address_t synaptogenesis_formation_init(address_t address);

//! \brief Formation rule for synaptogenesis
//! \param[in] rewiring_data Pointer to rewiring data
//! \param[in] current_state Pointer to current state
//! \param[in] time Time of formation
//! \param[in] row The row to form within
//! \return if row was modified
static inline bool synaptogenesis_formation_rule(rewiring_data_t *rewiring_data,
        current_state_t *current_state, uint32_t time, address_t row);

#endif // _FORMATION_H_
