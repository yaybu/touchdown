# Copyright 2016 Isotoma Limited
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

from .service import ServiceStubber


class EC2InstanceStubber(ServiceStubber):

    client_service = 'ec2'

    def make_id(self, name):
        return 'i-' + super(EC2InstanceStubber, self).make_id(name)[:8]

    def add_describe_instances_empty_response_by_name(self):
        return self.add_response(
            'describe_instances',
            service_response={
                'Reservations': [],
            },
            expected_params={
                'Filters': [
                    {'Name': 'tag:Name', 'Values': [self.resource.name]},
                    {'Name': 'instance-state-name', 'Values': ['pending', 'running']},
                ],
            },
        )

    def add_describe_instances_one_response_by_name(self):
        return self.add_response(
            'describe_instances',
            service_response={
                'Reservations': [{
                    'Instances': [{
                        'InstanceId': self.make_id(self.resource.name),
                    }],
                }]
            },
            expected_params={
                'Filters': [
                    {'Name': 'tag:Name', 'Values': [self.resource.name]},
                    {'Name': 'instance-state-name', 'Values': ['pending', 'running']},
                ],
            },
        )
