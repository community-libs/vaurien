# ***** BEGIN LICENSE BLOCK *****
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
# ***** END LICENSE BLOCK *****

""" Configuration file reader / writer

https://wiki.mozilla.org/index.php?title=Services/Sync/Server/GlobalConfFile
"""
import re
import os
from os.path import abspath, normpath, expandvars, expanduser
from ConfigParser import RawConfigParser

_IS_NUMBER = re.compile('^-?[0-9].*')
_IS_ENV_VAR = re.compile('\$\{(\w.*)?\}')


def convert(value):
    """Converts a config value"""
    def _get_env(matchobj):
        var = matchobj.groups()[0]
        if var not in os.environ:
            raise KeyError(var)
        return os.environ[var]

    def _convert(value):
        if not isinstance(value, basestring):
            # already converted
            return value

        value = value.strip()
        if _IS_NUMBER.match(value):
            try:
                return int(value)
            except ValueError:
                pass
        elif value.startswith('"') and value.endswith('"'):
            return value[1:-1]
        elif value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        return _IS_ENV_VAR.sub(_get_env, value)

    if isinstance(value, basestring) and '\n' in value:
        return [line for line in [_convert(line)
                                  for line in value.split('\n')]
                if line != '']

    return _convert(value)


class Config(RawConfigParser):

    def __init__(self, filename):
        # let's read the file
        RawConfigParser.__init__(self)
        if isinstance(filename, basestring):
            self.read(filename)
        else:
            self.readfp(filename)

    def _read(self, fp, filename):
        # first pass
        RawConfigParser._read(self, fp, filename)

        # let's expand it now if needed
        defaults = self.defaults()

        if 'extends' in defaults:
            extends = defaults['extends']
            if not isinstance(extends, list):
                extends = [extends]
            for file_ in extends:
                self._extend(file_)

    def _serialize(self, value):
        """values are serialized on every set"""
        if isinstance(value, bool):
            value = str(value).lower()
        elif isinstance(value, (int, long)):
            value = str(value)
        elif isinstance(value, (list, tuple)):
            value = '\n'.join(['    %s' % line for line in value]).strip()
        else:
            value = str(value)
        return value

    def _unserialize(self, value):
        """values are serialized on every get"""
        return convert(value)

    def get_map(self, section=None):
        """returns a dict representing the config set"""
        if section:
            return dict(self.items(section))

        res = {}
        for section in self.sections():
            for option, value in self.items(section):
                option = '%s.%s' % (section, option)
                res[option] = self._unserialize(value)
        return res

    def set(self, section, option, value):
        value = self._serialize(value)
        RawConfigParser.set(self, section, option, value)

    def mget(self, section, option):
        value = self.get(section, option)
        if not isinstance(value, list):
            value = [value]
        return value

    def get(self, section, option):
        value = RawConfigParser.get(self, section, option)
        return self._unserialize(value)

    def items(self, section):
        items = RawConfigParser.items(self, section)
        return [(option, self._unserialize(value)) for option, value in items]

    def _extend(self, filename):
        """Expand the config with another file."""
        if not os.path.isfile(filename):
            raise IOError('No such file: %s' % filename)
        parser = RawConfigParser()
        parser.read([filename])
        for section in parser.sections():
            if not self.has_section(section):
                self.add_section(section)
            for option, value in parser.items(section):
                if self.has_option(section, option):
                    continue
                RawConfigParser.set(self, section, option, value)


def load_into_settings(filename, settings):
    """Load config file contents into a Pyramid settings dict.

    This is a helper function for initialising a Pyramid settings dict from
    a config file.  It flattens the config file sections into dotted settings
    names and updates the given dictionary in place.

    You would typically use this when constructing a Pyramid Configurator
    object, like so::

        def main(global_config, **settings):
            config_file = global_config['__file__']
            load_info_settings(config_file, settings)
            config = Configurator(settings=settings)

    """
    filename = abspath(normpath(expandvars(expanduser(filename))))

    if not os.path.isfile(filename):
        raise ValueError("Unexistant filename '%s'" % filename)

    config = Config(filename)

    # Put values from the config file into the pyramid settings dict.
    for section in config.sections():
        setting_prefix = section.replace(":", ".")
        for name, value in config.get_map(section).iteritems():
            settings[setting_prefix + "." + name] = value

    # Store a reference to the Config object itself for later retrieval.
    settings['config'] = config
    return config


class SettingsDict(dict):
    """A dict subclass with some extra helpers for dealing with app settings.

    This class extends the standard dictionary interface with some extra helper
    methods that are handy when dealing with application settings.  It expects
    the keys to be dotted setting names, where each component indicates one
    section in the settings heirarchy.  You get the following extras:

        * setdefaults:  copy any unset settings from another dict
        * getsection:   return a dict of settings for just one subsection
        * sections:     return a list of sections for the settings

    """

    separator = "."

    def copy(self):
        """D.copy() -> a shallow copy of D.

        This overrides the default dict.copy method to ensure that the
        copy is also an instance of SettingsDict.
        """
        new_items = self.__class__()
        for k, v in self.iteritems():
            new_items[k] = v
        return new_items

    def sections(self):
        """Return a list of sections for this dict"""
        sections = []
        for key in self.iterkeys():
            if self.separator in key:
                sec, _ = key.rsplit(self.separator, 1)
                if sec not in sections:
                    sections.append(sec)
        return sections

    def getsection(self, section):
        """Get a dict for just one sub-section of the config.

        This method extracts all the keys belonging to the name section and
        returns those values in a dict.  The section name is removed from
        each key.  For example::

            >>> c = SettingsDict({"a.one": 1, "a.two": 2, "b.three": 3})
            >>> c.getsection("a")
            {"one": 1, "two", 2}
            >>>
            >>> c.getsection("b")
            {"three": 3}
            >>>
            >>> c.getsection("c")
            {}

        """
        section_items = self.__class__()
        # If the section is "" then get keys without a section.
        if not section:
            for key, value in self.iteritems():
                if self.separator not in key:
                    section_items[key] = value
        # Otherwise, get keys prefixed with that section name.
        else:
            prefix = section + self.separator
            for key, value in self.iteritems():
                if key.startswith(prefix):
                    section_items[key[len(prefix):]] = value
        return section_items

    def setdefaults(self, *args, **kwds):
        """Import unset keys from another dict.

        This method lets you update the dict using defaults from another
        dict and/or using keyword arguments.  It's like the standard update()
        method except that it doesn't overwrite existing keys.
        """
        for arg in args:
            if hasattr(arg, "keys"):
                for k in arg:
                    self.setdefault(k, arg[k])
            else:
                for k, v in arg:
                    self.setdefault(k, v)
        for k, v in kwds.iteritems():
            self.setdefault(k, v)


DEFAULT_SETTINGS = SettingsDict({
    # default ratios
    'vaurien.proxy': 'localhost:8000',
    'vaurien.backend': 'localhost:80',
    'vaurien.behavior': '100:dummy',
    'vaurien.bufsize': 8192,
    'vaurien.timeout': 30,
    'vaurien.stay_connected': False,
    'vaurien.pool_max_size': 100,
    'vaurien.pool_timeout': 30,
    'vaurien.sync': False,
    'vaurien.backlog': 8192,

    # stats config
    'statsd.enabled': False,
    'statsd.host': 'localhost',
    'statsd.port': 8125,
    'statsd.prefix': 'vaurien',
    'statsd.sample_rate': 1.0
})
