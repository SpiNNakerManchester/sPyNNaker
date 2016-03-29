from pyNN.recording import files
from spynnaker.pyNN.models.neural_projections.connectors.from_list_connector \
    import FromListConnector
import os
import numpy


class FromFileConnector(FromListConnector):

    def __init__(
            self, file,  # @ReservedAssignment
            distributed=False, safe=True, verbose=False):

        real_file = file
        opened_file = False
        if isinstance(file, basestring):
            real_file = files.StandardTextFile(file, mode="r")
            opened_file = True

        conn_list = None
        if distributed:
            directory = os.path.dirname(real_file.file)
            filename = "{}.".format(os.path.basename(real_file.file))

            conns = list()
            for found_file in os.listdir(directory):
                if found_file.startswith(filename):
                    file_reader = files.StandardTextFile(found_file, mode="r")
                    conns.append(file_reader.read())
                    file_reader.close()
            conn_list = numpy.concatenate(conns)
        else:
            conn_list = real_file.read()

        if opened_file:
            real_file.close()

        FromListConnector.__init__(self, conn_list, safe, verbose)
