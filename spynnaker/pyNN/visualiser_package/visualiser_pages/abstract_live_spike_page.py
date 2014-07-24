from visualiser.abstract_page import AbstractPage


class AbstractLiveSpikePage(AbstractPage):

    def __init__(self, transciever, has_board):
        """constructor for an abstract page
        :return: should never be called
        :rtype: None
        :raise None: this object does not raise any known exceptions
        """
        AbstractPage.__init__(self)
        if has_board:
            transciever.allocate_listener_callback(self.recieved_spike)

    def recieved_spike(self, details):
        """the emthod used to process a spike for a page

        :param details: the details of a spike
        :type details: string
        :return: None (should never be called directly)
        :rtype: None
        :raise NotImplementedError: as should not be called directly
        """
        raise NotImplementedError

    def reset_values(self):
        """the method used to reset any data objects

        :return None (should never be called directly)
        :rtype: None
        :raise NotImplementedError: as should not be called directly
        """
        raise NotImplementedError