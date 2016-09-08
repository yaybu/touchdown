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

from .service import ServiceStubber


class LogFilterStubber(ServiceStubber):

    client_service = 'logs'

    def add_describe_log_filter_empty_response(self):
        self.add_response(
            'describe_metric_filters',
            service_response={},
            expected_params={'filterNamePrefix': self.resource.name,
                             'logGroupName': 'test-log-group'}
        )

    def add_describe_log_filter_one_response(self):
        self.add_response(
            'describe_metric_filters',
            service_response={
                'metricFilters': [{
                    'filterName': self.resource.name,
                    'filterPattern': 'pattern',
                    'metricTransformations': [{
                        'metricName': 'transformation-name',
                        'metricNamespace': 'transformation-namespace',
                        'metricValue': 'transformation-value',
                        }],
                }],
            },
            expected_params={'filterNamePrefix': self.resource.name,
                             'logGroupName': 'test-log-group'}
        )

    def add_create_log_filter(self):
        return self.add_response(
            'put_metric_filter',
            service_response={},
            expected_params={
                'filterName': self.resource.name,
                'filterPattern': 'pattern',
                'logGroupName': 'test-log-group',
                'metricTransformations': [{
                    'metricName': 'transformation-name',
                    'metricNamespace': 'transformation-namespace',
                    'metricValue': 'transformation-value',
                    }],
            }
        )

    def add_delete_log_filter(self):
        return self.add_response(
            'delete_metric_filter',
            service_response={
            },
            expected_params={
                'filterName': self.resource.name,
                'logGroupName': 'test-log-group',
            }
        )
