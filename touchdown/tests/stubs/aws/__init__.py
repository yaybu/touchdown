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
from .acm_certificate import CertificateStubber
from .ami_copy import ImageCopyStubber
from .auto_scaling_group import AutoScalingGroupStubber
from .bucket import BucketStubber
from .cache_cluster import CacheClusterStubber
from .customer_gateway import CustomerGatewayStubber
from .database import DatabaseStubber
from .distribution import DistributionStubber
from .ec2_instance import EC2InstanceStubber
from .elastic_ip import ElasticIpStubber
from .elasticache_subnet_group import ElastiCacheSubnetGroupStubber
from .endpoint import VpcEndpointStubber
from .event_rule import EventRuleStubber
from .external_account import ExternalAccountStubber
from .hosted_zone import HostedZoneStubber
from .instance_profile import InstanceProfileStubber
from .internet_gateway import InternetGatewayStubber
from .key import KeyStubber
from .keypair import KeyPairStubber
from .launch_configuration import LaunchConfigurationStubber
from .load_balancer import LoadBalancerStubber
from .log_filter import LogFilterStubber
from .log_group import LogGroupStubber
from .network_acl import NetworkAclStubber
from .password_policy import PasswordPolicyStubber
from .pipeline import PipelineStubber
from .queue import QueueStubber
from .rds_subnet_group import RdsSubnetGroupStubber
from .replication_group import ReplicationGroupStubber
from .resource import ResourceStubber
from .rest_api import RestApiStubber
from .role import RoleStubber
from .route_table import RouteTableStubber
from .s3_file import S3FileStubber
from .security_group import SecurityGroupStubber
from .server_certificate import ServerCertificateStubber
from .service import ServiceStubber, Stubber
from .streaming_distribution import StreamingDistributionStubber
from .subnet import SubnetStubber
from .topic import TopicStubber
from .volume import VolumeStubber
from .volume_attachment import VolumeAttachmentStubber
from .vpc import VpcStubber
from .vpn_connection import VpnConnectionStubber
from .vpn_gateway import VpnGatewayStubber

__all__ = [
    "AccountStubber",
    "AutoScalingGroupStubber",
    "BucketStubber",
    "CacheClusterStubber",
    "CertificateStubber",
    "CustomerGatewayStubber",
    "DatabaseStubber",
    "DistributionStubber",
    "EC2InstanceStubber",
    "ElastiCacheSubnetGroupStubber",
    "ElasticIpStubber",
    "EventRuleStubber",
    "ExternalAccountStubber",
    "HostedZoneStubber",
    "ImageCopyStubber",
    "InstanceProfileStubber",
    "InternetGatewayStubber",
    "KeyPairStubber",
    "KeyStubber",
    "LaunchConfigurationStubber",
    "LoadBalancerStubber",
    "LogFilterStubber",
    "LogGroupStubber",
    "NetworkAclStubber",
    "PasswordPolicyStubber",
    "PipelineStubber",
    "QueueStubber",
    "ReplicationGroupStubber",
    "ResourceStubber",
    "RestApiStubber",
    "RdsSubnetGroupStubber",
    "RoleStubber",
    "RouteTableStubber",
    "SecurityGroupStubber",
    "ServerCertificateStubber",
    "ServiceStubber",
    "StreamingDistributionStubber",
    "Stubber",
    "SubnetStubber",
    "S3FileStubber",
    "TopicStubber",
    "VolumeAttachmentStubber",
    "VolumeStubber",
    "VpcEndpointStubber",
    "VpcStubber",
    "VpnConnectionStubber",
    "VpnGatewayStubber",
]
