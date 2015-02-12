#ifndef PROFILER_H
#define PROFILER_H

#include <stdint.h>
#include "spinnaker.h"
#include "debug.h"

//---------------------------------------
// Macros
//---------------------------------------
// Types of profiler event
#define PROFILER_ENTER          (1 << 31)
#define PROFILER_EXIT           0

// Profiler tags
#define PROFILER_TIMER          0
#define PROFILER_DMA            1

#ifdef PROFILER_ENABLED

//---------------------------------------
// Externals
//---------------------------------------
extern uint32_t *profiler_count;
extern uint32_t profiler_samples_remaining;
extern uint32_t *profiler_output;

//---------------------------------------
// Declared functions
//---------------------------------------
// Initialised the profiler from a SDRAM region
void profiler_read_region(uint32_t* address);

// Finalises profiling - potentially slow process of writing profiler_count to SDRAM
void profiler_finalise();

// Sets up profiler - starts timer 2 etc
void profiler_init();

//---------------------------------------
// Inline functions
//---------------------------------------
static inline void profiler_write_entry(uint32_t tag)
{
  if(profiler_samples_remaining > 0)
  {
    // **NOTE** calling this from multiple ISRs causes 
    // issues which disabling interrupts doesn't fix!
    //uint sr = spin1_irq_disable();
    *profiler_output++ = tc[T2_COUNT];
    *profiler_output++ = tag;
    profiler_samples_remaining--;
    //spin1_mode_restore(sr);
  }
}
#else // PROFILER_ENABLED

#define profiler_read_region(address) skip()
#define profiler_finalise() skip()
#define profiler_init() skip()
#define profiler_write_entry(tag) skip()

#endif  // PROFILER_ENABLED

#endif  // PROFILER_H
