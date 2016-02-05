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

import sys

import progressbar


class StdWrapper(object):

    def __init__(self, pb, inner):
        self.pb = pb
        self.inner = inner

    def write(self, text):
        self.inner.write(text.ljust(self.pb.term_width, ' ') + '\r' + self.pb._format_line() + '\r')
        self.inner.flush()

    def flush(self):
        self.inner.flush()


class ProgressBar(progressbar.ProgressBar):

    def __init__(self, min_value=0, max_value=0, text=None):
        super(ProgressBar, self).__init__(
            max_value=max_value,
            widgets=[
                "[",
                progressbar.Percentage(),
                "] ",
                progressbar.FormatLabel("Processed %(value)s of %(max)s"),
            ],
            redirect_stdout=False,
            redirect_stderr=False,
            fd=sys.stdout,
        )

    def start(self):
        sys.stdout = StdWrapper(self, sys.stdout)
        return super(ProgressBar, self).start()

    def finish(self):
        if not self.end_time:
            super(ProgressBar, self).finish()
            sys.stdout.inner.write("\n")
            sys.stdout.flush()

        sys.stdout = sys.stdout.inner
