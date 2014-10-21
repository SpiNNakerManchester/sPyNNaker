#ifndef COMMON_IMPL_H
#define COMMON_IMPL_H

#include "common-typedefs.h"
#include "spin-print.h"
#include "debug.h"
#include "bit_field.h"

// Externals
extern bit_field_t out_spikes;

extern uint32_t simulation_ticks;
extern uint32_t timer_period;

// Inline functions
static inline void out_spike (index_t n) { bit_field_set (out_spikes, n); }

static inline key_t key_x (key_t k) { return (k >> 24); }
static inline key_t key_y (key_t k) { return ((k >> 16) & 0xFF); }
//static inline key_t key_p (key_t k) { return (((k >> 11) & 0x1F) + 1); }
static inline key_t key_p (key_t k) { return ((k >> 11) & 0x1F); }

static inline key_t make_key (key_t x, key_t y, key_t p)
{ return ((x << 24) | (y << 16) | ((p-1) << 11)); }

static inline uint32_t make_pid (key_t x, key_t y, key_t p)
{ return (((x << 3) + y)*18 + p); }

// Function declarations for bit_field.c:
void print_bit_field_bits (bit_field_t b, size_t s);
void print_bit_field      (bit_field_t b, size_t s);
void random_bit_field     (bit_field_t b, size_t s);

// Function declarations for configuration.c:
bool system_header_filled         (uint32_t* address, uint32_t* version, uint32_t flags);
bool system_data_filled           (uint32_t* address, uint32_t flags, uint32_t *spike_history_recording_region_size, uint32_t *neuron_potentials_recording_region_size, uint32_t *neuron_gsyns_recording_region_size);
bool system_data_test_bit         (system_data_e bit);
bool check_magic_number           (uint32_t* start);
bool vector_copied                (uint32_t*, uint32_t, uint32_t*, uint32_t);
bool half_word_vector_copied      (uint16_t*, uint32_t, uint32_t*, uint32_t);
bool byte_vector_copied           (uint8_t*,  uint32_t, uint32_t*, uint32_t);
bool check_deadbeef (uint32_t* start);
uint32_t* region_start           (uint32_t n, uint32_t* address);
uint32_t* configuration_reader_offset (uint32_t* address, uint32_t offset);

// Defined in spin1-api-configuration.c
address_t system_load_sram();
bool system_runs_to_completion();
bool system_data_extracted();

// Function declarations for recording.c
bool recording_data_filled(address_t output_region, uint32_t flags, recording_channel_e channel, uint32_t size_bytes);
bool recording_record(recording_channel_e channel, void *data, uint32_t size_bytes);
void recording_finalise();

// Defined in spikes.c
bool add_spike               (spike_t e);
bool next_spike              (spike_t* e);
void initialize_spike_buffer (uint size);
void print_spike_buffer      (void);
bool get_next_spike_if_equals(spike_t s);
uint32_t n_spikes_in_buffer(void);
counter_t buffer_overflows   (void);

// Defined in out_spikes.c
void  reset_out_spikes      (void);
void  initialize_out_spikes (size_t max_spike_sources);
void  record_out_spikes     (void);
bool  empty_out_spikes      (void);
bool  nonempty_out_spikes   (void);
bool  out_spike_test        (index_t n);
void  print_out_spikes      (void);

#endif  // COMMON_IMPL_H
