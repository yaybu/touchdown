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

from touchdown.tests.fixtures.fixture import Fixture
from touchdown.tests.fixtures.folder import TemporaryFolderFixture


class ConfigFixture(Fixture):

    def __enter__(self):
        self.folder = self.fixtures.enter_context(TemporaryFolderFixture(self.goal, self.workspace))
        self.local_file = self.folder.add_file(name='test.cfg')
        self.config_file = self.local_file.add_ini_file()
        return self.config_file
