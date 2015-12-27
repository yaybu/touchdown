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

from touchdown.core.plan import Plan
from touchdown.core import argument, resource
from touchdown.interfaces import File


class IniFile(resource.Resource):

    resource_name = "ini_file"

    name = argument.String()
    file = argument.Resource(File)


class Describe(Plan):

    resource = IniFile
    name = "describe"

    def write(self, c):
        fp = self.runner.get_plan(self.resource.file)
        s = six.StringIO()
        c.write(s)
        fp.write(s.getvalue())

    def read(self):
        fp = self.runner.get_plan(self.resource.file)
        config = configparser.ConfigParser()
        config.readfp(fp.read())
        return config

    def get_actions(self):
        self.object = self.read()
        return []
