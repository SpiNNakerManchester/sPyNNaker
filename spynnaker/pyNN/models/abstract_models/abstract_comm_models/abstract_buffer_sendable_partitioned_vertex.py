

class AbstractBufferSendablePartitionedVertex(object):

    def __init__(self):
        self._will_send_buffers = False
        self._threshold_for_reporting_bytes_written = None
        self._recording_region_size_in_bytes = None

    @property
    def will_send_buffers(self):
        """

        :return: returns true if the vertex requires listeners to receive
        buffers during runtime
        :rtype: bool
        """
        return self._will_send_buffers

    @property
    def size_of_buffer_to_read_in_bytes(self):
        """

        :return: the size of each buffer in the core that will need to be read
        at some point during execution
        """
        return self._threshold_for_reporting_bytes_written

    def set_recording_region_size_in_bytes(self, new_value):
        """

        :param new_value:
        :return:
        """
        if self._recording_region_size_in_bytes is not None:
            raise exceptions.ConfigurationException(
                "The recording region size in bytes has already been set."
                "setting it again is deemed an error due to inmutablilty. "
                "Please rectify and try again")
        self._recording_region_size_in_bytes = new_value