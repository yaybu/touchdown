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


class TestWafRule(StubberTestCase):
    '''Test that WAF rules can be created, updated and deleted.

    Note: Because WAF uses a change token, every 'real' request is
    preceded by a call to `get_change_token`. The change token this
    gives us should then be included in the request we actually want
    to make, and it is also returned to us.

    '''

    def test_annotate_rule(self):
        '''Test that when we annotate a rule, we gain the expected data.'''
        goal = self.create_goal('get')
        rule = self.aws.add_rule(name='myrule')
        describe = goal.get_service(rule, 'describe')

        stub = Stubber(describe.client)
        stub.add_response(
            'get_rule',
            expected_params={'RuleId': 'my-rule-id'},
            service_response={'Rule': {
                'RuleId': 'my-rule-id',
                'Predicates': [{
                    'Negated': True,
                    'Type': 'test',
                    'DataId': 'dummy',
                }],
            }},
        )

        # When annotating this rule, we should get an object populated
        # with the data from the predicates.
        with stub:
            obj = describe.annotate_object({
                'RuleId': 'my-rule-id'
            })

        assert obj == {
            'RuleId': 'my-rule-id',
            'Predicates': [{
                'Negated': True,
                'Type': 'test',
                'DataId': 'dummy',
            }],
        }

    def test_create_rule(self):
        '''Test that when we create a rule, we perform the expected client
        calls.

        '''
        goal = self.create_goal('apply')
        rule = self.aws.add_rule(name='myrule', metric_name='mymetric')
        apply = goal.get_service(rule, 'apply')

        stub = Stubber(apply.client)
        stub.add_response(
            'get_change_token',
            expected_params={},
            service_response={'ChangeToken': 'mychangetoken1'},
        )
        stub.add_response(
            'create_rule',
            expected_params={
                'ChangeToken': 'mychangetoken1',
                'Name': 'myrule',
                'MetricName': 'mymetric'},
            service_response={
                'ChangeToken': 'mychangetoken1'
            },
        )

        action = apply.create_object()
        with stub:
            action.run()

    def test_update_rule_with_predicates(self):
        '''Test that when we update a rule to have a predicate, we pass the
        information to link the rule to the match.

        '''
        goal = self.create_goal('apply')

        ip_set = self.aws.add_ip_set(
            name='my-ip-set',
            addresses=[])
        apply = goal.get_service(ip_set, 'apply')
        apply.object = {
            'IPSetId': 'my-ip-set-id',
        }

        rule = self.aws.add_rule(
            name='myrule',
            metric_name='mymetric',
            predicates=[
                {'ip_set': ip_set}])

        apply = goal.get_service(rule, 'apply')
        apply.object = {
            'RuleId': 'my-rule-id',
        }

        stub = Stubber(apply.client)
        stub.add_response(
            'get_change_token',
            expected_params={},
            service_response={'ChangeToken': 'mychangetoken1'},
        )
        stub.add_response(
            'update_rule',
            expected_params={
                'ChangeToken': 'mychangetoken1',
                'Updates': [{
                    'Action': 'INSERT',
                    'Predicate': {
                        'Negated': False,
                        'Type': 'IPMatch',
                        'DataId': 'my-ip-set-id'}}],
                'RuleId': 'my-rule-id'},
            service_response={
                'ChangeToken': 'mychangetoken1'
            },
        )

        with stub:
            for action in apply.update_object():
                action.run()

    def test_delete_rule(self):
        '''Test that the plan for deleting a rule has expected actions.'''
        goal = self.create_goal('destroy')
        rule = self.aws.add_rule(name='myrule', metric_name='mymetric')
        destroy = goal.get_service(rule, 'destroy')
        destroy.object = {
            'RuleId': 'my-rule-id',
            'Predicates': [{
                'Negated': True,
                'Type': 'test',
                'DataId': 'dummy',
            }],
        }

        stub = Stubber(destroy.client)
        stub.add_response(
            'get_change_token',
            expected_params={},
            service_response={'ChangeToken': 'mychangetoken1'},
        )
        stub.add_response(
            'update_rule',
            expected_params={
                'ChangeToken': 'mychangetoken1',
                'Updates': [{
                    'Action': 'DELETE',
                    'Predicate': {
                        'Negated': True,
                        'Type': 'test',
                        'DataId': 'dummy'}}],
                'RuleId': 'my-rule-id'},
            service_response={'ChangeToken': 'mychangetoken1'}
        )
        stub.add_response(
            'get_change_token',
            expected_params={},
            service_response={'ChangeToken': 'mychangetoken2'},
        )
        stub.add_response(
            'delete_rule',
            expected_params={
                'ChangeToken': 'mychangetoken2',
                'RuleId': 'my-rule-id'},
            service_response={'ChangeToken': 'mychangetoken2'},
        )
        actions = destroy.destroy_object()

        with stub:
            for action in actions:
                action.run()
