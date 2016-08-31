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


class TestWafWebACL(StubberTestCase):
    '''Test that WAF WebACLs can be created, updated and deleted.

    Note: Because WAF uses a change token, every 'real' request is
    preceded by a call to `get_change_token`. The change token this
    gives us should then be included in the request we actually want
    to make, and it is also returned to us.

    '''

    def test_annotate_web_acl(self):
        '''Test that when we annotate a web acl, we gain the expected data.'''
        goal = self.create_goal('get')
        web_acl = self.aws.add_web_acl(name='my-web-acl')
        describe = goal.get_service(web_acl, 'describe')

        stub = Stubber(describe.client)
        stub.add_response(
            'get_web_acl',
            expected_params={'WebACLId': 'my-web-acl-id'},
            service_response={
                'WebACL': {
                    'WebACLId': 'my-web-acl-id',
                    'DefaultAction': {
                        'Type': 'BLOCK',
                    },
                    'Rules': [{
                        'RuleId': 'my-rule-id',
                        'Priority': 10,
                        'Action': {
                            'Type': 'ALLOW',
                        },
                    }],
                }
            },
        )

        with stub:
            obj = describe.annotate_object({
                'WebACLId': 'my-web-acl-id'
            })

        assert obj == {
            'WebACLId': 'my-web-acl-id',
            'DefaultAction': {
                'Type': 'BLOCK',
            },
            'Rules': [{
                'RuleId': 'my-rule-id',
                'Priority': 10,
                'Action': {
                    'Type': 'ALLOW',
                },
            }],
        }

    def test_create_web_acl(self):
        '''Test that when we create a web_acl, we perform the expected client
        calls.

        '''
        goal = self.create_goal('apply')
        web_acl = self.aws.add_web_acl(name='my-web-acl', metric_name='mymetric', default_action='BLOCK')
        apply = goal.get_service(web_acl, 'apply')

        stub = Stubber(apply.client)
        stub.add_response(
            'get_change_token',
            expected_params={},
            service_response={'ChangeToken': 'mychangetoken1'},
        )
        stub.add_response(
            'create_web_acl',
            expected_params={
                'ChangeToken': 'mychangetoken1',
                'Name': 'my-web-acl',
                'MetricName': 'mymetric',
                'DefaultAction': {
                    'Type': 'BLOCK',
                }
            },
            service_response={
                'ChangeToken': 'mychangetoken1'
            },
        )

        action = apply.create_object()
        with stub:
            action.run()

    def test_update_web_acl_with_active_rules(self):
        '''Test that when we update a web_acl to have a rule, we pass the
        information to link the web_acl to the match.

        '''
        goal = self.create_goal('apply')

        rule = self.aws.add_rule(
            name='my-ip-set',
            metric_name='my-metric-name')
        apply = goal.get_service(rule, 'apply')
        apply.object = {
            'RuleId': 'my-rule-id',
        }

        web_acl = self.aws.add_web_acl(
            name='my-web-acl',
            metric_name='mymetric',
            default_action='BLOCK',
            activated_rules=[{
                'action': 'ALLOW',
                'priority': 10,
                'rule': rule,
            }],
        )

        apply = goal.get_service(web_acl, 'apply')
        apply.object = {
            'WebACLId': 'my-web-acl-id',
        }

        stub = Stubber(apply.client)
        stub.add_response(
            'get_change_token',
            expected_params={},
            service_response={'ChangeToken': 'mychangetoken1'},
        )
        stub.add_response(
            'update_web_acl',
            expected_params={
                'ChangeToken': 'mychangetoken1',
                'Updates': [{
                    'Action': 'INSERT',
                    'ActivatedRule': {
                        'RuleId': 'my-rule-id',
                        'Priority': 10,
                        'Action': {'Type': 'ALLOW'},
                    },
                }],
                'WebACLId': 'my-web-acl-id'},
            service_response={
                'ChangeToken': 'mychangetoken1'
            },
        )

        with stub:
            for action in apply.update_object():
                action.run()

    def test_delete_web_acl(self):
        '''Test that the plan for deleting a web_acl has expected actions.'''
        goal = self.create_goal('destroy')
        web_acl = self.aws.add_web_acl(name='my-web-acl', metric_name='mymetric')
        destroy = goal.get_service(web_acl, 'destroy')
        destroy.object = {
            'WebACLId': 'my-web-acl-id',
            'Rules': [{
                'Priority': 10,
                'RuleId': 'my-rule-id',
                'Action': {
                    'Type': 'BLOCK',
                },
            }],
        }

        stub = Stubber(destroy.client)
        stub.add_response(
            'get_change_token',
            expected_params={},
            service_response={'ChangeToken': 'mychangetoken1'},
        )
        stub.add_response(
            'update_web_acl',
            expected_params={
                'ChangeToken': 'mychangetoken1',
                'Updates': [{
                    'Action': 'DELETE',
                    'ActivatedRule': {
                        'Action': {'Type': 'BLOCK'},
                        'Priority': 10,
                        'RuleId': 'my-rule-id',
                    }
                }],
                'WebACLId': 'my-web-acl-id'},
            service_response={'ChangeToken': 'mychangetoken1'}
        )
        stub.add_response(
            'get_change_token',
            expected_params={},
            service_response={'ChangeToken': 'mychangetoken2'},
        )
        stub.add_response(
            'delete_web_acl',
            expected_params={
                'ChangeToken': 'mychangetoken2',
                'WebACLId': 'my-web-acl-id'},
            service_response={'ChangeToken': 'mychangetoken2'},
        )
        actions = destroy.destroy_object()

        with stub:
            for action in actions:
                action.run()
