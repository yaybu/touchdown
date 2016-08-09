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


class VolumeAttachmentStubber(ServiceStubber):

    def add_describe_attachments_empty_response_by_instance_and_volume(self):
        return self.add_response(
            'describe_volumes',
            service_response={
                'Volumes': [],
            },
            expected_params={
                'Filters': [
                    {'Name': 'attachment.status', 'Values': ['attaching', 'attached']},
                    {'Name': 'attachment.instance-id', 'Values': ['i-abcdef12345']}
                ],
                'VolumeIds': ['vol-abcdef12345'],
            }
        )

    def add_attach_volume(self, device='/foo'):
        return self.add_response(
            'attach_volume',
            service_response={
            },
            expected_params={
                'Device': device,
                'InstanceId': 'i-abcdef12345',
                'VolumeId': 'vol-abcdef12345',
            }
        )
