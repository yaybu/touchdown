# Copyright 2014-2015 Isotoma Limited
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

from touchdown.core.resource import Resource
from touchdown.core.target import Target
from touchdown.core import argument

from ..account import AWS
from ..common import SimpleDescribe, SimpleApply, SimpleDestroy


class KeyPair(Resource):
    resource_name = "keypair"

    name = argument.String(aws_field="KeyName")
    public_key = argument.String(aws_field="PublicKeyMaterial")

    account = argument.Resource(AWS)


class Describe(SimpleDescribe, Target):

    resource = KeyPair
    service_name = 'ec2'
    describe_action = "describe_key_pairs"
    describe_list_key = "KeyPairs"
    key = 'KeyName'

    def get_describe_filters(self):
        return {"KeyNames": [self.resource.name]}


class Apply(SimpleApply, Describe):

    create_action = "import_key_pair"


class Destroy(SimpleDestroy, Describe):

    destroy_action = "destroy_key_pair"
