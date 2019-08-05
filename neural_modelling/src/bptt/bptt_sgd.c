#include <stdbool.h>
#include <stdint.h>
#include <math.h>

#include <spin1_api.h>
#include <debug.h>


#include <data_specification.h>
#include <simulation.h>
#include <recording.h>


//----------------------------------------------------------------------------
// Enumerations
//----------------------------------------------------------------------------
typedef enum
{
  REGION_SYSTEM,
  REGION_BPTT_SGD,
  REGION_RECORDING,
  REGION_PARAM,
} region_t;

//----------------------------------------------------------------------------
// Globals
//----------------------------------------------------------------------------
static uint32_t infinite_run;
static uint32_t _time = 0;
//! the number of timer ticks that this model should run for before exiting.
uint32_t simulation_ticks = 0;

//----------------------------------------------------------------------------
// Functions
//----------------------------------------------------------------------------

static bool initialize(uint32_t *timer_period)
{
    io_printf(IO_BUF, "Initialise bptt_sgd: started\n");

    // Get the address this core's DTCM data starts at from SRAM
    address_t address = data_specification_get_data_address();

    // Read the header
    if (!data_specification_read_header(address))
    {
        return false;
    }

    // Get the timing details and set up thse simulation interface
    if (!simulation_initialise(data_specification_get_region(REGION_SYSTEM, address),
    					APPLICATION_NAME_HASH, timer_period, &simulation_ticks,
						&infinite_run, 1, NULL))
    {
        return false;
    }

    io_printf(IO_BUF, "simulation time = %u\n", simulation_ticks);

    // Read BPTT SGD Region
    address_t bptt_sgd_region = data_specification_get_region(REGION_BPTT_SGD, address);
    io_printf(IO_BUF, "bptt_gd data value: %u\n", bptt_sgd_region[0]);


    //get recording region
    address_t recording_address = data_specification_get_region(
                                       REGION_RECORDING,address);

    // Read param region
    address_t param_region = data_specification_get_region(REGION_PARAM, address);

    io_printf(IO_BUF, "params region 1: %u\n", param_region[0]);
    io_printf(IO_BUF, "params region 2: %u\n", param_region[1]);

    // Setup recording
    uint32_t recording_flags = 0;
    if (!recording_initialize(recording_address, &recording_flags))
    {
        rt_error(RTE_SWERR);
        return false;
    }

     io_printf(IO_BUF, "Initialise: completed successfully\n");

     return true;
}

void resume_callback() {
    recording_reset();
}

void timer_callback(uint unused, uint dummy)
{
//    io_printf(IO_BUF, "time = %d", _time);
    use(unused);
    use(dummy);
    // If a fixed number of simulation ticks are specified and these have passed
    //
    //  ticks++;
    //this makes it count twice, WTF!?

    _time++;

    io_printf(IO_BUF, "Simulation time: %u\n", _time);

    if (!infinite_run && _time >= simulation_ticks)
    {
        io_printf(IO_BUF, "if time = %d\n", _time);
        //spin1_pause();
        recording_finalise();
        // go into pause and resume state to avoid another tick
        simulation_handle_pause_resume(resume_callback);
        //    spin1_callback_off(MC_PACKET_RECEIVED);

        simulation_ready_to_read();

         _time -= 1;
         return;
     }

}







//-------------------------------------------------------------------------------

//----------------------------------------------------------------------------
// Entry point
//----------------------------------------------------------------------------
void c_main(void)
{
    // Load DTCM data
    uint32_t timer_period;
    if (!initialize(&timer_period))
    {
        io_printf(IO_BUF,"Error in initialisation - exiting!\n");
        rt_error(RTE_SWERR);
        return;
    }




    // Set timer tick (in microseconds)
    io_printf(IO_BUF, "setting timer tick callback for %d microseconds\n",
              timer_period);
    spin1_set_timer_tick(timer_period);

    io_printf(IO_BUF, "simulation_ticks %d\n", simulation_ticks);

    // Register callback
    spin1_callback_on(TIMER_TICK, timer_callback, 2);
//    spin1_callback_on(MC_PACKET_RECEIVED, mc_packet_received_callback, -1);

    _time = UINT32_MAX;

    simulation_run();
}


