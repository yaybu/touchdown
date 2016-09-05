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

import threading

from touchdown.core.utils import force_str


class BaseFrontend(object):

    def __init__(self):
        self.preseeds = {}

    def preseed(self, question, response):
        self.preseeds[question] = response

    def failure(self, text):
        self.echo(text)

    def echo(self, text, nl=True, **kwargs):
        text = force_str(text)
        if threading.current_thread().name != 'MainThread':
            text = '[{}] {}'.format(threading.current_thread().name, text)
        if nl:
            self._echo('{}\n'.format(text))
        else:
            self._echo(text)

    def render_plan(self, plan):
        for resource, actions in plan:
            self.echo('%s:' % resource)
            for action in actions:
                description = list(action.description)
                self.echo('  * %s' % description[0])
                for line in description[1:]:
                    self.echo('      %s' % line)
            self.echo('')

    def confirm_plan(self, plan):
        self.echo('Generated a plan to update infrastructure configuration:')
        self.echo('')
        self.render_plan(plan)
        return self.confirm('Do you want to continue?')

    def progressbar(self, **kwargs):
        raise NotImplementedError(self.progressbar)

    def prompt(self, message, key=None, default=None):
        if key in self.preseeds:
            return self.preseeds[key]
        return None

    def confirm(self, message):
        raise NotImplementedError(self.confirm)

    def start(self, subcommand, goal):
        pass

    def finish(self):
        pass
