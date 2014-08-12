#include "spin-neuron-impl.h"

bool system_load_dtcm ()
{
  log_info("system_load_dtcm: started");

  // Get the address this core's DTCM data starts at from SRAM
  address_t address = system_load_sram();

  uint32_t version;
  uint32_t flags   = 0;
  if(!system_header_filled (address, &version, flags))
  {
    return (false);
  }

  uint32_t spike_history_recording_region_size, neuron_potentials_recording_region_size, neuron_gsyns_recording_region_size;
  if (!system_data_filled (region_start(0, address), flags, &spike_history_recording_region_size, &neuron_potentials_recording_region_size, &neuron_gsyns_recording_region_size))
    return (false);

  if (!neural_data_filled (region_start(1, address), flags))  // modified for use with simon's data blob
    return (false);

  if (!synaptic_current_data_filled (region_start(2, address), flags))
    return (false);

  if (!row_size_table_filled (region_start(3, address), flags))
    return (false);

  if (!master_population_table_filled (region_start(4, address), flags))
    return (false);

  if (!synaptic_data_filled (region_start(5, address), flags))
    return (false);

   if (!plasticity_region_filled(region_start(6, address), flags))
    return false;

  // Setup output recording regions
  if (!recording_data_filled (region_start(7, address), flags, e_recording_channel_spike_history, spike_history_recording_region_size))
    return (false);

  if (!recording_data_filled (region_start(8, address), flags, e_recording_channel_neuron_potential, neuron_potentials_recording_region_size))
    return (false);

  if (!recording_data_filled (region_start(9, address), flags, e_recording_channel_neuron_gsyn, neuron_gsyns_recording_region_size))
    return (false);


  log_info("system_load_dtcm: completed successfully");

  return (true);
}
