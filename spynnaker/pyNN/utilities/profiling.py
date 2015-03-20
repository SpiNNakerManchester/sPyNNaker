import bisect
import numpy as np

MS_SCALE = (1.0 / 200032.4)

default_tag_labels = ["Timer", "Process DMA Read", "Handle incoming spike", "Process fixed synapses", "Process plastic synapses"]

def process_core_profile_data(data):
    # If there's no data, return an empty dictionary
    if len(data) == 0:
        print("No samples recorded")
        return {}
    
    # Create 32-bit view of data and slice this to seperate times, tags and flags
    data_view = data.view(np.uint32)
    sample_times = data_view[::2]
    sample_tags_and_flags = data_view[1::2]
    
    # Further split the tags and flags word into seperate arrays of tags and flags
    sample_tags = np.bitwise_and(sample_tags_and_flags, 0x7FFFFFFF)
    sample_flags = np.right_shift(sample_tags_and_flags, 31)
    
    # Find indices of samples relating to entries and exits
    sample_entry_indices = np.where(sample_flags == 1)
    sample_exit_indices = np.where(sample_flags == 0)
    
    # Convert count-down times to count up times from 1st sample
    sample_times = np.subtract(sample_times[0], sample_times)
    sample_times_ms = np.multiply(sample_times, MS_SCALE, dtype=np.float)

    # Slice tags and times into entry and exits
    entry_tags = sample_tags[sample_entry_indices]
    entry_times_ms = sample_times_ms[sample_entry_indices]
    exit_tags = sample_tags[sample_exit_indices]
    exit_times_ms = sample_times_ms[sample_exit_indices]

    # Loop through unique tags
    tag_dictionary = {}
    unique_tags = np.unique(sample_tags)
    for tag in unique_tags:
        # Get indices where these tags occur
        tag_entry_indices = np.where(entry_tags == tag)
        tag_exit_indices = np.where(exit_tags == tag)
        
        # Use these to get subset for this tag
        tag_entry_times_ms = entry_times_ms[tag_entry_indices]
        tag_exit_times_ms = exit_times_ms[tag_exit_indices]
        
        # If the first exit is before the first
        # Entry, add a dummy entry at beginning
        if tag_exit_times_ms[0] < tag_entry_times_ms[0]:
            print "WARNING: profile starts mid-tag"
            tag_entry_times_ms = np.append(0.0, tag_entry_times_ms)
        
        if len(tag_entry_times_ms) > len(tag_exit_times_ms):
            print "WARNING: profile finishes mid-tag"
            tag_entry_times_ms = tag_entry_times_ms[:len(tag_exit_times_ms)-len(tag_entry_times_ms)]
 
        # Subtract entry times from exit times to get durations of each call
        tag_durations_ms = np.subtract(tag_exit_times_ms, tag_entry_times_ms)
        
        # Add entry times and durations to dictionary
        tag_dictionary[tag] = (tag_entry_times_ms, tag_durations_ms)
        
    return tag_dictionary

def display_tag_summary(times, duration):
    print("\t\tMean time:%f" % (np.average(times[1])))

    # Digitize the sample entry times into these bins
    sample_timestep_indices = np.digitize(times[0], np.arange(duration))
    assert len(sample_timestep_indices) == len(times[1])
    
    # Calculate the average number of samples in each bin
    print("\t\tMean samples per timestep:%f" % (np.average(np.bincount(sample_timestep_indices))))
    
    # Determine the last sample time (if profiler runs out 
    # Of space to write samples it may not be duration)
    last_sample_time = np.amax(sample_timestep_indices) + 1
    print("\t\tLast sample time:%fms" % (last_sample_time))
    
    # Create bins to hold total time spent in this tag during each
    # Timestep and add duration to total in corresponding bin
    total_sample_duration_per_timestep = np.zeros(last_sample_time)
    for sample_duration, index in zip(times[1], sample_timestep_indices):
        total_sample_duration_per_timestep[index] += sample_duration

    print("\t\tMean time per timestep:%f" % (np.average(total_sample_duration_per_timestep)))
    
def display_summary(processed_profiling_data, duration, tag_labels=default_tag_labels):
    # Summarise data for all tags
    for tag, times in processed_profiling_data.iteritems():
        if tag_labels is None:
            print("\tTag:%u" % (tag))
        else:
            print("\tTag:%s (%u)" % (tag_labels[tag], tag))
        
        display_tag_summary(times, duration)

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