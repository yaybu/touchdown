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


class Error(Exception):
    pass


class ServiceNotReady(Error):
    pass


class CommandFailed(Error):

    def __init__(self, exit_code, stdout=None, stderr=None):
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
        Error.__init__(self, str(self))

    def __str__(self):
        return 'Bundle deployment failed with exit code: {}'.format(
            self.exit_code)


class RemoteCommandFailed(CommandFailed):

    def __init__(self, exit_code, stdout=None, stderr=None):
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
        Error.__init__(self, str(self))

    def __str__(self):
        return 'Bundle deployment failed with exit code: {}'.format(
            self.exit_code)


class NothingChanged(Error):
    pass


class InvalidParameter(Error):
    pass


class NotFound(Error):
    pass


class InvalidPlan(Error):
    pass


class NonConformingPolicy(Error):
    pass


class CycleError(Error):
    ''' The graph has a cycle so there is no way to apply changes to the cluster
    sanely '''
