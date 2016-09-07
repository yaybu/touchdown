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

import base64
import tarfile

from cryptography.fernet import Fernet
from six import BytesIO

from touchdown.core import argument
from touchdown.core.plan import Plan
from touchdown.interfaces import File

from .key import Key


def encrypt(aes_key, aes_key_protected, blob):
    io = BytesIO()
    tar = tarfile.open(name='xxxx', fileobj=io, mode='w')

    ti = tarfile.TarInfo('key')
    ti.size = len(aes_key_protected)
    tar.addfile(ti, BytesIO(aes_key_protected))

    f = Fernet(base64.urlsafe_b64encode(aes_key))
    encrypted = f.encrypt(blob)

    ti = tarfile.TarInfo('blob')
    ti.size = len(encrypted)
    tar.addfile(ti, BytesIO(encrypted))

    tar.close()
    return io.getvalue()


class Wrapper(File):

    resource_name = 'cipher'

    name = argument.String()
    file = argument.Resource(File)

    key = argument.Resource(Key)


class FileIo(Plan):

    resource = Wrapper
    service_name = 'kms'
    name = 'fileio'

    signature = []

    def read(self):
        kms = self.runner.get_service(self.resource.key, 'describe')
        tar = tarfile.open(
            name='ffff',
            fileobj=BytesIO(
                self.runner.get_service(self.resource.file, 'fileio').read().read(),
            ),
            mode='r',
        )
        f = Fernet(base64.urlsafe_b64encode(kms.decrypt_data_key(tar.extractfile('key').read())))
        return BytesIO(f.decrypt(tar.extractfile('blob').read()))

    def write(self, c):
        kms = self.runner.get_service(self.resource.key, 'describe')
        aes_key, aes_key_protected = kms.create_data_key()
        fp = self.runner.get_service(self.resource.file, 'fileio')
        fp.write(encrypt(aes_key, aes_key_protected, c))
