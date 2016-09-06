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

from touchdown.core import argument, serializers
from touchdown.core.plan import Plan, Present
from touchdown.core.resource import Resource

from ..account import BaseAccount
from ..common import SimpleApply, SimpleDescribe, SimpleDestroy, Waiter


class DomainValidationOption(Resource):

    resource_name = 'domain_validation_option'

    domain = argument.String(field='DomainName')
    validation_domain = argument.String(field='ValidationDomain')


class Certificate(Resource):

    resource_name = 'acm_certificate'

    name = argument.String(field='DomainName')
    arn = argument.Output('CertificateArn')
    alternate_names = argument.List(
        argument.String(),
        field='SubjectAlternativeNames',
    )
    validation_options = argument.ResourceList(
        DomainValidationOption,
        field='DomainValidationOptions',
    )
    account = argument.Resource(BaseAccount)


class CertificateWaiter(Waiter):

    def get_waiter_filters(self):
        return {
            'CertificateArn': self.plan.resource_id,
        }


class Describe(SimpleDescribe, Plan):

    resource = Certificate
    service_name = 'acm'
    api_version = '2015-12-08'
    describe_action = 'list_certificates'
    describe_envelope = 'CertificateSummaryList'
    describe_filters = {}
    key = 'CertificateArn'

    def describe_object_matches(self, obj):
        return obj['DomainName'] == self.resource.name

    def get_waiter(self, description, waiter, eventual_consistency_threshold=1):
        return CertificateWaiter(self, description, waiter, eventual_consistency_threshold)


class Apply(SimpleApply, Describe):

    create_action = 'request_certificate'
    create_response = 'id-only'
    waiter = 'certificate_issued'

    signature = [
        Present('name'),
    ]


class Destroy(SimpleDestroy, Describe):

    destroy_action = 'delete_certificate'

    def get_destroy_serializer(self):
        return serializers.Dict(
            CertificateArn=self.resource.arn,
        )
