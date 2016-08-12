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


class VolumeStubber(ServiceStubber):

    client_service = 'ec2'

    def add_describe_volumes_empty_response_by_name(self):
        return self.add_client_error(
            'describe_volumes',
            service_error_code='InvalidVolume.NotFound',
            service_message='',
        )

    def add_describe_volumes_one_response_by_name(self):
        return self.add_response(
            'describe_volumes',
            service_response={
                'Volumes': [{
                    'VolumeId': 'vol-abcdef12345',
                    'State': 'available',
                }],
            },
            expected_params={
                'Filters': [
                    {'Name': 'tag:Name', 'Values': [self.resource.name]}
                ],
            },
        )

    def add_create_volume(self, availability_zone='eu-west-1a'):
        return self.add_response(
            'create_volume',
            service_response={
                'VolumeId': 'vol-abcdef12345',
            },
            expected_params={
                'AvailabilityZone': 'eu-west-1a',
            },
        )

    def add_create_tags(self, **tags):
        tag_list = [{'Key': k, 'Value': v} for (k, v) in tags.items()]
        self.add_response(
            'create_tags',
            service_response={
            },
            expected_params={
                'Resources': ['vol-abcdef12345'],
                'Tags': tag_list,
            },
        )

    def add_delete_volume(self):
        return self.add_response(
            'delete_volume',
            service_response={
            },
            expected_params={
                'VolumeId': 'vol-abcdef12345',
            },
        )
