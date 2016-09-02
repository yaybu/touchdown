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


class ImageCopyStubber(ServiceStubber):

    client_service = 'ec2'

    def make_id(self, name):
        return 'ami-' + super(ImageCopyStubber, self).make_id(name)[:8]

    def add_describe_images_empty_response(self):
        return self.add_response(
            'describe_images',
            service_response={
                'Images': [],
            },
            expected_params={
                'Filters': [
                    {'Name': 'name', 'Values': [self.resource.name]},
                ],
            },
        )

    def add_describe_images_one_response(self):
        return self.add_response(
            'describe_images',
            service_response={
                'Images': [{
                    'Name': self.resource.name,
                    'ImageId': self.make_id(self.resource.name),
                    'State': 'available',
                }],
            },
            expected_params={
                'Filters': [
                    {'Name': 'name', 'Values': [self.resource.name]},
                ],
            },
        )

    def add_describe_image_attribute(self):
        return self.add_response(
            'describe_image_attribute',
            service_response={},
            expected_params={
                'Attribute': 'launchPermission',
                'ImageId': self.make_id(self.resource.name),
            },
        )

    def add_copy_image(self):
        return self.add_response(
            'copy_image',
            service_response={
                'ImageId': self.make_id(self.resource.name),
            },
            expected_params={
                'Name': self.resource.name,
                'SourceImageId': 'ami-9d5a86fe',
                'SourceRegion': 'eu-west-1',
            },
        )

    def add_deregister_image(self):
        return self.add_response(
            'deregister_image',
            service_response={},
            expected_params={
                'ImageId': self.make_id(self.resource.name),
            },
        )
