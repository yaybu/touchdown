# Copyright 2015 Isotoma Limited
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

from touchdown.core import argument, resource, serializers

from .provisioner import Provisioner


class Output(resource.Resource):

    resource_name = 'output'

    name = argument.String()

    provisioner = argument.Resource(Provisioner)


class OutputAsString(serializers.Serializer):

    def __init__(self, resource):
        self.resource = resource

    def render(self, runner, object):
        if self.pending(runner, object):
            return serializers.Pending(self.resource)

        # Extract the contents from the file on the (potentially remote) target
        service = runner.get_service(self.resource.provisioner.target, 'describe')
        client = service.get_client()
        return client.get_path_contents(self.resource.name)

    def pending(self, runner, object):
        provisioner = runner.get_service(self.resource.provisioner, 'apply')
        return provisioner.object['Result'] == 'Pending'

    def dependencies(self, object):
        return frozenset((self.resource, ))


argument.String.register_adapter(Output, lambda r: OutputAsString(r))


class OutputAsBytes(serializers.Serializer):

    def __init__(self, resource):
        self.resource = resource

    def render(self, runner, object):
        if self.pending(runner, object):
            return serializers.Pending(self.resource)

        # Extract the contents from the file on the (potentially remote) target
        service = runner.get_service(self.resource.provisioner.target, 'describe')
        client = service.get_client()
        return client.get_path_bytes(self.resource.name)

    def pending(self, runner, object):
        provisioner = runner.get_service(self.resource.provisioner, 'apply')
        return provisioner.object['Result'] == 'Pending'

    def dependencies(self, object):
        return frozenset((self.resource, ))


argument.Bytes.register_adapter(Output, lambda r: OutputAsBytes(r))
