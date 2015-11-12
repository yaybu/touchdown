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

import collections
import json

from touchdown.core.map import SerialMap
from touchdown.core import plan
from touchdown.core.goals import Goal, register


class Properties(object):

    def __init__(self, parent):
        self.parent = parent
        self.properties = collections.OrderedDict()

    def set(self, key, value):
        if value:
            self.properties[key] = value

    def set_ip(self, key, value):
        if value:
            self.properties[key] = str(value)

    def set_bool(self, key, value):
        if value is not None:
            self.properties[key] = True if value else False

    def set_ref(self, key, value):
        if value:
            self.properties[key] = {"Ref": self.parent.get_name(value)}

    def set_ref_list(self, key, value):
        values = [{"Ref": self.parent.get_name(v)} for v in value]
        if values:
            self.properties[key] = values


"""
policy
hosted_zone
record
alias_target
role
route
policy
alias_target
"""


class Export(Goal):

    """ Export config as a CloudFormation tempate """

    name = "cloudformation-export"
    mutator = False

    # FIXME: Deal with server certificates

    types = {
        "log_group": "AWS::Logs::LogGroup",
        "auto_scaling_group": "AWS::AutoScaling::AutoScalingGroup",
        "launch_configuration": "AWS::AutoScaling::LaunchConfiguration",
        "bucket": "AWS::S3::Bucket",
        "vpc": "AWS::EC2::VPC",
        "security_group": "AWS::EC2::SecurityGroup",
        "internet_gateway": "AWS::EC2::InternetGateway",
        "subnet": "AWS::EC2::Subnet",
        "route_table": "AWS::EC2::RouteTable",
        "network_acl": "AWS::EC2::NetworkACL",
        "load_balancer": "AWS::EC2::LoadBalancer",
        "alarm": "AWS::CloudWatch::Alarm",
        "distribution": "AWS::CloudFront::Distribution",
        "trail": "AWS::CloudTrail::Trail",
        "database": "AWS::RDS::DBInstance",
        "instance_profile": "AWS::IAM::InstanceProfile",
        "filter": "AWS::Logs::MetricFilter",
        "replication_group": "AWS::ElastiCache::ReplicationGroup",
        "hosted_zone": "AWS::Route53::HostedZone",
        "record": "AWS::Route53::RecordSet",
    }

    def serialize_hosted_zone(self, props, hosted_zone):
        props.set("Name", hosted_zone.name)

    def serialize_record(self, props, record):
        props.set_ref("HostedZoneId", record.parent)

    def serialize_filter(self, props, filter):
        # FIXME: Deal with unwrapping transformations
        props.set_ref("LogGroupName", filter.log_group)
        props.set("FilterPattern", filter.pattern)
        # props.set("MetricTransformations", filter.transformations)

    def serialize_replication_group(self, props, replication_group):
        props.set_bool("AutomaticFailoverEnabled", replication_group.automatic_failover)
        props.set_bool("AutoMinorVersionUpgrade", replication_group.auto_minor_version_upgrade)
        props.set("CacheNodeType", replication_group.instance_class)
        #props.set_ref("CacheParameterGroupName", replication_group.parameter_group)
        #props.set("CacheSecurityGroupNames" : [ String, ... ],
        props.set_ref("CacheSubnetGroupName", replication_group.subnet_group)
        props.set("Engine", replication_group.engine)
        props.set("EngineVersion", replication_group.engine_version)
        #props.set("NotificationTopicArn" : String,
        props.set("NumCacheClusters", replication_group.num_cache_clusters)
        props.set("Port", replication_group.port)
        props.set("PreferredCacheClusterAZs", replication_group.availability_zone)
        #props.set("PreferredMaintenanceWindow" : String,
        props.set("ReplicationGroupDescription", replication_group.description)
        props.set_ref_list("SecurityGroupIds", replication_group.security_groups)
        #props.set("SnapshotArns" : [ String, ... ],
        #props.set("SnapshotRetentionLimit" : Integer,
        #props.set("SnapshotWindow" : String

    def serialize_database(self, props, db):
        props.set("AllocatedStorage", db.allocated_storage)
        props.set_bool("AllowMajorVersionUpgrade", db.allow_major_version_upgrade)
        props.set_bool("AutoMinorVersionUpgrade", db.auto_minor_version_upgrade)
        props.set("AvailabilityZone", db.availability_zone)
        props.set("BackupRetentionPeriod", db.backup_retention_period)
        props.set("CharacterSetName", db.character_set_name)
        #props.set("DBClusterIdentifier" : String,
        props.set("DBInstanceClass", db.instance_class)
        props.set("DBInstanceIdentifier", db.name)
        props.set("DBName", db.db_name)
        #"DBParameterGroupName" : String,
        #"DBSecurityGroups" : [ String, ... ],
        #"DBSnapshotIdentifier" : String
        #"DBSubnetGroupName" : String,
        props.set("Engine", db.engine)
        props.set("EngineVersion", db.engine_version)
        props.set("Iops", db.iops)
        props.set_ref("KmsKeyId", db.key)
        #"LicenseModel" : String,
        props.set("MasterUsername", db.master_username)
        props.set("MasterUserPassword", db.master_password)
        props.set_bool("MultiAZ", db.multi_az)
        #"OptionGroupName" : String,
        props.set("Port", db.port)
        props.set("PreferredBackupWindow", db.preferred_backup_window)
        props.set("PreferredMaintenanceWindow", db.preferred_maintenance_window)
        props.set("PubliclyAccessible", db.publically_accessible)
        #"SourceDBInstanceIdentifier" : String,
        props.set_bool("StorageEncrypted", db.storage_encrypted)
        props.set("StorageType", db.storage_type)
        #"Tags" : [ Resource Tag, ..., ],
        props.set_ref_list("VPCSecurityGroups", db.security_groups)

    def serialize_trail(self, props, trail):
        props.set_bool("IncludeGlobalServiceEvents", trail.include_global)
        props.set_bool("IsLogging", True)
        props.set_ref("S3BucketName", trail.bucket)
        props.set("S3KeyPrefix", trail.bucket_prefix)
        props.set_ref("SnsTopicName", trail.topic)
        #FIXME: CloudWatch logs integration?

    def serialize_bucket(self, props, bucket):
        #"AccessControl" : String,
        props.set("BucketName", bucket.name)
        #"CorsConfiguration" : CORS Configuration,
        #"LifecycleConfiguration" : Lifecycle Configuration,
        #"LoggingConfiguration" : Logging Configuration,
        #"NotificationConfiguration" : Notification Configuration,
        #"Tags" : [ Resource Tag, ... ],
        #"VersioningConfiguration" : Versioning Configuration,
        #"WebsiteConfiguration" : Website Configuration Type

    def serialize_vpc(self, props, vpc):
        tags = {}
        tags.update(vpc.tags)
        tags['Name'] = vpc.name
        props.set("Tags", tags)

        props.set_ip("CidrBlock", vpc.cidr_block)
        #props.set("EnableDnsSupport", vpc.enable_dns_support)
        #props.set("EnableDnsHostnames", vpc.enable_dns_hostnames)
        props.set("InstanceTenancy", vpc.tenancy)

    def serialize_internet_gateway(self, props, internet_gateway):
        tags = {}
        tags.update(internet_gateway.tags)
        tags['Name'] = internet_gateway.name
        props.set("Tags", tags)

    def serialize_security_group(self, props, security_group):
        props.set("Description", security_group.description)
        # FIXME....
        props.set("SecurityGroupEgress", [])
        props.set("SecurityGroupIngress", [])
        props.set_ref("VpcId", security_group.vpc)

        tags = {}
        tags.update(security_group.tags)
        tags['Name'] = security_group.name
        props.set("Tags", tags)


    def serialize_subnet(self, props, subnet):
        props.set("AvailabilityZone", subnet.availability_zone)
        props.set_ip("CidrBlock", subnet.cidr_block)
        # props.set_bool("MapPublicIpOnLaunch", subnet.)
        props.set_ref("VpcId", subnet.vpc)

        tags = {}
        tags.update(subnet.tags)
        tags['Name'] = subnet.name
        props.set("Tags", tags)

    def serialize_route_table(self, props, route_table):
        props.set_ref("VpcId", route_table.vpc)

        tags = {}
        tags.update(route_table.tags)
        tags['Name'] = route_table.name
        props.set("Tags", tags)


    def serialize_network_acl(self, props, network_acl):
        tags = {}
        tags.update(network_acl.tags)
        tags['Name'] = network_acl.name
        props.set("Tags", tags)

    def serialize_alarm(self, props, alarm):
        # FIXME: Need to be able to unpickle interfaces
        # FIXME: Need to be able to map a dimension to a dict
        props.set_bool("ActionsEnabled", alarm.actions_enabled)
        #props.set_ref_list("AlarmActions", alarm.alarm_actions)
        props.set("AlarmDescription", alarm.description)
        props.set("AlarmName", alarm.name)
        props.set("ComparisonOperator", alarm.comparison_operator)
        #props.set("Dimensions", alarm.dimensions)
        props.set("EvaluationPeriods", alarm.evaluation_periods)
        #props.set_ref_list("InsufficientDataActions", alarm.insufficient_data_actions)
        props.set("MetricName", alarm.metric)
        props.set("Namespace", alarm.namespace)
        #props.set_ref_list("OKActions", alarm.ok_actions)
        props.set("Period", alarm.period)
        props.set("Statistic", alarm.statistic)
        props.set("Threshold", alarm.threshold)
        props.set("Unit", alarm.unit)

    def serialize_load_balancer(self, props, load_balancer):
        pass

    def serialize_instance_profile(self, props, instance_profile):
        pass

    def serialize_distribution(self, props, distribution):
        pass

    def get_name(self, node):
        if node in self.names:
            return self.names[node]
        name = node.name + "_" + node.resource_name + str(len(self.names))
        self.names[node] = name
        return name

    def get_ref(self, node):
        return {"Ref": self.get_name(node)}

    def serialize_log_group(self, props, resource):
        props.set("RetentionInDays", resource.retention)

    def serialize_launch_configuration(self, props, resource):
        props.set_bool("AssociatePulicIpAddress", resource.associate_public_ip_address)
        #"BlockDeviceMappings" : [ BlockDeviceMapping, ... ],
        #"ClassicLinkVPCId" : String,
        #"ClassicLinkVPCSecurityGroups" : [ String, ... ],
        props.set_bool("EbsOptimized", resource.ebs_optimized)
        props.set_ref("IamInstanceProfile", resource.instance_profile)
        props.set("ImageId", resource.image)
        #"InstanceId" : String,
        props.set("InstanceMonitoring", resource.instance_monitoring)
        props.set("InstanceType", resource.instance_type)
        props.set("KernelId", resource.kernel)
        props.set_ref("KeyName", resource.key_pair)
        props.set("PlacementTenancy", resource.placement_tenancy)
        props.set("RamDiskId", resource.ramdisk)
        props.set_ref_list("SecurityGroups", resource.security_groups)
        props.set("SpotPrice", resource.spot_price)
        # props.set("UserData", resource.user_data)

    def serialize_auto_scaling_group(self, props, resource):
        # props.set("AvailabilityZones",  : [ String, ... ],
        props.set("Cooldown", resource.default_cooldown)
        props.set("DesiredCapacity", resource.desired_capacity)
        props.set("HealthCheckGracePeriod", resource.health_check_grace_period)
        props.set("HealthCheckType", resource.health_check_type)
        props.set_ref('LaunchConfigurationName', resource.launch_configuration)
        props.set_ref_list('LoadBalancerNames', resource.load_balancers)
        props.set("MaxSize", resource.max_size)
        props.set("MinSize", resource.min_size)
        #"MetricsCollection" : [ MetricsCollection, ... ]
        #"NotificationConfigurations" : [ NotificationConfigurations, ... ],
        #"PlacementGroup" : String,
        #"Tags" : [ Auto Scaling Tag, ..., ],
        #"TerminationPolicies" : [ String, ..., ],
        props.set_ref_list("VPCZoneIdentifier", resource.subnets)

    def serialize_resource(self, resource):
        fn = getattr(self, "serialize_{}".format(resource.resource_name), None)
        if not fn:
            return
        props = Properties(self)
        fn(props, resource)

        return self.get_name(resource), {
            "Type": self.types[resource.resource_name],
            "Properties": props.properties,
        }

    def get_plan_class(self, resource):
        return plan.NullPlan

    def execute(self):
        self.names = {}

        resources = collections.OrderedDict()

        def serialize_map(resource):
            if resource.ensure and 'destroy' in resource.ensure:
                return
            res = self.serialize_resource(resource)
            if not res:
                return
            resources[res[0]] = res[1]

        list(SerialMap(
            self.ui,
            self.get_execution_order(),
            serialize_map,
        ))

        output = collections.OrderedDict()
        output['AWSTemplateFormatVersion'] = '2010-09-09'
        output['Parameters'] = {}
        output['Mappings'] = {}
        output['Resources'] = resources
        output['Outputs'] = {}

        print json.dumps(output, indent=4, separators=(',', ': '))


register(Export)
