# Copyright 2014-2015 Isotoma Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, softwserializersdistributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging

from touchdown.core import serializers


logger = logging.getLogger(__name__)


class Diff(object):

    def __init__(self, field, remote_value, local_value):
        self.field = field
        self.remote_value = remote_value
        self.local_value = local_value

    def __str__(self):
        return "{0.field} ({0.remote_value} => {0.local_value})".format(self)


class DiffSet(object):

    def __init__(self, runner, local, remote, group=""):
        self.runner = runner
        self.local = local
        self.remote = remote
        self.group = group

        self.diffs = []

        if self.local:
            self.build_diffs()

    def build_diffs(self):
        for name, orig, to in serializers.Resource().diff(self.runner, self.local, self.remote):
            self.diffs.append(Diff(name, orig, to))

    def get_descriptions(self):
        for diff in self.diffs:
            yield str(diff)

    def get_changes(self):
        for diff in self.diffs:
            yield diff

    def matches(self):
        return len(self) == 0

    def __len__(self):
        return len(self.diffs)
