# Copyright 2014 Isotoma Limited
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

import json

import requests

from touchdown.core import argument, errors, serializers
from touchdown.core.plan import Plan
from touchdown.core.resource import Resource

from ..account import BaseAccount
from ..common import SimpleApply, SimpleDescribe, SimpleDestroy


class Role(Resource):

    resource_name = "role"

    arn = argument.Output("Arn")

    name = argument.String(field="RoleName")
    path = argument.String(field='Path')
    assume_role_policy = argument.Dict(field="AssumeRolePolicyDocument", serializer=serializers.Json(serializers.Map()))

    policies = argument.Dict()
    account = argument.Resource(BaseAccount)

    def clean_assume_role_policy(self, policy):
        if frozenset(policy.keys()).difference(frozenset(("Version", "Statement"))):
            raise errors.InvalidParameter("Unexpected policy key")

        result = {}
        result['Version'] = policy.get('Version', '2012-10-17')
        result['Statement'] = []
        for statement in policy.get("Statement", []):
            s = {
                "Action": statement["Action"],
                "Effect": statement["Effect"],
                "Principal": statement["Principal"],
                "Sid": statement.get("Sid", ""),
            }
            if "Condition" in statement:
                s['Condition'] = statement['Condition']
            result['Statement'].append(s)
        return result


class Describe(SimpleDescribe, Plan):

    resource = Role
    service_name = 'iam'
    describe_action = "list_roles"
    describe_envelope = "Roles"
    describe_filters = {}
    key = 'RoleName'

    def describe_object_matches(self, role):
        return role['RoleName'] == self.resource.name


class Apply(SimpleApply, Describe):

    create_action = "create_role"

    def update_assume_role_policy(self):
        if not self.object:
            return

        pd = serializers.Argument("assume_role_policy")
        diff = pd.diff(self.runner, self.resource, json.dumps(self.object.get('AssumeRolePolicyDocument', {})))
        if diff.matches():
            return

        yield self.generic_action(
            "Update 'Assume Role Policy' document",
            self.client.update_assume_role_policy,
            RoleName=serializers.Identifier(),
            PolicyDocument=pd,
        )

    def update_object(self):
        policy_names = []

        for change in super(Apply, self).update_object():
            yield change

        for change in self.update_assume_role_policy():
            yield change

        # If the object exists then we can look at the roles it has
        # Otherwise we assume its a new role and it will have no policies
        if self.object:
            policy_names = self.client.list_role_policies(
                RoleName=self.resource.name,
            )['PolicyNames']

        for name, document in self.resource.policies.items():
            changed = False
            if name not in policy_names:
                changed = True

            # We can't do a single API to get all names and documents for all
            # policies, so for each policy that *might* have changed we have to
            # call teh API and check.
            # Save an API call by only doing it for policies that definitely
            # exist
            if not changed:
                policy = self.client.get_role_policy(
                    RoleName=self.resource.name,
                    PolicyName=name,
                )

                if policy['PolicyDocument'] != document:
                    changed = True

            if changed:
                yield self.generic_action(
                    "Put policy {}".format(name),
                    self.client.put_role_policy,
                    RoleName=self.resource.name,
                    PolicyName=name,
                    PolicyDocument=json.dumps(document),
                )

        for name in policy_names:
            if name not in self.resource.policies:
                yield self.generic_action(
                    "Delete policy {}".format(name),
                    self.client.delete_role_policy,
                    RoleName=self.resource.name,
                    PolicyName=name,
                )


class Destroy(SimpleDestroy, Describe):

    destroy_action = "delete_role"

    def destroy_object(self):
        result = self.client.list_role_policies(RoleName=self.resource.name)
        for name in result.get('PolicyNames', []):
            yield self.generic_action(
                "Delete policy {}".format(name),
                self.client.delete_role_policy,
                RoleName=self.resource.name,
                PolicyName=name,
            )

        for change in super(Destroy, self).destroy_object():
            yield change


class Plan(Describe):

    name = "get-signin-url"
    resource = Role
    service_name = "iam"

    def get_signin_url(self):
        role = self.describe_object()

        sts = self.runner.get_plan(self.resource.account).session.create_client("sts")
        creds = sts.assume_role(
            RoleArn=role['Arn'],
            RoleSessionName="touchdown-get-signin-url",
        )['Credentials']

        token = requests.get(
            "https://signin.aws.amazon.com/federation",
            params={
                "Action": "getSigninToken",
                "Session": json.dumps({
                    "sessionId": creds['AccessKeyId'],
                    "sessionKey": creds['SecretAccessKey'],
                    "sessionToken": creds['SessionToken'],
                }),
            },
        ).json()

        p = requests.PreparedRequest()
        p.prepare_url("https://signin.aws.amazon.com/federation", {
            "Action": "login",
            "Issuer": "touchdown",
            "Destination": "https://console.aws.amazon.com/",
            "SigninToken": token['SigninToken'],
        })
        return p.url
