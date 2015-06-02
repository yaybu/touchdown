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
from touchdown.aws.rds import Database

from .common import PricingData


pricing_data = [
    # MySQL
    PricingData(
        "https://a0.awsstatic.com/pricing/1/rds/mysql/pricing-standard-deployments.min.js",
        engine="mysql",
        multi_az=False,
    ),
    PricingData(
        "https://a0.awsstatic.com/pricing/1/rds/mysql/pricing-multiAZ-deployments.min.js",
        engine="mysql",
        multi_az=True,
    ),
    # Postgres
    PricingData(
        "https://a0.awsstatic.com/pricing/1/rds/postgresql/pricing-standard-deployments.min.js",
        engine="postgres",
        multi_az=False,
    ),
    PricingData(
        "https://a0.awsstatic.com/pricing/1/rds/postgresql/pricing-multiAZ-deployments.min.js",
        engine="postgres",
        multi_az=True,
    ),
]


class Plan(common.SimplePlan, plan.Plan):

    name = "cost"
    resource = Database
    service_name = "rds"

    def get_pricing_data(self):
        for data in pricing_data:
            if data.matches(self.resource):
                return data
        raise ValueError("Cannot find pricing file for {}".format(self.resource))

    def cost(self):
        return self.get_pricing_data().get_instance_type(
            self.resource.account.region,
            self.resource.instance_class,
        )
