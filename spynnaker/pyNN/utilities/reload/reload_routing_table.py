import pickle


class ReloadRoutingTable(object):
    """ A routing table to be reloaded
    """

    def __init__(self, routing_table_file_name):

        routing_table_file = open(routing_table_file_name, "rb")
        self._routing_table = pickle.load(routing_table_file)
        routing_table_file.close()

    @property
    def routing_table(self):
        return self._routing_table
