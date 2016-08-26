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

import datetime

from .service import ServiceStubber


class RoleStubber(ServiceStubber):

    client_service = 'iam'

    def add_list_roles_one_response_by_name(self):
        return self.add_response(
            'list_roles',
            service_response={
                'Roles': [
                    {
                        'RoleName': self.resource.name,
                        'Path': '/iam/myrole',
                        'RoleId': '1234567890123456',
                        'Arn': '12345678901234567890',
                        'CreateDate': datetime.datetime.now(),
                    }
                ]
            },
            expected_params={},
        )
