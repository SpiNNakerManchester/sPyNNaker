import math
import logging
import matplotlib.pyplot as plt
import numpy as np

from data_specification.enums import DataType

from spinn_front_end_common.utilities.utility_objs import ProvenanceDataItem

logger = logging.getLogger(__name__)

# Default value of fixed-point one for STDP
STDP_FIXED_POINT_ONE = (1 << 11)

def float_to_fixed(value, fixed_point_one):
    return int(round(float(value) * float(fixed_point_one)))


def write_exp_lut(spec, time_constant, size, shift,
                  fixed_point_one=STDP_FIXED_POINT_ONE):
    # Calculate time constant reciprocal
    time_constant_reciprocal = 1.0 / float(time_constant)

    # Generate LUT
    last_value = None
    for i in range(size):

        # Apply shift to get time from index
        time = (i << shift)

        # Multiply by time constant and calculate negative exponential
        value = float(time) * time_constant_reciprocal
        exp_float = math.exp(-value)

        # Convert to fixed-point and write to spec
        last_value = float_to_fixed(exp_float, fixed_point_one)
        spec.write_value(data=last_value, data_type=DataType.INT16)

    # return last value reverted to float (should be 0 if correct)
    return float(last_value) / float(fixed_point_one)


def get_lut_provenance(
        pre_population_label, post_population_label, rule_name, entry_name,
        param_name, last_entry):
    # pylint: disable=too-many-arguments
    top_level_name = "{}_{}_STDP_{}".format(
        pre_population_label, post_population_label, rule_name)
    return ProvenanceDataItem(
        [top_level_name, entry_name], last_entry, report=last_entry > 0,
        message=(
            "The last entry in the STDP exponential lookup table for the {}"
            " parameter of the {} between {} and {} was {} rather than 0,"
            " indicating that the lookup table was not big enough at this"
            " timestep and value.  Try reducing the parameter value, or"
            " increasing the timestep".format(
                param_name, rule_name, pre_population_label,
                post_population_label, last_entry)))

def write_pfpc_lut(spec, peak_time, lut_size, shift, time_probe,
                  fixed_point_one=STDP_FIXED_POINT_ONE):

        # Add this to function arguments in the future
        machine_time_step = 1.0
        sin_pwr = 20

        # Calculate required time constant
        time_constant = 1/(math.atan(sin_pwr)/peak_time)
        inv_tau = (1.0 / float(time_constant)) #* (machine_time_step / 1000.0)

#         # caluclate time of peak (from differentiating kernel and setting to zero)
#         kernel_peak_time = math.atan(20) / inv_tau

         # evaluate peak value of kernel to normalise LUT
        kernel_peak_value = (math.exp(-peak_time*inv_tau) *
              math.sin(peak_time*inv_tau)**sin_pwr)

        # Generate LUT
        out_float = []
        out_fixed = []

        for i in range(0,lut_size): # note that i corresponds to 1 timestep!!!!!!

            # Multiply by inverse of time constant
            value = float(i) * inv_tau

            # Only take first peak from kernel
            if (value > math.pi):
                exp_float = 0
            else:
                # Evaluate kernel
                exp_float = math.exp(-value) * math.sin(value)**sin_pwr / kernel_peak_value

            # Convert to fixed-point
            exp_fix = float_to_fixed(exp_float, fixed_point_one)

            if spec is None: # in testing mode so print
                out_float.append(exp_float)
                out_fixed.append(exp_fix)
                if i == time_probe:
                    print "dt = {}, kernel value = {} (fixed-point = {})".format(
                        time_probe, exp_float, exp_fix)

            else: # at runtime, so write to spec
                spec.write_value(data=exp_fix, data_type=DataType.INT16)

        if spec is None:
            print "peak: time {}, value {}".format(peak_time, kernel_peak_value)
            t = np.arange(0,lut_size)
            plt.plot(t,out_float, label='float')
            # plt.plot(t,out_fixed, label='fixed')
            plt.legend()
            plt.show()


def write_mfvn_lut(spec, time_constant, lut_size, shift, time_probe,
                  fixed_point_one=STDP_FIXED_POINT_ONE):
        peak_time = 100.0
        tau = peak_time * 2/math.pi;
        machine_time_step = 1.0

        # This offset is the quasi-symmetry point
        sin_pwr = 20

# Write peak time in timesteps
        peak_time_data = int(peak_time * (1000.0 / machine_time_step) - lut_size/2  + 0.5)
        #print "peak time data:", peak_time_data, "peak_time:", peak_time

#         if spec is not None:
#             spec.write_value(data=peak_time_data,
#                          data_type=DataType.INT32)

        # Calculate 1/tau in machine time steps
        inv_tau = (1.0 / float(tau)) #* (machine_time_step / 1000.0)

        zero_offset = math.atan(-1./sin_pwr) # abscissae of the max point obtained by deriving the kernel and equal to zero
        max_value = math.exp(-math.pi/2)*math.sin(-math.pi/2)**sin_pwr

        if spec is None :
            print tau, inv_tau, zero_offset, max_value

        # Generate LUT
        #last_value = None

#         t = np.arange(0,lut_size)
#         out = []
#         out_fixed = []
        exp_list = []
        for i in range(0,lut_size): # the sign needs to be checked and has to be consistent with the dt used in the synapse

            # Multiply by time constant and calculate negative exponential
            value = float(i) * inv_tau
            # we want a single bump only, so we clip the arg at pi/2
#             if (value) < 0:# math.pi*2:
#                 exp_float = 0.0
#                 print "clamp @ value = ", value
#             else:
            exp_float = math.exp(-value) * math.sin(value)**sin_pwr  / 0.213122689799 #max_value

            # Convert to fixed-point and write to spec
            exp_fix = float_to_fixed(exp_float, fixed_point_one)
            exp_list.append(exp_float)

            if spec is None :
                #out.append(exp_float)
                if i == time_probe:
                    print "dt = ", time_probe, "weight update = ", exp_float, "fixed = ", exp_fix
            else :
                spec.write_value(data=exp_fix, data_type=DataType.INT16)



#         if spec is None :
#             plt.plot(t,out)
#             plt.show()

