#include "last_neuron_selection_impl.h"

//! after a set of rewiring attempts, update the indices in the circular buffer
//! between which we will be looking at the next batch of attempts
void update_goal_posts(uint32_t time) {
    use(time);
    if (!received_any_spike()) {
        return;
    }
    cb_info.cb = get_circular_buffer();
    cb_info.cb_total_size = circular_buffer_real_size(cb_info.cb);

    cb_info.my_cb_output = cb_info.my_cb_input;
    cb_info.my_cb_input = (
        circular_buffer_input(cb_info.cb)
        & cb_info.cb_total_size);

    cb_info.no_spike_in_interval = (
        cb_info.my_cb_input >= cb_info.my_cb_output
        ? cb_info.my_cb_input - cb_info.my_cb_output
        : (cb_info.my_cb_input + cb_info.cb_total_size + 1) -
            cb_info.my_cb_output);
}



