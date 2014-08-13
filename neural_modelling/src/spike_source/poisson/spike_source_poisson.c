
#include "../common/spike_source_impl.h"

#include <random.h>

#include <string.h>

typedef struct slow_spike_source_t
{
  uint32_t neuron_id;
  uint32_t start_ticks;
  uint32_t end_ticks;

  accum mean_isi_ticks;
  accum time_to_spike_ticks;
} slow_spike_source_t;

typedef struct fast_spike_source_t
{
  uint32_t neuron_id;
  uint32_t start_ticks;
  uint32_t end_ticks;

  unsigned long fract exp_minus_lambda;
} fast_spike_source_t;

// Globals
static slow_spike_source_t *slow_spike_source_array = NULL;
static fast_spike_source_t *fast_spike_source_array = NULL;
static uint32_t num_slow_spike_sources = 0;
static uint32_t num_fast_spike_sources = 0;
static mars_kiss64_seed_t spike_source_seed;

static inline accum slow_spike_source_get_time_to_spike( accum mean_isi_ticks )
{
  return exponential_dist_variate( mars_kiss64_seed, spike_source_seed ) * mean_isi_ticks;
}

static inline uint32_t fast_spike_source_get_num_spikes( unsigned long fract exp_minus_lambda )
{
  return poisson_dist_variate_exp_minus_lambda( mars_kiss64_seed, spike_source_seed, exp_minus_lambda );
}


bool spike_source_poisson_parameters_filled(address_t address, uint32_t flags)
{
  use(flags);

  log_info("spike_source_poisson_parameters_filled: starting");

  // changed from above for new file format 13-1-2014
  key   = address[0];
  log_info("\tkey = %08x, (x: %u, y: %u) proc: %u",
           key, key_x (key), key_y (key), key_p (key));

  uint32_t seed_size = sizeof(mars_kiss64_seed_t) / sizeof(uint32_t);
  memcpy( spike_source_seed, &address[1], seed_size * sizeof(uint32_t));
  validate_mars_kiss64_seed( spike_source_seed);

  log_info("\tSeed (%u) = %u %u %u %u", seed_size, spike_source_seed[0], spike_source_seed[1], spike_source_seed[2], spike_source_seed[3]);

  num_slow_spike_sources = address[1 + seed_size];
  num_fast_spike_sources = address[2 + seed_size];
  num_spike_sources = num_slow_spike_sources + num_fast_spike_sources;
  log_info("\tslow spike sources = %u, fast spike sources = %u, spike sources = %u", num_slow_spike_sources, num_fast_spike_sources, num_spike_sources);

  // Allocate DTCM for array of slow spike sources and copy block of data
  slow_spike_source_array = (slow_spike_source_t*)spin1_malloc( num_slow_spike_sources * sizeof(slow_spike_source_t) );
  memcpy( slow_spike_source_array, &address[3 + seed_size], num_slow_spike_sources * sizeof(slow_spike_source_t) );

  // Loop through slow spike sources and initialise 1st time to spike
  for(index_t s = 0; s < num_slow_spike_sources; s++)
  {
    slow_spike_source_array[s].time_to_spike_ticks = slow_spike_source_get_time_to_spike(slow_spike_source_array[s].mean_isi_ticks);
  }

  // Allocate DTCM for array of fast spike sources and copy block of data
  uint32_t fast_spike_source_offset = 3 + seed_size + (num_slow_spike_sources * (sizeof(slow_spike_source_t) / sizeof(uint32_t)));
  fast_spike_source_array = (fast_spike_source_t*)spin1_malloc( num_fast_spike_sources * sizeof(fast_spike_source_t) );
  memcpy( fast_spike_source_array, &address[fast_spike_source_offset], num_fast_spike_sources * sizeof(fast_spike_source_t) );

#ifdef DEBUG
  for (index_t s = 0; s < num_fast_spike_sources; s++)
  {
	log_info("\t\tNeuron id %d, exp(-k) = %0.8x", fast_spike_source_array[s].neuron_id, fast_spike_source_array[s].exp_minus_lambda);
  }
#endif // DEBUG
  log_info("spike_source_poisson_parameters_filled: completed successfully");
  return (true);
}

bool spike_source_data_filled(address_t base_address, uint32_t flags, uint32_t spike_history_recording_region_size,
                              uint32_t neuron_potentials_recording_region_size, uint32_t neuron_gsyns_recording_region_size)
{
  use(neuron_potentials_recording_region_size);
  use(neuron_gsyns_recording_region_size);

  log_info("spike_source_data_filled: starting");

  if (!spike_source_poisson_parameters_filled (region_start(2, base_address), flags))  // modified for use with simon's data blob
    return (false);

  // Setup output recording regions
  if (!recording_data_filled (region_start(3, base_address), flags, e_recording_channel_spike_history, spike_history_recording_region_size))
    return (false);

  log_info("spike_source_data_filled: completed successfully");

  return true;
}

void spike_source_dma_callback(uint unused, uint tag)
{
  use(unused);
  use(tag);
}

void spike_source_generate(uint32_t tick)
{
  // Loop through slow spike sources
  for(index_t s = 0; s < num_slow_spike_sources; s++)
  {
    // If this spike source is active this tick
    slow_spike_source_t *slow_spike_source = &slow_spike_source_array[s];
    if(tick >= slow_spike_source->start_ticks && tick < slow_spike_source->end_ticks)
    {
      // If this spike source should spike now
      if(slow_spike_source->time_to_spike_ticks <= 0.0k)
      {
        // Write spike to out spikes
        out_spike(slow_spike_source->neuron_id);

        // Send package
        spin1_send_mc_packet(key | slow_spike_source->neuron_id, NULL, NO_PAYLOAD);

#ifdef SPIKE_DEBUG
          io_printf(IO_BUF, "Sending spike packet %x at %d\n",
        		  key | slow_spike_source->neuron_id, tick);
#endif // SPIKE_DEBUG

        // Update time to spike
        slow_spike_source->time_to_spike_ticks += slow_spike_source_get_time_to_spike(slow_spike_source->mean_isi_ticks);
      }

      // Subtract tick
      slow_spike_source->time_to_spike_ticks -= 1.0k;
    }
  }

  // Loop through fast spike sources
  for(index_t f = 0; f < num_fast_spike_sources; f++)
  {
    // If this spike source is active this tick
    fast_spike_source_t *fast_spike_source = &fast_spike_source_array[f];
    if(tick >= fast_spike_source->start_ticks && tick < fast_spike_source->end_ticks)
    {
      // Get number of spikes to send this tick
      uint32_t num_spikes = fast_spike_source_get_num_spikes(fast_spike_source->exp_minus_lambda);
      log_info("Generating %d spikes", num_spikes);

      // If there are any
      if(num_spikes > 0)
      {
        // Write spike to out spikes
        out_spike(fast_spike_source->neuron_id);

        // Send spikes
        const uint32_t spike_key = key | fast_spike_source->neuron_id;
        for(uint32_t s = 0; s < num_spikes; s++)
        {
#ifdef SPIKE_DEBUG
          io_printf(IO_BUF, "Sending spike packet %x at %d\n", spike_key, tick);
#endif // SPIKE_DEBUG
          while(!spin1_send_mc_packet(spike_key, NULL, NO_PAYLOAD)) {
              spin1_delay_us(1);
          }
        }
      }
    }
  }
}
