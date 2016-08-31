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


class TestWafByteMatch(StubberTestCase):

    def test_annotate_byte_match(self):
        '''Test that when we annotate an , we gain the expected data.'''

        goal = self.create_goal('get')
        # TODO: standardise naming - eg 'byte_match.py' vs
        # 'ip_set.py'. Should both be _set.
        byte_match_set = self.aws.add_byte_match_set(name='my-byte-match')
        describe = goal.get_service(byte_match_set, 'describe')

        stub = Stubber(describe.client)
        stub.add_response(
            'get_byte_match_set',
            expected_params={'ByteMatchSetId': 'my-byte-match-set-id'},
            service_response={'ByteMatchSet': {
                'ByteMatchSetId': 'my-byte-match',
                'ByteMatchTuples': [{
                    'FieldToMatch': {'Type': 'test_match_type'},
                    'TargetString': 'test_target',
                    'TextTransformation': 'test_transformation',
                    'PositionalConstraint': 'test_constraint',
                }],
            }},
        )

        with stub:
            obj = describe.annotate_object({
                'ByteMatchSetId': 'my-byte-match-set-id',
            })

        assert obj == {
            'ByteMatchSetId': 'my-byte-match',
            'ByteMatchTuples': [{
                'FieldToMatch': {'Type': 'test_match_type'},
                'TargetString': 'test_target',
                'TextTransformation': 'test_transformation',
                'PositionalConstraint': 'test_constraint'}],
        }

    def test_create_byte_match_set(self):
        '''Test that when we create an bytematch set, we perform the expected client
        calls.

        '''
        goal = self.create_goal('apply')
        byte_match_set = self.aws.add_byte_match_set(name='my-byte-match-set')
        apply = goal.get_service(byte_match_set, 'apply')

        stub = Stubber(apply.client)
        stub.add_response(
            'get_change_token',
            expected_params={},
            service_response={'ChangeToken': 'mychangetoken1'},
        )
        stub.add_response(
            'create_byte_match_set',
            expected_params={
                'ChangeToken': 'mychangetoken1',
                'Name': 'my-byte-match-set',
            },
            service_response={
                'ChangeToken': 'mychangetoken1'
            },
        )

        action = apply.create_object()
        with stub:
            action.run()

    def test_update_byte_match_set_with_tuple(self):
        '''Test that when we update a byte_match_set to have a tuple, we pass
        the information to link the tuple to the byte match set.

        '''
        goal = self.create_goal('apply')

        byte_match_set = self.aws.add_byte_match_set(
            name='my-byte-match-set',
            byte_matches=[{
                'field': 'URI',
                'transformation': 'LOWERCASE',
                'position': 'STARTS_WITH',
                'target': 'test_bad_string'}
            ],
        )

        apply = goal.get_service(byte_match_set, 'apply')
        apply.object = {
            'ByteMatchSetId': 'my-byte-match-set-id',
        }

        stub = Stubber(apply.client)
        stub.add_response(
            'get_change_token',
            expected_params={},
            service_response={'ChangeToken': 'mychangetoken1'},
        )
        stub.add_response(
            'update_byte_match_set',
            expected_params={
                'ChangeToken': 'mychangetoken1',
                'Updates': [{
                    'Action': 'INSERT',
                    'ByteMatchTuple': {
                        'FieldToMatch': {
                            'Type': 'URI',
                        },
                        'PositionalConstraint': 'STARTS_WITH',
                        'TargetString': 'test_bad_string',
                        'TextTransformation': 'LOWERCASE',
                    }
                }],
                'ByteMatchSetId': 'my-byte-match-set-id',
            },
            service_response={
                'ChangeToken': 'mychangetoken1'
            },
        )

        with stub:
            for action in apply.update_object():
                action.run()

    def test_delete_byte_match_set(self):
        '''Test that the plan for deleting an byte_match_set performs the right
        actions.

        '''
        goal = self.create_goal('destroy')
        byte_match_set = self.aws.add_byte_match_set(name='my-byte-match-set')
        destroy = goal.get_service(byte_match_set, 'destroy')
        destroy.object = {
            'ByteMatchSetId': 'my-byte-match-set-id',
            'ByteMatchTuples': [{
                'FieldToMatch': {'Type': 'test_match_type'},
                'TargetString': 'test_target',
                'TextTransformation': 'test_transformation',
                'PositionalConstraint': 'test_constraint',
            }],
        }

        stub = Stubber(destroy.client)
        stub.add_response(
            'get_change_token',
            expected_params={},
            service_response={'ChangeToken': 'mychangetoken1'},
        )
        stub.add_response(
            'update_byte_match_set',
            expected_params={
                'ChangeToken': 'mychangetoken1',
                'Updates': [{
                    'Action': 'DELETE',
                    'ByteMatchTuple': {
                        'FieldToMatch': {'Type': 'test_match_type'},
                        'TargetString': 'test_target',
                        'TextTransformation': 'test_transformation',
                        'PositionalConstraint': 'test_constraint',
                    },
                }],
                'ByteMatchSetId': 'my-byte-match-set-id'},
            service_response={'ChangeToken': 'mychangetoken1'}
        )
        stub.add_response(
            'get_change_token',
            expected_params={},
            service_response={'ChangeToken': 'mychangetoken2'},
        )
        stub.add_response(
            'delete_byte_match_set',
            expected_params={
                'ChangeToken': 'mychangetoken2',
                'ByteMatchSetId': 'my-byte-match-set-id'},
            service_response={'ChangeToken': 'mychangetoken2'},
        )
        actions = destroy.destroy_object()

        with stub:
            for action in actions:
                action.run()
