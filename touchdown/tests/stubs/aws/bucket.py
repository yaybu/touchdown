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
