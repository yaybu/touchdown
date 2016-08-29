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

import shutil
import tempfile

from touchdown.tests.fixtures.fixture import Fixture


class TemporaryFolder(object):

    def __enter__(self):
        self.folder = tempfile.mkdtemp()
        return self

    def __exit__(self, *args):
        shutil.rmtree(self.folder)


class TemporaryFolderFixture(Fixture):

    def __enter__(self):
        return self.workspace.add_local_folder(
            name=self.fixtures.enter_context(TemporaryFolder()).folder,
        )
