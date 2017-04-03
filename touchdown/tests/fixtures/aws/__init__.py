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

from .bucket import BucketFixture
from .customer_gateway import CustomerGatewayFixture
from .instance_profile import InstanceProfileFixture
from .launch_configuration import LaunchConfigurationFixture
from .network_acl import NetworkAclFixture
from .rest_api import RestApiFixture
from .role import RoleFixture
from .route_table import RouteTableFixture
from .subnet import SubnetFixture
from .vpc import VpcFixture
from .vpn_gateway import VpnGatewayFixture


__all__ = [
    'BucketFixture',
    'CustomerGatewayFixture',
    'InstanceProfileFixture',
    'LaunchConfigurationFixture',
    'NetworkAclFixture',
    'RestApiFixture',
    'RoleFixture',
    'RouteTableFixture',
    'SubnetFixture',
    'VpcFixture',
    'VpnGatewayFixture',
]
