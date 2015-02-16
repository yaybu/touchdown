# Copyright 2014-2015 Isotoma Limited
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

import logging


logger = logging.getLogger(__name__)


class Diff(object):

    def __init__(self, field, remote_value, local_value):
        self.field = field
        self.remote_value = remote_value
        self.local_value = local_value

    @property
    def local_name(self):
        return self.field.name

    @property
    def remote_name(self):
        return self.field.field

    def __str__(self):
        return "{0.local_name} ({0.remote_value} => {0.local_value})".format(self)


class DiffSet(object):

    def __init__(self, runner, local, remote, group=""):
        self.runner = runner
        self.local = local
        self.remote = remote
        self.group = group

        self.diffs = []

        if not self.local:
            return

        for name, field in local.fields:
            arg = field.argument
            if not field.present(local):
                continue
            if not getattr(arg, "field", ""):
                continue
            if not getattr(arg, "update", True):
                continue
            if getattr(arg, "group", "") != self.group:
                continue
            if not getattr(local, name) and arg.field not in remote:
                continue

            rendered = arg.serializer.render(runner, getattr(local, name))
            if arg.field not in remote:
                self.diffs.append(Diff(arg, "", rendered))
            elif rendered != remote[arg.field]:
                self.diffs.append(Diff(arg, remote[arg.field], rendered))

    def get_descriptions(self):
        for diff in self.diffs:
            yield str(diff)

    def get_changes(self):
        for diff in self.diffs:
            yield diff

    def matches(self):
        return len(self.diffs) == 0
