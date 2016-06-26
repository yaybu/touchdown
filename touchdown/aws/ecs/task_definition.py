# Copyright 2016 John Carr
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from touchdown.core import argument, serializers
from touchdown.core.plan import Plan
from touchdown.core.resource import Resource

from ..account import BaseAccount
from ..common import SimpleApply, SimpleDescribe, SimpleDestroy
from ..logs import LogGroup


class PortMapping(Resource):

    resource_name = 'port_mapping'

    container_port = argument.Integer(field='containerPort')
    host_port = argument.Integer(field='hostPort')
    protocol = argument.String(field='protocol', choices=['tcp', 'udp'])


class EnvironmentKeyValue(Resource):

    resource_name = 'environment'

    name = argument.String(field='name')
    value = argument.String(field='value')


class MountPoint(Resource):

    resource_name = 'mount_point'

    source_volume = argument.String(field='sourceVolume')
    container_path = argument.String(field='containerPath')
    read_only = argument.Boolean(field='readOnly')


class VolumeFrom(Resource):

    resource_name = 'volume_from'

    source_container = argument.String(field='sourceContainer')
    read_only = argument.Boolean(field='readOnly')


class ExtraHost(Resource):

    resource_name = 'extra_host'

    source_container = argument.String(field='sourceContainer')
    read_only = argument.Boolean(field='readOnly')


class Ulimit(Resource):

    resource_name = 'ulimit'

    name = argument.String(
        field='name',
        choices=[
            'core',
            'cpu',
            'data',
            'fsize',
            'locks',
            'memlock',
            'msgqueue',
            'nice',
            'nofile',
            'nproc',
            'rss',
            'rtprio',
            'rttime',
            'sigpending',
            'stack',
        ],
    )
    soft_limit = argument.Integer(field='softLimit')
    hard_limit = argument.Integer(field='hardLimit')


class Container(Resource):

    resource_name = 'container_definition'

    name = argument.String(field='name', min=1)
    image = argument.String(field='name', min=1)
    cpu = argument.Integer(field='cpu')
    memory = argument.Integer(field='memory')
    links = argument.List(argument.String(), filed='links')
    port_mappings = argument.ResourceList(PortMapping, field='portMappings')
    essential = argument.Boolean(field='essential')
    entry_point = argument.String(field='entryPoint')
    command = argument.String(field='command')
    environment = argument.ResourceList(
        EnvironmentKeyValue,
        field='environment'
    )
    mount_point = argument.ResourceList(
        MountPoint,
        field='mountPoints'
    )
    volumes_from = argument.ResourceList(
        VolumeFrom,
        field='volumes_from'
    )
    hostname = argument.String(field='hostname')
    user = argument.String(field='user')
    working_directory = argument.String(field='workingDirectory')
    disable_networking = argument.String(field='disableNetworking')
    privileged = argument.String(field='privileged')
    readonly_root = argument.String(field='readonlyRootFilesystem')

    dns_servers = argument.List(argument.String(), field='dnsServers')
    dns_search_domains = argument.List(argument.String(), field='dnsSearchDomains')
    extra_hosts = argument.ResourceList(ExtraHost, field='extraHosts')

    docker_security_options = argument.List(argument.String(), field='dockerSecurityOptions')
    docker_labels = argument.Dict(field='dockerLabels')

    ulimits = argument.ResourceList(Ulimit, field='ulimits')

    log_group = argument.Resource(
        LogGroup,
        serializer=serializers.Dict(
            logDriver='awslogs',
            options=serializers.Dict(**{
                'awslogs-group': serializers.Identifier(),
                'awslogs-region': serializers.Expression(lambda r, o: o.account.region),
            })
        ),
        field='logConfiguration',
    )

    account = argument.Resource(BaseAccount)


class Volume(Resource):

    resource_name = 'volume'

    name = argument.String(field='name')
    source_path = argument.String(
        field='host',
        serializer=argument.Dict(
            sourcePath=argument.String(),
        )
    )


class TaskDefinition(Resource):

    resource_name = 'ecs_task_definition'

    name = argument.String(field='family', min=1, max=255)
    containers = argument.ResourceList(Container, field='containerDefinitions')
    volumes = argument.ResourceList(Volume, field='volumes')


class Describe(SimpleDescribe, Plan):

    resource = TaskDefinition
    service_name = 'ecs'
    describe_action = 'describe_task_definition'
    describe_envelope = '[taskDefinition]'
    key = 'family'

    def get_describe_filters(self):
        return {
            'taskDefinition': self.resource.name,
        }


class Apply(SimpleApply, Describe):

    create_action = 'register_task_definition'


class Destroy(SimpleDestroy, Describe):

    destroy_action = 'deregister_task_definition'
