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

import copy
import datetime

from .service import ServiceStubber


class StreamingDistributionStubber(ServiceStubber):

    client_service = 'cloudfront'

    def disable(self, streaming_distribution_config):
        rv = copy.deepcopy(streaming_distribution_config)
        rv['Enabled'] = False
        return rv

    def add_list_streaming_distributions_empty_response(self):
        return self.add_response(
            'list_streaming_distributions',
            service_response={
                'StreamingDistributionList': {
                    'Items': [],
                    'Quantity': 0,
                    'Marker': '',
                    'MaxItems': 50,
                    'IsTruncated': False,
                },
            },
            expected_params={
            },
        )

    def add_list_streaming_distributions_one_response(self, streaming_distribution_config, status='Deployed'):
        summary = {
            'Id': 'CF123456',
            'Status': status,
            'LastModifiedTime': datetime.datetime.now(),
            'DomainName': 'example.com',
        }
        summary.update(streaming_distribution_config)

        for key in ('Logging', 'DefaultRootObject', 'CallerReference'):
            if key in summary:
                del summary[key]

        return self.add_response(
            'list_streaming_distributions',
            service_response={
                'StreamingDistributionList': {
                    'Items': [summary],
                    'Quantity': 1,
                    'Marker': '',
                    'MaxItems': 50,
                    'IsTruncated': False,
                }
            },
            expected_params={
            },
        )

    def add_get_streaming_distribution(self, streaming_distribution_config, status='Deployed'):
        return self.add_response(
            'get_streaming_distribution',
            service_response={
                'StreamingDistribution': {
                    'Id': 'CF123456',
                    'Status': status,
                    'LastModifiedTime': datetime.datetime.now(),
                    'DomainName': 'example.com',
                    'ActiveTrustedSigners': {
                        'Items': [],
                        'Quantity': 0,
                        'Enabled': False,
                    },
                    'StreamingDistributionConfig': streaming_distribution_config,
                },
                'ETag': 'ETAGZZZZZZ',
            },
            expected_params={
                'Id': 'CF123456',
            },
        )

    def add_create_streaming_distribution(self, streaming_distribution_config):
        return self.add_response(
            'create_streaming_distribution',
            service_response={
                'StreamingDistribution': {
                    'Id': 'CF123456',
                    'Status': 'InProgress',
                    'LastModifiedTime': datetime.datetime.now(),
                    'DomainName': '',
                    'ActiveTrustedSigners': {
                        'Items': [],
                        'Quantity': 0,
                        'Enabled': False,
                    },
                    'StreamingDistributionConfig': streaming_distribution_config,
                }
            },
            expected_params={
                'StreamingDistributionConfig': streaming_distribution_config,
            },
        )

    def add_update_streaming_distribution(self, streaming_distribution_config):
        return self.add_response(
            'update_streaming_distribution',
            service_response={
                'StreamingDistribution': {
                    'Id': 'CF123456',
                    'Status': 'InProgress',
                    'LastModifiedTime': datetime.datetime.now(),
                    'DomainName': '',
                    'ActiveTrustedSigners': {
                        'Items': [],
                        'Quantity': 0,
                        'Enabled': False,
                    },
                    'StreamingDistributionConfig': streaming_distribution_config,
                }
            },
            expected_params={
                'StreamingDistributionConfig': streaming_distribution_config,
                'Id': 'CF123456',
                'IfMatch': 'ETAGZZZZZZ',
            },
        )

    def add_delete_streaming_distribution(self):
        return self.add_response(
            'delete_streaming_distribution',
            service_response={
            },
            expected_params={
                'Id': 'CF123456',
                'IfMatch': 'ETAGZZZZZZ',
            },
        )
