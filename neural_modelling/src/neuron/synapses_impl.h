#ifndef SYNAPSES_IMPL_H
#define SYNAPSES_IMPL_H


// The data structure layout supported by this API is designed for
// mixed plastic and fixed synapses.
//
// The data structure is treated as an array of 32-bit words.
// Special meanings are ascribed to the 0-th and 1-st elements
// of the array.
//
// We are expecting the original source address in SDRAM to be
// in location 0. The number of array elements in the plastic
// region is held in the upper part of row[1]. A tag to indicate
// the nature of the synaptic row structure is held in the lower
// part of row[1].
//
//   0:  [ SDRAM address from which row is copied ] filled by DMA handler
//   1:  [ Originating spike id                   ] filled by DMA handler
//   2:  [ N = <plastic elements>         | <tag> ]
//   3:  [ First word of plastic region           ]
//   ...
// N+2:  [ Last word of plastic region            ]
// N+3:  [ First word of fixed region             ]
//   ...
//  M:   [ Last word of fixed region              ]

/*static inline tag_t plastic_tag(address_t row)
{ 
  return ((tag_t)(row[2] & PLASTIC_TAG_MASK)); 
}

static inline size_t plastic_size(address_t row)
{ 
  return ((size_t)(row[2] >> PLASTIC_TAG_BITS)); 
}*/

static inline size_t plastic_size(address_t row)
{ 
  return (size_t)row[2]; 
}

// The following uses the original SDRAM address (stored in row [0])
// to calculate the start address in SDRAM for the write-back DMA.
// **NOTE** The point of this is to get the address in SDRAM of row[1]
static inline address_t plastic_write_back_address(address_t row)
{ 
  return ((address_t)(row[0]) + 1); 
}

// Returns the address of the plastic region
static inline address_t plastic_region(address_t row)
{
  return ((address_t)(& (row [3]))); 
}

// Returns the address of the nonplastic (or fixed) region
static inline address_t fixed_region(address_t row)
{ 
  return ((address_t)(& (row[plastic_size(row) + 3]))); 
}

static inline spike_t originating_spike(address_t row)
{
  return (spike_t)row[1];
}

// Within the fixed-region extracted using the above API, fixed[0]
// Contains the number of 32-bit fixed synaptic words, fixed[1]
// Contains the number of 16-buit plastic synapse control words
// (The weights for the plastic synapses are assumed to be stored
// In some learning-rule-specific format in the plastic region)
//   0:            [ F = Num fixed synapses                                   ]
//   1:           [ P = Size of plastic region in words                       ]
//   2:           [ First fixed synaptic word                                 ]
//   ...
// F+1:           [ Last fixed synaptic word                                  ]
// F+2:           [ 1st plastic synapse control word|2nd plastic control word ]
//   ...
// F+1+ceil(P/2): [ Last word of fixed region              ]
static inline size_t num_fixed_synapses(address_t fixed)
{ 
  return ((size_t)(fixed[0])); 
}

static inline size_t num_plastic_controls(address_t fixed)
{ 
  return ((size_t)(fixed[1])); 
}

static inline control_t* plastic_controls(address_t fixed)
{ 
  return ((control_t*)(& (fixed [2 + num_fixed_synapses (fixed)]))); 
}

static inline uint32_t *fixed_weight_controls(address_t fixed)
{ 
  return (& (fixed [2])); 
}

// The following are offset calculations into the ring buffers
static inline index_t sparse_index       (uint32_t x)
{ 
  return (x & SYNAPSE_INDEX_MASK); 
}

static inline index_t sparse_type        (uint32_t x)
{ 
  return ((x >> SYNAPSE_INDEX_BITS) & SYNAPSE_TYPE_MASK); 
}

static inline index_t sparse_type_index  (uint32_t x)
{ 
  return (x & SYNAPSE_TYPE_INDEX_MASK); 
}

static inline index_t sparse_delay       (uint32_t x)
{ 
  return ((x >> SYNAPSE_TYPE_INDEX_BITS) & SYNAPSE_DELAY_MASK); 
}

static inline weight_t sparse_weight      (uint32_t x)
{ 
  return (x >> (32-SYNAPSE_WEIGHT_BITS)); 
}

static inline index_t offset_current     (uint32_t t,uint32_t i)
{ 
  return ((t << SYNAPSE_INDEX_BITS) | i); 
}

static inline index_t offset_sparse      (uint32_t d, uint32_t ti)
{ 
  return (((d & SYNAPSE_DELAY_MASK) << SYNAPSE_TYPE_INDEX_BITS) | ti); 
}

static inline index_t offset_ring_buffer (uint32_t d,uint32_t t,uint32_t i)
{ 
  return (((d & SYNAPSE_DELAY_MASK) << SYNAPSE_TYPE_INDEX_BITS) | (t << SYNAPSE_INDEX_BITS) | i); 
}

#endif  // SYNAPSES_IMPL_H