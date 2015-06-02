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

import requests
import re
import demjson


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

    def get(self):
        data = requests.get(self.url).content
        data = re.sub(re.compile(r'/\*.*\*/\n', re.DOTALL), '', data)
        data = re.sub(r'^callback\(', '', data)
        data = re.sub(r'\);*$', '', data)
        return demjson.decode(data)

    def get_region(self, region):
        filtered = filter(
            lambda r: r['region'] == self.REGIONS[region],
            self.get()['config']['regions'],
        )
        return filtered[0]

    def get_instance_type(self, region, instance_type):
        r = self.get_region(region)
        for i in r['types']:
            for t in i['tiers']:
                if t['name'] == instance_type:
                    return {
                        "currency": "USD",
                        "cost": t['prices']['USD'],
                    }

    def matches(self, resource):
        for tag, value in self.tags.items():
            if getattr(resource, tag, None) != value:
                return False
        return True
