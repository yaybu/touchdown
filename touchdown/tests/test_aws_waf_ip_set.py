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

from touchdown.tests.aws import Stubber, StubberTestCase


class TestWafIpSet(StubberTestCase):

    def test_annotate_ip_set(self):
        '''Test that when we annotate an ipset, we gain the expected data.'''

        goal = self.create_goal('get')
        ip_set = self.aws.add_ip_set(name='my-ip-set')
        describe = goal.get_service(ip_set, 'describe')

        stub = Stubber(describe.client)
        stub.add_response(
            'get_ip_set',
            expected_params={'IPSetId': 'my-ip-set-id'},
            service_response={'IPSet': {
                'IPSetId': 'my-ip-set-id',
                'IPSetDescriptors': [{'Type': 'IPV4', 'Value': '10.0.0.1/32'}]
            }},
        )

        with stub:
            obj = describe.annotate_object({
                'IPSetId': 'my-ip-set-id',
            })

        assert obj == {
            'IPSetId': 'my-ip-set-id',
            'IPSetDescriptors': [{
                'Type': 'IPV4',
                'Value': '10.0.0.1/32',
            }],
        }

    def test_create_ip_set(self):
        '''Test that when we create an IP set, we perform the expected client
        calls.

        '''
        goal = self.create_goal('apply')
        ip_set = self.aws.add_ip_set(name='my-ip-set')
        apply = goal.get_service(ip_set, 'apply')

        stub = Stubber(apply.client)
        stub.add_response(
            'get_change_token',
            expected_params={},
            service_response={'ChangeToken': 'mychangetoken1'},
        )
        stub.add_response(
            'create_ip_set',
            expected_params={
                'ChangeToken': 'mychangetoken1',
                'Name': 'my-ip-set',
            },
            service_response={
                'ChangeToken': 'mychangetoken1'
            },
        )

        action = apply.create_object()
        with stub:
            action.run()

    def test_update_ip_set_with_descriptors(self):
        '''Test that when we update a ip_set to have a descriptor, we pass the
        information to link the ip set to the descriptor.

        '''
        goal = self.create_goal('apply')

        ip_set = self.aws.add_ip_set(
            name='my-ip-set',
            addresses=[
                '10.0.0.1/32'
            ],
        )

        apply = goal.get_service(ip_set, 'apply')
        apply.object = {
            'IPSetId': 'my-ip-set-id',
        }

        stub = Stubber(apply.client)
        stub.add_response(
            'get_change_token',
            expected_params={},
            service_response={'ChangeToken': 'mychangetoken1'},
        )
        stub.add_response(
            'update_ip_set',
            expected_params={
                'ChangeToken': 'mychangetoken1',
                'Updates': [{
                    'Action': 'INSERT',
                    'IPSetDescriptor': {
                        'Type': 'IPV4',
                        'Value': '10.0.0.1/32'}}],
                'IPSetId': 'my-ip-set-id'},
            service_response={
                'ChangeToken': 'mychangetoken1'
            },
        )

        with stub:
            for action in apply.update_object():
                action.run()

    def test_delete_ip_set(self):
        '''Test that the plan for deleting an ip_set performs the right
        actions.

        '''
        goal = self.create_goal('destroy')
        ip_set = self.aws.add_ip_set(name='my-ip-set')
        destroy = goal.get_service(ip_set, 'destroy')
        destroy.object = {
            'IPSetId': 'my-ip-set-id',
            'IPSetDescriptors': [{
                'Type': 'IPV4',
                'Value': '10.0.0.1/32',
            }],
        }

        stub = Stubber(destroy.client)
        stub.add_response(
            'get_change_token',
            expected_params={},
            service_response={'ChangeToken': 'mychangetoken1'},
        )
        stub.add_response(
            'update_ip_set',
            expected_params={
                'ChangeToken': 'mychangetoken1',
                'Updates': [{
                    'Action': 'DELETE',
                    'IPSetDescriptor': {
                        'Type': 'IPV4',
                        'Value': '10.0.0.1/32'}
                }],
                'IPSetId': 'my-ip-set-id'},
            service_response={'ChangeToken': 'mychangetoken1'}
        )
        stub.add_response(
            'get_change_token',
            expected_params={},
            service_response={'ChangeToken': 'mychangetoken2'},
        )
        stub.add_response(
            'delete_ip_set',
            expected_params={
                'ChangeToken': 'mychangetoken2',
                'IPSetId': 'my-ip-set-id'},
            service_response={'ChangeToken': 'mychangetoken2'},
        )
        actions = destroy.destroy_object()

        with stub:
            for action in actions:
                action.run()
