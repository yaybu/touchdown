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

from touchdown.aws.ec2 import AutoScalingGroup
from touchdown.core import plan

from .common import CostEstimator, PricingData


class Ec2PerHour(PricingData):

    description = "Elastic Compute instance"
    expression = "config.regions[?region=='{region}'].instanceTypes[].sizes[?size=='{instance_type}'].valueColumns[0].prices.USD[]"
    rate = "hourly"

    def format_expression(self, resource):
        return self.expression.format(
            region=resource.account.region,
            instance_type=resource.launch_configuration.instance_type,
        )


class Plan(CostEstimator, plan.Plan):

    name = "cost"
    resource = AutoScalingGroup
    service_name = "ec2"

    pricing_data = [
        Ec2PerHour(
            "https://a0.awsstatic.com/pricing/1/ec2/linux-od.min.js",
        )
    ]
