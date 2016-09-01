# Copyright 2015 Isotoma Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import six

from six.moves import configparser
from touchdown.core import argument, resource
from touchdown.core.plan import Plan
from touchdown.core.utils import force_bytes, force_str
from touchdown.interfaces import File, FileNotFound


class IniFile(resource.Resource):

    resource_name = 'ini_file'

    name = argument.String()
    file = argument.Resource(File)


class Describe(Plan):

    resource = IniFile
    name = 'describe'

    def write(self, c):
        fp = self.runner.get_service(self.resource.file, 'fileio')
        s = six.StringIO()
        c.write(s)
        fp.write(force_bytes(s.getvalue()))

    def read(self):
        fp = self.runner.get_service(self.resource.file, 'fileio')
        config = configparser.ConfigParser()
        try:
            config.readfp(six.StringIO(force_str(fp.read().read())))
        except FileNotFound:
            pass
        return config

    def set(self, key, value):
        section, name = key.rsplit('.', 1)
        c = self.read()
        if not c.has_section(section):
            c.add_section(section)
        c.set(section, name, value)
        self.write(c)

    def get(self, key):
        section, name = key.rsplit('.', 1)
        c = self.read()
        try:
            return c.get(section, name)
        except (configparser.NoSectionError, configparser.NoOptionError):
            raise KeyError(key)

    def walk(self, key):
        c = self.read()
        try:
            return c.items(key)
        except configparser.NoSectionError:
            return []

    def get_actions(self):
        self.object = self.read()
        return []
