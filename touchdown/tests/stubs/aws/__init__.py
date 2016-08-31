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

from .account import AccountStubber
from .bucket import BucketStubber
from .database import DatabaseStubber
from .distribution import DistributionStubber
from .ec2_instance import EC2InstanceStubber
from .endpoint import VpcEndpointStubber
from .event_rule import EventRuleStubber
from .external_account import ExternalAccountStubber
from .hosted_zone import HostedZoneStubber
from .internet_gateway import InternetGatewayStubber
from .keypair import KeyPairStubber
from .launch_configuration import LaunchConfigurationStubber
from .network_acl import NetworkAclStubber
from .password_policy import PasswordPolicyStubber
from .queue import QueueStubber
from .rds_subnet_group import RdsSubnetGroupStubber
from .role import RoleStubber
from .route_table import RouteTableStubber
from .security_group import SecurityGroupStubber
from .subnet import SubnetStubber
from .topic import TopicStubber
from .volume_attachment import VolumeAttachmentStubber
from .volume import VolumeStubber
from .vpc import VpcStubber


__all__ = [
    'AccountStubber',
    'BucketStubber',
    'DatabaseStubber',
    'DistributionStubber',
    'EC2InstanceStubber',
    'EventRuleStubber',
    'ExternalAccountStubber',
    'HostedZoneStubber',
    'InternetGatewayStubber',
    'KeyPairStubber',
    'LaunchConfigurationStubber',
    'NetworkAclStubber',
    'PasswordPolicyStubber',
    'QueueStubber',
    'RdsSubnetGroupStubber',
    'RoleStubber',
    'RouteTableStubber',
    'SecurityGroupStubber',
    'SubnetStubber',
    'TopicStubber',
    'VolumeAttachmentStubber',
    'VolumeStubber',
    'VpcEndpointStubber',
    'VpcStubber',
]
