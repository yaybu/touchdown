# Copyright 2015 Isotoma Limited
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

import unittest

from touchdown.aws.ec2.ami import Describe
from touchdown.aws.session import session


class TestMetadata(unittest.TestCase):

    def test_waiter_waity_enough(self):
        waiter = session.get_waiter_model('ec2', api_version=Describe.api_version)
        self.assertEqual(waiter.get_waiter('ImageAvailable').max_attempts, 160)
