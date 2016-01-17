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


class GeneratePolicy(Goal):

    """ Generate AWS IAM Permission Policy to be able to apply changes """

    name = "generate-policy"
    mutator = False

    arns = {
        "keypair": "arn:aws:ec2:{region}:{account}:key-pair/{name}",
        "log_group": "arn:aws:logs:{region}:{account}:log-group:{name}",
        "auto_scaling_group": "arn:aws:autoscaling:{region}:{account}:autoScalingGroup:groupid:autoScalingGroupName/{name}",
        "scaling_policy": "arn:aws:autoscaling:{region}:{account}:scalingPolicy:policyid:autoScalingGroupName/groupfriendlyname:policyname/{name}",
        "launch_configuration": "AWS::AutoScaling::LaunchConfiguration",
        "bucket": "arn:aws:s3:::{name}",
        "vpc": "arn:aws:ec2:{region}:{account}:vpc/*",
        "security_group": "arn:aws:ec2:{region}:{account}:security-group/*",
        "internet_gateway": "arn:aws:ec2:{region}:{account}:internet-gateway/*",
        "subnet": "arn:aws:ec2:{region}:{account}:subnet/*",
        "route_table": "arn:aws:ec2:{region}:{account}:route-table/*",
        "network_acl": "arn:aws:ec2:{region}:{account}:network-acl/*",
        "load_balancer": "arn:aws:elasticloadbalancing:{region}:{account}:loadbalancer/{name}",
        "alarm": "AWS::CloudWatch::Alarm",
        "distribution": "AWS::CloudFront::Distribution",
        "trail": "arn:aws:cloudtrail:{region}:{account}:trail/{name}",
        "database": "arn:aws:rds:{region}:{account}:db:{name}",
        "instance_profile": "arn:aws:iam::{account}:instance-profile/{name}",
        "filter": "AWS::Logs::MetricFilter",
        "replication_group": "arn:aws:elasticache:{region}:{account}:replication_group:{name}",
        "hosted_zone": "arn:aws:route53:::hostedzone/{id}",
    }

    conditions = {
        "subnet": ("ec2:ResourceTag/Name", "{name}"),
        "route_table": ("ec2:ResourceTag/Name", "{name}"),
        "network_acl": ("ec2:ResourceTag/Name", "{name}"),
        "security_group": ("ec2:ResourceTag/Name", "{name}"),
        "internet_gateway": ("ec2:ResourceTag/Name", "{name}"),
        "vpc": ("ec2:ResourceTag/Name", "{name}"),
    }

    def visit_resource(self, resource):
        describe_plan = resource.meta.get_plan("describe")
        if not hasattr(describe_plan, 'service_name'):
            return

        apply_plan = resource.meta.get_plan("apply")
        destroy_plan = resource.meta.get_plan("destroy")

        actions = []

        resource_name = None
        if resource.resource_name in self.arns:
            resource_name = self.arns[resource.resource_name].format(
                id="XXXXXXXX",
                name=resource.name,
                account="123456789012",
                region="eu-west-1",
            )

        conditions = None
        if resource.resource_name in self.conditions:
            key, value = self.conditions[resource.resource_name]
            conditions = {
                "Condition": {
                    "StringEquals": {
                        key: value.format(
                            name=resource.name,
                        )
                    }
                }
            }

        if describe_plan and getattr(describe_plan, "describe_action", None):
            actions.append(':'.join((describe_plan.service_name, describe_plan.describe_action)))

        if apply_plan:
            actions.append(':'.join((apply_plan.service_name, apply_plan.create_action)))
            if apply_plan.update_action:
                actions.append(':'.join((apply_plan.service_name, apply_plan.update_action)))

        if destroy_plan:
            if 'never-destroy' in resource.ensure:
                yield self.statement(
                    effect='Deny',
                    action=':'.join((destroy_plan.service_name, destroy_plan.destroy_action)),
                    resource=resource_name,
                    conditions=conditions,
                )
            else:
                actions.append(':'.join((destroy_plan.service_name, destroy_plan.destroy_action)))

        yield self.statement(
            effect='Allow',
            action=actions,
            resource=resource_name,
            conditions=conditions,
        )

    def statement(self, effect, action, resource, conditions=None):
        statement = collections.OrderedDict()
        statement['Effect'] = effect
        statement['Action'] = action
        if resource:
            statement['Resource'] = resource
        if conditions:
            statement['Conditions'] = conditions
        return statement

    def get_plan_class(self, resource):
        return plan.NullPlan

    def execute(self):
        policy = collections.OrderedDict()
        policy['Version'] = '2012-10-17'
        statements = policy['Statements'] = []

        def serialize_map(resource):
            for statement in self.visit_resource(resource):
                statements.append(statement)

        list(SerialMap(
            self.ui,
            self.get_execution_order(),
            serialize_map,
        ))

        print (json.dumps(policy, indent=4, separators=(',', ': ')))


register(GeneratePolicy)
