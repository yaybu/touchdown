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

import progressbar


class ProgressBar(progressbar.ProgressBar):

    def __init__(self, min_value=0, max_value=0, text=None):
        super(ProgressBar, self).__init__(
            maxval=max_value,
            widgets=[
                progressbar.Percentage(),
                progressbar.Bar(),
            ],
            redirect_stdout=True,
            redirect_stderr=True,
        )

    def finish(self):
        if not self.finished:
            super(ProgressBar, self).finish()
