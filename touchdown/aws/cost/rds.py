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

from touchdown.aws.rds import Database
from touchdown.core import plan

from .common import CostEstimator, PricingData


class DatabasePerHour(PricingData):

    description = "Database instance"
    expression = "config.regions[?region=='{region}'].types[].tiers[?name=='{instance_class}'].prices.USD[]"
    rate = "hourly"

    def format_expression(self, resource):
        return self.expression.format(
            region=self.REGIONS[resource.account.region],
            instance_class=resource.instance_class,
        )


class DatabasePerGb(PricingData):

    description = "Database storage"
    expression = "config.regions[?region='{region}']"
    rate = "billing-period"

    def format_expression(self, resource):
        return self.expression.format(
            region=self.REGIONS[resource.account.region],
            instance_class=resource.instance_class,
        )


class Plan(CostEstimator, plan.Plan):

    name = "cost"
    resource = Database
    service_name = "rds"

    pricing_data = [
        # MySQL
        DatabasePerHour(
            "https://a0.awsstatic.com/pricing/1/rds/mysql/pricing-standard-deployments.min.js",
            engine="mysql",
            multi_az=False,
        ),
        DatabasePerHour(
            "https://a0.awsstatic.com/pricing/1/rds/mysql/pricing-multiAZ-deployments.min.js",
            engine="mysql",
            multi_az=True,
        ),
        # Postgres
        DatabasePerHour(
            "https://a0.awsstatic.com/pricing/1/rds/postgresql/pricing-standard-deployments.min.js",
            engine="postgres",
            multi_az=False,
        ),
        DatabasePerHour(
            "https://a0.awsstatic.com/pricing/1/rds/postgresql/pricing-multiAZ-deployments.min.js",
            engine="postgres",
            multi_az=True,
        ),
    ]
