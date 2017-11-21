#ifndef _SYNAPTOGENESIS_DYNAMICS_H_
#define _SYNAPTOGENESIS_DYNAMICS_H_


#include "../spike_processing.h"

address_t synaptogenesis_dynamics_initialise(
	address_t sdram_sp_address);

void synaptogenesis_dynamics_rewire(uint32_t time);

bool synaptogenesis_dynamics_formation_rule();

bool synaptogenesis_dynamics_elimination_rule();

void synaptic_row_restructure();

int32_t get_p_rew();

bool is_fast();

void update_goal_posts(uint32_t time);

//bool record_this_timestep = false;
//int recording_channel;
//static void record_rewiring(int rewiring_recording_channel) {
//    record_this_timestep = true;
//    recording_channel = rewiring_recording_channel;
//}

//static bool consume_recording() {
//    if (record_this_timestep) {
//        record_this_timestep = false;
//        return true;
//    }
//    return false;
//}

#endif // _SYNAPTOGENESIS_DYNAMICS_H_
