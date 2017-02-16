from collections import defaultdict
import itertools
from bitarray import bitarray


class RecordingCommon(object):
    def __init__(self, population):
        self._population = population
        self._sampling_interval = None

        # Create default dictionary of population-size bitarrays
        self._indices_to_record = defaultdict(
            lambda: bitarray(itertools.repeat(
                0, self._population._vertex.size), endian="little"))

    def _record(self, variable, new_ids, sampling_interval):
        # Get bitarray of indices to record for this variable
        indices = self._indices_to_record[variable]

        # **YUCK** update sampling interval if one is specified
        # (no idea why this has to be done in derived class)
        if sampling_interval is not None:
            self._sampling_interval = sampling_interval

        # Loop through the new ids
        for new_id in new_ids:
            # Convert to index
            new_index = self._population.id_to_index(new_id)

            # Set this bit in indices
            indices[new_index] = True
