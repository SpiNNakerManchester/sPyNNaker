#ifndef SYNAPSE_WEIGHT_IMPL_H
#define SYNAPSE_WEIGHT_IMPL_H

//---------------------------------------
// Structures
//---------------------------------------
// Plastic synapse types are just weights;
typedef weight_t plastic_synapse_t;

// The update state is purely a weight state
typedef weight_state_t update_state_t;

// **TODO** in these terms, this is pretty much common to everything so shouldn't be here
typedef struct final_state_t
{
  weight_t weight;
  plastic_synapse_t synaptic_word;
} final_state_t;

//---------------------------------------
// Synapse interface functions
//---------------------------------------
static inline update_state_t synapse_init(plastic_synapse_t synaptic_word)
{
  // Initialize the weight state from the synaptic word
  return weight_init(synaptic_word);
}
//---------------------------------------
static inline final_state_t synapse_get_final(update_state_t state)
{
  // Get weight from state
  weight_t weight = weight_get_final(state);
  
  // Return this as both the synaptic word and the weight
  return (final_state_t){ .weight = weight, .synaptic_word = weight };
}
#endif  // SYNAPSE_WEIGHT_IMPL_H