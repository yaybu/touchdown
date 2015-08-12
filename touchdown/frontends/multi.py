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


class MultiFrontend(object):

    def __init__(self, frontends):
        self.frontends = frontends

    def failure(self, text):
        for fe in self.frontends:
            fe.failure(text)

    def echo(self, text, nl=True, **kwargs):
        for fe in self.frontends:
            fe.echo(text, nl, **kwargs)

    def table(self, data):
        return self.frontends[0].table(data)

    def render_plan(self, plan):
        return self.frontends[0].render_plan(plan)

    def confirm_plan(self, plan):
        return self.frontends[0].confirm_plan(plan)

    def progressbar(self, **kwargs):
        return self.frontends[0].progressbar(**kwargs)

    def prompt(self, message, key=None, default=None):
        return self.frontends[0].prompt(message, key, default)

    def confirm(self, message):
        result = self.frontends[0].confirm(message)
        self.echo("Frontend {} chose {}".format(self.frontends[0], result))
        return result

    def finish(self):
        for fe in reversed(self.frontends):
            fe.finish()