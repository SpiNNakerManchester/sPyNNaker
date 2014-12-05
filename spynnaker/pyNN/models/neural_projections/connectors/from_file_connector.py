from spynnaker.pyNN.models.neural_projections.connectors.from_list_connector \
    import FromListConnector
from spynnaker.pyNN import exceptions
import re
import logging

logger = logging.getLogger(__name__)


class FromFileConnector(FromListConnector):

    def generate_synapse_list(
            self, presynaptic_population, postsynaptic_population, delay_scale,
            weight_scale, synapse_type):
        conn_file = open(self._filename, 'r')
        file_lines = conn_file.readlines()
        for line in file_lines:
            line.strip()
            form1 = re.match(r"\[(\([^()]*\),\s*)*(\([^()]*\)\s*)\]", line)

            # form 1: a list of tuples
            if form1:
                conn_sublist = [eval(conn.group(0)) for conn in
                                re.finditer(r"\([^()]*\)", line)]
            else:
                form2 = re.match(r"\(.*\)\s*", line)
                # form 2: a single tuple per line
                if form2:
                    conn_sublist = [eval(form2.group(0).rstrip(
                                    ", \a\b\f\n\r\t\v"))]
                else:
                    form3 = re.match(
                        r"((?:\[[^[\]\s]+\])|(?:[^[\],\s]+))((?:,\s*)"
                        + r"|\s+)((?:\[[^[\]\s]+\])|(?:[^[\],\s]+))"
                        + r"((?:,\s*)|\s+)((?:\+|\-)?\d+(?:\.\d+)?"
                        + r"(?:(?:E|e)(?:\+|\-)?\d+)?)((?:,\s*)|\s+)"
                        + r"((?:\+|\-)?\d+(?:\.\d+)?(?:(?:E|e)"
                        + r"(?:\+|\-)?\d+)?)\s*", line)

                    # form 3: a comma- or space-separated set of specifiers per
                    # line
                    if form3:
                        conn_sublist = [(eval(form3.group(1)),
                                         eval(form3.group(3)),
                                        float(form3.group(5)),
                                        float(form3.group(7)))]
                    else:
                        raise exceptions.ConfigurationException(
                            "Invalid connection file format")
            self._conn_list.extend(conn_sublist)
        return FromListConnector.generate_synapse_list(
            self, presynaptic_population, postsynaptic_population,
            delay_scale, weight_scale, synapse_type)

    def __init__(self, conn_file, distributed=False, safe=True, verbose=False):
        FromListConnector.__init__(self, safe=safe, verbose=verbose)
        if distributed:
            logger.warn("distributed loading of FromFileConnector files is "
                        "not supported and will be ignored")
        self._filename = conn_file
