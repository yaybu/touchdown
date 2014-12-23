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

from botocore import session


class VPCMixin(object):

    def __init__(self, *args, **kwargs):
        super(VPCMixin, self).__init__(*args, **kwargs)
        self.session = session.Session()
        # self.session.set_credentials(aws_access_key_id, aws_secret_access_key)
        self.service = self.session.get_service("ec2")
        self.endpoint = self.service.get_endpoint("eu-west-1")
