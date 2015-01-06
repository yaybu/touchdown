import mock
import textwrap

from touchdown.core import errors
from touchdown.core import workspace
from touchdown.core.runner import Runner
from touchdown.core.main import ConsoleInterface

from .test_aws import TestCase


class TestVpc(TestCase):

    def test_no_change(self):
        self.responses.add("POST", 'https://ec2.eu-west-1.amazonaws.com/', body=textwrap.dedent("""
            <DescribeVpcsResponse xmlns="http://ec2.amazonaws.com/doc/2014-10-01/">
            <requestId>7a62c49f-347e-4fc4-9331-6e8eEXAMPLE</requestId>
            <vpcSet>
              <item>
                <vpcId>vpc-1a2b3c4d</vpcId>
                <state>available</state>
                <cidrBlock>10.0.0.0/23</cidrBlock>
                <dhcpOptionsId>dopt-7a8b9c2d</dhcpOptionsId>
                <instanceTenancy>default</instanceTenancy>
                <isDefault>false</isDefault>
                <tagSet>
                  <item>
                    <key>Name</key>
                    <value>test-vpc</value>
                  </item>
                </tagSet>
              </item>
            </vpcSet>
            </DescribeVpcsResponse>
        """))

        self.aws.add_vpc(name='test-vpc')
        self.assertRaises(errors.NothingChanged, self.runner.apply)

    def test_create(self):
        self.responses.add("POST", 'https://ec2.eu-west-1.amazonaws.com/', body=textwrap.dedent("""
            <DescribeVpcsResponse xmlns="http://ec2.amazonaws.com/doc/2014-10-01/">
            <requestId>7a62c49f-347e-4fc4-9331-6e8eEXAMPLE</requestId>
            <vpcSet/>
            </DescribeVpcsResponse>
        """), expires=1)

        self.responses.add("POST", 'https://ec2.eu-west-1.amazonaws.com/', body=textwrap.dedent("""
           <CreateVpcResponse xmlns="http://ec2.amazonaws.com/doc/2014-10-01/">
             <requestId>7a62c49f-347e-4fc4-9331-6e8eEXAMPLE</requestId>
             <vpc>
               <vpcId>vpc-1a2b3c4d</vpcId>
               <state>pending</state>
               <cidrBlock>10.0.0.0/16</cidrBlock>   
               <dhcpOptionsId>dopt-1a2b3c4d2</dhcpOptionsId>
               <instanceTenancy>default</instanceTenancy>
               <tagSet/>
             </vpc>
            </CreateVpcResponse>
        """), expires=1)

        self.responses.add("POST", 'https://ec2.eu-west-1.amazonaws.com/', body=textwrap.dedent("""
            <DescribeVpcsResponse xmlns="http://ec2.amazonaws.com/doc/2014-10-01/">
            <requestId>7a62c49f-347e-4fc4-9331-6e8eEXAMPLE</requestId>
            <vpcSet>
              <item>
                <vpcId>vpc-1a2b3c4d</vpcId>
                <state>available</state>
                <cidrBlock>10.0.0.0/23</cidrBlock>
                <dhcpOptionsId>dopt-7a8b9c2d</dhcpOptionsId>
                <instanceTenancy>default</instanceTenancy>
                <isDefault>false</isDefault>
                <tagSet>
                  <item>
                    <key>Name</key>
                    <value>test-vpc</value>
                  </item>
                </tagSet>
              </item>
            </vpcSet>
            </DescribeVpcsResponse>
        """))

        self.aws.add_vpc(name='test-vpc', cidr_block='192.168.0.1/25')
        self.runner.apply()
