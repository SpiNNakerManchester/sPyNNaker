from visualiser_framework.abstract_page import AbstractPage
from abc import abstractmethod


class AbstractLiveSpikePage(AbstractPage):

    def __init__(self, transciever, has_board, label):
        """constructor for an abstract _page
        :return: should never be called
        :rtype: None
        :raise None: this object does not raise any known exceptions
        """
        AbstractPage.__init__(self, label)
        if has_board:
            transciever.allocate_listener_callback(self.recieved_spike)

    @abstractmethod
    def recieved_spike(self, details):
        """the emthod used to process a spike for a _page

        :param details: the details of a spike
        :type details: string
        :return: None (should never be called directly)
        :rtype: None
        :raise NotImplementedError: as should not be called directly
        """
        raise NotImplementedError

    @abstractmethod
    def reset_values(self):
        """the method used to reset any data objects

        :return None (should never be called directly)
        :rtype: None
        :raise NotImplementedError: as should not be called directly
        """
        raise NotImplementedError