import textwrap

from touchdown.core import errors

from .test_aws import TestCase


class TestKeypair(TestCase):

    def test_no_change(self):
        self.responses.add("POST", 'https://ec2.eu-west-1.amazonaws.com/', body=textwrap.dedent("""
            <DescribeKeyPairsResponse xmlns="http://ec2.amazonaws.com/doc/2014-10-01/">
                <requestId>59dbff89-35bd-4eac-99ed-be587EXAMPLE</requestId>
                <keySet>
                  <item>
                     <keyName>my-key-pair</keyName>
                     <keyFingerprint>1f:51:ae:28:bf:89:e9:d8:1f:25:5d:37:2d:7d:b8:ca:9f:f5:f1:6f</keyFingerprint>
                  </item>
               </keySet>
            </DescribeKeyPairsResponse>
        """))

        self.aws.add_keypair(name='my-key-pair')
        self.assertRaises(errors.NothingChanged, self.runner.apply)

    def test_create(self):
        self.responses.add("POST", 'https://ec2.eu-west-1.amazonaws.com/', body=textwrap.dedent("""
            <DescribeKeyPairsResponse xmlns="http://ec2.amazonaws.com/doc/2014-10-01/">
                <requestId>59dbff89-35bd-4eac-99ed-be587EXAMPLE</requestId>
                <keySet/>
            </DescribeKeyPairsResponse>
        """), expires=1)

        self.responses.add("POST", 'https://ec2.eu-west-1.amazonaws.com/', body=textwrap.dedent("""
            <ImportKeyPairResponse xmlns="http://ec2.amazonaws.com/doc/2014-10-01/">
                <requestId>7a62c49f-347e-4fc4-9331-6e8eEXAMPLE</requestId>
                <keyName>my-key-pair</keyName>
                <keyFingerprint>1f:51:ae:28:bf:89:e9:d8:1f:25:5d:37:2d:7d:b8:ca:9f:f5:f1:6f</keyFingerprint>
            </ImportKeyPairResponse>
        """), expires=1)

        self.responses.add("POST", 'https://ec2.eu-west-1.amazonaws.com/', body=textwrap.dedent("""
            <DescribeKeyPairsResponse xmlns="http://ec2.amazonaws.com/doc/2014-10-01/">
                <requestId>59dbff89-35bd-4eac-99ed-be587EXAMPLE</requestId>
                <keySet>
                  <item>
                     <keyName>my-key-pair</keyName>
                     <keyFingerprint>1f:51:ae:28:bf:89:e9:d8:1f:25:5d:37:2d:7d:b8:ca:9f:f5:f1:6f</keyFingerprint>
                  </item>
               </keySet>
            </DescribeKeyPairsResponse>
        """))

        self.aws.add_keypair(name='my-key-pair', public_key="")
        self.runner.apply()
