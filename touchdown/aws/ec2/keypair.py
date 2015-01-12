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

from ..account import Account
from ..common import SimpleDescribe, SimpleApply, SimpleDestroy


class KeyPair(Resource):

    """
    In order to securely use SSH with an EC2 instance (whether created directly
    or via a :py:class:`AutoScalingGroup`) you must first upload the key to the
    EC2 key pairs database. The KeyPair resource imports and keeps up to date
    an ssh public key.

    It can be used with any AWS account resource::

        aws.add_keypair(
            name="my-keypair",
            public_key=open(os.expanduser('~/.ssh/id_rsa.pub')),
        )
    """

    resource_name = "keypair"

    name = argument.String(field="KeyName")
    """ The name of the key. This field is required. """

    public_key = argument.String(field="PublicKeyMaterial")
    """ The public key material, in PEM form. Must be supplied in order to
    upload a key pair. """

    account = argument.Resource(Account)


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

    destroy_action = "delete_key_pair"
