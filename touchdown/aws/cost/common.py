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

import re
from decimal import Decimal

import requests

from touchdown.aws import common
from touchdown.core import errors

try:
    import demjson
except ImportError:
    demjson = None

try:
    import jmespath
except ImportError:
    jmespath = None


class PricingData(object):

    REGIONS = {
        "ap-northeast-1": "apac-tokyo",
        "ap-southeast-1": "apac-sin",
        "ap-southeast-2": "apac-syd",
        "eu-central-1": "eu-central-1",
        "eu-west-1": "eu-ireland",
        "us-east-1": "us-east",
        "us-gov-west-1": "us-gov-west-1",
        "us-west-1": "us-west",
        "us-west-2": "us-west-2",
        "sa-east-1": "sa-east-1",
    }

    def __init__(self, url, **tags):
        self.url = url
        self.tags = tags

    def format_expression(self, resource):
        return self.expression

    def get(self, resource):
        data = requests.get(self.url).content
        data = re.sub(re.compile(r'/\*.*\*/\n', re.DOTALL), '', data)
        data = re.sub(r'^callback\(', '', data)
        data = re.sub(r'\);*$', '', data)

        expression = self.format_expression(resource)

        return self.reduce(
            resource,
            jmespath.search(expression, demjson.decode(data)),
        )

    def get_scale(self, resource):
        return 1

    def reduce(self, resource, value):
        return sum(Decimal(v) for v in value) * self.get_scale(resource)

    def matches(self, resource):
        for tag, value in self.tags.items():
            if getattr(resource, tag, None) != value:
                return False
        return True


class CostEstimator(common.SimplePlan):

    name = "cost"

    def get_pricing_data(self):
        for data in self.pricing_data:
            if data.matches(self.resource):
                return data
        raise ValueError("Cannot find pricing file for {}".format(self.resource))

    def cost(self):
        if not demjson:
            raise errors.Error("Need to install 'demjson' to get pricing data for AWS resources")
        if not jmespath:
            raise errors.Error("Need to install 'jmespath' to get pricing data for AWS resource")
        return self.get_pricing_data().get(self.resource)
