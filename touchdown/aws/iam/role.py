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

from touchdown.core.resource import Resource
from touchdown.core.target import Target
from touchdown.core import argument

from ..account import AWS
from ..common import SimpleDescribe, SimpleApply, SimpleDestroy


class Role(Resource):

    resource_name = "role"

    name = argument.String(aws_field="Name")
    path = argument.String(aws_field='Path')
    policies = argument.Dict()
    account = argument.Resource(AWS)


class Describe(SimpleDescribe, Target):

    resource = Role
    service_name = 'iam'
    describe_action = "list_roles"
    describe_list_key = "Roles"
    key = 'Role'

    def describe_object(self):
        paginator = self.client.get_paginator("list_roles")
        for page in paginator.paginate():
            for role in page['Roles']:
                if role['RoleName'] == self.resource.name:
                    return role


class Apply(SimpleApply, Describe):

    create_action = "create_role"

    def update_object(self):
        policy_names = []

        # If the object exists then we can look at the roles it has
        # Otherwise we assume its a new role and it will have no policies
        if self.object:
            policy_names = self.client.list_role_policies(
                RoleName=self.resource.name,
            )['PolicyNames']

        for name, document in self.resource.policies.items():
            document = json.loads(document)

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

    destroy_action = "destroy_role"
