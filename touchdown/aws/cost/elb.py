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

from touchdown.core import plan
from touchdown.aws import common
from touchdown.aws.elb import LoadBalancer

from .common import PricingData


class Plan(common.SimplePlan, plan.Plan):

    name = "cost"
    resource = LoadBalancer
    service_name = "elb"

    def get_pricing_data(self):
        return PricingData(
            "https://a0.awsstatic.com/pricing/1/ec2/pricing-elb.min.js"
        )

    def cost(self):
        return self.get_pricing_data().get_region(
            self.resource.account.region,
        )
