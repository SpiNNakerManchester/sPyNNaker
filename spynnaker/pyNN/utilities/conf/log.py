import logging
import re

levels = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'error': logging.ERROR,
    'critical': logging.CRITICAL,
}


class ConfiguredFilter(object):
    def __init__(self, conf):
        self._levels = ConfiguredFormatter.construct_logging_parents(conf)
        self._default_level = levels[conf.get("Logging", "default")]

    def filter(self, record):
        """Get the level for the deepest parent, and filter appropriately."""
        level = ConfiguredFormatter.level_of_deepest_parent(self._levels,
                                                            record.name)

        if level is None:
            return record.levelno >= self._default_level

        return record.levelno >= level


class ConfiguredFormatter(logging.Formatter):
    def __init__(self, conf):
        level = conf.get("Logging", "default")
        if level == "debug":
            super(ConfiguredFormatter, self).__init__(
                fmt="%(asctime)-15s %(levelname)s: %(pathname)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S")
        else:
            super(ConfiguredFormatter, self).__init__(
                fmt="%(asctime)-15s %(levelname)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S")

    @staticmethod
    def construct_logging_parents(conf):
        """Create a dictionary of module names and logging levels."""
        # Construct the dictionary
        _levels = {}

        if not conf.has_section("Logging"):
            return _levels

        for label, level in levels.items():
            if conf.has_option("Logging", label):
                modules = map(
                    lambda s: s.strip(),
                    conf.get('Logging', label).split(',')
                )
                if '' not in modules:
                    _levels.update(
                        dict(map(lambda m: (m, level), modules)))
        return _levels

    @staticmethod
    def deepest_parent(parents, child):
        """Greediest match between child and parent."""
        # TODO: this can almost certainly be neater!
        # Repeatedly strip elements off the child until we match an item in
        # parents
        match = child

        while '.' in match and match not in parents:
            match = re.sub(r'\.[^.]+$', '', match)

        # If no match then return None, there is no deepest parent
        if match not in parents:
            match = None

        return match

    @staticmethod
    def level_of_deepest_parent(parents, child):
        """ The logging level of the greediest match between child and parent.
        """
        # child = re.sub( r'^pacman103\.', '', child )
        parent = ConfiguredFormatter.deepest_parent(parents.keys(), child)

        if parent is None:
            return None

        return parents[parent]
