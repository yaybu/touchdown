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


class SubnetStubber(ServiceStubber):

    client_service = 'ec2'

    def make_id(self, name):
        return 'subnet-' + super(SubnetStubber, self).make_id(name)[:8]

    def add_describe_subnets_empty_response(self):
        return self.add_response(
            'describe_subnets',
            service_response={
                'Subnets': [],
            },
            expected_params={
                'Filters': [
                    {'Name': 'cidrBlock', 'Values': [str(self.resource.cidr_block)]},
                    {'Name': 'vpcId', 'Values': ['vpc-f96b65a5']}
                ],
            },
        )

    def add_describe_subnets_one_response(self):
        return self.add_response(
            'describe_subnets',
            service_response={
                'Subnets': [{
                    'SubnetId': self.make_id(self.resource.name),
                    'State': 'available',
                }],
            },
            expected_params={
                'Filters': [
                    {'Name': 'cidrBlock', 'Values': [str(self.resource.cidr_block)]},
                    {'Name': 'vpcId', 'Values': ['vpc-f96b65a5']}
                ],
            },
        )

    def add_describe_network_acls(self, network_acls=None):
        if not network_acls:
            network_acls = [{
                'NetworkAclId': 'nacl-abcd1234',
            }]

        for nacl in network_acls:
            nacl['Associations'] = [{
                'SubnetId': self.make_id(self.resource.name),
                'NetworkAclId': nacl['NetworkAclId'],
                'NetworkAclAssociationId': 'ASSOCIATION-ID-HERE',
            }]

        return self.add_response(
            'describe_network_acls',
            service_response={
                'NetworkAcls': network_acls or [],
            },
            expected_params={
                'Filters': [
                    {'Name': 'association.subnet-id', 'Values': [self.make_id(self.resource.name)]}
                ],
            },
        )

    def add_describe_route_tables(self):
        return self.add_response(
            'describe_route_tables',
            service_response={
                'RouteTables': [],
            },
            expected_params={
                'Filters': [
                    {'Name': 'association.subnet-id', 'Values': [self.make_id(self.resource.name)]}
                ],
            },
        )

    def add_create_subnet(self):
        return self.add_response(
            'create_subnet',
            service_response={
                'Subnet': {
                    'SubnetId': self.make_id(self.resource.name),
                }
            },
            expected_params={
                'CidrBlock': str(self.resource.cidr_block),
                'VpcId': 'vpc-f96b65a5'
            },
        )

    def add_create_tags(self, **tags):
        tag_list = [{'Key': k, 'Value': v} for (k, v) in tags.items()]
        self.add_response(
            'create_tags',
            service_response={
            },
            expected_params={
                'Resources': [self.make_id(self.resource.name)],
                'Tags': tag_list,
            },
        )

    def add_associate_route_table(self, route_table_id):
        return self.add_response(
            'associate_route_table',
            service_response={
            },
            expected_params={
                'SubnetId': self.make_id(self.resource.name),
                'RouteTableId': route_table_id,
            },
        )

    def add_replace_network_acl_association(self):
        return self.add_response(
            'replace_network_acl_association',
            service_response={
            },
            expected_params={
                'AssociationId': 'ASSOCIATION-ID-HERE',
                'NetworkAclId': 'nacl-d4aef56e',
            },
        )

    def add_delete_subnet(self):
        return self.add_response(
            'delete_subnet',
            service_response={
            },
            expected_params={
                'SubnetId': self.make_id(self.resource.name),
            },
        )
