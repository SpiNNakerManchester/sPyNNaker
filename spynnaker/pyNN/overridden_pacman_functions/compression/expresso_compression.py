import os
import tempfile
import subprocess
from collections import defaultdict

from rig.routing_table import RoutingTableEntry


class ExpressoCompression(object):
    """ does expresso compression
    
    """

    def __init__(self):
        pass

    def compress(self, entries, report_folder):
        """Call Espresso with appropriate arguments to minimise a routing 
                table.
                :param entries: the uncompressed entries
                :return the compressed entries.
                """

        # Begin by breaking entries up into sets of unique routes
        route_entries = defaultdict(set)
        for entry in entries:
            route_entries[frozenset(entry.route)].add((entry.key, entry.mask))

        # Sort these groups into ascending order of length
        groups = sorted(route_entries.items(), key=lambda kv: len(kv[1]))

        # Prepare to create a new table
        new_table = list()

        # Minimise each group individually using all the groups later on in the
        # table as the off-set.
        for i, (route, entries) in enumerate(groups):
            compression_file = os.path.join(report_folder,
                                            "temp_compressor.txt")
            f = open(compression_file, "w")
            f.write(b".i 32\n.o 1\n.type fr\n")

            # Write the "on-set"
            for key, mask in entries:
                f.write(self._key_mask_to_espresso(key, mask) + b" 1\n")

            # Write the offset
            for _, entries in groups[i + 1:]:
                for key, mask in entries:
                    f.write(self._key_mask_to_espresso(key, mask) + b" 0\n")

            f.write(b".e")
            f.flush()
            f.close()

            # Perform the minimisation and read back the result
            with tempfile.TemporaryFile() as g:
                print os.path.abspath(compression_file)
                subprocess.call(
                    ["espresso", os.path.abspath(compression_file)], stdout=g)

                # Read back from g()
                g.seek(0)
                for line in g:
                    if b'.' not in line:
                        key, mask = self._espresso_to_key_mask(
                            line.decode("utf-8").strip().split()[0])
                        new_table.append(
                            RoutingTableEntry(route, key, mask))

        return new_table

    @staticmethod
    def _key_mask_to_espresso(key, mask):
        vals = {(False, False): b'-',
                (False, True): b'0',
                (True, True): b'1'}
        return b''.join(vals[bool(key & bit), bool(mask & bit)] for
                        bit in (1 << i for i in range(32)))

    @staticmethod
    def _espresso_to_key_mask(text):
        key = 0x0
        mask = 0x0

        for i, bit in enumerate(text):
            if bit in "01":
                mask |= (1 << i)

                if bit == '1':
                    key |= (1 << i)

        return key, mask
