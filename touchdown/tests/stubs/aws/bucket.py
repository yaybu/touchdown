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


class BucketStubber(ServiceStubber):

    client_service = 's3'

    def add_get_bucket_location(self, location_constraint='eu-central-1'):
        return self.add_response(
            'get_bucket_location',
            {'LocationConstraint': location_constraint},
            {'Bucket': self.resource.name},
        )

    def add_get_bucket_cors(self, rules=None):
        return self.add_response(
            'get_bucket_cors',
            {'CORSRules': rules or []},
            {'Bucket': self.resource.name},
        )

    def add_get_bucket_policy(self, policy=None):
        return self.add_response(
            'get_bucket_policy',
            {'Policy': policy or '{}'},
            {'Bucket': self.resource.name},
        )

    def add_get_bucket_notification_configuration(self):
        return self.add_response(
            'get_bucket_notification_configuration',
            {},
            {'Bucket': self.resource.name},
        )

    def add_get_bucket_accelerate_configuration(self):
        return self.add_response(
            'get_bucket_accelerate_configuration',
            {},
            {'Bucket': self.resource.name},
        )

    def add_list_buckets_empty_response(self):
        return self.add_response(
            'list_buckets',
            service_response={},
            expected_params={},
        )

    def add_list_buckets_one_response(self):
        return self.add_response(
            'list_buckets',
            service_response={
                'Buckets': [{
                    'Name': self.resource.name,
                }],
            },
            expected_params={},
        )

    def add_head_bucket(self):
        return self.add_response(
            'head_bucket',
            service_response={},
            expected_params={'Bucket': self.resource.name},
        )

    def add_list_objects(self, contents):
        return self.add_response(
            'list_objects',
            service_response={
                'Contents': contents,
            },
            expected_params={'Bucket': self.resource.name},
        )

    def add_delete_objects(self, contents):
        return self.add_response(
            'delete_objects',
            service_response={},
            expected_params={
                'Delete': {
                    'Objects': [{'Key': key} for key in contents],
                    'Quiet': True,
                },
                'Bucket': self.resource.name,
            },
        )

    def add_create_bucket(self):
        return self.add_response(
            'create_bucket',
            service_response={},
            expected_params={
                'Bucket': self.resource.name,
                'CreateBucketConfiguration': {
                    'LocationConstraint': 'eu-west-1',
                }
            },
        )

    def add_put_bucket_notification_configuration(self):
        return self.add_response(
            'put_bucket_notification_configuration',
            service_response={},
            expected_params={
                'Bucket': self.resource.name,
                'NotificationConfiguration': {
                    'LambdaFunctionConfigurations': [],
                }
            },
        )

    def add_delete_bucket(self):
        return self.add_response(
            'delete_bucket',
            service_response={},
            expected_params={
                'Bucket': self.resource.name,
            },
        )
