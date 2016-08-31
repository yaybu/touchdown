# Copyright 2014 Isotoma Limited
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

from __future__ import absolute_import, print_function

from .base import BaseFrontend


class MultiFrontend(BaseFrontend):

    def __init__(self, frontends):
        super(MultiFrontend, self).__init__()
        self.frontends = frontends

    def failure(self, text):
        for fe in self.frontends:
            fe.failure(text)

    def echo(self, text, nl=True, **kwargs):
        for fe in self.frontends:
            fe.echo(text, nl, **kwargs)

    def progressbar(self, **kwargs):
        return self.frontends[0].progressbar(**kwargs)

    def prompt(self, message, key=None, default=None):
        retval = super(MultiFrontend, self).prompt(message, key, default)
        if retval:
            return retval
        return self.frontends[0].prompt(message, key, default)

    def confirm(self, message):
        result = self.frontends[0].confirm(message)
        self.echo('Primary frontend chose {}'.format(result))
        return result

    def start(self, subcommand, goal):
        for fe in self.frontends:
            fe.start(subcommand, goal)

    def finish(self):
        for fe in reversed(self.frontends):
            fe.finish()
