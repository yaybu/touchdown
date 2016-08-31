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

import datetime


class ProgressBar(object):

    def __init__(self, frontend, max_value=0, **kwargs):
        self.frontend = frontend
        self.max_value = max_value
        self.current = 0

    def update(self, current):
        self.current = current

    def __enter__(self):
        self.start_time = datetime.datetime.now()
        return self

    def __exit__(self, *exc_info):
        duration = datetime.datetime.now() - self.start_time
        self.frontend.echo('{} tasks executed out of {}'.format(self.current, self.max_value))
        self.frontend.echo('Tasks executed in {}'.format(duration))
