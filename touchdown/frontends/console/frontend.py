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

import six

from ..base import BaseFrontend
from ..progress import ProgressBar


class ConsoleFrontend(BaseFrontend):

    def __init__(self, interactive=True):
        super(ConsoleFrontend, self).__init__()
        self.interactive = interactive

    def _echo(self, text, nl=True, **kwargs):
        print(text, end='')

    def progressbar(self, **kwargs):
        return ProgressBar(self, **kwargs)

    def prompt(self, message, key=None, default=None):
        retval = super(ConsoleFrontend, self).prompt(message, key, default)
        if retval:
            return retval
        response = six.moves.input('{}: '.format(message))
        while not response:
            response = six.moves.input('{}: '.format(message))
        return response

    def confirm(self, message):
        if not self.interactive:
            return True
        response = six.moves.input('{} [Y/n] '.format(message))
        while response.lower() not in ('y', 'n', ''):
            response = six.moves.input('{} [Y/n] '.format(message))
        return response.lower() != 'n'
