from collections import defaultdict
import filedict


class ExtractedData(object):

    def __init__(self):
        self._data = defaultdict(filedict.FileDict)

    def get(self, projection, attribute):
        if projection in self._data:
            if attribute in self._data[projection]:
                return self._data[projection][attribute]

    def set(self, projection, attribute, data):
        self._data[projection][attribute] = data
