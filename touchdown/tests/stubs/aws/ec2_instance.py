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
                    {'Name': 'instance-state-name', 'Values': [
                        'pending', 'running', 'shutting-down', ' stopping', 'stopped'
                    ]},
                ],
            },
        )

    def add_describe_instances_one_response_by_name(self, state='running'):
        return self.add_response(
            'describe_instances',
            service_response={
                'Reservations': [{
                    'Instances': [{
                        'InstanceId': self.make_id(self.resource.name),
                        'State': {
                            'Name': state
                        },
                        'VpcId': 'vpc-de3db33',
                        'PrivateIpAddress': '10.0.0.42',
                    }],
                }]
            },
            expected_params={
                'Filters': [
                    {'Name': 'tag:Name', 'Values': [self.resource.name]},
                    {'Name': 'instance-state-name', 'Values': [
                        'pending', 'running', 'shutting-down', ' stopping', 'stopped'
                    ]},
                ],
            },
        )

    def add_run_instance(self):
        return self.add_response(
            'run_instances',
            service_response={
                'Instances': [{
                    'InstanceId': self.make_id(self.resource.name),
                }],
            },
            expected_params={
                'BlockDeviceMappings': [],
                'MaxCount': 1,
                'MinCount': 1,
                'ImageId': 'foobarbaz',
            },
        )

    def add_run_instance_with_profile(self):
        return self.add_response(
            'run_instances',
            service_response={
                'Instances': [{
                    'InstanceId': self.make_id(self.resource.name),
                }],
            },
            expected_params={
                'IamInstanceProfile': {
                    'Name': 'my-test-profile',
                },
                'BlockDeviceMappings': [],
                'MaxCount': 1,
                'MinCount': 1,
                'ImageId': 'foobarbaz',
            },
        )

    def add_create_tags(self, **tags):
        tag_list = [{'Key': k, 'Value': v} for (k, v) in tags.items()]
        self.add_response(
            'create_tags',
            service_response={
            },
            expected_params={
                'Resources': [self.make_id(self.resource.name)],
                'Tags': tag_list,
            },
        )

    def add_terminate_instances(self):
        return self.add_response(
            'terminate_instances',
            service_response={
            },
            expected_params={
                'InstanceIds': [self.make_id(self.resource.name)],
            },
        )
