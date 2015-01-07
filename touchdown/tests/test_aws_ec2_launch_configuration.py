import textwrap

from touchdown.core import errors

from .test_aws import TestCase


class TestLaunchConfiguration(TestCase):

    def test_no_change(self):
        self.responses.add_fixture("POST", 'https://autoscaling.eu-west-1.amazonaws.com/', 'aws_ec2_launch_configuration_describe')

        lc = self.aws.add_launch_configuration(name='my-test-lc', image='ami-514ac838')
        self.assertRaises(errors.NothingChanged, self.runner.apply)

        self.assertEqual(
            self.runner.get_target(lc).object['LaunchConfigurationName'],
            "my-test-lc",
        )

    def test_create(self):
        self.responses.add_fixture("POST", 'https://autoscaling.eu-west-1.amazonaws.com/', 'aws_ec2_launch_configuration_describe_404', expires=1)
        self.responses.add_fixture("POST", 'https://autoscaling.eu-west-1.amazonaws.com/', 'aws_ec2_launch_configuration_create', expires=1)
        self.responses.add_fixture("POST", 'https://autoscaling.eu-west-1.amazonaws.com/', 'aws_ec2_launch_configuration_describe')

        lc = self.aws.add_launch_configuration(name='my-test-lc', image='ami-514ac838')
        self.runner.apply()

        self.assertEqual(
            self.runner.get_target(lc).object['LaunchConfigurationName'],
            "my-test-lc",
        )
