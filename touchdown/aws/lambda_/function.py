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
import itertools
import types
import zipfile

from six import BytesIO

from touchdown.aws.iam import Role
from touchdown.aws.vpc import SecurityGroup, Subnet
from touchdown.core import action, argument, serializers
from touchdown.core.plan import XOR, Plan, Present
from touchdown.core.resource import Resource

from ..account import BaseAccount
from ..common import SimpleApply, SimpleDescribe, SimpleDestroy


def get_code_sha256(bytes_value):
    hasher = hashlib.sha256(bytes_value)
    return base64.b64encode(hasher.digest()).decode('utf-8')


class Skip(action.Action):

    def __init__(self, inner):
        super(Skip, self).__init__(inner.plan)
        self.inner = inner

    @property
    def description(self):
        return self.inner.description

    def run(self):
        arguments = self.inner.action.get_arguments()
        if 'ZipFile' in arguments:
            if get_code_sha256(arguments['ZipFile']) == self.plan.object['CodeSha256']:
                self.plan.echo('Not uploading new zip as sha unchanged')
                return
        return self.inner.run()


class FunctionSerializer(serializers.Serializer):

    def __init__(self, function):
        self.function = function

    def mkinfo(self, name):
        info = zipfile.ZipInfo(
            name,
            date_time=(2004, 7, 6, 0, 0, 0),
        )
        info.external_attr = 0o644 << 16
        return info

    def render(self, runner, func):
        buf = BytesIO()
        zf = zipfile.ZipFile(
            buf,
            mode='w',
            compression=zipfile.ZIP_DEFLATED
        )
        zf.writestr(self.mkinfo('main.py'), inspect.getsource(self.function))
        zf.close()
        return buf.getvalue()

argument.Bytes.register_adapter(types.FunctionType, lambda r: FunctionSerializer(r))


class Function(Resource):

    resource_name = 'lambda_function'

    arn = argument.Output('FunctionArn')

    name = argument.String(field='FunctionName', min=1, max=140)
    description = argument.String(field='Description', max=256)
    timeout = argument.Integer(field='Timeout', default=3)
    runtime = argument.String(
        field='Runtime',
        default='python2.7',
        choices=['nodejs', 'java8', 'python2.7'],
    )
    handler = argument.String(field='Handler', min=0, max=128)
    role = argument.Resource(
        Role,
        field='Role',
        serializer=serializers.Property('Arn'),
    )

    code = argument.Bytes(
        field='Code',
        update=False,
        serializer=serializers.Dict(
            ZipFile=serializers.Bytes(),
        )
    )

    s3_file = argument.Resource(
        'touchdown.aws.s3.file.File',
        field='Code',
        update=False,
        serializer=serializers.Dict(
            S3Bucket=serializers.Property('Bucket'),
            S3Key=serializers.Property('Key'),
            # S3ObjectionVersion=,
        )
    )

    memory = argument.Integer(field='MemorySize', default=128, min=128, max=1536)
    publish = argument.Boolean(field='Publish', default=True, update=False)

    security_groups = argument.ResourceList(SecurityGroup, field='SecurityGroupIds', group='vpc_config')
    subnets = argument.ResourceList(Subnet, field='SubnetIds', group='vpc_config')
    vpc_config = argument.Serializer(
        serializer=serializers.Resource(group='vpc_config'),
        field='VpcConfig',
    )

    account = argument.Resource(BaseAccount)


class Describe(SimpleDescribe, Plan):

    resource = Function
    service_name = 'lambda'
    api_version = '2015-03-31'
    describe_action = 'get_function_configuration'
    describe_notfound_exception = 'ResourceNotFoundException'
    describe_envelope = '[@]'
    key = 'FunctionName'


class Apply(SimpleApply, Describe):

    create_action = 'create_function'
    create_envelope = '@'
    update_action = 'update_function_configuration'

    retryable = {
        'InvalidParameterValueException': [
            'The role defined for the function cannot be assumed by Lambda.',
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
            Present('s3_file'),
        ),
    )

    def get_all_unaliased_versions(self):
        versions = self.client.list_versions_by_function(FunctionName=self.resource.name)['Versions']

        # Drop any that have aliases pointing at them
        aliases = self.client.list_aliases(FunctionName=self.resource.name)
        ignore_versions = list(a['FunctionVersion'] for a in aliases['Aliases'])
        versions = filter(lambda x: x['Version'] not in ignore_versions, versions)

        # Drop the version $LATEST - for our purposes its an alias and we don't
        # want it
        versions = filter(lambda x: x['Version'] != '$LATEST', versions)

        # Sort on the Version and drop the last one. This should be the most
        # recent one - i.e. what $LATEST is pointing at.
        versions = sorted(versions, key=lambda x: int(x['Version']))
        versions = versions[:-1]

        return versions

    def remove_orphaned_versions(self):
        for version in self.get_all_unaliased_versions():
            yield self.generic_action(
                'Delete old version {Version}'.format(**version),
                self.client.delete_function,
                FunctionName=self.resource.name,
                Qualifier=version['Version'],
            )

    def update_code_by_zip(self):
        if not self.resource.code:
            return

        update_code = False
        arg = serializers.Argument('code', self.resource.meta.fields['code'])
        if arg.pending(self.runner, self.resource):
            digest = '<...>'
            update_code = True
        else:
            serialized = arg.render(self.runner, self.resource)
            digest = get_code_sha256(serialized['ZipFile'])
            if self.object['CodeSha256'] != digest:
                update_code = True

        if update_code:
            yield Skip(self.generic_action(
                ['Update function code', '{} => {}'.format(self.object['CodeSha256'], digest)],
                self.client.update_function_code,
                FunctionName=self.resource.name,
                ZipFile=self.resource.code,
                Publish=True,
            ))

    def update_code_by_s3(self):
        if not self.resource.s3_file:
            return

        update_code = False
        arg = serializers.Argument('code', self.resource.meta.fields['code'])
        if arg.pending(self.runner, self.resource):
            update_code = True

        if self.object.get('S3Bucket', '') != self.resource.s3_file.bucket.name:
            update_code = True

        if self.object.get('S3Key', '') != self.resource.s3_file.name:
            update_code = True

        if update_code:
            yield self.generic_action(
                'Update function code',
                self.client.update_function_code,
                FunctionName=self.resource.name,
                S3Bucket=self.resource.s3_file.bucket.name,
                S3Key=self.resource.s3_file.name,
                Publish=True,
            )

    def update_object(self):
        if not self.object:
            return []

        return itertools.chain(
            self.remove_orphaned_versions(),
            self.update_code_by_zip(),
            self.update_code_by_s3(),
            super(Apply, self).update_object(),
        )


class Destroy(SimpleDestroy, Describe):

    destroy_action = 'delete_function'
