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

from touchdown.aws.elasticache import CacheCluster, ReplicationGroup
from touchdown.core import plan

from .common import CostEstimator, PricingData


class ElastiCachePerHour(PricingData):

    description = "ElastiCache instance"
    expression = "config.regions[?region=='{region}'].types[].tiers[?name=='{instance_type}'].prices.USD[]"
    rate = "hourly"

    def format_expression(self, resource):
        return self.expression.format(
            region=resource.account.region,
            instance_type=resource.instance_class,
        )


class CacheClusterPlan(CostEstimator, plan.Plan):

    resource = CacheCluster
    service_name = "elasticache"

    def get_scale(self, resource):
        return resource.num_cache_nodes

    pricing_data = [
        ElastiCachePerHour(
            "https://a0.awsstatic.com/pricing/1/elasticache/pricing-standard-deployments-elasticache.min.js",
        )
    ]


class ReplicationGroupPlan(CostEstimator, plan.Plan):

    resource = ReplicationGroup
    service_name = "elasticache"

    pricing_data = [
        ElastiCachePerHour(
            "https://a0.awsstatic.com/pricing/1/elasticache/pricing-standard-deployments-elasticache.min.js",
        )
    ]
