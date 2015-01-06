import textwrap

from touchdown.core import errors

from .test_aws import TestCase


class TestLaunchConfiguration(TestCase):

    def test_no_change(self):
        self.responses.add("POST", 'https://autoscaling.eu-west-1.amazonaws.com/', body=textwrap.dedent("""
            <DescribeLaunchConfigurationsResponse xmlns="http://autoscaling.amazonaws.com/doc/2011-01-01/">
              <DescribeLaunchConfigurationsResult>
                <LaunchConfigurations>
                  <member>
                    <AssociatePublicIpAddress>true</AssociatePublicIpAddress>
                    <SecurityGroups/>
                    <PlacementTenancy>dedicated</PlacementTenancy>
                    <CreatedTime>2013-01-21T23:04:42.200Z</CreatedTime>
                    <KernelId/>
                    <LaunchConfigurationName>my-test-lc</LaunchConfigurationName>
                    <UserData/>
                    <InstanceType>m1.small</InstanceType>
                    <LaunchConfigurationARN>arn:aws:autoscaling:us-east-1:803981987763:launchConfiguration:
                    9dbbbf87-6141-428a-a409-0752edbe6cad:launchConfigurationName/my-test-lc</LaunchConfigurationARN>
                    <BlockDeviceMappings/>
                    <ImageId>ami-514ac838</ImageId>
                    <KeyName/>
                    <RamdiskId/>
                    <InstanceMonitoring>
                      <Enabled>true</Enabled>
                    </InstanceMonitoring>
                    <EbsOptimized>false</EbsOptimized>
                  </member>
                </LaunchConfigurations>
              </DescribeLaunchConfigurationsResult>
              <ResponseMetadata>
                <RequestId>d05a22f8-b690-11e2-bf8e-2113fEXAMPLE</RequestId>
              </ResponseMetadata>
            </DescribeLaunchConfigurationsResponse>
        """))

        lc = self.aws.add_launch_configuration(name='my-test-lc', image='ami-514ac838')
        self.assertRaises(errors.NothingChanged, self.runner.apply)

        self.assertEqual(
            self.runner.get_target(lc).object['LaunchConfigurationName'],
            "my-test-lc",
        )

    def test_create(self):
        self.responses.add("POST", 'https://autoscaling.eu-west-1.amazonaws.com/', body=textwrap.dedent("""
            <DescribeLaunchConfigurationsResponse xmlns="http://autoscaling.amazonaws.com/doc/2011-01-01/">
              <DescribeLaunchConfigurationsResult>
                <LaunchConfigurations/>
              </DescribeLaunchConfigurationsResult>
              <ResponseMetadata>
                <RequestId>d05a22f8-b690-11e2-bf8e-2113fEXAMPLE</RequestId>
              </ResponseMetadata>
            </DescribeLaunchConfigurationsResponse>
        """), expires=1)

        self.responses.add("POST", 'https://autoscaling.eu-west-1.amazonaws.com/', body=textwrap.dedent("""
            <CreateLaunchConfigurationResponse xmlns="http://autoscaling.amazonaws.com/doc/2011-01-01/">
            <ResponseMetadata>
               <RequestId>7c6e177f-f082-11e1-ac58-3714bEXAMPLE</RequestId>
            </ResponseMetadata>
            </CreateLaunchConfigurationResponse>
        """), expires=1)

        self.responses.add("POST", 'https://autoscaling.eu-west-1.amazonaws.com/', body=textwrap.dedent("""
            <DescribeLaunchConfigurationsResponse xmlns="http://autoscaling.amazonaws.com/doc/2011-01-01/">
              <DescribeLaunchConfigurationsResult>
                <LaunchConfigurations>
                  <member>
                    <AssociatePublicIpAddress>true</AssociatePublicIpAddress>
                    <SecurityGroups/>
                    <PlacementTenancy>dedicated</PlacementTenancy>
                    <CreatedTime>2013-01-21T23:04:42.200Z</CreatedTime>
                    <KernelId/>
                    <LaunchConfigurationName>my-test-lc</LaunchConfigurationName>
                    <UserData/>
                    <InstanceType>m1.small</InstanceType>
                    <LaunchConfigurationARN>arn:aws:autoscaling:us-east-1:803981987763:launchConfiguration:
                    9dbbbf87-6141-428a-a409-0752edbe6cad:launchConfigurationName/my-test-lc</LaunchConfigurationARN>
                    <BlockDeviceMappings/>
                    <ImageId>ami-514ac838</ImageId>
                    <KeyName/>
                    <RamdiskId/>
                    <InstanceMonitoring>
                      <Enabled>true</Enabled>
                    </InstanceMonitoring>
                    <EbsOptimized>false</EbsOptimized>
                  </member>
                </LaunchConfigurations>
              </DescribeLaunchConfigurationsResult>
              <ResponseMetadata>
                <RequestId>d05a22f8-b690-11e2-bf8e-2113fEXAMPLE</RequestId>
              </ResponseMetadata>
            </DescribeLaunchConfigurationsResponse>
        """))

        lc = self.aws.add_launch_configuration(name='my-test-lc', image='ami-514ac838')
        self.runner.apply()

        self.assertEqual(
            self.runner.get_target(lc).object['LaunchConfigurationName'],
            "my-test-lc",
        )
