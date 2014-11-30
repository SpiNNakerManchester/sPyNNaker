#ifndef SYNAPSE_WEIGHT_IMPL_H
#define SYNAPSE_WEIGHT_IMPL_H

//---------------------------------------
// Structures
//---------------------------------------
// Plastic synapse types are just weights;
typedef weight_t plastic_synapse_t;

// The update state is purely a weight state
typedef weight_state_t update_state_t;

// The final state is just a weight as this is  
// Both the weight and the synaptic word
typedef weight_t final_state_t;

//---------------------------------------
// Synapse interface functions
//---------------------------------------
static inline update_state_t synapse_init(plastic_synapse_t synaptic_word)
{
  return weight_init(synaptic_word);
}
//---------------------------------------
static inline final_state_t synapse_get_final(update_state_t state)
{
  return weight_get_final(state);
}
//---------------------------------------
static inline weight_t synapse_get_final_weight(final_state_t final_state)
{
  return final_state;
}
//---------------------------------------
static inline plastic_synapse_t synapse_get_final_synaptic_word(final_state_t final_state)
{
  return final_state;
}
#endif  // SYNAPSE_WEIGHT_IMPL_H