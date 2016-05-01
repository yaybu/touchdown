# Copyright 2015 Isotoma Limited
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

import base64
import hashlib
import inspect
import zipfile

from six import StringIO

from touchdown.aws.iam import Role
from touchdown.aws.vpc import SecurityGroup, Subnet
from touchdown.core import argument, serializers
from touchdown.core.plan import XOR, Plan, Present
from touchdown.core.resource import Resource

from ..account import BaseAccount
from ..common import SimpleApply, SimpleDescribe, SimpleDestroy


class FunctionSerializer(serializers.Formatter):

    def mkinfo(self, name):
        info = zipfile.ZipInfo(
            name,
            date_time=(2004, 7, 6, 0, 0, 0),
        )
        info.external_attr = 0o644 << 16
        return info

    def render(self, runner, func):
        buf = StringIO()
        zf = zipfile.ZipFile(
            buf,
            mode='w',
            compression=zipfile.ZIP_DEFLATED
        )
        zf.writestr(self.mkinfo("main.py"), inspect.getsource(func))
        zf.close()
        return buf.getvalue()


class Function(Resource):

    resource_name = "lambda_function"

    arn = argument.Output("FunctionArn")

    name = argument.String(field="FunctionName", min=1, max=140)
    description = argument.String(name="Description")
    timeout = argument.Integer(name="Timeout", default=3)
    runtime = argument.String(
        field="Runtime",
        default='python2.7',
        choices=['nodejs', 'java8', 'python2.7'],
    )
    handler = argument.String(field="Handler", min=0, max=128)
    role = argument.Resource(
        Role,
        field="Role",
        serializer=serializers.Property("Arn"),
    )

    code = argument.Function(
        field="Code",
        serializer=serializers.Dict(
            ZipFile=FunctionSerializer(),
        )
    )

    code_from_bytes = argument.String(
        field="Code",
        serializer=serializers.Dict(
            ZipFile=serializers.String(),
        )
    )

    code_from_s3 = argument.Resource(
        "touchdown.aws.s3.File",
        field="Code",
        serializer=serializers.Dict(
            S3Bucket=serializers.Property("Bucket"),
            S3Key=serializers.Property("Key"),
            # S3ObjectionVersion=,
        )
    )

    memory = argument.Integer(name="MemorySize", default=128, min=128, max=1536)
    publish = argument.Boolean(name="Publish", default=True)

    security_groups = argument.ResourceList(SecurityGroup, field="SecurityGroupIds", group="vpc_config")
    subnets = argument.ResourceList(Subnet, field="SubnetIds", group="vpc_config")
    vpc_config = argument.Serializer(
        serializer=serializers.Resource(group="vpc_config"),
        field="VpcConfig",
    )

    account = argument.Resource(BaseAccount)


class Describe(SimpleDescribe, Plan):

    resource = Function
    service_name = 'lambda'
    describe_action = "get_function_configuration"
    describe_notfound_exception = "ResourceNotFoundException"
    describe_envelope = "@"
    key = 'FunctionName'


class Apply(SimpleApply, Describe):

    create_action = "create_function"
    create_envelope = "@"
    update_action = "update_function_configuration"

    retryable = {
        "InvalidParameterValueException": [
            "The role defined for the function cannot be assumed by Lambda.",
        ],
    }

    signature = (
        Present('name'),
        Present('role'),
        Present('handler'),
        # Runtime must be present - but default is valid
        # Present('runtime'),
        XOR(
            Present('code'),
            Present('code_from_bytes'),
            Present('code_from_s3'),
        ),
    )

    def update_object(self):
        update_code = False
        if self.object:
            serialized = serializers.Resource().render(self.runner, self.resource)
            if 'ZipFile' in serialized['Code']:
                hasher = hashlib.sha256(serialized['Code']['ZipFile'])
                digest = base64.b64encode(hasher.digest()).decode('utf-8')
                if self.object['CodeSha256'] != digest:
                    update_code = True
            elif 'S3Bucket' in serialized['Code']:
                f = self.get_plan(self.resource.code_from_s3)
                if f.object['LastModified'] > self.object['LastModified']:
                    update_code = True

        if update_code:
            kwargs = {
                "FunctionName": self.resource.name,
                "Publish": True,
            }
            kwargs.update(serialized['Code'])
            yield self.generic_action(
                "Update function code",
                self.client.update_function_code,
                **kwargs
            )


class Destroy(SimpleDestroy, Describe):

    destroy_action = "delete_function"
