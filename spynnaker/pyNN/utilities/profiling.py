import bisect
import numpy as np

MS_SCALE = (1.0 / 200032.4)

default_tag_labels = ["Timer",
                      "Process DMA Read",
                      "Handle incoming spike",
                      "Process fixed synapses", "Process plastic synapses"]

def print_summary(profiling_data, duration):
    """
    Print a summary of the profiling data to standard out
    Showing how much time is spent in each profiler tag
    """
    ms_time_bins = np.arange(duration * 1000.0)

    # Summarise data for all tags
    for tag_name, times in profiling_data.iteritems():
        print("Tag:%s" % (default_tag_labels[tag_name]))

        print("\tMean time:%fms" % (np.average(times[1])))

        print("\tWith standard deviation %fms" % (np.std(times[1])))

        print("\tStandard error:%fms" % (np.std(times[1])/np.sqrt(times[1].size)))

        # Digitize the sample entry times into these bins
        sample_timestep_indices = np.digitize(times[0], ms_time_bins)
        assert len(sample_timestep_indices) == len(times[1])

        # Calculate the average number of samples in each bin
        print("\tMean samples per timestep:%f" %
              (np.average(np.bincount(sample_timestep_indices))))

        # Determine the last sample time (if profiler runs out
        # Of space to write samples it may not be duration)
        last_sample_time = np.amax(sample_timestep_indices) + 1
        print("\tLast sample time:%fms" % (last_sample_time))

        # Create bins to hold total time spent in this tag during each
        # Timestep and add duration to total in corresponding bin
        total_sample_duration_per_timestep = np.zeros(last_sample_time)
        for sample_duration, index in zip(times[1], sample_timestep_indices):
            total_sample_duration_per_timestep[index] += sample_duration

        print("\tMean time per timestep:%fms" %
              (np.average(total_sample_duration_per_timestep)))

def subtract_tag(profile_data, tag, subtract_tag):
    subtract_entry_times = profile_data[subtract_tag][0]
    
    # Calculate exit times for both tags
    exit_times = profile_data[tag][0] + profile_data[tag][1]
    subtract_exit_times = subtract_entry_times + profile_data[subtract_tag][1]
    
    # Loop through tag's entry and exit times
    durations = np.empty(profile_data[tag][0].shape)
    for i, (entry_time, exit_time, duration) in enumerate(zip(profile_data[tag][0], exit_times, profile_data[tag][1])):
        # Bisect to find range of subtract tags within tag
        first_subtract_exit = bisect.bisect_right(subtract_exit_times, entry_time)
        last_subtract_entry = bisect.bisect_left(subtract_entry_times, exit_time)
        
        # Extract this slice of subtract tag durations
        durations_to_subtract = profile_data[subtract_tag][1][first_subtract_exit:last_subtract_entry]

        # Subtract sum of durations from existing duration and append
        durations[i] = duration - np.sum(durations_to_subtract)
    
    # Return new trimmed tag
    return (profile_data[tag][0], durations)

def time_filter_core_profiling_data(profile_data, min_time, max_time):
    filtered_tag_dictionary = {}
    for tag, times in profile_data.iteritems():
        # Get indices of entry times which fall within time range
        filtered_indices = np.where((times[0] >= float(min_time)) & (times[0] < float(max_time)))
        
        # Add entry times and durations, filtered by new indices to filtered tag dictionary
        filtered_tag_dictionary[tag] = (times[0][filtered_indices], times[1][filtered_indices])
    
    return filtered_tag_dictionary
